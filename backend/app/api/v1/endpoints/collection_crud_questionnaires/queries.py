"""
Query operations for collection questionnaires.
Read-only functions for retrieving questionnaire and related data.
"""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

# Import modular functions
from app.api.v1.endpoints import collection_serializers
from app.api.v1.endpoints.questionnaire_templates import (
    get_bootstrap_questionnaire_template,
)

from .commands import _start_agent_generation
from .utils import (
    _convert_template_field_to_question,
    _get_selected_application_info,
)

logger = logging.getLogger(__name__)


async def _get_flow_by_id(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> CollectionFlow:
    """Get and validate collection flow by ID."""
    flow_result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == UUID(flow_id),
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.client_account_id == context.client_account_id,
        )
    )
    flow = flow_result.scalar_one_or_none()
    if not flow:
        logger.warning(f"Collection flow not found: {flow_id}")
        raise HTTPException(status_code=404, detail="Collection flow not found")
    return flow


async def _get_existing_questionnaires_tenant_scoped(
    flow: CollectionFlow, db: AsyncSession, context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """Get existing questionnaires from database with tenant scoping."""
    questionnaires_result = await db.execute(
        select(AdaptiveQuestionnaire)
        .where(
            AdaptiveQuestionnaire.collection_flow_id == flow.id,
            AdaptiveQuestionnaire.client_account_id == context.client_account_id,
            AdaptiveQuestionnaire.engagement_id == context.engagement_id,
        )
        .order_by(AdaptiveQuestionnaire.created_at.desc())
    )
    questionnaires = questionnaires_result.scalars().all()

    if questionnaires:
        logger.info(f"Found {len(questionnaires)} questionnaires in database")
        return [
            collection_serializers.build_questionnaire_response(q)
            for q in questionnaires
        ]
    return []


async def _get_existing_assets(
    db: AsyncSession, context: RequestContext
) -> List[Asset]:
    """Get existing assets for engagement."""
    assets_result = await db.execute(
        select(Asset)
        .where(Asset.engagement_id == context.engagement_id)
        .where(Asset.client_account_id == context.client_account_id)
        .order_by(Asset.created_at.desc())
    )
    return list(assets_result.scalars().all())


async def get_adaptive_questionnaires(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Get adaptive questionnaires for a collection flow.

    Returns existing questionnaires if available, otherwise generates new ones
    using AI agent analysis or falls back to template-based generation.
    """
    try:
        logger.info(f"Getting adaptive questionnaires for flow {flow_id}")

        # Get flow with tenant scoping
        flow = await _get_flow_by_id(flow_id, db, context)

        # Check for existing questionnaires in database with tenant scoping
        existing_questionnaires = await _get_existing_questionnaires_tenant_scoped(
            flow, db, context
        )

        if existing_questionnaires:
            logger.info(
                f"Returning {len(existing_questionnaires)} existing questionnaires"
            )
            return existing_questionnaires

        # Get existing assets for this engagement
        existing_assets = await _get_existing_assets(db, context)

        logger.info(f"Found {len(existing_assets)} existing assets for engagement")

        # AI agent generation should be preferred approach
        if flow.flow_metadata and flow.flow_metadata.get("use_agent_generation", True):
            logger.info("Using AI agent generation for questionnaires")
            return await _start_agent_generation(
                flow_id, flow, existing_assets, context, db
            )

        logger.info("Falling back to template-based questionnaire generation")

        # Fall back to template-based generation
        selected_application_name, selected_application_id = (
            _get_selected_application_info(flow, existing_assets)
        )

        # Get template
        template = get_bootstrap_questionnaire_template(
            flow_id, selected_application_id, selected_application_name, existing_assets
        )

        questions = []
        # Note: template returns "form_fields" not "fields"
        for field in template.get("form_fields", []):
            question = _convert_template_field_to_question(
                field, selected_application_name
            )
            questions.append(question)

        return [
            AdaptiveQuestionnaireResponse(
                id=str(UUID("00000000-0000-0000-0000-000000000001")),
                collection_flow_id=flow_id,
                title="Bootstrap Data Collection Questionnaire",
                description="Initial questionnaire to gather essential asset information",
                target_gaps=[],
                questions=questions,
                validation_rules={},
                completion_status="pending",
                responses_collected={},
                created_at=datetime.now(timezone.utc),
            )
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
