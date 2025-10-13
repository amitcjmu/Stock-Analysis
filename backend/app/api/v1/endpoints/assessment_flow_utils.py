"""
Assessment Flow Utilities
Helper functions for assessment flow operations including phase navigation,
progress calculations, template management, and readiness scoring.
"""

import logging
from typing import Any, Dict, List, Optional

from app.models.assessment_flow import AssessmentPhase

logger = logging.getLogger(__name__)


def get_next_phase_for_navigation(
    current_phase: AssessmentPhase,
) -> Optional[AssessmentPhase]:
    """Determine next phase based on navigation.

    Args:
        current_phase: Current assessment phase

    Returns:
        Next phase in the sequence, or None if at the end
    """
    phase_sequence = [
        AssessmentPhase.ARCHITECTURE_MINIMUMS,
        AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES,
        AssessmentPhase.APP_ON_PAGE_GENERATION,
        AssessmentPhase.FINALIZATION,
    ]

    try:
        current_index = phase_sequence.index(current_phase)
        if current_index < len(phase_sequence) - 1:
            return phase_sequence[current_index + 1]
    except ValueError:
        pass

    return None


def get_progress_for_phase(phase: AssessmentPhase) -> int:
    """Get progress percentage for phase.

    Args:
        phase: Assessment phase to get progress for

    Returns:
        Progress percentage (0-100)
    """
    progress_map = {
        AssessmentPhase.INITIALIZATION: 10,
        AssessmentPhase.ARCHITECTURE_MINIMUMS: 25,
        AssessmentPhase.TECH_DEBT_ANALYSIS: 50,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES: 75,
        AssessmentPhase.APP_ON_PAGE_GENERATION: 90,
        AssessmentPhase.FINALIZATION: 100,
    }

    return progress_map.get(phase, 0)


async def get_available_templates() -> List[Dict[str, Any]]:
    """Get available architecture standards templates.

    Returns:
        List of available template dictionaries
    """
    # Implementation to return available templates
    return [
        {
            "id": "cloud_native_template",
            "name": "Cloud Native Architecture",
            "domain": "infrastructure",
            "description": "Standards for cloud-native applications",
        },
        {
            "id": "security_template",
            "name": "Security Standards",
            "domain": "security",
            "description": "Security and compliance requirements",
        },
        {
            "id": "microservices_template",
            "name": "Microservices Architecture",
            "domain": "architecture",
            "description": "Standards for microservices-based applications",
        },
        {
            "id": "data_governance_template",
            "name": "Data Governance",
            "domain": "data",
            "description": "Data management and governance standards",
        },
        {
            "id": "compliance_template",
            "name": "Compliance Standards",
            "domain": "compliance",
            "description": "Regulatory and compliance requirements",
        },
    ]


def calculate_overall_readiness_score(flow_state) -> float:
    """Calculate overall readiness score based on assessment completion.

    Args:
        flow_state: Assessment flow state object

    Returns:
        Overall readiness score (0.0-100.0)
    """
    score = 0.0

    # Base score from progress
    score += flow_state.progress * 0.4  # 40% weight for progress

    # Architecture standards captured
    if flow_state.architecture_captured:
        score += 15.0  # 15 points

    # Component analysis completion
    if flow_state.identified_components:
        component_count = len(
            [app for app in flow_state.identified_components.values() if app]
        )
        total_apps = len(flow_state.selected_application_ids)
        if total_apps > 0:
            score += (component_count / total_apps) * 20.0  # 20 points max

    # Tech debt analysis completion
    if flow_state.tech_debt_analysis:
        debt_count = len([app for app in flow_state.tech_debt_analysis.values() if app])
        total_apps = len(flow_state.selected_application_ids)
        if total_apps > 0:
            score += (debt_count / total_apps) * 15.0  # 15 points max

    # 6R decisions completion
    if flow_state.sixr_decisions:
        decision_count = len([app for app in flow_state.sixr_decisions.values() if app])
        total_apps = len(flow_state.selected_application_ids)
        if total_apps > 0:
            score += (decision_count / total_apps) * 10.0  # 10 points max

    return min(100.0, max(0.0, score))


