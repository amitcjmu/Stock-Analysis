"""
Utility operations for field mappings.
Handles validation, counting, cleanup, and health check operations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db

from ..models.mapping_schemas import (
    MappingValidationRequest,
    MappingValidationResponse,
)
from ..services.mapping_service import MappingService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.post("/validate", response_model=MappingValidationResponse)
async def validate_field_mappings(
    request: MappingValidationRequest,
    service: MappingService = Depends(get_mapping_service),
):
    """Validate a set of field mappings."""
    try:
        validation_result = await service.validate_mappings(request)
        return validation_result
    except Exception as e:
        logger.error(safe_log_format("Error validating field mappings: {e}", e=e))
        raise HTTPException(status_code=500, detail="Failed to validate field mappings")


@router.get("/imports/{import_id}/mappings/count")
async def get_mapping_count(
    import_id: str, service: MappingService = Depends(get_mapping_service)
):
    """Get count of field mappings for an import."""
    try:
        mappings = await service.get_field_mappings(import_id)
        return {
            "import_id": import_id,
            "total_mappings": len(mappings),
            "approved_mappings": len([m for m in mappings if m.is_approved]),
            "pending_mappings": len([m for m in mappings if not m.is_approved]),
        }
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error getting mapping count for import {import_id}: {e}",
                import_id=import_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail="Failed to get mapping count")


@router.post("/imports/{import_id}/cleanup-artifacts")
async def cleanup_json_artifacts(
    import_id: str,
    service: MappingService = Depends(get_mapping_service),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Clean up JSON artifact field mappings for an import.

    This endpoint removes field mappings where the source_field contains
    JSON metadata like "mappings", "skipped_fields", etc. that should not
    have been stored as actual CSV field names.
    """
    try:
        logger.info(
            safe_log_format(
                "🧹 Cleaning up JSON artifacts for import: {import_id}",
                import_id=import_id,
            )
        )

        # Get the data import
        from uuid import UUID
        from sqlalchemy import select
        from app.models.data_import import DataImport

        # Convert string UUID to UUID object if needed
        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id
        except ValueError as e:
            logger.error(safe_log_format("❌ Invalid UUID format: {e}", e=e))
            raise HTTPException(
                status_code=400,
                detail=f"Invalid UUID format for import_id: {import_id}",
            )

        import_query = select(DataImport).where(DataImport.id == import_uuid)
        import_result = await db.execute(import_query)
        data_import = import_result.scalar_one_or_none()

        if not data_import:
            raise HTTPException(
                status_code=404, detail=f"Data import {import_id} not found"
            )

        # Initialize the storage manager mixin directly to access cleanup method
        from app.services.data_import.storage_manager.mapping_operations import (
            FieldMappingOperationsMixin,
        )

        # Create a minimal class with the required attributes
        class CleanupService(FieldMappingOperationsMixin):
            def __init__(self, db_session, client_account_id):
                self.db = db_session
                self.client_account_id = client_account_id

        cleanup_service = CleanupService(db, context.client_account_id)
        removed_count = await cleanup_service.cleanup_json_artifact_mappings(
            data_import
        )

        return {
            "status": "success",
            "message": f"Cleaned up {removed_count} JSON artifact field mappings",
            "import_id": import_id,
            "artifacts_removed": removed_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error cleaning up JSON artifacts: {e}", e=e))
        raise HTTPException(status_code=500, detail="Failed to clean up JSON artifacts")


@router.get("/health")
async def health_check():
    """Health check endpoint for field mapping routes."""
    return {
        "status": "healthy",
        "service": "field_mapping_routes",
        "endpoints": [
            "GET /imports/{import_id}/mappings",
            "POST /imports/{import_id}/mappings",
            "PUT /mappings/{mapping_id}",
            "DELETE /mappings/{mapping_id}",
            "POST /imports/{import_id}/reanalyze",
            "POST /imports/{import_id}/generate",
            "POST /imports/latest/mappings",
            "POST /validate",
            "GET /imports/{import_id}/mappings/count",
            "POST /imports/{import_id}/cleanup-artifacts",
        ],
    }
