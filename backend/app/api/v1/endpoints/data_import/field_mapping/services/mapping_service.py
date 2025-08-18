"""
Core field mapping service containing business logic.
Enhanced to use CrewAI agents for intelligent field mapping.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import ImportFieldMapping

from ..models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
    MappingValidationRequest,
    MappingValidationResponse,
)

# Legacy hardcoded mapping helpers removed - using CrewAI agents only
# from ..utils.mapping_helpers import (
#     intelligent_field_mapping, calculate_mapping_confidence
# )
from ..validators.mapping_validators import MappingValidator

# CrewAI integration for intelligent field mapping
CREWAI_FIELD_MAPPING_ENABLED = (
    os.getenv("CREWAI_FIELD_MAPPING_ENABLED", "true").lower() == "true"
)
try:
    # Imports for future CrewAI integration - currently not used but structure ready
    CREWAI_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI field mapping components ready for integration")
except ImportError as e:
    CREWAI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI components not available, using fallback: {e}")

logger = logging.getLogger(__name__)


class MappingService:
    """Service for field mapping operations."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.validator = MappingValidator()

    async def get_field_mappings(self, import_id: str) -> List[FieldMappingResponse]:
        """Get all field mappings for an import."""

        # Convert string UUIDs to UUID objects if needed
        from uuid import UUID

        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for import_id: {import_id}")

        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()

        # NO HARDCODED FILTERING - Let CrewAI agents determine what's valid
        # The agents should have already made intelligent decisions about
        # which fields to map

        # CrewAI agents determine valid mappings - no hardcoded validation
        valid_mappings = []
        for mapping in mappings:
            # Trust the agent decisions - no hardcoded filtering

            # Debug logging to identify the issue
            logger.info(
                f"🔍 DEBUG: Field mapping - source_field type: "
                f"{type(mapping.source_field)}, value: {mapping.source_field}"
            )
            logger.info(
                f"🔍 DEBUG: Field mapping - target_field type: "
                f"{type(mapping.target_field)}, value: {mapping.target_field}"
            )

            # Convert JSON transformation_rules to string, handle None values
            transformation_rule_str = None
            if mapping.transformation_rules:
                if isinstance(mapping.transformation_rules, dict):
                    # Convert dict to JSON string if needed
                    import json

                    transformation_rule_str = json.dumps(
                        mapping.transformation_rules, default=str
                    )
                elif isinstance(mapping.transformation_rules, str):
                    transformation_rule_str = mapping.transformation_rules
                else:
                    transformation_rule_str = str(mapping.transformation_rules)

            valid_mappings.append(
                FieldMappingResponse(
                    id=mapping.id,
                    source_field=str(mapping.source_field),  # Ensure string type
                    target_field=str(
                        mapping.target_field
                    ),  # Keep as string, frontend handles "UNMAPPED"
                    transformation_rule=transformation_rule_str,
                    # Note: validation_rule is separate from transformation_rule in schema
                    # but database only stores transformation_rules - validation is handled
                    # by mapping validators during processing
                    validation_rule=None,  # Database doesn't store validation rules separately
                    is_required=getattr(mapping, "is_required", False),
                    is_approved=mapping.status == "approved",
                    confidence=(
                        float(mapping.confidence_score)
                        if mapping.confidence_score is not None
                        else 0.0
                    ),
                    created_at=mapping.created_at,
                    updated_at=mapping.updated_at,
                )
            )

        logger.info(
            f"✅ Returning {len(valid_mappings)} field mappings for import {import_id}"
        )
        return valid_mappings

    async def create_field_mapping(
        self, import_id: str, mapping_data: FieldMappingCreate
    ) -> FieldMappingResponse:
        """Create a new field mapping."""

        # Convert string UUIDs to UUID objects if needed
        from uuid import UUID

        try:
            if isinstance(import_id, str):
                import_uuid = UUID(import_id)
            else:
                import_uuid = import_id

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for import_id: {import_id}")

        # Validate mapping data
        validation_result = await self.validator.validate_mapping(mapping_data)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid mapping: {validation_result.validation_errors}")

        # Create mapping record
        mapping = ImportFieldMapping(
            data_import_id=import_uuid,
            client_account_id=client_account_uuid,
            source_field=mapping_data.source_field,
            target_field=mapping_data.target_field,
            match_type="user_defined",
            confidence_score=mapping_data.confidence,
            transformation_rules=mapping_data.transformation_rule,
            status="approved",  # User-created mappings are auto-approved
        )

        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)

        logger.info(
            f"Created field mapping: {mapping_data.source_field} -> "
            f"{mapping_data.target_field}"
        )

        # Serialize transformation_rules properly for response
        transformation_rule_str = None
        if mapping.transformation_rules:
            if isinstance(mapping.transformation_rules, dict):
                import json

                transformation_rule_str = json.dumps(
                    mapping.transformation_rules, default=str
                )
            elif isinstance(mapping.transformation_rules, str):
                transformation_rule_str = mapping.transformation_rules
            else:
                transformation_rule_str = str(mapping.transformation_rules)

        return FieldMappingResponse(
            id=mapping.id,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation_rule=transformation_rule_str,
            validation_rule=None,  # Database doesn't store validation rules separately
            is_required=False,
            is_approved=True,
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )

    async def bulk_update_field_mappings(
        self, mapping_ids: List[str], update_data: FieldMappingUpdate
    ) -> Dict[str, Any]:
        """Update multiple field mappings in a single database transaction."""
        from ..utils.bulk_operations import BulkOperations

        bulk_ops = BulkOperations(self.db, self.context)
        return await bulk_ops.bulk_update_field_mappings(mapping_ids, update_data)

    async def update_field_mapping(
        self, mapping_id: str, update_data: FieldMappingUpdate
    ) -> FieldMappingResponse:
        """Update an existing field mapping."""

        # Convert string UUID to UUID object if needed
        from uuid import UUID

        try:
            if isinstance(mapping_id, str):
                mapping_uuid = UUID(mapping_id)
            else:
                mapping_uuid = mapping_id

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for mapping_id: {mapping_id}")

        # Get existing mapping
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()

        if not mapping:
            # Check if mapping exists but access is denied (different client_account)
            debug_query = select(ImportFieldMapping).where(
                ImportFieldMapping.id == mapping_uuid
            )
            debug_result = await self.db.execute(debug_query)
            debug_mapping = debug_result.scalar_one_or_none()

            if debug_mapping:
                logger.warning(
                    f"Field mapping {mapping_id} access denied - "
                    f"different client account"
                )
                raise ValueError(f"Field mapping {mapping_id} not found")
            else:
                logger.info(f"Field mapping {mapping_id} does not exist")
                raise ValueError(f"Field mapping {mapping_id} not found")

        # Update fields
        if update_data.target_field is not None:
            mapping.target_field = update_data.target_field
        if update_data.transformation_rule is not None:
            mapping.transformation_rules = update_data.transformation_rule
        # Note: validation_rule is not stored in database - validation is handled
        # by mapping validators during processing, not persisted as rules
        # if update_data.validation_rule is not None:
        #     mapping.transformation_rules = update_data.validation_rule
        # is_required field doesn't exist in ImportFieldMapping model
        # if update_data.is_required is not None:
        #     mapping.is_required = update_data.is_required
        if update_data.is_approved is not None:
            mapping.status = "approved" if update_data.is_approved else "suggested"

        mapping.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(mapping)

        logger.info(f"Updated field mapping {mapping_id}")

        # Serialize transformation_rules properly for response
        transformation_rule_str = None
        if mapping.transformation_rules:
            if isinstance(mapping.transformation_rules, dict):
                import json

                transformation_rule_str = json.dumps(
                    mapping.transformation_rules, default=str
                )
            elif isinstance(mapping.transformation_rules, str):
                transformation_rule_str = mapping.transformation_rules
            else:
                transformation_rule_str = str(mapping.transformation_rules)

        return FieldMappingResponse(
            id=mapping.id,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation_rule=transformation_rule_str,
            validation_rule=None,  # Database doesn't store validation rules separately
            # is_required field doesn't exist in ImportFieldMapping model
            is_required=False,
            is_approved=mapping.status == "approved",
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )

    async def generate_mappings_for_import(self, import_id: str) -> Dict[str, Any]:
        """Generate field mappings for an entire import."""
        from ..utils.mapping_generator import MappingGenerator

        generator = MappingGenerator(self.db, self.context)
        return await generator.generate_mappings_for_import(import_id)

    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping."""

        # Convert string UUID to UUID object if needed
        from uuid import UUID

        try:
            if isinstance(mapping_id, str):
                mapping_uuid = UUID(mapping_id)
            else:
                mapping_uuid = mapping_id

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format: {e}")
            raise ValueError(f"Invalid UUID format for mapping_id: {mapping_id}")

        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        mapping = result.scalar_one_or_none()

        if not mapping:
            return False

        await self.db.delete(mapping)
        await self.db.commit()

        logger.info(f"Deleted field mapping {mapping_id}")
        return True

    async def validate_mappings(
        self, request: MappingValidationRequest
    ) -> MappingValidationResponse:
        """Validate a set of field mappings."""
        from ..utils.validation_helper import ValidationHelper

        validation_helper = ValidationHelper()
        return await validation_helper.validate_mappings(request)

    # Helper methods moved to utility modules for better organization

    # All field mapping logic has been moved to the discovery flow's field mapping phase
    # The real CrewAI field mapping crew handles all intelligent mapping
    # This service should only retrieve existing mappings, not generate them
