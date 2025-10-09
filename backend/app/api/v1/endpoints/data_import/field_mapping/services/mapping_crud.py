"""
Field Mapping CRUD Service
Handles CREATE, UPDATE, DELETE operations for field mappings
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import ImportFieldMapping
from app.utils.json_utils import safe_json_dumps

from ..models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
)
from ..validators.mapping_validators import MappingValidator

logger = logging.getLogger(__name__)


class MappingCRUDService:
    """Service for field mapping CREATE, UPDATE, DELETE operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.validator = MappingValidator()

    async def create_field_mapping(
        self, import_id: str, mapping_data: FieldMappingCreate
    ) -> FieldMappingResponse:
        """Create a new field mapping."""

        # Convert string UUIDs to UUID objects if needed
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

        # Get engagement_id and master_flow_id from context (same pattern as client_account_id)
        if isinstance(self.context.engagement_id, str):
            engagement_id_uuid = UUID(self.context.engagement_id)
        else:
            engagement_id_uuid = self.context.engagement_id

        # Use flow_id from context as master_flow_id
        master_flow_id_uuid = None
        if self.context.flow_id:
            if isinstance(self.context.flow_id, str):
                master_flow_id_uuid = UUID(self.context.flow_id)
            else:
                master_flow_id_uuid = self.context.flow_id

        # Create mapping record
        mapping = ImportFieldMapping(
            data_import_id=import_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_id_uuid,
            master_flow_id=master_flow_id_uuid,
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

        return self._serialize_mapping(mapping)

    async def update_field_mapping(
        self, mapping_id: str, update_data: FieldMappingUpdate
    ) -> FieldMappingResponse:
        """Update an existing field mapping."""

        # Convert string UUID to UUID object if needed
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
        if update_data.is_approved is not None:
            mapping.status = "approved" if update_data.is_approved else "suggested"

        mapping.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(mapping)

        logger.info(f"Updated field mapping {mapping_id}")

        return self._serialize_mapping(mapping)

    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping."""

        # Convert string UUID to UUID object if needed
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

    async def bulk_update_field_mappings(
        self, mapping_ids: List[str], update_data: FieldMappingUpdate
    ) -> Dict[str, Any]:
        """Update multiple field mappings in a single database transaction."""
        from ..utils.bulk_operations import BulkOperations

        bulk_ops = BulkOperations(self.db, self.context)
        return await bulk_ops.bulk_update_field_mappings(mapping_ids, update_data)

    def _serialize_mapping(self, mapping: ImportFieldMapping) -> FieldMappingResponse:
        """Serialize a mapping to response model"""
        # Serialize transformation_rules properly for response
        transformation_rule_str = None
        if mapping.transformation_rules:
            if isinstance(mapping.transformation_rules, dict):
                transformation_rule_str = safe_json_dumps(mapping.transformation_rules)
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
            is_approved=mapping.status == "approved",
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )
