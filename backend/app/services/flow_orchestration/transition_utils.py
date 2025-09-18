"""
Flow Transition Utilities

Provides optimized transition logic to avoid unnecessary AI calls and reduce response times
from 20+ seconds to < 1 second for simple phase transitions.

CC: Generated with Claude Code
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def is_simple_transition(
    flow_data: Dict[str, Any], validation_data: Dict[str, Any]
) -> bool:
    """
    Determine if a flow transition can use simple logic instead of AI analysis.

    Simple transitions are:
    1. Phase completion with no errors
    2. Standard phase progression without field mapping issues
    3. No clarification requests needed
    4. No complex error states requiring AI interpretation
    5. NOT a data processing phase that requires AI agents

    Args:
        flow_data: Flow status information
        validation_data: Validation results from phase checks

    Returns:
        bool: True if transition can use fast path (< 1 second)
    """
    try:
        current_phase = flow_data.get("current_phase", "")

        # CRITICAL: Never use simple transition for AI-required phases
        ai_required_phases = [
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "field_mapping",
        ]
        if current_phase in ai_required_phases:
            logger.info(
                f"❌ Simple transition blocked - {current_phase} requires AI processing"
            )
            return False

        # Check if phase is marked as valid/complete
        phase_valid = validation_data.get("phase_valid", False)

        # Check for any complex issues that require AI
        has_issues = validation_data.get("issues", [])
        has_errors = validation_data.get("error") is not None

        # Check for field mapping complexity
        needs_field_mapping = _requires_field_mapping_analysis(
            flow_data, validation_data
        )

        # Check for clarification requests
        needs_clarification = _requires_clarification(validation_data)

        # Simple transition criteria:
        # - NOT an AI-required phase AND
        # - Phase is valid AND
        # - No complex issues AND
        # - No errors requiring AI interpretation AND
        # - No field mapping complexity AND
        # - No clarifications needed
        is_simple = (
            phase_valid
            and not has_issues
            and not has_errors
            and not needs_field_mapping
            and not needs_clarification
        )

        logger.info(
            f"Transition analysis - current_phase: {current_phase}, "
            f"phase_valid: {phase_valid}, "
            f"has_issues: {bool(has_issues)}, has_errors: {has_errors}, "
            f"needs_field_mapping: {needs_field_mapping}, "
            f"needs_clarification: {needs_clarification}, "
            f"is_simple: {is_simple}"
        )

        return is_simple

    except Exception as e:
        logger.warning(f"Error in simple transition check: {e}")
        # If we can't determine, use AI (safe fallback)
        return False


def needs_ai_analysis(
    flow_data: Dict[str, Any], validation_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Determine when AI analysis is actually needed for flow transitions.

    AI is needed for:
    1. Data processing phases (data_cleansing, asset_inventory, dependency_analysis)
    2. Field mapping validation and suggestions
    3. Complex error interpretation
    4. Clarification request generation
    5. Ambiguous phase completion states

    Args:
        flow_data: Flow status information
        validation_data: Validation results from phase checks

    Returns:
        Tuple[bool, str]: (needs_ai, reason)
    """
    try:
        current_phase = flow_data.get("current_phase", "")

        # CRITICAL: Always use AI for data processing phases
        ai_required_phases = [
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
        ]
        if current_phase in ai_required_phases:
            # Check if phase was already processed by AI
            ai_processed_key = f"{current_phase}_ai_processed"
            if flow_data.get(ai_processed_key, False):
                logger.info(f"✅ Phase {current_phase} already processed by AI")
                return False, "phase_already_ai_processed"
            else:
                logger.info(f"🤖 AI agent required for phase {current_phase}")
                return True, f"ai_processing_required_for_{current_phase}"

        # Field mapping scenarios requiring AI
        if _requires_field_mapping_analysis(flow_data, validation_data):
            return True, "field_mapping_analysis_required"

        # Complex error scenarios requiring interpretation
        if _has_complex_errors(validation_data):
            return True, "complex_error_interpretation_required"

        # Clarification requests requiring intelligent generation
        if _requires_clarification(validation_data):
            return True, "clarification_generation_required"

        # Ambiguous completion states
        if _has_ambiguous_completion(flow_data, validation_data):
            return True, "ambiguous_completion_state"

        # If none of the above, simple logic suffices
        return False, "simple_transition_sufficient"

    except Exception as e:
        logger.error(f"Error in AI analysis check: {e}")
        # If we can't determine, use AI (safe fallback)
        return True, "error_in_analysis_check"


def _requires_field_mapping_analysis(
    flow_data: Dict[str, Any], validation_data: Dict[str, Any]
) -> bool:
    """Check if field mapping analysis is required."""
    try:
        current_phase = flow_data.get("current_phase", "")

        # Field mapping phase always requires AI
        if current_phase == "field_mapping":
            return True

        # Check for field mapping related issues
        issues = validation_data.get("issues", [])
        field_mapping_issues = [
            issue
            for issue in issues
            if isinstance(issue, str)
            and "field" in issue.lower()
            and "mapping" in issue.lower()
        ]

        return len(field_mapping_issues) > 0

    except Exception as e:
        logger.warning(f"Error checking field mapping requirements: {e}")
        return False


def _has_complex_errors(validation_data: Dict[str, Any]) -> bool:
    """Check if there are complex errors requiring AI interpretation."""
    try:
        # Simple validation errors don't need AI
        error = validation_data.get("error")
        if not error:
            return False

        # Complex error indicators
        complex_error_keywords = [
            "mapping",
            "relationship",
            "dependency",
            "conflict",
            "ambiguous",
            "interpretation",
            "analysis",
        ]

        error_str = str(error).lower()
        has_complex_keywords = any(
            keyword in error_str for keyword in complex_error_keywords
        )

        return has_complex_keywords

    except Exception as e:
        logger.warning(f"Error checking complex errors: {e}")
        return False


def _requires_clarification(validation_data: Dict[str, Any]) -> bool:
    """Check if clarification requests are needed."""
    try:
        # Check for explicit clarification requests
        user_action_needed = validation_data.get("user_action_needed", "")
        specific_issue = validation_data.get("specific_issue", "")

        # Clarification indicators
        clarification_keywords = [
            "clarification",
            "unclear",
            "ambiguous",
            "specify",
            "which",
            "choose",
            "select",
        ]

        text_to_check = f"{user_action_needed} {specific_issue}".lower()
        needs_clarification = any(
            keyword in text_to_check for keyword in clarification_keywords
        )

        return needs_clarification

    except Exception as e:
        logger.warning(f"Error checking clarification requirements: {e}")
        return False


def _has_ambiguous_completion(
    flow_data: Dict[str, Any], validation_data: Dict[str, Any]
) -> bool:
    """Check if the completion state is ambiguous and requires AI interpretation."""
    try:
        phase_valid = validation_data.get("phase_valid", False)
        completion_status = validation_data.get("completion_status", "")

        # If phase is clearly valid or invalid, not ambiguous
        if phase_valid is True or phase_valid is False:
            return False

        # Check for ambiguous completion statuses
        ambiguous_statuses = ["partial", "incomplete", "uncertain", "requires_review"]

        is_ambiguous = any(
            status in completion_status.lower() for status in ambiguous_statuses
        )

        return is_ambiguous

    except Exception as e:
        logger.warning(f"Error checking ambiguous completion: {e}")
        return False


def get_fast_path_response(
    flow_data: Dict[str, Any], validation_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Generate a fast path response for simple transitions without AI.

    Args:
        flow_data: Flow status information
        validation_data: Validation results from phase checks

    Returns:
        Optional[Dict[str, Any]]: Fast path response or None if AI needed
    """
    try:
        if not is_simple_transition(flow_data, validation_data):
            return None

        flow_id = flow_data.get("flow_id")
        flow_type = flow_data.get("flow_type", "discovery")
        current_phase = flow_data.get("current_phase", "data_import")

        # Simple phase progression logic
        next_phase = _get_next_phase_simple(flow_type, current_phase)

        if next_phase:
            # Continue to next phase - FIX: Don't append flow_id to phase routes
            # Map phase names to proper route paths
            phase_routes = {
                "discovery": {
                    "data_import": "/discovery/data-import",
                    "field_mapping": "/discovery/attribute-mapping",  # UI uses attribute-mapping route
                    "data_cleansing": "/discovery/data-cleansing",
                    "asset_inventory": "/discovery/inventory",
                    "dependency_analysis": "/discovery/dependencies",
                    "tech_debt_assessment": "/discovery/tech-debt",
                },
                "collection": {
                    "questionnaires": "/collection/questionnaires",
                    "validation": "/collection/validation",
                    "review": "/collection/review",
                },
            }

            # Get proper route for the phase
            routing_decision = phase_routes.get(flow_type, {}).get(
                next_phase, f"/{flow_type}/overview"
            )

            return {
                "routing_decision": routing_decision,
                "user_guidance": f"Phase '{current_phase}' completed. Continue to {next_phase}.",
                "action_type": "navigation",
                "confidence": 0.95,
                "next_phase": next_phase,
                "completion_status": "phase_complete",
                "fast_path": True,
                "execution_time": 0.1,  # Fast path indicator
            }
        else:
            # Flow complete - route to progress page to show completion status
            # Guard against missing flow_id (FIX for Qodo review)
            if flow_type == "collection":
                if flow_id and str(flow_id).strip() not in ["None", "", "unknown"]:
                    routing_path = f"/{flow_type}/progress/{flow_id}"
                else:
                    routing_path = f"/{flow_type}/progress"  # Fallback without flow_id
            else:
                # Discovery flows can use overview
                routing_path = f"/{flow_type}/overview"

            return {
                "routing_decision": routing_path,
                "user_guidance": f"{flow_type.title()} flow completed successfully.",
                "action_type": "navigation",
                "confidence": 0.98,
                "completion_status": "flow_complete",
                "fast_path": True,
                "execution_time": 0.1,  # Fast path indicator
            }

    except Exception as e:
        logger.error(f"Error generating fast path response: {e}")
        return None


def _get_next_phase_simple(flow_type: str, current_phase: str) -> Optional[str]:
    """Get next phase using simple logic for common flow types."""

    # Discovery flow phase progression
    # CC FIX: Removed tech_debt_assessment - it belongs to Collection flow, not Discovery flow
    discovery_phases = [
        "data_import",
        "field_mapping",
        "data_cleansing",
        "asset_inventory",
        "dependency_analysis",
    ]

    # Collection flow phase progression (aligned with actual routes)
    collection_phases = [
        "select-applications",  # Start with application selection
        "adaptive-forms",  # Then adaptive forms
        "bulk-upload",  # Or bulk upload
        "data-integration",  # Data integration phase
        "progress",  # Final progress/completion phase
    ]

    # Assessment flow phase progression (basic)
    assessment_phases = ["preparation", "analysis", "scoring", "reporting"]

    try:
        if flow_type == "discovery":
            phases = discovery_phases
        elif flow_type == "collection":
            phases = collection_phases
        elif flow_type == "assessment":
            phases = assessment_phases
        else:
            # Unknown flow type, can't do simple progression
            return None

        if current_phase in phases:
            current_index = phases.index(current_phase)
            if current_index < len(phases) - 1:
                return phases[current_index + 1]

        # Current phase not found or is last phase
        return None

    except Exception as e:
        logger.warning(f"Error getting next phase for {flow_type}: {e}")
        return None
