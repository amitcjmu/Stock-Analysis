"""
Questionnaire Generation Helpers
Helper functions for questionnaire generation phase in collection flow.

Extracted from collection.py to reduce file complexity (per pre-commit file length check).
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import AdaptiveQuestionnaire
from app.services.ai_analysis.questionnaire_generator.tools.generation import (
    QuestionnaireGenerationTool,
)
from app.services.collection_flow.state_management import (
    CollectionFlowStateService,
    CollectionPhase,
)
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def prepare_gap_data(
    db: AsyncSession,
    context: RequestContext,
    persisted_gaps: List[CollectionDataGap],
    child_flow,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Prepare gap data and business context for questionnaire generation.

    Args:
        db: Database session
        context: Request context
        persisted_gaps: List of CollectionDataGap entities
        child_flow: Collection flow entity

    Returns:
        Tuple of (data_gaps dict, business_context dict)
    """
    # Transform gaps into data_gaps format
    missing_critical_fields = {}
    data_quality_issues = {}
    assets_with_gaps = set()

    for gap in persisted_gaps:
        asset_id = str(gap.asset_id)
        assets_with_gaps.add(asset_id)

        if asset_id not in missing_critical_fields:
            missing_critical_fields[asset_id] = []

        # CRITICAL FIX: Pass field_name as string, not dict
        # group_attributes_by_category expects {"asset_id": ["field_name1", "field_name2"]}
        # NOT {"asset_id": [{"field_name": "...", ...}, ...]}
        missing_critical_fields[asset_id].append(gap.field_name)

    # Load asset information
    assets_result = await db.execute(
        select(Asset).where(
            Asset.id.in_([UUID(aid) for aid in assets_with_gaps]),
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        )
    )
    assets = assets_result.scalars().all()

    # Build business context
    business_context = {
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "collection_flow_id": str(child_flow.id),
        "total_assets": len(assets),
        "assets": {str(a.id): {"name": a.name, "type": a.asset_type} for a in assets},
    }

    data_gaps = {
        "missing_critical_fields": missing_critical_fields,
        "data_quality_issues": data_quality_issues,
        "assets_with_gaps": list(assets_with_gaps),
    }

    return data_gaps, business_context


async def generate_questionnaires(
    data_gaps: Dict[str, Any], business_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate questionnaires using QuestionnaireGenerationTool.

    Args:
        data_gaps: Data gaps dictionary
        business_context: Business context dictionary

    Returns:
        Generation result dictionary
    """
    tool = QuestionnaireGenerationTool()
    return await tool._arun(
        data_gaps=data_gaps,
        business_context=business_context,
    )


async def persist_questionnaires(
    db: AsyncSession,
    context: RequestContext,
    state_service: CollectionFlowStateService,
    generation_result: Dict[str, Any],
    persisted_gaps: List[CollectionDataGap],
    child_flow,
    phase_name: str,
) -> Dict[str, Any]:
    """
    Persist generated questionnaires to database and transition phase.

    Args:
        db: Database session
        context: Request context
        state_service: Collection flow state service
        generation_result: Result from questionnaire generation
        persisted_gaps: List of gaps that were processed
        child_flow: Collection flow entity
        phase_name: Phase name

    Returns:
        Phase execution result dictionary
    """
    questionnaire_sections = generation_result.get("questionnaires", [])

    if not questionnaire_sections:
        logger.warning(
            "No questionnaire sections generated - transitioning to manual_collection"
        )
        await state_service.transition_phase(
            flow_id=child_flow.id,
            new_phase=CollectionPhase.MANUAL_COLLECTION,
        )
        return {
            "status": "success",
            "phase": phase_name,
            "message": "No questionnaires generated",
            "questionnaires_generated": 0,
        }

    # Flatten all questions from all sections into single questionnaire
    all_questions = []
    for section in questionnaire_sections:
        all_questions.extend(section.get("questions", []))

    # CRITICAL FIX: Build target_gaps from persisted_gaps
    # This populates the field that frontend polls to show questionnaires
    target_gaps = []
    for gap in persisted_gaps:
        target_gaps.append(
            {
                "field_name": gap.field_name,
                "gap_type": gap.gap_type,
                "gap_category": gap.gap_category,
                "asset_id": str(gap.asset_id),
                "priority": gap.priority,
                "impact_on_sixr": gap.impact_on_sixr,
            }
        )

    questionnaire = AdaptiveQuestionnaire(
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        collection_flow_id=child_flow.id,
        title="Data Gap Collection Questionnaire",
        description=f"Generated from {len(persisted_gaps)} identified data gaps",
        template_name="gap_based_questionnaire",
        template_type="detailed",
        version="1.0",
        applicable_tiers=["tier_1", "tier_2"],
        questions=all_questions,
        question_count=len(all_questions),
        target_gaps=target_gaps,  # CRITICAL FIX: Populate target_gaps from persisted gaps
        validation_rules={},
        scoring_rules={},
        completion_status="pending",
        responses_collected={},
        is_active=True,
        is_template=False,
        created_at=datetime.now(timezone.utc),
    )

    db.add(questionnaire)
    await db.commit()
    await db.refresh(questionnaire)

    logger.info(
        f"✅ Persisted questionnaire {questionnaire.id} with {len(all_questions)} questions "
        f"from {len(questionnaire_sections)} sections"
    )

    # Auto-transition to manual_collection after successful generation
    await state_service.transition_phase(
        flow_id=child_flow.id,
        new_phase=CollectionPhase.MANUAL_COLLECTION,
    )

    return {
        "status": "success",
        "phase": phase_name,
        "questionnaires_generated": 1,
        "questions_generated": len(all_questions),
        "sections_generated": len(questionnaire_sections),
        "questionnaire_id": str(questionnaire.id),
        "gaps_processed": len(persisted_gaps),
        "metadata": generation_result.get("metadata", {}),
    }
