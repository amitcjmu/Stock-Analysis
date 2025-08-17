"""
Assessment Flow Validators
Validation logic for assessment flows including phase validation,
user input validation, and flow state validation.
"""

import logging
from typing import Any, Dict

from app.models.assessment_flow import AssessmentPhase

logger = logging.getLogger(__name__)


async def validate_phase_user_input(
    phase: AssessmentPhase, user_input: Dict[str, Any]
) -> None:
    """Validate user input for specific phase.

    Args:
        phase: Assessment phase to validate input for
        user_input: User input data to validate

    Raises:
        ValueError: If validation fails for the specific phase
    """
    # Implementation for phase-specific input validation
    if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
        if "standards_confirmed" not in user_input:
            raise ValueError("Architecture standards confirmation required")

    elif phase == AssessmentPhase.TECH_DEBT_ANALYSIS:
        if "analysis_approved" not in user_input:
            raise ValueError("Tech debt analysis approval required")

    elif phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES:
        if "strategies_reviewed" not in user_input:
            raise ValueError("Component 6R strategies review required")

    elif phase == AssessmentPhase.APP_ON_PAGE_GENERATION:
        if "page_data_approved" not in user_input:
            raise ValueError("App-on-page data approval required")

    elif phase == AssessmentPhase.FINALIZATION:
        if "finalization_confirmed" not in user_input:
            raise ValueError("Assessment finalization confirmation required")

    # Add more validation as needed for each phase
    logger.debug(f"User input validation passed for phase: {phase.value}")


def validate_assessment_phase_transition(
    current_phase: AssessmentPhase, target_phase: AssessmentPhase
) -> bool:
    """Validate if transition from current phase to target phase is allowed.

    Args:
        current_phase: Current assessment phase
        target_phase: Target assessment phase

    Returns:
        True if transition is allowed, False otherwise
    """
    phase_sequence = [
        AssessmentPhase.INITIALIZATION,
        AssessmentPhase.ARCHITECTURE_MINIMUMS,
        AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES,
        AssessmentPhase.APP_ON_PAGE_GENERATION,
        AssessmentPhase.FINALIZATION,
    ]

    try:
        current_index = phase_sequence.index(current_phase)
        target_index = phase_sequence.index(target_phase)

        # Allow backward navigation and forward progression
        return target_index <= current_index + 1
    except ValueError:
        # If phase not found in sequence, allow transition
        return True


def validate_application_selection(
    selected_application_ids: list[str], max_applications: int = 100
) -> None:
    """Validate application selection for assessment flow.

    Args:
        selected_application_ids: List of selected application IDs
        max_applications: Maximum allowed applications (default: 100)

    Raises:
        ValueError: If validation fails
    """
    if not selected_application_ids:
        raise ValueError("At least one application must be selected for assessment")

    if len(selected_application_ids) > max_applications:
        raise ValueError(
            f"Cannot assess more than {max_applications} applications at once"
        )

    # Check for duplicates
    if len(selected_application_ids) != len(set(selected_application_ids)):
        raise ValueError("Duplicate application IDs are not allowed")

    logger.debug(
        f"Application selection validation passed for {len(selected_application_ids)} applications"
    )


def validate_sixr_decisions(decisions: list[Dict[str, Any]]) -> None:
    """Validate 6R decision data structure.

    Args:
        decisions: List of 6R decision dictionaries

    Raises:
        ValueError: If validation fails
    """
    valid_strategies = [
        "rehost",
        "replatform",
        "repurchase",
        "refactor",
        "retire",
        "retain",
    ]

    for decision in decisions:
        if "strategy" not in decision:
            raise ValueError("Each 6R decision must include a strategy")

        if decision["strategy"] not in valid_strategies:
            raise ValueError(
                f"Invalid 6R strategy: {decision['strategy']}. Must be one of: {valid_strategies}"
            )

        if "rationale" not in decision or not decision["rationale"]:
            raise ValueError("Each 6R decision must include a rationale")

    logger.debug(f"6R decisions validation passed for {len(decisions)} decisions")


def validate_architecture_standards(standards: Dict[str, Any]) -> None:
    """Validate architecture standards structure.

    Args:
        standards: Architecture standards dictionary

    Raises:
        ValueError: If validation fails
    """
    required_domains = ["infrastructure", "security", "compliance"]

    for domain in required_domains:
        if domain not in standards:
            raise ValueError(f"Architecture standards must include {domain} domain")

    logger.debug("Architecture standards validation passed")


def validate_component_data(components: list[Dict[str, Any]]) -> None:
    """Validate component identification data.

    Args:
        components: List of component dictionaries

    Raises:
        ValueError: If validation fails
    """
    required_fields = ["name", "type", "description"]

    for component in components:
        for field in required_fields:
            if field not in component or not component[field]:
                raise ValueError(f"Each component must include {field}")

    logger.debug(f"Component data validation passed for {len(components)} components")
