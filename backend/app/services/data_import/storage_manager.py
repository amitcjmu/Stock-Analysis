"""
Import Storage Manager Module

Handles all database storage operations including:
- Database storage operations and CRUD
- Data persistence and retrieval
- Storage optimization and indexing
- Raw record management
"""

import logging
import uuid as uuid_pkg
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.core.logging import get_logger
from app.core.exceptions import DatabaseError
from app.models.data_import import DataImport, RawImportRecord, ImportFieldMapping

logger = get_logger(__name__)


class ImportStorageManager:
    """
    Manages database storage operations for data imports.
    """
    
    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id
        
    async def find_or_create_import(
        self, 
        import_id: uuid_pkg.UUID,
        engagement_id: str,
        user_id: str,
        filename: str,
        file_size: int,
        file_type: str,
        intended_type: str
    ) -> DataImport:
        """
        Find an existing import or create a new one.
        
        Args:
            import_id: UUID of the import
            engagement_id: Engagement ID
            user_id: User who initiated the import
            filename: Name of the imported file
            file_size: Size of the file in bytes
            file_type: MIME type of the file
            intended_type: Type of data being imported
            
        Returns:
            DataImport: The found or created import record
        """
        try:
            logger.info(f"Looking for existing import record {import_id}")
            
            existing_import_query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(existing_import_query)
            data_import = result.scalar_one_or_none()
            
            if not data_import:
                # Create new DataImport record since none exists
                logger.info(f"No existing import record found. Creating new DataImport record with ID: {import_id}")
                data_import = DataImport(
                    id=import_id,
                    client_account_id=self.client_account_id,
                    engagement_id=engagement_id,
                    import_name=f"{filename} Import",
                    import_type=intended_type,
                    description=f"Data import for {intended_type} category",
                    filename=filename,
                    file_size=file_size,
                    mime_type=file_type,
                    source_system=intended_type,  # Set source system based on intended type
                    status="pending",
                    progress_percentage=0.0,  # Initialize progress
                    total_records=0,  # Will be updated when records are stored
                    processed_records=0,
                    failed_records=0,
                    imported_by=user_id
                )
                self.db.add(data_import)
                await self.db.flush()  # Flush to get the record in the session
                logger.info(f"✅ Created new DataImport record: {data_import.id}")
            else:
                logger.info(f"✅ Found existing DataImport record: {data_import.id}")
                
            return data_import
            
        except Exception as e:
            logger.error(f"Failed to find or create import record: {e}")
            raise DatabaseError(f"Failed to find or create import record: {str(e)}")
    
    async def store_raw_records(
        self, 
        data_import: DataImport,
        file_data: List[Dict[str, Any]],
        engagement_id: str
    ) -> int:
        """
        Store raw import records in the database.
        
        Args:
            data_import: The import record to associate with
            file_data: List of raw data records
            engagement_id: Engagement ID
            
        Returns:
            int: Number of records stored
        """
        try:
            records_stored = 0
            
            if file_data:
                # Store the raw records from the CSV
                for idx, record in enumerate(file_data):
                    raw_record = RawImportRecord(
                        data_import_id=data_import.id,
                        client_account_id=self.client_account_id,
                        engagement_id=engagement_id,
                        row_number=idx + 1,
                        raw_data=record,
                        is_processed=False,
                        is_valid=True
                    )
                    self.db.add(raw_record)
                    records_stored += 1
                    
                logger.info(f"✅ Stored {records_stored} raw records for import {data_import.id}")
            
            return records_stored
            
        except Exception as e:
            logger.error(f"Failed to store raw records: {e}")
            raise DatabaseError(f"Failed to store raw records: {str(e)}")
    
    async def create_field_mappings(
        self, 
        data_import: DataImport,
        file_data: List[Dict[str, Any]],
        master_flow_id: Optional[str] = None
    ) -> int:
        """
        Create basic field mappings for the import.
        
        Args:
            data_import: The import record
            file_data: List of raw data records
            master_flow_id: Optional master flow ID to link to
            
        Returns:
            int: Number of field mappings created
        """
        try:
            mappings_created = 0
            
            if file_data:
                # Create basic field mappings for each column
                sample_record = file_data[0]
                for field_name in sample_record.keys():
                    field_mapping = ImportFieldMapping(
                        data_import_id=data_import.id,
                        client_account_id=self.client_account_id,
                        source_field=field_name,
                        target_field=field_name.lower().replace(' ', '_'),
                        confidence_score=0.8,  # Default confidence
                        match_type="direct",
                        status="suggested",
                        master_flow_id=master_flow_id
                    )
                    self.db.add(field_mapping)
                    mappings_created += 1
                    
                logger.info(f"✅ Created {mappings_created} field mappings for import {data_import.id}")
            
            return mappings_created
            
        except Exception as e:
            logger.error(f"Failed to create field mappings: {e}")
            raise DatabaseError(f"Failed to create field mappings: {str(e)}")
    
    async def update_import_status(
        self, 
        data_import: DataImport,
        status: str,
        total_records: int = 0,
        processed_records: int = 0,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the import status and record counts.
        
        Args:
            data_import: The import record to update
            status: New status for the import
            total_records: Total number of records
            processed_records: Number of processed records
        """
        try:
            data_import.status = status
            data_import.total_records = total_records
            data_import.processed_records = processed_records
            
            # Calculate and update progress percentage
            if total_records > 0:
                data_import.progress_percentage = (processed_records / total_records) * 100
            else:
                data_import.progress_percentage = 0.0
            
            if status == "completed":
                data_import.completed_at = datetime.utcnow()
                data_import.progress_percentage = 100.0
            elif status == "discovery_initiated":
                data_import.progress_percentage = 10.0  # Discovery flow started
            elif status in ["failed", "discovery_failed"]:
                data_import.error_message = error_message
                data_import.error_details = error_details
                # Keep existing progress percentage on failure
                
            logger.info(f"✅ Updated import {data_import.id} status to {status} (progress: {data_import.progress_percentage}%)")
            
        except Exception as e:
            logger.error(f"Failed to update import status: {e}")
            raise DatabaseError(f"Failed to update import status: {str(e)}")
    
    async def update_field_mappings_with_flow(
        self, 
        data_import_id: uuid_pkg.UUID,
        master_flow_id: str
    ) -> None:
        """
        Update field mappings with the master flow ID after flow creation.
        
        Args:
            data_import_id: ID of the data import
            master_flow_id: ID of the master flow to link to
        """
        try:
            # Verify the master flow exists first
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            
            check_query = select(CrewAIFlowStateExtensions.flow_id).where(
                CrewAIFlowStateExtensions.flow_id == master_flow_id,
                CrewAIFlowStateExtensions.client_account_id == self.client_account_id
            )
            result = await self.db.execute(check_query)
            master_flow_exists = result.scalar() is not None
            
            if master_flow_exists:
                update_stmt = update(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_import_id
                ).values(master_flow_id=master_flow_id, updated_at=func.now())
                await self.db.execute(update_stmt)
                logger.info(f"✅ Updated field mappings with master_flow_id: {master_flow_id}")
            else:
                logger.warning(f"⚠️ Master flow {master_flow_id} not found - skipping field mapping update")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to update field mappings with flow ID (non-critical): {e}")
    
    async def update_data_import_with_flow(
        self, 
        data_import_id: uuid_pkg.UUID,
        master_flow_id: str
    ) -> bool:
        """
        Update DataImport record with master flow ID after flow creation.
        
        Args:
            data_import_id: ID of the data import
            master_flow_id: ID of the master flow to link to
            
        Returns:
            bool: True if update succeeded, False otherwise
        """
        try:
            # Verify the master flow exists first
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            
            check_query = select(CrewAIFlowStateExtensions.flow_id).where(
                CrewAIFlowStateExtensions.flow_id == master_flow_id,
                CrewAIFlowStateExtensions.client_account_id == self.client_account_id
            )
            result = await self.db.execute(check_query)
            master_flow_exists = result.scalar() is not None
            
            if master_flow_exists:
                # Update the DataImport record with master_flow_id
                update_stmt = update(DataImport).where(
                    DataImport.id == data_import_id,
                    DataImport.client_account_id == self.client_account_id
                ).values(
                    master_flow_id=master_flow_id, 
                    updated_at=func.now()
                )
                result = await self.db.execute(update_stmt)
                
                if result.rowcount > 0:
                    logger.info(f"✅ Updated DataImport {data_import_id} with master_flow_id: {master_flow_id}")
                    return True
                else:
                    logger.warning(f"⚠️ No DataImport record found with ID {data_import_id} for update")
                    return False
            else:
                # Try waiting a bit and checking again - race condition mitigation
                logger.warning(f"⚠️ Master flow {master_flow_id} not found on first check, waiting 1 second and retrying...")
                import asyncio
                await asyncio.sleep(1)
                
                # Check again
                result = await self.db.execute(check_query)
                master_flow_exists = result.scalar() is not None
                
                if master_flow_exists:
                    logger.info(f"✅ Master flow {master_flow_id} found on retry - proceeding with update")
                    update_stmt = update(DataImport).where(
                        DataImport.id == data_import_id,
                        DataImport.client_account_id == self.client_account_id
                    ).values(
                        master_flow_id=master_flow_id, 
                        updated_at=func.now()
                    )
                    result = await self.db.execute(update_stmt)
                    
                    if result.rowcount > 0:
                        logger.info(f"✅ Updated DataImport {data_import_id} with master_flow_id: {master_flow_id} (after retry)")
                        return True
                    else:
                        logger.warning(f"⚠️ No DataImport record found with ID {data_import_id} for update (after retry)")
                        return False
                else:
                    logger.error(f"❌ Master flow {master_flow_id} still not found after retry - skipping DataImport update")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update DataImport with flow ID: {e}")
            return False
    
    async def update_raw_import_records_with_flow(
        self, 
        data_import_id: uuid_pkg.UUID,
        master_flow_id: str
    ) -> int:
        """
        Update RawImportRecord records with master flow ID after flow creation.
        
        Args:
            data_import_id: ID of the data import
            master_flow_id: ID of the master flow to link to
            
        Returns:
            int: Number of records updated
        """
        try:
            # Verify the master flow exists first
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            
            check_query = select(CrewAIFlowStateExtensions.flow_id).where(
                CrewAIFlowStateExtensions.flow_id == master_flow_id,
                CrewAIFlowStateExtensions.client_account_id == self.client_account_id
            )
            result = await self.db.execute(check_query)
            master_flow_exists = result.scalar() is not None
            
            if master_flow_exists:
                # Update all RawImportRecord records for this data import
                update_stmt = update(RawImportRecord).where(
                    RawImportRecord.data_import_id == data_import_id,
                    RawImportRecord.client_account_id == self.client_account_id
                ).values(
                    master_flow_id=master_flow_id
                )
                result = await self.db.execute(update_stmt)
                
                updated_count = result.rowcount
                logger.info(f"✅ Updated {updated_count} RawImportRecord records with master_flow_id: {master_flow_id}")
                return updated_count
            else:
                logger.warning(f"⚠️ Master flow {master_flow_id} not found - skipping RawImportRecord update")
                return 0
                
        except Exception as e:
            logger.error(f"❌ Failed to update RawImportRecord records with flow ID: {e}")
            return 0
    
    async def update_all_records_with_flow(
        self, 
        data_import_id: uuid_pkg.UUID,
        master_flow_id: str
    ) -> Dict[str, Any]:
        """
        Update all related records (DataImport, RawImportRecord, ImportFieldMapping) 
        with master flow ID using a fresh database session.
        
        This method uses a fresh database session to avoid transaction isolation issues
        where the master flow was committed in a different transaction.
        
        Args:
            data_import_id: ID of the data import
            master_flow_id: ID of the master flow to link to
            
        Returns:
            Dict containing update results for each table
        """
        try:
            logger.info(f"🔗 Starting comprehensive master_flow_id linkage for data_import_id: {data_import_id}")
            
            # Use a fresh database session to avoid transaction isolation issues
            from app.core.database import AsyncSessionLocal
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            
            async with AsyncSessionLocal() as fresh_db:
                # Get the master flow record to extract the PRIMARY KEY (id)
                # CRITICAL: Foreign keys reference crewai_flow_state_extensions.id (PK), not flow_id
                check_query = select(CrewAIFlowStateExtensions.id, CrewAIFlowStateExtensions.flow_id).where(
                    CrewAIFlowStateExtensions.flow_id == master_flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id
                )
                result = await fresh_db.execute(check_query)
                master_flow_record = result.first()
            
                if not master_flow_record:
                    error_msg = f"Master flow {master_flow_id} not found - aborting all updates"
                    logger.warning(f"⚠️ {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "data_import_updated": False,
                        "raw_import_records_updated": 0,
                        "field_mappings_updated": False
                    }
                
                # The foreign keys actually reference flow_id column, not the primary key id
                # Just use the flow_id directly since that's what the FK constraint references
                logger.info(f"✅ Master flow {master_flow_id} found in database")
                
                # Initialize results tracking
                results = {
                    "success": True,
                    "data_import_updated": False,
                    "raw_import_records_updated": 0,
                    "field_mappings_updated": False,
                    "error": None
                }
            
                # Update DataImport record using the PRIMARY KEY
                try:
                    update_stmt = update(DataImport).where(
                        DataImport.id == data_import_id,
                        DataImport.client_account_id == self.client_account_id
                    ).values(
                        master_flow_id=master_flow_id,  # Use the flow_id directly as that's what the FK references
                        updated_at=func.now()
                    )
                    result = await fresh_db.execute(update_stmt)
                    results["data_import_updated"] = result.rowcount > 0
                    
                    if results["data_import_updated"]:
                        logger.info(f"✅ Updated DataImport record with master_flow_id: {master_flow_id}")
                    else:
                        logger.warning(f"⚠️ No DataImport record found with ID {data_import_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to update DataImport record: {e}")
                    results["success"] = False
                    results["error"] = f"DataImport update failed: {str(e)}"
            
                # Update RawImportRecord records
                try:
                    update_stmt = update(RawImportRecord).where(
                        RawImportRecord.data_import_id == data_import_id,
                        RawImportRecord.client_account_id == self.client_account_id
                    ).values(
                        master_flow_id=master_flow_id  # Use the flow_id directly as that's what the FK references
                    )
                    result = await fresh_db.execute(update_stmt)
                    results["raw_import_records_updated"] = result.rowcount
                    
                    if results["raw_import_records_updated"] > 0:
                        logger.info(f"✅ Updated {results['raw_import_records_updated']} RawImportRecord records with master_flow_id: {master_flow_id}")
                    else:
                        logger.warning(f"⚠️ No RawImportRecord records found for data_import_id {data_import_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to update RawImportRecord records: {e}")
                    results["success"] = False
                    results["error"] = f"RawImportRecord update failed: {str(e)}"
            
                # Update ImportFieldMapping records
                try:
                    update_stmt = update(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == data_import_id
                    ).values(master_flow_id=master_flow_id, updated_at=func.now())  # Use the flow_id directly as that's what the FK references
                    result = await fresh_db.execute(update_stmt)
                    results["field_mappings_updated"] = result.rowcount > 0
                    
                    if results["field_mappings_updated"]:
                        logger.info(f"✅ Updated ImportFieldMapping records with master_flow_id: {master_flow_id}")
                    else:
                        logger.warning(f"⚠️ No ImportFieldMapping records found for data_import_id {data_import_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to update ImportFieldMapping records: {e}")
                    results["success"] = False
                    results["error"] = f"ImportFieldMapping update failed: {str(e)}"
            
                # Commit all updates
                await fresh_db.commit()
                
                # Log comprehensive results
                if results["success"]:
                    logger.info(f"🎉 Successfully completed master_flow_id linkage for data_import_id: {data_import_id}")
                    logger.info(f"📊 Results: DataImport={results['data_import_updated']}, RawRecords={results['raw_import_records_updated']}, FieldMappings={results['field_mappings_updated']}")
                else:
                    logger.error(f"💥 Master_flow_id linkage failed for data_import_id: {data_import_id} - Error: {results['error']}")
                
                return results
                
        except Exception as e:
            error_msg = f"Comprehensive master_flow_id linkage failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "data_import_updated": False,
                "raw_import_records_updated": 0,
                "field_mappings_updated": False
            }
    
    async def get_import_by_id(self, import_id: str) -> Optional[DataImport]:
        """
        Retrieve a data import by its ID.
        
        Args:
            import_id: ID of the import to retrieve
            
        Returns:
            DataImport or None if not found
        """
        try:
            import_query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(import_query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to retrieve import {import_id}: {e}")
            return None
    
    async def get_raw_records(
        self, 
        data_import_id: uuid_pkg.UUID,
        limit: int = 1000
    ) -> List[RawImportRecord]:
        """
        Retrieve raw import records for a data import.
        
        Args:
            data_import_id: ID of the data import
            limit: Maximum number of records to retrieve
            
        Returns:
            List of RawImportRecord objects
        """
        try:
            records_query = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import_id)
                .order_by(RawImportRecord.row_number)
                .limit(limit)
            )
            
            result = await self.db.execute(records_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to retrieve raw records: {e}")
            return []
    
    async def update_raw_records_with_cleansed_data(
        self,
        data_import_id: uuid_pkg.UUID,
        cleansed_data: List[Dict[str, Any]],
        validation_results: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Update raw import records with cleansed data and validation results.
        
        Args:
            data_import_id: ID of the data import
            cleansed_data: List of cleansed data records
            validation_results: Optional validation results from data validation phase
            
        Returns:
            Number of records updated
        """
        try:
            # Get existing raw records
            raw_records = await self.get_raw_records(data_import_id, limit=10000)
            
            if not raw_records:
                logger.warning(f"No raw records found for data_import_id {data_import_id}")
                return 0
            
            updated_count = 0
            
            # Match cleansed data to raw records by index
            for idx, raw_record in enumerate(raw_records):
                if idx < len(cleansed_data):
                    # Update the raw record with cleansed data
                    raw_record.cleansed_data = cleansed_data[idx]
                    raw_record.is_processed = True
                    raw_record.processed_at = datetime.utcnow()
                    
                    # Add validation results if available
                    if validation_results:
                        raw_record.validation_errors = validation_results.get("validation_errors", {})
                        raw_record.processing_notes = validation_results.get("summary", "Data cleansed and validated")
                        raw_record.is_valid = validation_results.get("is_valid", True)
                    
                    updated_count += 1
            
            # Flush changes to database
            await self.db.flush()
            
            logger.info(f"✅ Updated {updated_count} raw records with cleansed data")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to update raw records with cleansed data: {e}")
            return 0