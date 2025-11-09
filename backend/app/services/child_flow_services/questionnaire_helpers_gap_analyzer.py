"""
Questionnaire Generation with GapAnalyzer Integration

Enhanced helpers that use GapAnalyzer for intelligent questionnaire generation.
Provides backward-compatible wrapper for existing questionnaire_helpers.py.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System - Day 14
Author: CC (Claude Code)
GPT-5 Recommendations: #1 (tenant scoping), #3 (async), #8 (JSON safety)
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.canonical_applications import CanonicalApplication
from app.services.gap_detection.gap_analyzer import GapAnalyzer

logger = logging.getLogger(__name__)


async def prepare_gap_data_with_analyzer(
    db: AsyncSession,
    context: RequestContext,
    asset_ids: List[UUID],
    child_flow,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Prepare gap data using GapAnalyzer for comprehensive multi-layer analysis.

    This function replaces the legacy prepare_gap_data() which relied on
    CollectionDataGap table. The new approach uses GapAnalyzer for real-time
    analysis across all data layers.

    Args:
        db: Database session
        context: Request context with tenant scoping
        asset_ids: List of asset UUIDs to analyze
        child_flow: Collection flow entity

    Returns:
        Tuple of (data_gaps dict, business_context dict) for questionnaire generation

    Performance: <200ms for typical engagement (per implementation plan target)
    """
    logger.info(
        f"Analyzing gaps for {len(asset_ids)} assets using GapAnalyzer (Issue #980)"
    )

    # Initialize services
    gap_analyzer = GapAnalyzer()

    # CRITICAL FIX (Issue #980): Import GapPriority for direct gap counting
    from app.services.gap_detection.schemas import GapPriority

    # Aggregate gaps from all assets
    all_assets_data = {}
    total_critical_gaps = 0
    total_high_gaps = 0
    gap_reports = []  # Store gap reports for direct questionnaire generation

    for asset_id in asset_ids:
        asset_id_str = str(asset_id)  # Define early for use in all_assets_data
        # Load asset and application data
        asset_result = await db.execute(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        asset = asset_result.scalar_one_or_none()

        if not asset:
            logger.warning(f"Asset {asset_id} not found, skipping")
            continue

        # Load canonical application if available (match by asset name)
        app_result = await db.execute(
            select(CanonicalApplication).where(
                CanonicalApplication.canonical_name == asset.name,
                CanonicalApplication.client_account_id == context.client_account_id,
                CanonicalApplication.engagement_id == context.engagement_id,
            )
        )
        application = app_result.scalar_one_or_none()

        # Run comprehensive gap analysis
        gap_report = await gap_analyzer.analyze_asset(
            asset=asset,
            application=application,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            db=db,
        )

        # CRITICAL FIX (Issue #980): Store gap_reports directly instead of transforming
        # This allows direct gap-to-questionnaire generation without critical attributes mapping
        gap_reports.append(gap_report)

        all_assets_data[asset_id_str] = {
            "name": asset.name,
            "type": asset.asset_type,
            "completeness": gap_report.overall_completeness,
            "assessment_ready": gap_report.is_ready_for_assessment,
        }

        # Aggregate gap counts directly from gap_report
        critical_gaps = [
            g for g in gap_report.all_gaps if g.priority == GapPriority.CRITICAL
        ]
        high_gaps = [g for g in gap_report.all_gaps if g.priority == GapPriority.HIGH]
        total_critical_gaps += len(critical_gaps)
        total_high_gaps += len(high_gaps)

    # CRITICAL FIX (Issue #980): Build data_gaps with gap_reports for direct generation
    data_gaps = {
        "gap_reports": gap_reports,  # Pass gap reports directly for Issue #980 compliance
        "assets_with_gaps": [str(aid) for aid in asset_ids],  # All analyzed assets
    }

    # Build consolidated business context
    # CRITICAL FIX (Issue #980): Include context and db for direct gap generation
    business_context = {
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "collection_flow_id": str(child_flow.id),
        "total_assets": len(asset_ids),
        "assets": all_assets_data,
        "context": context,  # Pass context for direct gap generation
        "db": db,  # Pass db for direct gap generation
        "gap_analysis_metadata": {
            "analyzer_version": "GapAnalyzer-v1.0",
            "total_assets_analyzed": len(asset_ids),
            "assets_with_gaps": len(data_gaps["assets_with_gaps"]),
            "total_critical_gaps": total_critical_gaps,
            "total_high_gaps": total_high_gaps,
            "source": "issue_980_intelligent_gap_detection",
        },
    }

    logger.info(
        f"GapAnalyzer processed {len(asset_ids)} assets: "
        f"{len(data_gaps['assets_with_gaps'])} with gaps "
        f"(critical: {total_critical_gaps}, high: {total_high_gaps})"
    )

    return data_gaps, business_context


async def generate_questionnaires_from_analyzer(
    data_gaps: Dict[str, Any], business_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate questionnaires DIRECTLY from GapAnalyzer gaps (Issue #980).

    This bypasses the critical attributes mapping system and generates questions
    directly from the gaps identified by GapAnalyzer. This ensures that ALL gaps
    blocking assessment readiness are included in the questionnaire.

    Args:
        data_gaps: Data gaps dictionary from GapAnalyzer (contains gap_reports)
        business_context: Business context dictionary

    Returns:
        Generation result dictionary with sections and questions
    """
    logger.info("Generating questionnaires DIRECTLY from GapAnalyzer gaps (Issue #980)")

    # CRITICAL FIX: Use direct gap-to-questionnaire generation
    # Check if we have gap_reports (from GapAnalyzer) or missing_critical_fields (old format)
    if "gap_reports" in data_gaps:
        # New format: Direct gap reports from GapAnalyzer
        from app.services.collection.gap_to_questionnaire_adapter import (
            GapToQuestionnaireAdapter,
        )

        adapter = GapToQuestionnaireAdapter()

        # Process each gap report
        all_sections = []
        total_questions = 0

        for gap_report in data_gaps["gap_reports"]:
            result = await adapter.generate_questionnaire_from_gaps(
                gap_report=gap_report,
                context=business_context.get("context"),  # Extract context if embedded
                db=business_context.get("db"),  # Extract db if embedded
            )
            all_sections.extend(result.get("questionnaires", []))
            total_questions += result.get("metadata", {}).get("total_questions", 0)

        return {
            "status": "success",
            "questionnaires": all_sections,
            "metadata": {
                "total_sections": len(all_sections),
                "total_questions": total_questions,
                "generation_method": "direct_gap_analysis",  # Flag for Issue #980
            },
        }
    else:
        # Fallback to old critical attributes system (for backward compatibility)
        logger.warning(
            "Using deprecated QuestionnaireGenerationTool with critical attributes mapping. "
            "Consider migrating to direct gap analysis (Issue #980)."
        )
        from app.services.ai_analysis.questionnaire_generator.tools.generation import (
            QuestionnaireGenerationTool,
        )

        tool = QuestionnaireGenerationTool()
        result = await tool._arun(
            data_gaps=data_gaps,
            business_context=business_context,
        )

        logger.info(
            f"Generated {result.get('metadata', {}).get('total_sections', 0)} sections "
            f"with {result.get('metadata', {}).get('total_questions', 0)} questions"
        )

        return result


async def analyze_and_generate_questionnaires(
    db: AsyncSession,
    context: RequestContext,
    asset_ids: List[UUID],
    child_flow,
) -> Dict[str, Any]:
    """
    One-shot function: analyze gaps and generate questionnaires.

    Convenience function that combines gap analysis and questionnaire generation
    into a single call. Ideal for new implementations.

    Args:
        db: Database session
        context: Request context
        asset_ids: List of asset UUIDs
        child_flow: Collection flow entity

    Returns:
        Questionnaire generation result

    Example:
        result = await analyze_and_generate_questionnaires(
            db=db,
            context=context,
            asset_ids=[asset.id for asset in assets],
            child_flow=flow,
        )
        sections = result.get("questionnaires", [])
    """
    # Step 1: Analyze gaps
    data_gaps, business_context = await prepare_gap_data_with_analyzer(
        db=db,
        context=context,
        asset_ids=asset_ids,
        child_flow=child_flow,
    )

    # Step 2: Generate questionnaires
    result = await generate_questionnaires_from_analyzer(
        data_gaps=data_gaps,
        business_context=business_context,
    )

    return result


__all__ = [
    "prepare_gap_data_with_analyzer",
    "generate_questionnaires_from_analyzer",
    "analyze_and_generate_questionnaires",
]
