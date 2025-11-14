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
from app.schemas.data_import_schemas import StoreImportRequest, CleansingStats
from app.services.data_import.background_execution_service import (
    BackgroundExecutionService,
    ImportProcessorBackgroundRunner,
)

from .child_flow_service import DataImportChildFlowService
from .storage_manager import ImportStorageManager

# from .import_service import DataImportService  # Currently unused
from .transaction_manager import ImportTransactionManager
from .response_builder import ImportResponseBuilder

logger = get_logger(__name__)

VALID_IMPORT_CATEGORIES = {
    "cmdb_export",
    "app_discovery",
    "infrastructure",
    "sensitive_data",
}

IMPORT_CATEGORY_ALIASES = {
    "cmdb": "cmdb_export",
    "cmdbexport": "cmdb_export",
    "cmdb_export": "cmdb_export",
    "application_discovery": "app_discovery",
    "application": "app_discovery",
    "app_discovery": "app_discovery",
    "app-discovery": "app_discovery",
    "infrastructure_assessment": "infrastructure",
    "infrastructure": "infrastructure",
    "infra": "infrastructure",
    "sensitive": "sensitive_data",
    "sensitive_data": "sensitive_data",
    "sensitive-data": "sensitive_data",
    "sensitive_data_assets": "sensitive_data",
}


def _normalize_import_category(raw_value: Optional[str]) -> str:
    """Normalize arbitrary category strings to canonical values."""
    if not raw_value:
        return "cmdb_export"

    normalized = raw_value.strip().lower().replace(" ", "_").replace("-", "_")
    mapped = IMPORT_CATEGORY_ALIASES.get(normalized, normalized)
    if mapped in VALID_IMPORT_CATEGORIES:
        return mapped

    logger.warning("Unknown import category '%s'; defaulting to cmdb_export", raw_value)
    return "cmdb_export"


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
                    "data": import_data.get("data", []),
                    "import_metadata": import_data.get("import_metadata"),
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
                # CRITICAL FIX: For CSV uploads, use direct storage operations to ensure raw_import_records are created
                from .storage_manager.operations import ImportStorageOperations

                storage_ops = ImportStorageOperations(
                    self.db, context.client_account_id
                )

                raw_category = (
                    store_request.import_category
                    or store_request.upload_context.intended_type
                )
                import_category = _normalize_import_category(raw_category)
                processing_config = store_request.processing_config or {}

                # Create data_import record and store raw_import_records directly
                data_import = await storage_ops.store_import_data(
                    file_content=json.dumps(store_request.file_data).encode("utf-8"),
                    filename=store_request.metadata.filename,
                    file_content_type="application/json",
                    import_type=store_request.upload_context.intended_type,
                    status="processing",
                    engagement_id=context.engagement_id,
                    imported_by=context.user_id,
                    import_category=import_category,
                    processing_config=processing_config,
                )
                logger.info(
                    f"🗳️ Data import record created with raw records: {data_import.id}"
                )

                # Simple audit logging for CSV data cleansing
                if (
                    store_request.cleansing_stats
                    and store_request.cleansing_stats.rows_cleansed > 0
                ):
                    await self._log_cleansing_audit(
                        store_request.cleansing_stats, context, data_import.id
                    )

                # 🔧 CC FIX: Ensure CrewAI environment is configured BEFORE creating MFO
                # This prevents "OPENAI_API_KEY is required" errors during initialize_all_flows()
                # which is called in MasterFlowOrchestrator.__init__ -> core.py:90-94
                from app.core.crewai_env_setup import ensure_crewai_environment

                ensure_crewai_environment()
                logger.info(
                    "✅ CrewAI environment configured for MasterFlowOrchestrator initialization"
                )

                child_flow_service = DataImportChildFlowService(self.db, context)
                flow_metadata = await child_flow_service.create_import_flow(
                    data_import=data_import,
                    storage_ops=storage_ops,
                    raw_records=store_request.file_data,
                    import_category=import_category,
                    processing_config=processing_config,
                )

                logger.info(
                    "🗳️ Transaction completed - data_import %s linked to master flow %s",
                    data_import.id,
                    flow_metadata["master_flow_id"],
                )

            # Start background processing AFTER transaction commits to avoid race conditions
            if (
                hasattr(data_import, "flow_execution_data")
                and data_import.flow_execution_data
            ):
                flow_execution_data = data_import.flow_execution_data
                flow_id = flow_execution_data["flow_id"]
                logger.info(
                    "🚀 Starting background import execution for flow_id=%s", flow_id
                )

                background_service = BackgroundExecutionService(
                    self.db, context.client_account_id
                )
                processor_runner = ImportProcessorBackgroundRunner(background_service)
                await processor_runner.start_background_import_execution(
                    master_flow_id=flow_id,
                    data_import_id=str(data_import.id),
                    raw_records=flow_execution_data.get("file_data", []),
                    import_category=flow_execution_data.get("import_category"),
                    processing_config=flow_execution_data.get("processing_config", {}),
                    context=context,
                )
                logger.info("✅ Background import execution started for %s", flow_id)

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

    async def _log_cleansing_audit(
        self,
        cleansing_stats: CleansingStats,
        context: RequestContext,
        data_import_id: Any,
    ) -> None:
        """
        Simple audit log for CSV data cleansing.

        Args:
            cleansing_stats: Cleansing statistics from the request
            context: Request context with user and tenant information
            data_import_id: ID of the data import record
        """
        try:
            from app.models.rbac.audit_models import AccessAuditLog

            audit_log = AccessAuditLog(
                user_id=context.user_id,
                action_type="data_import_cleansing",
                resource_type="data_import",
                resource_id=str(data_import_id),
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                result="success",
                reason=(
                    f"CSV data cleansing: {cleansing_stats.rows_cleansed} row(s) had "
                    "unquoted commas replaced with spaces for column alignment during "
                    "data import"
                ),
                details={
                    "total_rows": cleansing_stats.total_rows,
                    "rows_cleansed": cleansing_stats.rows_cleansed,
                    "rows_skipped": cleansing_stats.rows_skipped,
                    "cleansing_type": "comma_replacement",
                    "cleansing_reason": "column_alignment",
                },
                ip_address=context.ip_address,
                user_agent=context.user_agent,
            )

            self.db.add(audit_log)
            await self.db.commit()
            logger.info(
                f"✅ Audit log created for data import cleansing: "
                f"{cleansing_stats.rows_cleansed} rows cleansed for import {data_import_id}"
            )
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to log data import cleansing audit: {str(e)}. "
                "Import will continue without audit log."
            )
            # Don't raise - audit logging should not break the import flow
