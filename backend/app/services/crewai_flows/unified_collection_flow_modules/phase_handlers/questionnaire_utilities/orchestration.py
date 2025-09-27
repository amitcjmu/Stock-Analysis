"""
Questionnaire Utilities - Orchestration

Functions for orchestrating questionnaire generation workflow and integration.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import (
    CollectionFlowError,
    CollectionFlowState,
)
from .utils import get_next_phase_name

logger = logging.getLogger(__name__)


async def check_loop_prevention(
    collection_orchestrator, state: CollectionFlowState, gap_result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Check for infinite loop prevention and return early exit if needed"""
    if not await collection_orchestrator.prevent_infinite_loops(
        state, "questionnaire_generation", max_iterations=2
    ):
        logger.warning(
            f"Skipping questionnaire generation due to loop prevention for flow {state.flow_id}"
        )

        # Get appropriate next phase
        next_phase = get_next_phase_name(state, "")

        return {
            "phase": "questionnaire_generation",
            "status": "skipped",
            "reason": "infinite_loop_prevention",
            "next_phase": next_phase,
        }
    return None


async def record_orchestrator_submission(
    collection_orchestrator,
    state: CollectionFlowState,
    questionnaire_type: str,
    questionnaires: List[Dict[str, Any]],
    identified_gaps: List[Dict[str, Any]],
    form_configs: List[Dict[str, Any]],
) -> None:
    """Record questionnaire generation with orchestrator"""
    from app.services.unified_discovery.workflow_models import (
        QuestionnaireType,
    )

    q_type = (
        QuestionnaireType.BOOTSTRAP
        if questionnaire_type == "bootstrap"
        else QuestionnaireType.DETAILED
    )

    # Record questionnaire generation with enhanced orchestrator if available
    try:
        if (
            hasattr(collection_orchestrator, "enhanced_orchestrator")
            and collection_orchestrator.enhanced_orchestrator
        ):
            await collection_orchestrator.enhanced_orchestrator.record_questionnaire_submission(
                state,
                q_type,
                {
                    "questionnaires_generated": len(questionnaires),
                    "responses": {},  # Empty for generation, not submission
                    "completion_percentage": 0.0,  # Generation complete, not submission
                    "generation_metadata": {
                        "type": questionnaire_type,
                        "gaps_addressed": len(identified_gaps),
                        "forms_created": len(form_configs),
                    },
                },
            )
        else:
            logger.warning(
                "Enhanced orchestrator not available, skipping submission recording"
            )

    except Exception as orchestrator_error:
        logger.error(
            f"❌ Failed to record questionnaire submission: {type(orchestrator_error).__name__}"
        )
        # Continue execution rather than failing - this is non-critical


async def finalize_generation(
    collection_orchestrator,
    unified_flow_management,
    state: CollectionFlowState,
    questionnaire_type: str,
) -> Dict[str, Any]:
    """Finalize questionnaire generation with workflow advancement and pause"""
    # Advance workflow if appropriate
    advancement_result = await collection_orchestrator.advance_to_next_phase(state)

    # Get next phase name
    next_phase_name = get_next_phase_name(state, questionnaire_type)

    # Pause for user input
    state.pause_points.append("manual_collection_required")
    await unified_flow_management.pause_flow(
        reason=f"{questionnaire_type.title()} questionnaires generated - manual collection required",
        phase="questionnaire_generation",
    )

    return {
        "phase": "questionnaire_generation",
        "status": "completed",
        "questionnaire_type": questionnaire_type,
        "next_phase": next_phase_name,
        "requires_user_input": True,
        "workflow_advanced": advancement_result.get("advanced", False),
        "orchestration_applied": True,
    }


async def handle_generation_error(
    flow_context, state: CollectionFlowState, e: Exception
) -> None:
    """Handle questionnaire generation errors with proper rollback and logging"""
    # Ensure database rollback on errors
    try:
        if hasattr(flow_context, "db_session") and flow_context.db_session:
            await flow_context.db_session.rollback()
            logger.info(
                "🔄 Database transaction rolled back due to questionnaire generation error"
            )
    except Exception as rollback_error:
        logger.error(f"❌ Failed to rollback database transaction: {rollback_error}")

    # Use secure logging for errors
    logger.error(
        safe_log_format(
            "❌ Questionnaire generation failed: {error_type}, Flow: {flow_id}",
            error_type=type(e).__name__,
            flow_id=str(state.flow_id),
        )
    )

    # Add error to state with sanitized message
    if hasattr(state, "add_error"):
        state.add_error(
            "questionnaire_generation", f"Generation failed: {type(e).__name__}"
        )

    raise CollectionFlowError(f"Questionnaire generation failed: {type(e).__name__}")


async def handle_no_questionnaires_generated(
    state: CollectionFlowState,
    questionnaire_type: str,
    flow_context=None,
    state_manager=None,
) -> Dict[str, Any]:
    """Handle the case when no questionnaires are generated"""
    logger.warning(f"No questionnaires generated for flow {state.flow_id}")

    # CC: Update state to mark questionnaire generation as completed with 0 questionnaires
    if hasattr(state, "set_phase_status"):
        state.set_phase_status("questionnaire_generation", "completed")

    # CC: Persist state changes before returning to maintain workflow consistency
    if flow_context and state_manager:
        try:
            await state_manager.save_state(state)
            # Commit database transaction if available
            if hasattr(flow_context, "db_session") and flow_context.db_session:
                await flow_context.db_session.commit()
                logger.debug("✅ State persisted after no questionnaires generated")
        except Exception as save_error:
            logger.error(
                f"❌ Failed to persist state before early return: {save_error}"
            )
            # Continue execution - this is not critical enough to fail the entire operation

    return {
        "phase": "questionnaire_generation",
        "status": "completed",
        "questionnaire_type": questionnaire_type,
        "questionnaires_generated": 0,
        "next_phase": get_next_phase_name(state, questionnaire_type),
        "requires_user_input": False,
        "warning": "No questionnaires were generated based on current data gaps",
    }
