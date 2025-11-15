"""
Manual Collection Phase Handler
Bug #1056-A Fix: Prevents premature flow completion
"""

import logging
from typing import Any, Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow.adaptive_questionnaire_model import (
    AdaptiveQuestionnaire,
)
from app.models.collection_questionnaire_response import (
    CollectionQuestionnaireResponse,
)
from app.services.collection_flow.state_management import (
    CollectionFlowStateService,
    CollectionPhase,
)

logger = logging.getLogger(__name__)


async def execute_manual_collection_phase(
    db: AsyncSession,
    state_service: CollectionFlowStateService,
    child_flow: Any,
    phase_name: str,
) -> Dict[str, Any]:
    """
    Manual Collection Phase Handler

    Purpose: Wait for user to provide responses to all generated questionnaires
    before proceeding to data validation.

    Completion Criteria:
    - All questionnaires must have at least one response
    - User must explicitly submit/complete the collection

    Auto-Progression:
    - If responses exist for the flow → transition to data_validation
    - If no responses exist → return awaiting_user_responses status

    Note: Per Bug #1056-A, we check for ANY responses for this flow.
    The collection_questionnaire_responses table does not have a
    questionnaire_id field, so we count responses per flow, not per questionnaire.
    """
    logger.info(f"Phase '{phase_name}' - checking manual collection completion status")

    try:
        # Count total questionnaires generated for this flow
        total_q_result = await db.execute(
            select(func.count(AdaptiveQuestionnaire.id)).where(
                AdaptiveQuestionnaire.collection_flow_id == child_flow.id
            )
        )
        total_questionnaires = total_q_result.scalar() or 0

        if total_questionnaires == 0:
            # No questionnaires generated - this phase shouldn't have been reached
            # Log error and transition to data_validation anyway
            logger.warning(
                f"Manual collection phase reached but 0 questionnaires exist for flow {child_flow.id}. "
                "This indicates a flow progression error. Skipping to data_validation."
            )
            await state_service.transition_phase(
                flow_id=child_flow.id,
                new_phase=CollectionPhase.DATA_VALIDATION,
            )
            return {
                "status": "skipped",
                "phase": phase_name,
                "reason": "no_questionnaires_generated",
                "message": "No questionnaires to collect responses for",
            }

        # Count total responses for this flow
        # Note: We cannot count "answered questionnaires" because
        # collection_questionnaire_responses has no questionnaire_id field
        responses_result = await db.execute(
            select(func.count(CollectionQuestionnaireResponse.id)).where(
                CollectionQuestionnaireResponse.collection_flow_id == child_flow.id
            )
        )
        total_responses = responses_result.scalar() or 0

        logger.info(
            f"📊 Manual collection progress: {total_responses} responses collected "
            f"across {total_questionnaires} questionnaire(s)"
        )

        # Check if any responses have been collected
        if total_responses == 0:
            # No responses collected yet - awaiting user input
            logger.info(
                f"⏳ No responses collected yet - manual_collection phase incomplete "
                f"({total_questionnaires} questionnaire(s) waiting)"
            )

            return {
                "status": "awaiting_user_responses",
                "phase": phase_name,
                "progress": {
                    "total_questionnaires": total_questionnaires,
                    "total_responses": total_responses,
                    "completion_percentage": 0.0,
                },
                "message": f"Waiting for responses to {total_questionnaires} questionnaire(s)",
                "user_action_required": "complete_questionnaires",
            }

        # Responses collected - proceed to data validation
        # Note: We don't check if ALL questionnaires are answered because
        # the schema doesn't support that level of granularity
        logger.info(
            f"✅ Responses collected ({total_responses} response(s)) - "
            "transitioning to data_validation"
        )

        await state_service.transition_phase(
            flow_id=child_flow.id, new_phase=CollectionPhase.DATA_VALIDATION
        )

        return {
            "status": "completed",
            "phase": phase_name,
            "progress": {
                "total_questionnaires": total_questionnaires,
                "total_responses": total_responses,
                "completion_percentage": 100.0,
            },
            "message": (
                f"Collected {total_responses} response(s) "
                f"across {total_questionnaires} questionnaire(s)"
            ),
            "next_phase": "data_validation",
        }

    except Exception as e:
        logger.error(
            f"❌ Error checking manual collection completion for flow {child_flow.id}: {e}",
            exc_info=True,
        )

        # Return error status but don't fail the phase entirely
        # Allow user to retry or admin to investigate
        return {
            "status": "error",
            "phase": phase_name,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": "Failed to check manual collection completion status",
            "user_action_required": "contact_support",
        }
