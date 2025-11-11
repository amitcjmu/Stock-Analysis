"""
Legacy Transformer for Backward Compatibility

Transforms gaps to legacy critical attributes format.
DEPRECATED: Use adapter.generate_questionnaire_from_gaps() instead.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.gap_detection.schemas import (
    ComprehensiveGapReport,
    FieldGap,
    GapPriority,
)

logger = logging.getLogger(__name__)


class LegacyTransformer:
    """Handles legacy transformation format for backward compatibility."""

    async def transform(
        self,
        gap_report: ComprehensiveGapReport,
        context: RequestContext,
        db: AsyncSession,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Transform ComprehensiveGapReport into legacy questionnaire format.

        Args:
            gap_report: Comprehensive gap analysis report from GapAnalyzer
            context: Request context with tenant scoping
            db: Database session for additional lookups

        Returns:
            Tuple of (data_gaps dict, business_context dict)
        """
        logger.info(
            f"Transforming gap report for asset {gap_report.asset_id} "
            f"with {len(gap_report.all_gaps)} total gaps"
        )

        # Extract critical and high priority gaps only
        priority_gaps = self._filter_priority_gaps(gap_report)

        # Group gaps by asset (supporting multi-asset future expansion)
        missing_critical_fields = self._build_missing_fields_map(
            priority_gaps, gap_report.asset_id
        )

        # Build data_gaps structure
        data_gaps = {
            "missing_critical_fields": missing_critical_fields,
            "data_quality_issues": {},  # Can be enhanced with enrichment gaps
            "assets_with_gaps": [str(gap_report.asset_id)],
        }

        # CRITICAL FIX: Get actual asset name from database for questionnaire context
        from sqlalchemy import select
        from app.models.asset import Asset

        asset_name = str(gap_report.asset_id)  # Fallback to UUID
        asset_type = "application"  # Default

        asset_result = await db.execute(
            select(Asset).where(Asset.id == gap_report.asset_id)
        )
        asset = asset_result.scalar_one_or_none()
        if asset:
            asset_name = asset.name or asset.asset_name or str(gap_report.asset_id)
            asset_type = asset.asset_type or "application"

        # Build business context
        business_context = {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "total_assets": 1,  # Single asset for now
            "assets": {
                str(gap_report.asset_id): {
                    "name": asset_name,  # CRITICAL FIX: Use actual asset name, not UUID
                    "type": asset_type,  # Use actual asset type
                }
            },
            "gap_analysis_metadata": {
                "overall_completeness": gap_report.overall_completeness,
                "assessment_ready": gap_report.is_ready_for_assessment,
                "total_gaps_found": len(gap_report.all_gaps),
                "critical_gaps": len(
                    [
                        g
                        for g in gap_report.all_gaps
                        if g.priority == GapPriority.CRITICAL
                    ]
                ),
                "high_gaps": len(
                    [g for g in gap_report.all_gaps if g.priority == GapPriority.HIGH]
                ),
            },
        }

        logger.info(
            f"Transformed {len(priority_gaps)} priority gaps into questionnaire input "
            f"(critical: {business_context['gap_analysis_metadata']['critical_gaps']}, "
            f"high: {business_context['gap_analysis_metadata']['high_gaps']})"
        )

        return data_gaps, business_context

    def _filter_priority_gaps(
        self, gap_report: ComprehensiveGapReport
    ) -> List[FieldGap]:
        """
        Filter gaps to only critical and high priority.

        Medium and low priority gaps are excluded to avoid overwhelming users
        with questionnaires. These can be collected through less intrusive means.
        """
        priority_gaps = [
            gap
            for gap in gap_report.all_gaps
            if gap.priority in [GapPriority.CRITICAL, GapPriority.HIGH]
        ]

        logger.debug(
            f"Filtered {len(priority_gaps)} priority gaps from {len(gap_report.all_gaps)} total gaps"
        )

        return priority_gaps

    def _build_missing_fields_map(
        self, priority_gaps: List[FieldGap], asset_id: UUID
    ) -> Dict[str, List[str]]:
        """
        Build missing_critical_fields map for questionnaire generation.

        Format: {"asset_id": ["field_name1", "field_name2", ...]}

        This format is required by QuestionnaireGenerationTool._process_missing_fields()
        which expects a dict mapping asset_id to list of field names (NOT field objects).
        """
        asset_id_str = str(asset_id)
        field_names = []

        for gap in priority_gaps:
            # Extract field name from gap
            # FieldGap.field_name contains the actual field name
            if gap.field_name:
                field_names.append(gap.field_name)

        logger.debug(
            f"Built missing fields map with {len(field_names)} fields for asset {asset_id_str}"
        )

        return {asset_id_str: field_names} if field_names else {}


__all__ = ["LegacyTransformer"]
