"""
Mapping generator utility for creating field mappings from import data.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, RawImportRecord

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

    async def generate_mappings_for_import(self, import_id: str) -> Dict[str, Any]:
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
        from app.models.data_import import ImportFieldMapping

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
        logger.info("🔍 Checking if discovery flow has generated mappings via CrewAI")

        # If no CrewAI mappings exist, use data-driven mapping approach
        logger.warning(
            "⚠️ CrewAI field mapping not available, using data-driven mapping approach"
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
