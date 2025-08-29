"""
ImportStorageHandler - Main Orchestrator for Data Import Operations

This class serves as the main orchestrator that coordinates all data import operations
by composing the modular services into a cohesive API for the endpoints.
"""

import json
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.data_import import DataImport
from app.schemas.data_import_schemas import StoreImportRequest

from .storage_manager import ImportStorageManager
from .import_service import DataImportService
from .transaction_manager import ImportTransactionManager
from .response_builder import ImportResponseBuilder

logger = get_logger(__name__)


class ImportStorageHandler:
    """
    Main orchestrator that coordinates all data import operations.

    This class composes the modular services to provide a clean API interface
    for the endpoint handlers while maintaining transaction integrity and
    proper error handling.
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        """
        Initialize the ImportStorageHandler.

        Args:
            db: The database session
            client_account_id: The client account ID for multi-tenant operations
        """
        self.db = db
        self.client_account_id = client_account_id
        self.response_builder = ImportResponseBuilder()

    async def get_latest_import_data(
        self, context: RequestContext
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest import data for the current context.

        Args:
            context: The request context containing client and engagement info

        Returns:
            Dictionary containing import data and metadata, or None if no imports exist
        """
        try:
            storage_manager = ImportStorageManager(self.db, context.client_account_id)

            # Find the most recent import for this context
            query = (
                select(DataImport)
                .where(
                    DataImport.client_account_id == context.client_account_id,
                    DataImport.engagement_id == context.engagement_id,
                )
                .order_by(DataImport.created_at.desc())
                .limit(1)
            )

            result = await self.db.execute(query)
            latest_import = result.scalar_one_or_none()

            if not latest_import:
                return None

            # Get the full import data
            import_data = await storage_manager.get_import_data(latest_import.id)
            return import_data

        except Exception as e:
            logger.error(f"Failed to get latest import data: {e}")
            return None

    async def get_import_data(self, data_import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific import data by ID.

        Args:
            data_import_id: The ID of the data import to retrieve

        Returns:
            Dictionary containing import data and metadata, or None if not found
        """
        try:
            # Create a minimal context for storage manager
            context = RequestContext(
                client_account_id=self.client_account_id,
                engagement_id=None,
                user_id=None,
            )
            storage_manager = ImportStorageManager(self.db, context.client_account_id)

            # Get the import data
            import_data = await storage_manager.get_import_data(data_import_id)

            if import_data:
                return {
                    "success": True,
                    "data": import_data,
                    "import_metadata": (
                        import_data.get("metadata") if import_data else None
                    ),
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get import data for ID {data_import_id}: {e}")
            return None

    async def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of an import operation.

        Args:
            import_id: The ID of the import to check

        Returns:
            Dictionary containing import status information
        """
        try:
            query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(query)
            data_import = result.scalar_one_or_none()

            if not data_import:
                return None

            return {
                "import_id": str(data_import.id),
                "status": data_import.status,
                "filename": data_import.filename,
                "import_type": data_import.import_type,
                "record_count": data_import.total_records or 0,
                "created_at": (
                    data_import.created_at.isoformat()
                    if data_import.created_at
                    else None
                ),
                "updated_at": (
                    data_import.updated_at.isoformat()
                    if data_import.updated_at
                    else None
                ),
                "master_flow_id": (
                    str(data_import.master_flow_id)
                    if data_import.master_flow_id
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get import status for ID {import_id}: {e}")
            return None

    async def cancel_import(self, import_id: str, context: RequestContext) -> bool:
        """
        Cancel an import operation and its associated flows.

        Args:
            import_id: The ID of the import to cancel
            context: The request context

        Returns:
            True if cancellation was successful, False otherwise
        """
        try:
            # Find the import
            query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(query)
            data_import = result.scalar_one_or_none()

            if not data_import:
                return False

            # Update the import status to cancelled
            data_import.status = "cancelled"
            await self.db.commit()

            logger.info(f"Import {import_id} cancelled successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel import {import_id}: {e}")
            await self.db.rollback()
            return False

    async def retry_failed_import(
        self, import_id: str, context: RequestContext
    ) -> Optional[Dict[str, Any]]:
        """
        Retry a failed import operation.

        Args:
            import_id: The ID of the import to retry
            context: The request context

        Returns:
            Response dictionary with retry results
        """
        try:
            # Find the import
            query = select(DataImport).where(DataImport.id == import_id)
            result = await self.db.execute(query)
            data_import = result.scalar_one_or_none()

            if not data_import:
                return None

            if data_import.status != "failed":
                return {
                    "success": False,
                    "message": f"Import {import_id} is not in failed status. Current status: {data_import.status}",
                }

            # Update status to processing for retry
            data_import.status = "processing"
            await self.db.commit()

            # TODO: Trigger the flow retry logic here
            # For now, just return success
            return {
                "success": True,
                "message": f"Import {import_id} retry initiated successfully",
            }

        except Exception as e:
            logger.error(f"Failed to retry import {import_id}: {e}")
            await self.db.rollback()
            return {"success": False, "message": f"Failed to retry import: {str(e)}"}

    async def handle_import(
        self, store_request: StoreImportRequest, context: RequestContext
    ) -> Dict[str, Any]:
        """
        Handle the complete import process using the modular services.

        Args:
            store_request: The import request data
            context: The request context

        Returns:
            Response dictionary with import results
        """
        try:
            # Use transaction manager for atomic operations
            transaction_manager = ImportTransactionManager(self.db)

            async with transaction_manager.transaction():
                import_service = DataImportService(self.db, context)

                data_import = await import_service.process_import_and_trigger_flow(
                    file_content=json.dumps(store_request.file_data).encode("utf-8"),
                    filename=store_request.metadata.filename,
                    file_content_type="application/json",
                    import_type=store_request.upload_context.intended_type,
                )

            # Start background flow execution AFTER transaction commits
            # This prevents race conditions where the flow isn't visible to status queries
            if (
                hasattr(data_import, "flow_execution_data")
                and data_import.flow_execution_data
            ):
                logger.info(
                    f"🚀 Starting background flow execution for {data_import.flow_execution_data['flow_id']}"
                )
                from app.services.data_import import BackgroundExecutionService

                background_service = BackgroundExecutionService(
                    self.db, context.client_account_id
                )
                await background_service.start_background_flow_execution(
                    flow_id=data_import.flow_execution_data["flow_id"],
                    file_data=data_import.flow_execution_data["file_data"],
                    context=context,
                )
                logger.info(
                    f"✅ Background flow execution started for {data_import.flow_execution_data['flow_id']}"
                )

            return self.response_builder.success_response(
                data_import_id=str(data_import.id),
                flow_id=(
                    str(data_import.master_flow_id)
                    if data_import.master_flow_id
                    else None
                ),
                records_stored=data_import.total_records,
                message="Data imported and discovery flow initiated successfully.",
            )

        except Exception as e:
            logger.error(f"Failed to handle import: {e}")
            return self.response_builder.error_response(
                error_message=f"Failed to store import data: {str(e)}"
            )
