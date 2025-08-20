"""
Top-level field mapping router for frontend compatibility.
Creates the expected /api/v1/field-mapping endpoints that delegate to the modular field mapping system.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.data_import.field_mapping.models.mapping_schemas import (
    FieldMappingUpdate,
)
from app.api.v1.endpoints.data_import.field_mapping.services.mapping_service import (
    MappingService,
)
from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-mapping")


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.post("/approve/{mapping_id}")
async def approve_field_mapping(
    mapping_id: str,
    approved: bool = True,
    approval_note: str = None,
    service: MappingService = Depends(get_mapping_service),
):
    """
    Approve or reject a single field mapping.
    Frontend compatibility endpoint that delegates to the modular approval system.
    """
    try:
        logger.info(
            f"Field mapping approval request: mapping_id={mapping_id}, approved={approved}"
        )

        update_data = FieldMappingUpdate(is_approved=approved)
        updated_mapping = await service.update_field_mapping(mapping_id, update_data)

        return {
            "mapping_id": mapping_id,
            "status": "approved" if approved else "rejected",
            "approval_note": approval_note,
            "updated_mapping": updated_mapping,
            "success": True,
        }

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Mapping {mapping_id} not found: {e}", mapping_id=mapping_id, e=e
            )
        )
        raise HTTPException(
            status_code=404, detail=f"Field mapping not found: {mapping_id}"
        )
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error approving mapping {mapping_id}: {e}", mapping_id=mapping_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail="Failed to approve field mapping")


@router.get("/health")
async def health_check():
    """Health check for top-level field mapping endpoints."""
    return {
        "status": "healthy",
        "service": "field_mapping_top_level",
        "delegates_to": "data_import.field_mapping_modular",
        "endpoints": ["/approve/{mapping_id}"],
    }
