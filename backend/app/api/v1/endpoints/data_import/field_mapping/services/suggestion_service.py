"""
AI-powered field mapping suggestion service.

This service delegates to the canonical FieldMappingService for agent-driven
mapping suggestions, following ADR-015 (persistent agents).
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import import DataImport, RawImportRecord

# Import canonical FieldMappingService for agent-driven mapping intelligence
from app.services.field_mapping_service import FieldMappingService

from ..models.mapping_schemas import FieldMappingAnalysis, FieldMappingSuggestion

logger = logging.getLogger(__name__)


class SuggestionService:
    """
    Service for generating AI-powered field mapping suggestions.

    This service wraps the canonical FieldMappingService to provide
    REST API compatibility while delegating intelligence to agents.
    Follows ADR-015 by using agent-driven logic instead of hardcoded heuristics.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        # Initialize canonical FieldMappingService for agent-driven mapping intelligence
        self._field_mapping_service: FieldMappingService = None

    @property
    def field_mapping_service(self) -> FieldMappingService:
        """Lazy initialization of canonical FieldMappingService."""
        if self._field_mapping_service is None:
            self._field_mapping_service = FieldMappingService(self.db, self.context)
        return self._field_mapping_service

    async def get_field_mapping_suggestions(
        self, import_id: str
    ) -> FieldMappingAnalysis:
        """
        Get AI-powered field mapping suggestions for an import.

        Delegates to canonical FieldMappingService for agent-driven analysis.
        """
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

        # Get sample data for analysis
        sample_query = (
            select(RawImportRecord)
            .where(RawImportRecord.data_import_id == import_id)
            .limit(5)
        )  # Get first 5 records for analysis

        sample_result = await self.db.execute(sample_query)
        sample_records = sample_result.scalars().all()

        if not sample_records:
            raise ValueError("No sample data found for analysis")

        # Extract source fields and sample data
        # CRITICAL: Establish field order from first record to prevent data corruption
        source_fields = []
        sample_data_rows = []

        for idx, record in enumerate(sample_records):
            if record.raw_data:
                if idx == 0:
                    # Establish consistent field order from first record
                    source_fields = list(record.raw_data.keys())
                    logger.info(
                        f"Established field order from first record: {source_fields}"
                    )

                # Ensure values align with established field order
                if source_fields:
                    # Extract values in the same order as source_fields
                    ordered_values = [
                        record.raw_data.get(field) for field in source_fields
                    ]
                    sample_data_rows.append(ordered_values)
                else:
                    # Fallback: if source_fields not established yet (should not happen)
                    sample_data_rows.append(list(record.raw_data.values()))

        if not source_fields:
            raise ValueError("No source fields found in data")

        logger.info(
            f"Analyzing {len(source_fields)} fields with {len(sample_data_rows)} sample records"
        )

        # Delegate to canonical FieldMappingService for agent-driven analysis
        # This follows ADR-015 by using persistent agents instead of hardcoded heuristics
        mapping_analysis = await self.field_mapping_service.analyze_columns(
            columns=source_fields,
            data_import_id=import_uuid,
            master_flow_id=(
                data_import.master_flow_id
                if hasattr(data_import, "master_flow_id")
                else None
            ),
            asset_type="server",  # Default to server, could be enhanced to detect from data
            sample_data=sample_data_rows,
        )

        # Convert canonical MappingAnalysis to REST API FieldMappingAnalysis format
        suggestions = [
            FieldMappingSuggestion(
                source_field=rule.source_field,
                target_field=rule.target_field,
                confidence=rule.confidence,
                transformation_rule=rule.transformation_rule,
                match_type=rule.match_type or "ai_suggested",
            )
            for rule in mapping_analysis.suggested_mappings
        ]

        return FieldMappingAnalysis(
            total_fields=mapping_analysis.total_fields,
            mapped_fields=mapping_analysis.mapped_count,
            unmapped_fields=mapping_analysis.unmapped_count,
            confidence_score=mapping_analysis.avg_confidence,
            suggestions=suggestions,
        )

    async def get_suggestion_confidence_metrics(self, import_id: str) -> Dict[str, Any]:
        """
        Get confidence metrics for suggestions.

        Delegates to canonical FieldMappingService analysis.
        """
        analysis = await self.get_field_mapping_suggestions(import_id)

        confidence_levels = {
            "high": len([s for s in analysis.suggestions if s.confidence >= 0.8]),
            "medium": len(
                [s for s in analysis.suggestions if 0.5 <= s.confidence < 0.8]
            ),
            "low": len([s for s in analysis.suggestions if s.confidence < 0.5]),
        }

        return {
            "total_suggestions": len(analysis.suggestions),
            "confidence_levels": confidence_levels,
            "average_confidence": analysis.confidence_score,
            "ai_generated": len(
                analysis.suggestions
            ),  # All suggestions are now AI-generated
            "pattern_based": 0,  # No hardcoded patterns anymore
        }
