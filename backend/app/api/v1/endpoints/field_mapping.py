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
from pydantic import BaseModel
from typing import Optional
from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-mapping")


class FieldMappingUpdateRequest(BaseModel):
    """Request model for updating field mappings."""

    target_field: str
    source_field: Optional[str] = None
    confidence_score: Optional[float] = None


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


@router.put("/update/{mapping_id}")
async def update_field_mapping(
    mapping_id: str,
    request: FieldMappingUpdateRequest,
    service: MappingService = Depends(get_mapping_service),
):
    """
    Update a field mapping's target field.
    Frontend endpoint for updating field mappings before approval.
    """
    try:
        logger.info(
            f"Field mapping update request: mapping_id={mapping_id}, target_field={request.target_field}"
        )

        # Create update data with the new target field
        update_data = FieldMappingUpdate(target_field=request.target_field)

        # Update the mapping
        updated_mapping = await service.update_field_mapping(mapping_id, update_data)

        return {
            "mapping_id": mapping_id,
            "target_field": request.target_field,
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
                "Error updating mapping {mapping_id}: {e}", mapping_id=mapping_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail="Failed to update field mapping")


@router.delete("/mappings/{mapping_id}")
async def delete_field_mapping(
    mapping_id: str,
    service: MappingService = Depends(get_mapping_service),
):
    """
    Remove an approved field mapping by changing status to 'rejected'.
    This moves the mapping back to 'Needs Review' for re-processing.
    """
    try:
        logger.info(f"🗑️ Field mapping removal request: mapping_id={mapping_id}")

        # Change is_approved to False instead of deleting
        # This moves the mapping back to "Needs Review" column
        update_data = FieldMappingUpdate(is_approved=False)
        updated_mapping = await service.update_field_mapping(mapping_id, update_data)

        if not updated_mapping:
            logger.warning(
                safe_log_format(
                    "Mapping {mapping_id} not found for status update",
                    mapping_id=mapping_id,
                )
            )
            raise HTTPException(
                status_code=404, detail=f"Field mapping not found: {mapping_id}"
            )

        logger.info(
            f"✅ Successfully moved field mapping {mapping_id} back to needs review"
        )

        return {
            "mapping_id": mapping_id,
            "is_approved": False,
            "success": True,
            "message": "Field mapping moved to needs review",
            "updated_mapping": updated_mapping,
        }

    except HTTPException:
        raise
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
                "Error updating mapping {mapping_id}: {e}", mapping_id=mapping_id, e=e
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to update field mapping status"
        )


@router.get("/health")
async def health_check():
    """Health check for top-level field mapping endpoints."""
    return {
        "status": "healthy",
        "service": "field_mapping_top_level",
        "delegates_to": "data_import.field_mapping_modular",
        "endpoints": [
            "/approve/{mapping_id}",
            "/update/{mapping_id}",
            "/mappings/{mapping_id} (DELETE)",
        ],
    }
