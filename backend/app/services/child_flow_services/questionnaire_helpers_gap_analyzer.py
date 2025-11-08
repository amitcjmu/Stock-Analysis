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
from app.models.application_enrichment import ApplicationEnrichment
from app.services.ai_analysis.questionnaire_generator.tools.generation import (
    QuestionnaireGenerationTool,
)
from app.services.collection.gap_to_questionnaire_adapter import (
    GapToQuestionnaireAdapter,
)
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
    adapter = GapToQuestionnaireAdapter()

    # Aggregate gaps from all assets
    all_missing_fields = {}
    all_assets_data = {}
    total_critical_gaps = 0
    total_high_gaps = 0

    for asset_id in asset_ids:
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

        # Load application enrichment if available
        app_result = await db.execute(
            select(ApplicationEnrichment).where(
                ApplicationEnrichment.asset_id == asset_id,
                ApplicationEnrichment.client_account_id == context.client_account_id,
                ApplicationEnrichment.engagement_id == context.engagement_id,
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

        # Transform report to questionnaire input
        asset_data_gaps, asset_business_context = (
            await adapter.transform_to_questionnaire_input(
                gap_report=gap_report,
                context=context,
                db=db,
            )
        )

        # Merge into aggregate structures
        asset_id_str = str(asset_id)
        if asset_id_str in asset_data_gaps.get("missing_critical_fields", {}):
            all_missing_fields[asset_id_str] = asset_data_gaps[
                "missing_critical_fields"
            ][asset_id_str]

        all_assets_data[asset_id_str] = {
            "name": asset.name,
            "type": asset.asset_type,
            "completeness": gap_report.overall_completeness,
            "assessment_ready": gap_report.assessment_ready,
        }

        # Aggregate gap counts
        metadata = asset_business_context.get("gap_analysis_metadata", {})
        total_critical_gaps += metadata.get("critical_gaps", 0)
        total_high_gaps += metadata.get("high_gaps", 0)

    # Build consolidated data_gaps structure
    data_gaps = {
        "missing_critical_fields": all_missing_fields,
        "data_quality_issues": {},  # Can be enhanced with enrichment gaps
        "assets_with_gaps": [
            str(aid) for aid in asset_ids if str(aid) in all_missing_fields
        ],
    }

    # Build consolidated business context
    business_context = {
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "collection_flow_id": str(child_flow.id),
        "total_assets": len(asset_ids),
        "assets": all_assets_data,
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
    Generate questionnaires using QuestionnaireGenerationTool with GapAnalyzer data.

    This is a wrapper around the existing QuestionnaireGenerationTool that accepts
    data from GapAnalyzer. No changes needed to the tool itself - the adapter
    ensures format compatibility.

    Args:
        data_gaps: Data gaps dictionary from GapAnalyzer
        business_context: Business context dictionary

    Returns:
        Generation result dictionary with sections and questions
    """
    logger.info(
        "Generating questionnaires from GapAnalyzer data "
        f"({len(data_gaps.get('missing_critical_fields', {}))} assets with gaps)"
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
