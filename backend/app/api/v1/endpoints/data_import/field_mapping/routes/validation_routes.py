"""
Field mapping validation route handlers.
"""

import logging
from typing import List

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.mapping_schemas import (
    FieldMappingCreate,
    MappingValidationRequest,
    MappingValidationResponse,
)
from ..services.validation_service import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["field-mapping-validation"])


def get_validation_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> ValidationService:
    """Dependency injection for validation service."""
    return ValidationService(db, context)


@router.post("/validate-mapping", response_model=MappingValidationResponse)
async def validate_field_mapping(
    mapping: FieldMappingCreate,
    service: ValidationService = Depends(get_validation_service),
):
    """Validate a single field mapping."""
    try:
        result = await service.validate_single_mapping(mapping)
        return result
    except Exception as e:
        logger.error(f"Error validating field mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate field mapping")


@router.post("/validate-mappings", response_model=MappingValidationResponse)
async def validate_field_mappings(
    request: MappingValidationRequest,
    service: ValidationService = Depends(get_validation_service),
):
    """Validate multiple field mappings."""
    try:
        result = await service.validate_multiple_mappings(request.mappings)
        return result
    except Exception as e:
        logger.error(f"Error validating field mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate field mappings")


@router.post("/validate-compatibility")
async def validate_field_compatibility(
    source_field: str,
    target_field: str,
    sample_data: List = None,
    service: ValidationService = Depends(get_validation_service),
):
    """Validate compatibility between source and target fields."""
    try:
        result = await service.validate_field_compatibility(
            source_field, target_field, sample_data
        )
        return result
    except Exception as e:
        logger.error(f"Error validating field compatibility: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to validate field compatibility"
        )
