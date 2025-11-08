"""
Gap-to-Questionnaire Adapter

Bridges GapAnalyzer ComprehensiveGapReport to IntelligentQuestionnaireGenerator.
Transforms multi-layer gap analysis into targeted questionnaire generation.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 14
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #8 (JSON safety)
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


class GapToQuestionnaireAdapter:
    """
    Adapter that transforms ComprehensiveGapReport into questionnaire generation input.

    This adapter is the bridge between the new gap detection system (GapAnalyzer)
    and the existing questionnaire generation system (IntelligentQuestionnaireGenerator).

    Key Features:
    - Prioritizes critical/high gaps for questionnaire generation
    - Preserves asset context and gap metadata
    - Filters out low-priority gaps to reduce noise
    - Maintains backward compatibility with existing questionnaire format
    """

    def __init__(self):
        """Initialize the adapter."""
        pass

    async def transform_to_questionnaire_input(
        self,
        gap_report: ComprehensiveGapReport,
        context: RequestContext,
        db: AsyncSession,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Transform ComprehensiveGapReport into questionnaire generation inputs.

        This method extracts critical and high-priority gaps from the comprehensive
        report and formats them for the IntelligentQuestionnaireGenerator.

        Args:
            gap_report: Comprehensive gap analysis report from GapAnalyzer
            context: Request context with tenant scoping
            db: Database session for additional lookups

        Returns:
            Tuple of (data_gaps dict, business_context dict) formatted for
            QuestionnaireGenerationTool._arun()

        Performance: O(n) where n = total gaps, target <10ms for typical reports
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

        # Build business context
        business_context = {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "total_assets": 1,  # Single asset for now
            "assets": {
                str(gap_report.asset_id): {
                    "name": gap_report.asset_id,  # Will be resolved by questionnaire tool
                    "type": "application",  # Default, can be enhanced
                }
            },
            "gap_analysis_metadata": {
                "overall_completeness": gap_report.overall_completeness,
                "assessment_ready": gap_report.assessment_ready,
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

        Args:
            gap_report: Comprehensive gap report

        Returns:
            List of FieldGap objects with priority >= HIGH
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

        Args:
            priority_gaps: List of high-priority gaps
            asset_id: Asset UUID

        Returns:
            Dict mapping asset_id to list of missing field names
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

    async def enhance_with_existing_data(
        self,
        data_gaps: Dict[str, Any],
        asset_id: UUID,
        db: AsyncSession,
        context: RequestContext,
    ) -> Dict[str, Any]:
        """
        Enhance data_gaps with existing field values for pre-fill.

        This allows the questionnaire to show existing values for verification
        rather than asking for completely new input.

        Args:
            data_gaps: Base data_gaps dict
            asset_id: Asset UUID
            db: Database session
            context: Request context

        Returns:
            Enhanced data_gaps dict with existing_field_values
        """
        # Query asset and application enrichment data
        from sqlalchemy import select

        from app.models.asset import Asset

        result = await db.execute(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        asset = result.scalar_one_or_none()

        if not asset:
            logger.warning(f"Asset {asset_id} not found for data enhancement")
            return data_gaps

        # Build existing field values map
        existing_values = {}
        if asset.operating_system:
            existing_values["operating_system"] = asset.operating_system
        if asset.ip_address:
            existing_values["ip_address"] = asset.ip_address

        # Add enrichment data if available
        if hasattr(asset, "enrichment_data") and asset.enrichment_data:
            enrichment = asset.enrichment_data
            if enrichment.database_version:
                existing_values["database_version"] = enrichment.database_version
            if enrichment.backup_frequency:
                existing_values["backup_frequency"] = enrichment.backup_frequency

        # Add to data_gaps
        if existing_values:
            data_gaps["existing_field_values"] = {str(asset_id): existing_values}
            logger.debug(
                f"Enhanced data_gaps with {len(existing_values)} existing field values"
            )

        return data_gaps


__all__ = ["GapToQuestionnaireAdapter"]
