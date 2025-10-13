"""
Mapping generator utility for creating field mappings from import data.
"""

import logging
import os
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, RawImportRecord, ImportFieldMapping

from .mapping_creator import FieldMappingCreator
from .mapping_summarizer import MappingSummarizer
from .pattern_builder import FieldPatternBuilder

logger = logging.getLogger(__name__)


class MappingGenerator:
    """Utility for generating field mappings for imports."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize mapping generator."""
        self.db = db
        self.context = context

    async def generate_mappings_for_import(
        self, import_id: str
    ) -> Dict[str, Any]:  # noqa: C901
        """Generate field mappings for an entire import."""

        # Convert string UUID to UUID object if needed
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
                "message": (
                    f"Field mappings already exist "
                    f"({len(existing_mappings)} mappings)"
                ),
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
        logger.info("🔍 Checking if CrewAI field mapping is available")

        # Check if CrewAI is enabled
        use_crewai = os.getenv("CREWAI_FIELD_MAPPING_ENABLED", "true").lower() == "true"
        bypass_crewai = (
            os.getenv("BYPASS_CREWAI_FOR_FIELD_MAPPING", "false").lower() == "true"
        )

        if use_crewai and not bypass_crewai:
            try:
                logger.info(
                    "🤖 Using persistent field_mapper agent for intelligent field mapping"
                )
                logger.info(
                    f"   Context: client={self.context.client_account_id}, engagement={self.context.engagement_id}"
                )

                # Use the persistent field_mapper agent from TenantScopedAgentPool
                # Per ADR-015, ADR-024: Persistent agents with TenantMemoryManager
                from app.services.persistent_agents.field_mapping_persistent import (
                    execute_field_mapping,
                )
                from app.services.service_registry import ServiceRegistry

                # Get sample data for agent to analyze
                sample_data = []
                sample_query = (
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == import_uuid)
                    .limit(5)  # Get a few samples for analysis
                )
                sample_result = await self.db.execute(sample_query)
                sample_records = sample_result.scalars().all()

                for record in sample_records:
                    if record.raw_data:
                        sample_data.append(record.raw_data)

                if sample_data:
                    # Get service registry instance with required db and context parameters
                    service_registry = ServiceRegistry(self.db, self.context)

                    # Execute field mapping using persistent agent
                    mapping_result = await execute_field_mapping(
                        context=self.context,
                        service_registry=service_registry,
                        raw_data=sample_data,
                    )

                    # Handle both return shapes for resilience (mapped_fields list or mappings dict)
                    has_mapped_fields = mapping_result and mapping_result.get(
                        "mapped_fields"
                    )
                    has_mappings_dict = mapping_result and mapping_result.get(
                        "mappings"
                    )

                    if has_mapped_fields or has_mappings_dict:
                        logger.info(
                            "✅ Persistent field_mapper agent successfully generated field mappings"
                        )
                        logger.info(
                            "   Agent has memory and will improve over time for this client/engagement"
                        )

                        # Convert agent mappings to database format
                        mappings_created = []

                        if has_mapped_fields:
                            # New shape: mapped_fields is a list of mapping objects
                            mapped_fields_list = mapping_result.get("mapped_fields", [])
                            for mapping_info in mapped_fields_list:
                                source_field = mapping_info.get(
                                    "source", mapping_info.get("source_field", "")
                                )
                                target_field = mapping_info.get(
                                    "target",
                                    mapping_info.get("target_field", "UNMAPPED"),
                                )
                                confidence = mapping_info.get(
                                    "confidence",
                                    mapping_info.get("confidence_score", 0.7),
                                )
                                reasoning = mapping_info.get(
                                    "reasoning", "Persistent agent mapping"
                                )

                                # Create database mapping
                                mapping = ImportFieldMapping(
                                    data_import_id=import_uuid,
                                    client_account_id=client_account_uuid,
                                    source_field=source_field,
                                    target_field=target_field,
                                    match_type="ai_generated",
                                    confidence_score=confidence,
                                    status="suggested",
                                    suggested_by="persistent_field_mapper",
                                    transformation_rules=(
                                        {"agent_reasoning": reasoning}
                                        if reasoning
                                        else None
                                    ),
                                )
                                self.db.add(mapping)
                                mappings_created.append(
                                    {
                                        "source": source_field,
                                        "target": target_field,
                                        "confidence": confidence,
                                        "match_type": "ai_generated",
                                    }
                                )
                        else:
                            # Legacy shape: mappings is a dict keyed by source field
                            crewai_mappings = mapping_result.get("mappings", {})

                            # Process all fields, using agent mappings where available
                            for source_field in field_names:
                                if source_field in crewai_mappings:
                                    mapping_info = crewai_mappings[source_field]
                                    if isinstance(mapping_info, dict):
                                        target_field = mapping_info.get(
                                            "target_field", "UNMAPPED"
                                        )
                                        confidence = mapping_info.get("confidence", 0.5)
                                        reasoning = mapping_info.get("reasoning", "")
                                    else:
                                        target_field = mapping_info
                                        confidence = 0.7
                                        reasoning = "Legacy agent mapping"
                                else:
                                    # Field not mapped by agent
                                    target_field = "UNMAPPED"
                                    confidence = 0.0
                                    reasoning = "No match found by agent"

                                # Create database mapping
                                mapping = ImportFieldMapping(
                                    data_import_id=import_uuid,
                                    client_account_id=client_account_uuid,
                                    source_field=source_field,
                                    target_field=target_field,
                                    match_type="ai_generated",
                                    confidence_score=confidence,
                                    status="suggested",
                                    suggested_by="crewai_mapper",
                                    transformation_rules=(
                                        {"agent_reasoning": reasoning}
                                        if reasoning
                                        else None
                                    ),
                                )
                                self.db.add(mapping)
                                mappings_created.append(
                                    {
                                        "source": source_field,
                                        "target": target_field,
                                        "confidence": confidence,
                                        "match_type": "ai_generated",
                                    }
                                )

                        # Commit all mappings
                        await self.db.commit()

                        return MappingSummarizer.create_mapping_summary(
                            mappings_created, import_id
                        )

            except Exception as e:
                logger.error(
                    f"⚠️ FIELD_MAPPING_AGENT_UNAVAILABLE: {e}",
                    exc_info=True,
                    extra={"error_code": "FIELD_MAPPING_AGENT_UNAVAILABLE"},
                )
                logger.warning("   Falling back to heuristic field mapping")

        # If CrewAI not available or failed, use data-driven mapping approach
        logger.warning(
            "⚠️ Using heuristic field mapping approach (CrewAI not available or disabled)"
        )

        # Get all available target fields from the assets table schema
        from app.api.v1.endpoints.data_import.handlers.field_handler import (
            get_assets_table_fields,
        )

        try:
            available_target_fields = await get_assets_table_fields(self.db)
            target_field_names = [field["name"] for field in available_target_fields]
            logger.info(
                f"Found {len(target_field_names)} available target fields "
                f"from database schema"
            )
        except Exception as e:
            logger.warning(
                f"Could not get target fields from database: {e}, using basic fallback"
            )
            # Minimal fallback for core fields only
            target_field_names = [
                "asset_name",
                "hostname",
                "ip_address",
                "operating_system",
                "cpu_cores",
                "memory_gb",
                "storage_gb",
                "environment",
            ]

        # Create intelligent field mapping patterns based on available target fields
        BASE_FIELD_PATTERNS = FieldPatternBuilder.build_field_patterns(
            target_field_names
        )

        logger.info(
            f"Built {len(BASE_FIELD_PATTERNS)} field patterns from "
            f"available target fields"
        )

        mappings_created = []
        mapping_creator = FieldMappingCreator(self.db)

        # Only create mappings for fields that actually exist in the uploaded data
        logger.info(
            f"Creating mappings for {len(field_names)} source fields "
            f"from uploaded data: {field_names}"
        )

        for source_field in field_names:
            mapping_result = mapping_creator.create_field_mapping(
                source_field, BASE_FIELD_PATTERNS, import_uuid, client_account_uuid
            )
            mappings_created.append(mapping_result)

        # Commit all mappings
        await self.db.commit()

        # Create summary using utility
        return MappingSummarizer.create_mapping_summary(mappings_created, import_id)
