"""
Phase Validation Helpers for Assessment Flow Execution Engine

Extracted from base.py to reduce file length and improve modularity.
These helpers support phase prerequisite validation logic.
"""

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


def get_phase_order() -> list[str]:
    """
    Get the standard phase progression order for assessment flows.

    Returns:
        List of phase names in execution order
    """
    # Phase order must match assessment_flow_config.py phases list
    # (No "initialization" phase - that's a flow-level handler, not a phase)
    return [
        "readiness_assessment",
        "complexity_analysis",
        "dependency_analysis",
        "tech_debt_assessment",
        "risk_assessment",
        "recommendation_generation",
    ]


def check_phase_progression_resumption(
    phase_name: str,
    current_phase: Optional[str],
    phase_order: list[str],
    current_idx: int,
) -> bool:
    """
    Check if we're resuming flow execution from a later phase.

    This handles the case where we're returning from collection flow
    and the current_phase is already at or past the phase we want to execute.

    Args:
        phase_name: Name of phase to validate
        current_phase: Current phase from flow state
        phase_order: List of phases in execution order
        current_idx: Index of phase_name in phase_order

    Returns:
        True if resuming from later phase (prerequisites implicitly met)
    """
    if not current_phase:
        return False

    try:
        current_phase_idx = phase_order.index(current_phase)
        if current_phase_idx >= current_idx:
            # We're already at or past the phase we want to execute
            # This happens when resuming from collection flow
            logger.info(
                f"✅ Phase '{phase_name}' prerequisites met - flow already at '{current_phase}' "
                f"(likely returning from collection flow)"
            )
            return True
    except ValueError:
        # Current phase not in standard order, continue with normal validation
        pass

    return False


def is_prior_phase_completed(
    prior_phase: str,
    phase_results: Dict[str, Any],
    phases_completed: list[str],
    current_phase: Optional[str],
    phase_order: list[str],
) -> bool:
    """
    Check if a prior phase has been completed.

    A phase is considered completed if:
    1. It has results in phase_results, OR
    2. It's in the phases_completed list, OR
    3. The current_phase has progressed past it

    Args:
        prior_phase: Name of prior phase to check
        phase_results: Dictionary of phase results
        phases_completed: List of completed phase names
        current_phase: Current phase from flow state
        phase_order: List of phases in execution order

    Returns:
        True if prior phase is completed
    """
    # Check both phase_results and phases_completed list
    if prior_phase in phase_results or prior_phase in phases_completed:
        return True

    # Additional check: if we're past this phase index based on current_phase, it's OK
    if current_phase:
        try:
            current_phase_idx = phase_order.index(current_phase)
            prior_phase_idx = phase_order.index(prior_phase)
            if current_phase_idx > prior_phase_idx:
                # We've progressed past this phase already
                return True
        except ValueError:
            pass

    return False


async def validate_asset_readiness(
    db: Any,
    master_flow: CrewAIFlowStateExtensions,
    phase_name: str,
    selected_app_ids: list[str],
) -> None:
    """
    Validate that selected assets are ready for assessment.

    Args:
        db: Database session
        master_flow: Master flow state
        phase_name: Name of phase being validated
        selected_app_ids: List of application IDs to validate

    Raises:
        ValueError: If asset readiness check fails
    """
    if not selected_app_ids:
        return

    from app.services.integrations.discovery_integration import (
        DiscoveryFlowIntegration,
    )

    discovery_integration = DiscoveryFlowIntegration()
    try:
        await discovery_integration.verify_applications_ready_for_assessment(
            db=db,
            application_ids=selected_app_ids,
            client_account_id=master_flow.client_account_id,
        )
        logger.info(
            f"✅ Phase prerequisite validation passed: "
            f"{len(selected_app_ids)} assets ready for '{phase_name}'"
        )
    except ValueError as e:
        raise ValueError(
            f"Cannot execute phase '{phase_name}' - asset readiness check failed: {str(e)}"
        )
