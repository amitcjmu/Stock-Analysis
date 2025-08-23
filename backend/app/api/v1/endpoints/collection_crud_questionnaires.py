"""
Collection Flow Questionnaire Query Operations
Questionnaire-specific read operations for collection flows.
"""

import logging
from datetime import datetime
from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.context import RequestContext
from app.models import User
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for a collection flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of adaptive questionnaires

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # First verify the flow exists and user has access
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # CRITICAL FIX: Check for questionnaires in master flow execution
        # Questionnaires are created during MFO execution in the questionnaire_generation phase
        questionnaires = []

        if flow.master_flow_id:
            logger.info(
                f"Looking for questionnaires from master flow execution: {flow.master_flow_id}"
            )

            # Try to get questionnaires that were created during master flow execution
            # These might be stored in crewai_flow_state_extensions.flow_persistence_data
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            master_flow_result = await db.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow.master_flow_id,
                    CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                )
            )
            master_flow = master_flow_result.scalar_one_or_none()

            if master_flow and master_flow.flow_persistence_data:
                # Check if questionnaires exist in the master flow's persistence data
                persistence_data = master_flow.flow_persistence_data
                if isinstance(persistence_data, dict):
                    # Look for questionnaires in different possible keys
                    questionnaire_data = (
                        persistence_data.get("questionnaires", [])
                        or persistence_data.get("adaptive_questionnaires", [])
                        or persistence_data.get("generated_questionnaires", [])
                        or []
                    )

                    if questionnaire_data:
                        logger.info(
                            f"Found {len(questionnaire_data)} questionnaires in master flow persistence data"
                        )

                        # Convert master flow questionnaire data to AdaptiveQuestionnaireResponse format
                        for idx, q_data in enumerate(questionnaire_data):
                            if isinstance(q_data, dict):
                                questionnaire = AdaptiveQuestionnaireResponse(
                                    id=q_data.get("id", f"generated_{idx}"),
                                    collection_flow_id=flow_id,
                                    title=q_data.get(
                                        "title", f"Generated Questionnaire {idx + 1}"
                                    ),
                                    description=q_data.get(
                                        "description",
                                        "AI-generated questionnaire from gap analysis",
                                    ),
                                    target_gaps=q_data.get("target_gaps", []),
                                    questions=q_data.get("questions", []),
                                    validation_rules=q_data.get("validation_rules", []),
                                    completion_status=q_data.get(
                                        "completion_status", "pending"
                                    ),
                                    responses_collected=q_data.get(
                                        "responses_collected", []
                                    ),
                                    created_at=q_data.get(
                                        "created_at", datetime.utcnow().isoformat()
                                    ),
                                    completed_at=q_data.get("completed_at"),
                                )
                                questionnaires.append(questionnaire)
                    else:
                        logger.info(
                            f"No questionnaire data found in master flow persistence for flow {flow.master_flow_id}"
                        )
                else:
                    logger.info(
                        f"Master flow {flow.master_flow_id} has no valid persistence data"
                    )

        # Fallback: Get questionnaires directly linked to collection flow (legacy approach)
        if not questionnaires:
            logger.info(
                "No master flow questionnaires found, checking direct collection flow questionnaires"
            )
            result = await db.execute(
                select(AdaptiveQuestionnaire)
                .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
                .order_by(AdaptiveQuestionnaire.created_at.desc())
            )
            db_questionnaires = result.scalars().all()

            if db_questionnaires:
                logger.info(
                    f"Found {len(db_questionnaires)} direct questionnaires for collection flow {flow_id}"
                )
                # Convert to response format
                questionnaires = [
                    collection_serializers.serialize_adaptive_questionnaire(q)
                    for q in db_questionnaires
                ]

        logger.debug(
            "Found %d total questionnaires for flow %s",
            len(questionnaires),
            flow_id,
        )

        # If no questionnaires exist yet, provide a bootstrap questionnaire instead of hard failing
        if not questionnaires:
            logger.info(f"No questionnaires found yet for flow {flow_id}")
            logger.debug(
                "About to check applications for engagement %s",
                context.engagement_id,
            )

            # Minimal bootstrap questionnaire to select application(s)
            bootstrap_questionnaire = AdaptiveQuestionnaireResponse(
                id=f"bootstrap_{flow_id}",
                collection_flow_id=flow_id,
                title="Application Selection",
                description=(
                    "Please select one or more applications from your inventory to begin adaptive collection."
                ),
                target_gaps=["application_selection"],
                questions=[
                    {
                        "field_id": "application_name",
                        "question_text": "Which application are we collecting data for?",
                        "field_type": "text",
                        "required": True,
                        "help_text": "Enter the application name exactly as it appears in inventory",
                    },
                    {
                        "field_id": "application_type",
                        "question_text": "What type of application is this?",
                        "field_type": "select",
                        "required": True,
                        "options": [
                            "web",
                            "desktop",
                            "mobile",
                            "service",
                            "batch",
                        ],
                    },
                ],
                validation_rules={
                    "required": ["application_name", "application_type"],
                },
                completion_status="pending",
                responses_collected={},
                created_at=datetime.utcnow(),
                completed_at=None,
            )

            logger.info(
                "Returning bootstrap questionnaire to enable in-form application selection"
            )
            return [bootstrap_questionnaire]

        return [
            (
                collection_serializers.serialize_adaptive_questionnaire(q)
                if hasattr(q, "__dict__") and hasattr(q, "id")
                else q
            )  # Already serialized from master flow data
            for q in questionnaires
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
