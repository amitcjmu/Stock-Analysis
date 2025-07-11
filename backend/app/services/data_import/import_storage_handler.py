"""
Import Storage Handler - Modular Composition Service

This is the main orchestration service that composes all the modular components
to handle data import operations. It maintains all existing functionality
while providing a clean, modular architecture.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.core.exceptions import DataImportError, ValidationError as AppValidationError
from app.schemas.data_import_schemas import StoreImportRequest

from .import_validator import ImportValidator
from .storage_manager import ImportStorageManager
from .flow_trigger_service import FlowTriggerService
from .transaction_manager import ImportTransactionManager
from .background_execution_service import BackgroundExecutionService
from .response_builder import ImportResponseBuilder, ImportStorageResponse

logger = get_logger(__name__)


class ImportStorageHandler:
    """
    Main orchestration service for data import operations.
    
    This service composes all modular components to provide a unified interface
    for data import handling while maintaining clean separation of concerns.
    """
    
    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id
        
        # Initialize all modular components
        self.validator = ImportValidator(db, client_account_id)
        self.storage_manager = ImportStorageManager(db, client_account_id)
        self.flow_trigger = FlowTriggerService(db, client_account_id)
        self.transaction_manager = ImportTransactionManager(db)
        self.background_service = BackgroundExecutionService(db, client_account_id)
        self.response_builder = ImportResponseBuilder()
        
    async def handle_import(
        self,
        store_request: StoreImportRequest,
        context: RequestContext
    ) -> ImportStorageResponse:
        """
        Handle the complete data import process.
        
        This method orchestrates all the modular components to:
        1. Validate the import request and check for conflicts
        2. Store the data in the database
        3. Create and trigger discovery flows
        4. Handle background execution
        5. Return appropriate responses
        
        Args:
            store_request: The import request containing data and metadata
            context: Request context with client/engagement information
            
        Returns:
            ImportStorageResponse: The response indicating success or failure
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract data from request
            file_data = store_request.file_data
            filename = store_request.metadata.filename
            file_size = store_request.metadata.size
            file_type = store_request.metadata.type
            intended_type = store_request.upload_context.intended_type
            import_validation_id = store_request.upload_context.get_validation_id()
            
            logger.info(f"🔄 Starting data import handling for session: {import_validation_id}")
            logger.info(f"🔍 File data count: {len(file_data) if file_data else 0}")
            
            # Step 1: Validate context and import request
            await self.validator.validate_import_context(context)
            import_uuid = await self.validator.validate_import_id(import_validation_id)
            
            # Step 2: Check for existing incomplete discovery flows
            existing_flow_validation = await self.validator.validate_no_incomplete_discovery_flow(
                context.client_account_id,
                context.engagement_id
            )
            
            if not existing_flow_validation["can_proceed"]:
                return self.response_builder.conflict_response(
                    conflict_message=existing_flow_validation["message"],
                    existing_flow=existing_flow_validation.get("existing_flow"),
                    recommendations=existing_flow_validation.get("recommendations")
                )
            
            # Step 3: Validate import data
            data_validation = await self.validator.validate_import_data(file_data)
            if not data_validation["is_valid"]:
                return self.response_builder.validation_error_response(
                    validation_message=f"Data validation failed: {'; '.join(data_validation['issues'])}",
                    details=data_validation
                )
            
            # Step 4: Execute import within atomic transaction
            async with self.transaction_manager.transaction():
                # Find or create the import record
                data_import = await self.storage_manager.find_or_create_import(
                    import_id=import_uuid,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id,
                    filename=filename,
                    file_size=file_size,
                    file_type=file_type,
                    intended_type=intended_type
                )
                
                # Store raw records
                records_stored = await self.storage_manager.store_raw_records(
                    data_import=data_import,
                    file_data=file_data,
                    engagement_id=context.engagement_id
                )
                
                # Create basic field mappings
                await self.storage_manager.create_field_mappings(
                    data_import=data_import,
                    file_data=file_data
                )
                
                # Update import status to processing
                await self.storage_manager.update_import_status(
                    data_import=data_import,
                    status="processing",
                    total_records=records_stored,
                    processed_records=records_stored
                )
                
                # Step 5: Create discovery flow atomically
                flow_id = None
                flow_success = False
                flow_error_message = None
                
                try:
                    flow_id = await self.flow_trigger.trigger_discovery_flow_atomic(
                        data_import_id=str(data_import.id),
                        engagement_id=context.engagement_id,
                        user_id=context.user_id,
                        file_data=file_data,
                        context=context
                    )
                    
                    if flow_id:
                        flow_success = True
                        logger.info(f"✅ Discovery flow created successfully: {flow_id}")
                    else:
                        flow_error_message = "Discovery Flow initialization failed"
                        logger.error("❌ Discovery flow creation failed - no flow_id returned")
                        
                except Exception as flow_error:
                    logger.error(f"❌ Discovery flow creation failed: {flow_error}")
                    flow_error_message = f"Discovery Flow failed: {str(flow_error)}"
                
                # Step 6: Update final import status
                if flow_success:
                    await self.storage_manager.update_import_status(
                        data_import=data_import,
                        status="discovery_initiated"
                    )
                else:
                    await self.storage_manager.update_import_status(
                        data_import=data_import,
                        status="discovery_failed"
                    )
                
                # Transaction will be committed automatically by context manager
                
            # Step 7: Post-commit operations
            if flow_success and flow_id:
                # Update field mappings with flow ID
                await self.storage_manager.update_field_mappings_with_flow(
                    data_import_id=data_import.id,
                    master_flow_id=flow_id
                )
                
                # Start background flow execution
                await self.background_service.start_background_flow_execution(
                    flow_id=flow_id,
                    file_data=file_data,
                    context=context
                )
            
            # Step 8: Build and return response
            if flow_success:
                return self.response_builder.success_response(
                    data_import_id=str(data_import.id),
                    flow_id=flow_id,
                    records_stored=records_stored,
                    message=f"Successfully stored {records_stored} records and initiated Discovery Flow"
                )
            else:
                return self.response_builder.partial_success_response(
                    data_import_id=str(data_import.id),
                    records_stored=records_stored,
                    flow_error=flow_error_message,
                    flow_id=flow_id
                )
                
        except AppValidationError as e:
            logger.error(f"❌ Validation error: {e.message}")
            return self.response_builder.validation_error_response(
                validation_message=e.message,
                field=getattr(e, 'field', None),
                details=getattr(e, 'details', None)
            )
            
        except Exception as e:
            logger.error(f"❌ Import handling failed: {e}")
            return self.response_builder.error_response(
                error_message=f"Failed to handle import: {str(e)}"
            )
    
    async def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an import operation.
        
        Args:
            import_id: ID of the import to check
            
        Returns:
            Dict containing import status information
        """
        try:
            data_import = await self.storage_manager.get_import_by_id(import_id)
            
            if not data_import:
                return None
            
            return {
                "import_id": str(data_import.id),
                "status": data_import.status,
                "filename": data_import.filename,
                "total_records": data_import.total_records,
                "processed_records": data_import.processed_records,
                "created_at": data_import.created_at.isoformat() if data_import.created_at else None,
                "completed_at": data_import.completed_at.isoformat() if data_import.completed_at else None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get import status: {e}")
            return None
    
    async def get_import_data(self, import_id: str, limit: int = 1000) -> Optional[Dict[str, Any]]:
        """
        Get the data for an import operation.
        
        Args:
            import_id: ID of the import
            limit: Maximum number of records to return
            
        Returns:
            Dict containing import data
        """
        try:
            data_import = await self.storage_manager.get_import_by_id(import_id)
            
            if not data_import:
                return None
            
            raw_records = await self.storage_manager.get_raw_records(
                data_import_id=data_import.id,
                limit=limit
            )
            
            return {
                "import_metadata": self.response_builder.format_import_metadata(
                    data_import=data_import,
                    records_count=len(raw_records)
                ),
                "data": [record.raw_data for record in raw_records],
                "total_records": data_import.total_records,
                "limited_records": len(raw_records) >= limit
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get import data: {e}")
            return None
    
    async def cancel_import(self, import_id: str, context: RequestContext) -> bool:
        """
        Cancel an import operation and its associated flows.
        
        Args:
            import_id: ID of the import to cancel
            context: Request context
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            data_import = await self.storage_manager.get_import_by_id(import_id)
            
            if not data_import:
                logger.warning(f"Import {import_id} not found for cancellation")
                return False
            
            # Update import status
            await self.storage_manager.update_import_status(
                data_import=data_import,
                status="cancelled"
            )
            
            # If there's an associated flow, cancel it
            # Note: We'd need to track flow IDs in the import record for this
            # For now, we'll just update the import status
            
            logger.info(f"✅ Import {import_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel import: {e}")
            return False
    
    async def retry_failed_import(
        self,
        import_id: str,
        context: RequestContext
    ) -> Optional[ImportStorageResponse]:
        """
        Retry a failed import operation.
        
        Args:
            import_id: ID of the import to retry
            context: Request context
            
        Returns:
            ImportStorageResponse or None
        """
        try:
            data_import = await self.storage_manager.get_import_by_id(import_id)
            
            if not data_import:
                return None
            
            if data_import.status not in ["failed", "discovery_failed"]:
                return self.response_builder.error_response(
                    error_message=f"Import {import_id} is not in a failed state (current: {data_import.status})"
                )
            
            # Get the original data
            raw_records = await self.storage_manager.get_raw_records(data_import.id)
            file_data = [record.raw_data for record in raw_records]
            
            # Retry the flow creation
            try:
                flow_id = await self.flow_trigger.trigger_discovery_flow_atomic(
                    data_import_id=str(data_import.id),
                    engagement_id=context.engagement_id,
                    user_id=context.user_id,
                    file_data=file_data,
                    context=context
                )
                
                if flow_id:
                    await self.storage_manager.update_import_status(
                        data_import=data_import,
                        status="discovery_initiated"
                    )
                    
                    # Start background execution
                    await self.background_service.start_background_flow_execution(
                        flow_id=flow_id,
                        file_data=file_data,
                        context=context
                    )
                    
                    return self.response_builder.success_response(
                        data_import_id=str(data_import.id),
                        flow_id=flow_id,
                        records_stored=len(file_data),
                        message="Import retry successful - Discovery Flow initiated"
                    )
                else:
                    return self.response_builder.error_response(
                        error_message="Import retry failed - could not create discovery flow"
                    )
                    
            except Exception as retry_error:
                logger.error(f"❌ Import retry failed: {retry_error}")
                return self.response_builder.error_response(
                    error_message=f"Import retry failed: {str(retry_error)}"
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to retry import: {e}")
            return self.response_builder.error_response(
                error_message=f"Failed to retry import: {str(e)}"
            )
    
    async def get_latest_import_data(self, context: RequestContext) -> Optional[Dict[str, Any]]:
        """
        Get the latest import data for the current context.
        
        Args:
            context: Request context with client and engagement information
            
        Returns:
            Dict containing import data and metadata, or None if not found
        """
        try:
            # Find the latest import for this context
            from sqlalchemy import select, and_
            import uuid as uuid_pkg
            
            # Convert context IDs to UUIDs for database query
            try:
                client_uuid = uuid_pkg.UUID(context.client_account_id)
                engagement_uuid = uuid_pkg.UUID(context.engagement_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid UUID format in context: client={context.client_account_id}, engagement={context.engagement_id}")
                return None
            
            # Query for latest import
            from app.models.data_import import DataImport
            latest_import_query = select(DataImport).where(
                and_(
                    DataImport.client_account_id == client_uuid,
                    DataImport.engagement_id == engagement_uuid
                )
            ).order_by(DataImport.created_at.desc()).limit(1)
            
            result = await self.db.execute(latest_import_query)
            latest_import = result.scalar_one_or_none()
            
            if not latest_import:
                return None
            
            # Get raw records for the import
            raw_records = await self.storage_manager.get_raw_records(
                data_import_id=latest_import.id,
                limit=1000  # Limit for performance
            )
            
            return {
                "import_metadata": self.response_builder.format_import_metadata(
                    data_import=latest_import,
                    records_count=len(raw_records)
                ),
                "data": [record.raw_data for record in raw_records],
                "total_records": latest_import.total_records,
                "limited_records": len(raw_records) >= 1000
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get latest import data: {e}")
            return None