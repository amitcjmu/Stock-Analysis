"""
Validation helper utilities for field mapping.
"""

from datetime import datetime

# from typing import List  # Currently unused

from ..models.mapping_schemas import (
    FieldMappingResponse,
    MappingValidationRequest,
    MappingValidationResponse,
)
from ..validators.mapping_validators import MappingValidator


class ValidationHelper:
    """Helper for mapping validation operations."""

    def __init__(self):
        """Initialize validation helper."""
        self.validator = MappingValidator()

    async def validate_mappings(
        self, request: MappingValidationRequest
    ) -> MappingValidationResponse:
        """Validate a set of field mappings."""
        validation_errors = []
        warnings = []
        validated_mappings = []

        for mapping_data in request.mappings:
            try:
                # Validate individual mapping
                validation_result = await self.validator.validate_mapping(mapping_data)

                if validation_result.is_valid:
                    validated_mappings.append(
                        FieldMappingResponse(
                            id=0,  # Temporary ID for new mappings
                            source_field=mapping_data.source_field,
                            target_field=mapping_data.target_field,
                            transformation_rule=mapping_data.transformation_rule,
                            validation_rule=mapping_data.validation_rule,
                            is_required=mapping_data.is_required,
                            is_approved=False,
                            confidence=mapping_data.confidence,
                            created_at=datetime.utcnow(),
                        )
                    )
                else:
                    validation_errors.extend(validation_result.validation_errors)

                warnings.extend(validation_result.warnings)

            except Exception as e:
                validation_errors.append(
                    f"Error validating mapping {mapping_data.source_field}: {str(e)}"
                )

        return MappingValidationResponse(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            warnings=warnings,
            validated_mappings=validated_mappings,
        )
