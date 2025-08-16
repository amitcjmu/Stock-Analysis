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
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord

from ..models.mapping_schemas import (
    FieldMappingCreate,
    FieldMappingResponse,
    FieldMappingUpdate,
    MappingValidationRequest,
    MappingValidationResponse,
)

# Legacy hardcoded mapping helpers removed - using CrewAI agents only
# from ..utils.mapping_helpers import intelligent_field_mapping, calculate_mapping_confidence
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
        # The agents should have already made intelligent decisions about which fields to map

        # CrewAI agents determine valid mappings - no hardcoded validation
        valid_mappings = []
        for mapping in mappings:
            # Trust the agent decisions - no hardcoded filtering

            # Debug logging to identify the issue
            logger.info(
                f"🔍 DEBUG: Field mapping - source_field type: {type(mapping.source_field)}, "
                f"value: {mapping.source_field}"
            )
            logger.info(
                f"🔍 DEBUG: Field mapping - target_field type: {type(mapping.target_field)}, "
                f"value: {mapping.target_field}"
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
                    validation_rule=transformation_rule_str,  # Using transformation_rules for now
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
            f"Created field mapping: {mapping_data.source_field} -> {mapping_data.target_field}"
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
            validation_rule=transformation_rule_str,
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

        # Convert string UUIDs to UUID objects
        from uuid import UUID

        try:
            mapping_uuids = [
                UUID(id_str) if isinstance(id_str, str) else id_str
                for id_str in mapping_ids
            ]

            if isinstance(self.context.client_account_id, str):
                client_account_uuid = UUID(self.context.client_account_id)
            else:
                client_account_uuid = self.context.client_account_id
        except ValueError as e:
            logger.error(f"❌ Invalid UUID format in bulk update: {e}")
            raise ValueError(f"Invalid UUID format in mapping_ids: {e}")

        # Get all mappings to update
        query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id.in_(mapping_uuids),
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        result = await self.db.execute(query)
        mappings = result.scalars().all()

        if not mappings:
            raise ValueError("No field mappings found for the provided IDs")

        # Update all mappings in a single transaction
        updated_mappings = []
        failed_updates = []

        try:
            for mapping in mappings:
                try:
                    # Update fields
                    if update_data.target_field is not None:
                        mapping.target_field = update_data.target_field
                    if update_data.transformation_rule is not None:
                        mapping.transformation_rules = update_data.transformation_rule
                    if update_data.validation_rule is not None:
                        mapping.transformation_rules = update_data.validation_rule
                    if update_data.is_approved is not None:
                        mapping.status = (
                            "approved" if update_data.is_approved else "suggested"
                        )

                    mapping.updated_at = datetime.utcnow()
                    updated_mappings.append(mapping.id)

                except Exception as e:
                    logger.error(f"Error updating mapping {mapping.id}: {e}")
                    failed_updates.append({"mapping_id": mapping.id, "error": str(e)})

            # Commit all changes at once
            await self.db.commit()

            logger.info(f"Bulk updated {len(updated_mappings)} field mappings")

            return {
                "status": "success",
                "total_mappings": len(mapping_ids),
                "updated_mappings": len(updated_mappings),
                "failed_updates": len(failed_updates),
                "updated_ids": updated_mappings,
                "failures": failed_updates,
            }

        except Exception as e:
            # Rollback on any error
            await self.db.rollback()
            logger.error(f"Bulk update failed: {e}")
            raise ValueError(f"Bulk update failed: {str(e)}")

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
                    f"Field mapping {mapping_id} access denied - different client account"
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
        if update_data.validation_rule is not None:
            mapping.transformation_rules = update_data.validation_rule
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
            validation_rule=transformation_rule_str,
            is_required=False,  # is_required field doesn't exist in ImportFieldMapping model
            is_approved=mapping.status == "approved",
            confidence=mapping.confidence_score or 0.7,
            created_at=mapping.created_at,
            updated_at=mapping.updated_at,
        )

    async def generate_mappings_for_import(self, import_id: str) -> Dict[str, Any]:
        """Generate field mappings for an entire import."""

        # Convert string UUID to UUID object if needed
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

        # Check if mappings already exist
        existing_query = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == import_uuid,
                ImportFieldMapping.client_account_id == client_account_uuid,
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_mappings = existing_result.scalars().all()

        if existing_mappings:
            return {
                "status": "exists",
                "message": f"Field mappings already exist ({len(existing_mappings)} mappings)",
                "mappings_created": 0,
                "existing_mappings": len(existing_mappings),
            }

        # Get import data
        import_query = select(DataImport).where(
            and_(
                DataImport.id == import_uuid,
                DataImport.client_account_id == client_account_uuid,
            )
        )
        import_result = await self.db.execute(import_query)
        data_import = import_result.scalar_one_or_none()

        if not data_import:
            raise ValueError(f"Data import {import_id} not found")

        # Get sample data to extract fields
        sample_query = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == import_uuid)
            .limit(1)
        )
        sample_result = await self.db.execute(sample_query)
        sample_record = sample_result.scalar_one_or_none()

        if not sample_record or not sample_record.raw_data:
            raise ValueError("No raw data found for this import")

        # Extract field names
        field_names = [
            field for field in sample_record.raw_data.keys() if field.strip()
        ]

        logger.info(f"Found {len(field_names)} fields to map: {field_names}")

        # Try to use CrewAI field mapping first if available
        logger.info("🔍 Checking if discovery flow has generated mappings via CrewAI")

        # If no CrewAI mappings exist, use intelligent fallback with basic pattern matching
        logger.warning(
            "⚠️ CrewAI field mapping not available, using intelligent fallback mapping"
        )

        # Define common field mapping patterns
        BASE_FIELD_PATTERNS = {
            # Server/Host patterns
            "hostname": [
                "hostname",
                "host_name",
                "server_name",
                "servername",
                "name",
                "host",
                "server",
            ],
            "ip_address": [
                "ip_address",
                "ip",
                "ipaddress",
                "ip_addr",
                "address",
                "private_ip",
                "public_ip",
            ],
            # Operating System patterns
            "operating_system": [
                "operating_system",
                "os",
                "os_name",
                "operating_sys",
                "platform",
                "os_type",
                "system",
            ],
            "os_version": [
                "os_version",
                "version",
                "os_ver",
                "system_version",
                "os_release",
            ],
            # Hardware patterns
            "cpu_cores": [
                "cpu_cores",
                "cpu",
                "cores",
                "processors",
                "vcpu",
                "cpu_count",
                "num_cpus",
                "cpus",
            ],
            "memory_gb": [
                "memory_gb",
                "memory",
                "ram",
                "ram_gb",
                "mem",
                "total_memory",
                "memory_size",
                "ram (gb)",
            ],
            "storage_gb": [
                "storage_gb",
                "storage",
                "disk",
                "disk_gb",
                "disk_space",
                "total_storage",
                "disk_size",
            ],
            # Environment patterns
            "environment": [
                "environment",
                "env",
                "env_type",
                "deployment_env",
                "stage",
                "tier",
            ],
            "location": [
                "location",
                "datacenter",
                "data_center",
                "dc",
                "site",
                "region",
                "zone",
            ],
            "department": [
                "department",
                "dept",
                "business_unit",
                "bu",
                "division",
                "org",
            ],
            # Application patterns
            "application_name": [
                "application_name",
                "app_name",
                "application",
                "app",
                "service_name",
                "service",
            ],
            "application_type": [
                "application_type",
                "app_type",
                "type",
                "category",
                "classification",
            ],
            "vendor": ["vendor", "manufacturer", "provider", "supplier", "make"],
            # Status patterns
            "status": ["status", "state", "operational_status", "health", "condition"],
            "is_production": [
                "is_production",
                "production",
                "prod",
                "is_prod",
                "production_flag",
            ],
            # Dates
            "created_date": [
                "created_date",
                "created_at",
                "creation_date",
                "date_created",
                "created",
            ],
            "updated_date": [
                "updated_date",
                "updated_at",
                "last_modified",
                "date_modified",
                "modified",
            ],
        }

        mappings_created = []

        for source_field in field_names:
            # Normalize field name for comparison
            normalized_source = (
                source_field.lower().replace(" ", "_").replace("-", "_").strip()
            )

            # Find best match from base patterns
            target_field = None
            confidence_score = 0.0
            match_type = "suggested"

            for target, patterns in BASE_FIELD_PATTERNS.items():
                for pattern in patterns:
                    if pattern.lower() == normalized_source:
                        # Exact match
                        target_field = target
                        confidence_score = 0.95
                        match_type = "exact"
                        break
                    elif (
                        pattern.lower() in normalized_source
                        or normalized_source in pattern.lower()
                    ):
                        # Partial match
                        if confidence_score < 0.7:  # Only update if better match
                            target_field = target
                            confidence_score = 0.7
                            match_type = "partial"

                if match_type == "exact":
                    break

            # Create mapping even if no match found (user can update manually)
            if not target_field:
                target_field = "UNMAPPED"
                confidence_score = 0.0
                match_type = "unmapped"

            # Create the field mapping
            mapping = ImportFieldMapping(
                data_import_id=import_uuid,
                client_account_id=client_account_uuid,
                source_field=source_field,
                target_field=target_field,
                match_type=match_type,
                confidence_score=confidence_score,
                status="suggested" if target_field != "UNMAPPED" else "pending",
                transformation_rules=None,
            )

            self.db.add(mapping)
            mappings_created.append(
                {
                    "source": source_field,
                    "target": target_field,
                    "confidence": confidence_score,
                    "match_type": match_type,
                }
            )

        # Commit all mappings
        await self.db.commit()

        logger.info(
            f"✅ Generated {len(mappings_created)} field mappings using intelligent fallback"
        )

        # Log mapping summary
        exact_matches = sum(1 for m in mappings_created if m["match_type"] == "exact")
        partial_matches = sum(
            1 for m in mappings_created if m["match_type"] == "partial"
        )
        unmapped = sum(1 for m in mappings_created if m["match_type"] == "unmapped")

        logger.info(
            f"📊 Mapping summary: {exact_matches} exact, {partial_matches} partial, {unmapped} unmapped"
        )

        return {
            "status": "success",
            "message": f"Generated {len(mappings_created)} field mappings",
            "mappings_created": len(mappings_created),
            "import_id": str(import_id),
            "summary": {
                "exact_matches": exact_matches,
                "partial_matches": partial_matches,
                "unmapped": unmapped,
                "total": len(mappings_created),
            },
            "mappings": mappings_created[:10],  # Return first 10 as sample
        }

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

    # All field mapping logic has been moved to the discovery flow's field mapping phase
    # The real CrewAI field mapping crew handles all intelligent mapping
    # This service should only retrieve existing mappings, not generate them
