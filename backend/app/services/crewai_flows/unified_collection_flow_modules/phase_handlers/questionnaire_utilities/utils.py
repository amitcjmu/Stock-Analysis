"""
Questionnaire Utilities - Helper Functions

Basic utility functions for questionnaire generation.
"""

import logging
from typing import Any, Dict

from app.models.collection_flow import CollectionFlowState

logger = logging.getLogger(__name__)


def get_next_phase_name(state: CollectionFlowState, questionnaire_type: str) -> str:
    """
    Determine the appropriate next phase name based on current state and questionnaire type.

    Args:
        state: Current collection flow state
        questionnaire_type: Type of questionnaire (bootstrap or detailed)

    Returns:
        Next phase name string
    """
    # For bootstrap questionnaires, typically advance to basic collection
    if questionnaire_type == "bootstrap":
        return "manual_collection"  # Bootstrap leads to manual data collection
    # For detailed questionnaires, usually continue with manual collection
    return "manual_collection"


def determine_questionnaire_type(identified_gaps: list) -> str:
    """Determine questionnaire type based on gap analysis"""
    return "bootstrap" if not identified_gaps else "detailed"


def prepare_questionnaire_config(
    state: CollectionFlowState,
    config: Dict[str, Any],
    identified_gaps: list,
    questionnaire_type: str,
) -> Dict[str, Any]:
    """Prepare questionnaire configuration"""
    from datetime import datetime, timezone

    return {
        "data_gaps": identified_gaps,
        "business_context": config.get("client_requirements", {}).get(
            "business_context", {}
        ),
        "automation_tier": state.automation_tier.value,
        "collection_flow_id": str(state.flow_id),  # Ensure string for serialization
        "questionnaire_type": questionnaire_type,  # Include type metadata
        "workflow_context": {
            "phase": state.current_phase.value,
            "progress": state.progress,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
