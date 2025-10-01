"""
Questionnaire Utilities - State Management

Functions for managing collection flow state during questionnaire generation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import (
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)

logger = logging.getLogger(__name__)


def update_state_for_generation(state: CollectionFlowState) -> None:
    """Update state for questionnaire generation phase"""
    state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
    state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
    state.updated_at = datetime.now(timezone.utc)


async def save_and_update_state(
    flow_context,
    state_manager,
    state: CollectionFlowState,
    questionnaires: List[Dict[str, Any]],
    form_configs: List[Dict[str, Any]],
    questionnaire_type: str,
    identified_gaps: List[Dict[str, Any]],
) -> None:
    """
    Save questionnaires and update flow state with generation metadata.

    Args:
        flow_context: Flow context object
        state_manager: State manager instance
        state: Current collection flow state
        questionnaires: Generated questionnaires
        form_configs: Form configurations
        questionnaire_type: Type of questionnaire
        identified_gaps: Identified data gaps
    """
    logger.info(
        safe_log_format(
            "Saving questionnaires and updating state",
            questionnaire_count=len(questionnaires),
            questionnaire_type=questionnaire_type,
            flow_id=str(state.flow_id),
        )
    )

    # Update state with questionnaire data
    state.phase_state = state.phase_state or {}
    state.phase_state.update(
        {
            "questionnaires": questionnaires,
            "form_configs": form_configs,
            "questionnaire_type": questionnaire_type,
            "generation_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "gap_count": len(identified_gaps),
                "questionnaires_generated": len(questionnaires),
            },
        }
    )

    # Update flow status
    state.status = CollectionStatus.QUESTIONNAIRES_READY
    state.updated_at = datetime.now(timezone.utc)

    logger.info(
        safe_log_format(
            "State updated successfully",
            questionnaires_count=len(questionnaires),
            flow_id=str(state.flow_id),
        )
    )


async def commit_database_transaction(flow_context) -> None:
    """
    Commit the database transaction for questionnaire generation.

    Args:
        flow_context: Flow context with database session
    """
    try:
        await flow_context.db_session.commit()
        logger.info("Database transaction committed successfully")
    except Exception as e:
        logger.error(f"Failed to commit database transaction: {e}")
        await flow_context.db_session.rollback()
        raise
