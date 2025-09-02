"""
Gap Analysis Summary Service

Populates the collection_gap_analysis summary table with structured results.
This service transforms gap analysis results from the phase handlers into
normalized database records for querying and reporting.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionGapAnalysis

logger = logging.getLogger(__name__)


class GapAnalysisSummaryService:
    """Service for managing gap analysis summaries in the collection_gap_analysis table"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def populate_gap_analysis_summary(
        self,
        collection_flow_id: str,
        gap_results: Dict[str, Any],
        context: RequestContext,
    ) -> CollectionGapAnalysis:
        """
        Populate the collection_gap_analysis summary table with gap analysis results.

        Args:
            collection_flow_id: The collection flow UUID (not flow_id)
            gap_results: Gap analysis results from the phase handler
            context: Request context for tenant scoping

        Returns:
            Created CollectionGapAnalysis record
        """
        try:
            # Convert string flow ID to UUID if needed
            if isinstance(collection_flow_id, str):
                collection_flow_uuid = UUID(collection_flow_id)
            else:
                collection_flow_uuid = collection_flow_id

            logger.info(
                f"Populating gap analysis summary for collection flow {collection_flow_uuid}"
            )

            # Extract gap data from results
            identified_gaps = gap_results.get("identified_gaps", [])
            gap_categories = gap_results.get("gap_categories", {})
            recommendations = gap_results.get("recommendations", [])
            sixr_impact = gap_results.get("sixr_impact", {})

            # Categorize gaps into critical and optional
            critical_gaps = []
            optional_gaps = []

            for gap in identified_gaps:
                gap_entry = {
                    "field_name": gap.get("field_name", gap.get("name", "unknown")),
                    "category": gap.get("category", "unknown"),
                    "impact": gap.get("business_impact", gap.get("impact", "unknown")),
                    "collection_method": gap.get("recommended_method", "manual"),
                    "description": gap.get("description", ""),
                    "required": gap.get("required", True),
                }

                # Classify by priority/severity
                priority = gap.get("priority", "").lower()
                severity = gap.get("severity", "").lower()

                if priority in ["critical", "high"] or severity in ["critical", "high"]:
                    critical_gaps.append(gap_entry)
                else:
                    optional_gaps.append(gap_entry)

            # Build gap categories mapping
            processed_categories = {}
            for category, fields in gap_categories.items():
                if isinstance(fields, list):
                    processed_categories[category] = fields
                else:
                    # Handle cases where fields might be a dict or other structure
                    processed_categories[category] = [str(fields)]

            # Calculate metrics
            total_fields_required = gap_results.get("total_fields", 0) or len(
                identified_gaps
            )
            fields_collected = gap_results.get("fields_collected", 0)

            if total_fields_required == 0:
                total_fields_required = len(identified_gaps) + fields_collected

            fields_missing = len(identified_gaps)

            # Calculate completeness percentage
            if total_fields_required > 0:
                completeness_percentage = round(
                    (fields_collected / total_fields_required) * 100, 2
                )
            else:
                completeness_percentage = 100.0

            # Extract quality metrics
            data_quality_score = gap_results.get("quality_score")
            if data_quality_score is None:
                data_quality_score = sixr_impact.get("data_quality_score")

            confidence_level = gap_results.get("confidence")
            if confidence_level is None:
                confidence_level = sixr_impact.get("confidence_score")

            automation_coverage = gap_results.get("automation_coverage")

            # Build questionnaire requirements
            questionnaire_requirements = gap_results.get("questionnaire_specs", {})
            if not questionnaire_requirements and critical_gaps:
                # Generate basic questionnaire requirements if none provided
                questionnaire_requirements = {
                    "required_questionnaires": len(critical_gaps),
                    "critical_fields": [gap["field_name"] for gap in critical_gaps],
                    "collection_methods": list(
                        set(
                            gap["collection_method"]
                            for gap in critical_gaps + optional_gaps
                        )
                    ),
                }

            # Check if summary already exists (update vs create)
            existing_result = await self.db.execute(
                select(CollectionGapAnalysis).where(
                    CollectionGapAnalysis.collection_flow_id == collection_flow_uuid,
                    CollectionGapAnalysis.client_account_id
                    == context.client_account_id,
                    CollectionGapAnalysis.engagement_id == context.engagement_id,
                )
            )
            existing_summary = existing_result.scalar_one_or_none()

            if existing_summary:
                # Update existing record
                existing_summary.total_fields_required = total_fields_required
                existing_summary.fields_collected = fields_collected
                existing_summary.fields_missing = fields_missing
                existing_summary.completeness_percentage = completeness_percentage
                existing_summary.data_quality_score = data_quality_score
                existing_summary.confidence_level = confidence_level
                existing_summary.automation_coverage = automation_coverage
                existing_summary.critical_gaps = critical_gaps
                existing_summary.optional_gaps = optional_gaps
                existing_summary.gap_categories = processed_categories
                existing_summary.recommended_actions = recommendations
                existing_summary.questionnaire_requirements = questionnaire_requirements
                existing_summary.updated_at = datetime.utcnow()

                gap_summary = existing_summary
                logger.info(
                    f"Updated existing gap analysis summary for flow {collection_flow_uuid}"
                )

            else:
                # Create new summary record
                gap_summary = CollectionGapAnalysis(
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    collection_flow_id=collection_flow_uuid,
                    total_fields_required=total_fields_required,
                    fields_collected=fields_collected,
                    fields_missing=fields_missing,
                    completeness_percentage=completeness_percentage,
                    data_quality_score=data_quality_score,
                    confidence_level=confidence_level,
                    automation_coverage=automation_coverage,
                    critical_gaps=critical_gaps,
                    optional_gaps=optional_gaps,
                    gap_categories=processed_categories,
                    recommended_actions=recommendations,
                    questionnaire_requirements=questionnaire_requirements,
                )

                self.db.add(gap_summary)
                logger.info(
                    f"Created new gap analysis summary for flow {collection_flow_uuid}"
                )

            # Use atomic transaction pattern
            await self.db.flush()

            logger.info(
                f"Gap analysis summary: {len(critical_gaps)} critical gaps, "
                f"{len(optional_gaps)} optional gaps, "
                f"{completeness_percentage}% complete"
            )

            return gap_summary

        except Exception as e:
            logger.error(f"Failed to populate gap analysis summary: {str(e)}")
            # Re-raise to let caller handle transaction rollback
            raise

    async def get_gap_analysis_summary(
        self, collection_flow_id: str, context: RequestContext
    ) -> Optional[CollectionGapAnalysis]:
        """
        Get gap analysis summary for a collection flow.

        Args:
            collection_flow_id: The collection flow UUID
            context: Request context for tenant scoping

        Returns:
            CollectionGapAnalysis record or None if not found
        """
        try:
            # Convert string flow ID to UUID if needed
            if isinstance(collection_flow_id, str):
                collection_flow_uuid = UUID(collection_flow_id)
            else:
                collection_flow_uuid = collection_flow_id

            result = await self.db.execute(
                select(CollectionGapAnalysis).where(
                    CollectionGapAnalysis.collection_flow_id == collection_flow_uuid,
                    CollectionGapAnalysis.client_account_id
                    == context.client_account_id,
                    CollectionGapAnalysis.engagement_id == context.engagement_id,
                )
            )

            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get gap analysis summary: {str(e)}")
            return None

    async def ensure_gap_summary_from_state(
        self, collection_flow_id: str, context: RequestContext
    ) -> Optional[CollectionGapAnalysis]:
        """
        Ensure gap analysis summary exists by extracting from flow state if needed.
        This provides backwards compatibility during the transition period.

        Args:
            collection_flow_id: The collection flow UUID
            context: Request context for tenant scoping

        Returns:
            CollectionGapAnalysis record or None
        """
        try:
            # First check if summary already exists
            existing_summary = await self.get_gap_analysis_summary(
                collection_flow_id, context
            )
            if existing_summary:
                return existing_summary

            # Try to extract from collection flow state if no summary exists
            collection_flow_uuid = (
                UUID(collection_flow_id)
                if isinstance(collection_flow_id, str)
                else collection_flow_id
            )

            flow_result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.id == collection_flow_uuid,
                    CollectionFlow.client_account_id == context.client_account_id,
                    CollectionFlow.engagement_id == context.engagement_id,
                )
            )
            collection_flow = flow_result.scalar_one_or_none()

            if not collection_flow:
                logger.warning(f"Collection flow {collection_flow_id} not found")
                return None

            # Check if gap analysis results exist in persistence_data
            if not collection_flow.persistence_data:
                logger.info(f"No persistence data found for flow {collection_flow_id}")
                return None

            gap_results = collection_flow.persistence_data.get("gap_analysis_results")
            if not gap_results:
                # Also check phase_results for backwards compatibility
                phase_results = collection_flow.persistence_data.get(
                    "phase_results", {}
                )
                gap_results = phase_results.get("gap_analysis")

            if gap_results:
                logger.info(
                    f"Found gap results in persistence data, creating summary for flow {collection_flow_id}"
                )
                summary = await self.populate_gap_analysis_summary(
                    collection_flow_id, gap_results, context
                )
                await self.db.commit()
                return summary

            logger.info(f"No gap analysis results found for flow {collection_flow_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to ensure gap summary from state: {str(e)}")
            return None
