"""
Field mapping validation service.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from ..models.mapping_schemas import FieldMappingCreate, MappingValidationResponse
from ..validators.mapping_validators import MappingValidator

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for field mapping validation operations."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.validator = MappingValidator()
    
    async def validate_single_mapping(self, mapping: FieldMappingCreate) -> MappingValidationResponse:
        """Validate a single field mapping."""
        return await self.validator.validate_mapping(mapping)
    
    async def validate_multiple_mappings(
        self, 
        mappings: List[FieldMappingCreate]
    ) -> MappingValidationResponse:
        """Validate multiple field mappings."""
        all_errors = []
        all_warnings = []
        valid_mappings = []
        
        for mapping in mappings:
            result = await self.validator.validate_mapping(mapping)
            all_errors.extend(result.validation_errors)
            all_warnings.extend(result.warnings)
            
            if result.is_valid:
                valid_mappings.extend(result.validated_mappings)
        
        return MappingValidationResponse(
            is_valid=len(all_errors) == 0,
            validation_errors=all_errors,
            warnings=all_warnings,
            validated_mappings=valid_mappings
        )
    
    async def validate_field_compatibility(
        self,
        source_field: str,
        target_field: str,
        sample_data: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Validate compatibility between source and target fields."""
        return self.validator.validate_field_compatibility(
            source_field, target_field, sample_data
        )