def get_phase_sequence() -> List[AssessmentPhase]:
    """Get the complete assessment phase sequence.

    Returns:
        List of assessment phases in order
    """
    return [
        AssessmentPhase.INITIALIZATION,
        AssessmentPhase.ARCHITECTURE_MINIMUMS,
        AssessmentPhase.TECH_DEBT_ANALYSIS,
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES,
        AssessmentPhase.APP_ON_PAGE_GENERATION,
        AssessmentPhase.FINALIZATION,
    ]


def get_phase_description(phase: AssessmentPhase) -> str:
    """Get human-readable description for assessment phase.

    Args:
        phase: Assessment phase

    Returns:
        Human-readable phase description
    """
    descriptions = {
        AssessmentPhase.INITIALIZATION: "Initializing assessment flow with selected applications",
        AssessmentPhase.ARCHITECTURE_MINIMUMS: "Defining architecture standards and minimums",
        AssessmentPhase.TECH_DEBT_ANALYSIS: "Analyzing technical debt and modernization opportunities",
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES: "Determining 6R strategies for application components",
        AssessmentPhase.APP_ON_PAGE_GENERATION: "Generating comprehensive application profiles",
        AssessmentPhase.FINALIZATION: "Finalizing assessment and preparing for planning",
    }

    return descriptions.get(phase, f"Assessment phase: {phase.value}")


def calculate_phase_completion_percentage(flow_state, phase: AssessmentPhase) -> float:
    """Calculate completion percentage for a specific phase.

    Args:
        flow_state: Assessment flow state object
        phase: Assessment phase to calculate completion for

    Returns:
        Completion percentage (0.0-100.0) for the phase
    """
    if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
        return 100.0 if flow_state.architecture_captured else 0.0

    elif phase == AssessmentPhase.TECH_DEBT_ANALYSIS:
        if not flow_state.tech_debt_analysis:
            return 0.0
        completed_apps = len(
            [app for app in flow_state.tech_debt_analysis.values() if app]
        )
        total_apps = len(flow_state.selected_application_ids)
        return (completed_apps / total_apps * 100.0) if total_apps > 0 else 0.0

    elif phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES:
        if not flow_state.sixr_decisions:
            return 0.0
        completed_apps = len([app for app in flow_state.sixr_decisions.values() if app])
        total_apps = len(flow_state.selected_application_ids)
        return (completed_apps / total_apps * 100.0) if total_apps > 0 else 0.0

    elif phase == AssessmentPhase.APP_ON_PAGE_GENERATION:
        if not flow_state.app_on_page_data:
            return 0.0
        completed_apps = len(
            [app for app in flow_state.app_on_page_data.values() if app]
        )
        total_apps = len(flow_state.selected_application_ids)
        return (completed_apps / total_apps * 100.0) if total_apps > 0 else 0.0

    elif phase == AssessmentPhase.FINALIZATION:
        if not flow_state.apps_ready_for_planning:
            return 0.0
        return 100.0 if len(flow_state.apps_ready_for_planning) > 0 else 0.0

    return 0.0


def format_assessment_summary(flow_state) -> Dict[str, Any]:
    """Format assessment flow state into a summary.

    Args:
        flow_state: Assessment flow state object

    Returns:
        Formatted summary dictionary
    """
    total_apps = len(flow_state.selected_application_ids)

    summary = {
        "flow_id": flow_state.flow_id,
        "status": flow_state.status.value,
        "current_phase": flow_state.current_phase.value,
        "progress": flow_state.progress,
        "total_applications": total_apps,
        "readiness_score": calculate_overall_readiness_score(flow_state),
        "phase_completion": {
            "architecture_minimums": calculate_phase_completion_percentage(
                flow_state, AssessmentPhase.ARCHITECTURE_MINIMUMS
            ),
            "tech_debt_analysis": calculate_phase_completion_percentage(
                flow_state, AssessmentPhase.TECH_DEBT_ANALYSIS
            ),
            "component_sixr_strategies": calculate_phase_completion_percentage(
                flow_state, AssessmentPhase.COMPONENT_SIXR_STRATEGIES
            ),
            "app_on_page_generation": calculate_phase_completion_percentage(
                flow_state, AssessmentPhase.APP_ON_PAGE_GENERATION
            ),
            "finalization": calculate_phase_completion_percentage(
                flow_state, AssessmentPhase.FINALIZATION
            ),
        },
        "apps_ready_for_planning": len(flow_state.apps_ready_for_planning or []),
    }

    return summary


