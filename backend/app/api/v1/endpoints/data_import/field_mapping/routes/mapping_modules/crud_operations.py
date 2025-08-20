"""
CRUD operations for field mappings.
Basic create, read, update, delete operations.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db

from ...models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
)
from ...services.mapping_service import MappingService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.get("/imports/{import_id}/mappings", response_model=List[FieldMappingResponse])
async def get_field_mappings(
    import_id: str, service: MappingService = Depends(get_mapping_service)
):
    """Get all field mappings for a specific import."""
    try:
        mappings = await service.get_field_mappings(import_id)

        # Debug logging to check the response format
        logger.info(
            f"🔍 DEBUG: Retrieved {len(mappings)} mappings for import {import_id}"
        )
        if mappings:
            logger.debug(
                f"🔍 DEBUG: Sample mapping: {mappings[0].__dict__ if hasattr(mappings[0], '__dict__') else mappings[0]}"
            )

        return mappings

    except ValueError as e:
        logger.warning(safe_log_format("Invalid import ID: {e}", e=e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(safe_log_format("Error retrieving field mappings: {e}", e=e))
        raise HTTPException(status_code=500, detail="Failed to retrieve field mappings")


@router.post("/imports/{import_id}/mappings", response_model=FieldMappingResponse)
async def create_field_mapping(
    import_id: str,
    mapping_data: FieldMappingCreate,
    service: MappingService = Depends(get_mapping_service),
):
    """Create a new field mapping."""
    try:
        mapping = await service.create_field_mapping(import_id, mapping_data)
        return mapping
    except ValueError as e:
        logger.warning(
            safe_log_format("Validation error creating field mapping: {e}", e=e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(safe_log_format("Error creating field mapping: {e}", e=e))
        raise HTTPException(status_code=500, detail="Failed to create field mapping")


@router.put("/mappings/{mapping_id}", response_model=FieldMappingResponse)
async def update_field_mapping(
    mapping_id: str,
    update_data: FieldMappingUpdate,
    service: MappingService = Depends(get_mapping_service),
):
    """Update an existing field mapping."""
    try:
        mapping = await service.update_field_mapping(mapping_id, update_data)
        return mapping
    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Validation error updating field mapping {mapping_id}: {e}",
                mapping_id=mapping_id,
                e=e,
            )
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error updating field mapping {mapping_id}: {e}",
                mapping_id=mapping_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail="Failed to update field mapping")


@router.delete("/mappings/{mapping_id}")
async def delete_field_mapping(
    mapping_id: str, service: MappingService = Depends(get_mapping_service)
):
    """Delete a field mapping."""
    try:
        deleted = await service.delete_field_mapping(mapping_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Field mapping not found")
        return {"status": "success", "message": "Field mapping deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error deleting field mapping {mapping_id}: {e}",
                mapping_id=mapping_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail="Failed to delete field mapping")
