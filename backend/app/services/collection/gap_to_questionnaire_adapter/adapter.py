"""
Main Adapter Class for Gap-to-Questionnaire Transformation

Coordinates transformation between GapAnalyzer and QuestionnaireGenerator.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.gap_detection.schemas import (
    ComprehensiveGapReport,
    GapPriority,
)

from .question_builder import QuestionBuilder
from .section_builder import SectionBuilder
from .legacy_transformer import LegacyTransformer
from .data_enhancer import DataEnhancer

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
        """Initialize the adapter with helper components."""
        self.question_builder = QuestionBuilder()
        self.section_builder = SectionBuilder(self.question_builder)
        self.legacy_transformer = LegacyTransformer()
        self.data_enhancer = DataEnhancer()

    async def generate_questionnaire_from_gaps(
        self,
        gap_report: ComprehensiveGapReport,
        context: RequestContext,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Generate questionnaire DIRECTLY from GapAnalyzer gaps (Issue #980).

        This bypasses the critical attributes mapping system and generates questions
        directly from the gaps identified by GapAnalyzer. This ensures that ALL gaps
        blocking assessment readiness are included in the questionnaire.

        Args:
            gap_report: Comprehensive gap analysis report from GapAnalyzer
            context: Request context with tenant scoping
            db: Database session for additional lookups

        Returns:
            Questionnaire generation result with sections and questions
        """
        logger.info(
            f"Generating questionnaire DIRECTLY from gaps for asset {gap_report.asset_id} "
            f"with {len(gap_report.all_gaps)} total gaps"
        )

        # CRITICAL: Use gaps with HIGH or CRITICAL priority
        # Note: readiness_blockers contains descriptive strings, not field names,
        # so we filter by priority only
        blocking_gaps = [
            gap
            for gap in gap_report.all_gaps
            if gap.priority in [GapPriority.CRITICAL, GapPriority.HIGH]
        ]

        if not blocking_gaps:
            logger.warning(
                f"No critical or high priority gaps found for asset {gap_report.asset_id}. "
                f"No questionnaire will be generated from gaps."
            )
            # Don't use all gaps as fallback - only generate questions for high-priority gaps
            return []

        logger.info(
            f"Generating questions for {len(blocking_gaps)} blocking gaps "
            f"(out of {len(gap_report.all_gaps)} total gaps)"
        )

        # Get asset info for context
        from sqlalchemy import select
        from app.models.asset import Asset

        asset_result = await db.execute(
            select(Asset).where(Asset.id == gap_report.asset_id)
        )
        asset = asset_result.scalar_one_or_none()
        asset_name = str(gap_report.asset_id)
        asset_type = "application"
        if asset:
            asset_name = asset.name or asset.asset_name or str(gap_report.asset_id)
            asset_type = asset.asset_type or "application"

        # Build sections from gaps using section builder
        sections = self.section_builder.build_sections_from_gaps(
            blocking_gaps, gap_report.asset_id, asset_name, asset_type
        )

        # Build result structure
        all_questions = []
        for section in sections:
            all_questions.extend(section.get("questions", []))

        result = {
            "status": "success",
            "questionnaires": sections,
            "metadata": {
                "total_sections": len(sections),
                "total_questions": len(all_questions),
                "asset_id": str(gap_report.asset_id),
                "asset_name": asset_name,
                "gaps_processed": len(blocking_gaps),
                "total_gaps": len(gap_report.all_gaps),
            },
        }

        logger.info(
            f"✅ Generated {len(sections)} sections with {len(all_questions)} questions "
            f"directly from {len(blocking_gaps)} gaps"
        )

        return result

    async def transform_to_questionnaire_input(
        self,
        gap_report: ComprehensiveGapReport,
        context: RequestContext,
        db: AsyncSession,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Transform ComprehensiveGapReport into questionnaire generation inputs.

        DEPRECATED: This method uses the old critical attributes mapping system.
        Use generate_questionnaire_from_gaps() instead for Issue #980 compliance.

        Args:
            gap_report: Comprehensive gap analysis report from GapAnalyzer
            context: Request context with tenant scoping
            db: Database session for additional lookups

        Returns:
            Tuple of (data_gaps dict, business_context dict) formatted for
            QuestionnaireGenerationTool._arun()

        Performance: O(n) where n = total gaps, target <10ms for typical reports
        """
        logger.warning(
            "Using deprecated transform_to_questionnaire_input() - "
            "consider using generate_questionnaire_from_gaps() for Issue #980 compliance"
        )

        return await self.legacy_transformer.transform(gap_report, context, db)

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
        return await self.data_enhancer.enhance(data_gaps, asset_id, db, context)


__all__ = ["GapToQuestionnaireAdapter"]