def get_assessment_phase_requirements(phase: AssessmentPhase) -> Dict[str, Any]:
    """Get requirements and prerequisites for a specific assessment phase.

    Args:
        phase: Assessment phase

    Returns:
        Requirements dictionary for the phase
    """
    requirements = {
        AssessmentPhase.INITIALIZATION: {
            "prerequisites": [],
            "required_inputs": ["selected_application_ids"],
            "user_interaction": False,
            "estimated_duration": "2-5 minutes",
        },
        AssessmentPhase.ARCHITECTURE_MINIMUMS: {
            "prerequisites": ["INITIALIZATION"],
            "required_inputs": ["engagement_standards", "application_overrides"],
            "user_interaction": True,
            "estimated_duration": "15-30 minutes",
        },
        AssessmentPhase.TECH_DEBT_ANALYSIS: {
            "prerequisites": ["ARCHITECTURE_MINIMUMS"],
            "required_inputs": ["standards_confirmation"],
            "user_interaction": True,
            "estimated_duration": "30-60 minutes",
        },
        AssessmentPhase.COMPONENT_SIXR_STRATEGIES: {
            "prerequisites": ["TECH_DEBT_ANALYSIS"],
            "required_inputs": ["debt_analysis_approval"],
            "user_interaction": True,
            "estimated_duration": "45-90 minutes",
        },
        AssessmentPhase.APP_ON_PAGE_GENERATION: {
            "prerequisites": ["COMPONENT_SIXR_STRATEGIES"],
            "required_inputs": ["sixr_decisions_approval"],
            "user_interaction": False,
            "estimated_duration": "10-20 minutes",
        },
        AssessmentPhase.FINALIZATION: {
            "prerequisites": ["APP_ON_PAGE_GENERATION"],
            "required_inputs": ["finalization_apps", "export_preferences"],
            "user_interaction": True,
            "estimated_duration": "5-10 minutes",
        },
    }

    return requirements.get(phase, {})


def validate_phase_prerequisites(
    flow_state, target_phase: AssessmentPhase
) -> tuple[bool, List[str]]:
    """Validate if prerequisites are met for transitioning to target phase.

    Args:
        flow_state: Assessment flow state object
        target_phase: Target phase to validate prerequisites for

    Returns:
        Tuple of (is_valid, list_of_missing_prerequisites)
    """
    missing_prerequisites = []

    if target_phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
        # Check if asset resolution is complete (will be validated by asset resolution service)
        pass  # Validation handled by asset resolution service

    elif target_phase == AssessmentPhase.TECH_DEBT_ANALYSIS:
        if not flow_state.architecture_captured:
            missing_prerequisites.append("Architecture standards must be captured")

    elif target_phase == AssessmentPhase.COMPONENT_SIXR_STRATEGIES:
        if not flow_state.tech_debt_analysis:
            missing_prerequisites.append("Tech debt analysis must be completed")

    elif target_phase == AssessmentPhase.APP_ON_PAGE_GENERATION:
        if not flow_state.sixr_decisions:
            missing_prerequisites.append("6R decisions must be completed")

    elif target_phase == AssessmentPhase.FINALIZATION:
        if not flow_state.app_on_page_data:
            missing_prerequisites.append("App-on-page data must be generated")

    return len(missing_prerequisites) == 0, missing_prerequisites
