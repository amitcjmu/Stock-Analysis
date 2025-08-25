"""
Analysis and generation operations for field mappings.
Handles reanalysis, generation, and intelligent mapping operations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format

from ...models.mapping_schemas import FieldMappingCreate
from ...services.mapping_service import MappingService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.post("/imports/{import_id}/reanalyze")
async def trigger_field_mapping_reanalysis(
    import_id: str,
    service: MappingService = Depends(get_mapping_service),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Trigger re-analysis of field mappings using CrewAI agents.
    This will regenerate field mappings with the latest logic.
    """
    try:
        logger.info(
            safe_log_format(
                "🔄 Triggering field mapping re-analysis for import: {import_id}",
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

        # Trigger re-analysis via critical attributes module
        from app.api.v1.endpoints.data_import.critical_attributes import (
            _trigger_field_mapping_reanalysis,
        )

        await _trigger_field_mapping_reanalysis(context, data_import, db)

        return {
            "status": "success",
            "message": "Field mapping re-analysis triggered successfully",
            "import_id": import_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Error triggering field mapping re-analysis: {e}", e=e)
        )
        raise HTTPException(
            status_code=500, detail="Failed to trigger field mapping re-analysis"
        )


@router.post("/imports/{import_id}/generate")
async def generate_field_mappings(
    import_id: str,
    force_regenerate: bool = False,
    service: MappingService = Depends(get_mapping_service),
):
    """Generate field mappings for an entire import."""
    try:
        # If force_regenerate is True, delete existing mappings first
        if force_regenerate:
            logger.info(
                safe_log_format(
                    "🔄 Force regenerating field mappings for import {import_id}",
                    import_id=import_id,
                )
            )

            await _cleanup_existing_mappings(import_id, service)

        result = await service.generate_mappings_for_import(import_id)
        return result
    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Error generating mappings for import {import_id}: {e}",
                import_id=import_id,
                e=e,
            )
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error generating mappings for import {import_id}: {e}",
                import_id=import_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail="Failed to generate field mappings")


@router.post("/imports/latest/mappings")
async def create_field_mapping_latest(
    mapping_data: Optional[FieldMappingCreate] = None,
    force_regenerate: bool = False,
    request: Request = None,
    service: MappingService = Depends(get_mapping_service),
):
    """Create field mapping for the latest import in current context."""
    try:
        # Get latest import for context
        latest_import = await _get_latest_import(service)
        if not latest_import:
            raise HTTPException(
                status_code=404,
                detail="No processed data import found in current context",
            )

        import_id = str(latest_import.id)
        logger.info(f"🎯 Using latest import: {import_id}")

        if force_regenerate:
            # Generate field mappings (which will trigger force regeneration)
            return await generate_field_mappings(
                import_id, force_regenerate=True, service=service
            )
        elif mapping_data:
            # Create specific field mapping
            mapping = await service.create_field_mapping(import_id, mapping_data)
            return mapping
        else:
            # Generate all mappings for the import
            result = await service.generate_mappings_for_import(import_id)
            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error in create_field_mapping_latest: {e}", e=e))
        raise HTTPException(
            status_code=500, detail="Failed to create field mapping for latest import"
        )


async def _cleanup_existing_mappings(import_id: str, service: MappingService):
    """Clean up existing mappings and JSON artifacts."""
    # CRITICAL FIX: Clean up JSON artifacts first, then delete all existing mappings
    from sqlalchemy import and_, delete, select

    from app.models.data_import import DataImport, ImportFieldMapping

    # Get the data import record for cleanup
    import_query = select(DataImport).where(DataImport.id == import_id)
    import_result = await service.db.execute(import_query)
    data_import = import_result.scalar_one_or_none()

    if data_import:
        # Clean up JSON artifacts first
        try:
            from app.services.data_import.storage_manager.mapping_operations import (
                FieldMappingOperationsMixin,
            )

            class CleanupService(FieldMappingOperationsMixin):
                def __init__(self, db_session, client_account_id):
                    self.db = db_session
                    self.client_account_id = client_account_id

            cleanup_service = CleanupService(
                service.db, service.context.client_account_id
            )
            removed_count = await cleanup_service.cleanup_json_artifact_mappings(
                data_import
            )

            if removed_count > 0:
                logger.info(
                    f"🧹 Cleaned up {removed_count} JSON artifact mappings before regeneration"
                )

        except Exception as cleanup_error:
            logger.warning(
                f"⚠️ JSON artifact cleanup failed but continuing: {cleanup_error}"
            )

    # Delete all existing mappings to trigger CrewAI regeneration
    delete_query = delete(ImportFieldMapping).where(
        and_(
            ImportFieldMapping.data_import_id == import_id,
            ImportFieldMapping.client_account_id == service.context.client_account_id,
        )
    )
    await service.db.execute(delete_query)
    await service.db.commit()
    logger.info(
        safe_log_format(
            "✅ Deleted existing field mappings for import {import_id}",
            import_id=import_id,
        )
    )


async def _get_latest_import(service: MappingService):
    """Get the latest processed import for the current context."""
    from sqlalchemy import and_, select

    from app.models.data_import import DataImport

    latest_query = (
        select(DataImport)
        .where(
            and_(
                DataImport.status.in_(["processed", "completed"]),
                DataImport.client_account_id == service.context.client_account_id,
                DataImport.engagement_id == service.context.engagement_id,
            )
        )
        .order_by(DataImport.completed_at.desc())
        .limit(1)
    )

    result = await service.db.execute(latest_query)
    return result.scalar_one_or_none()
