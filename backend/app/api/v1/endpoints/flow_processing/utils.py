"""
Flow Processing Utilities
Helper functions and utilities for flow processing
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_flow_metadata(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and normalize flow metadata for processing."""
    return {
        "flow_id": flow_data.get("flow_id", "unknown"),
        "flow_type": flow_data.get("flow_type", "discovery"),
        "current_phase": flow_data.get("current_phase", "data_import"),
        "status": flow_data.get("status", "active"),
        "phases_completed": flow_data.get("phases_completed", {}),
        "client_account_id": flow_data.get("client_account_id"),
        "engagement_id": flow_data.get("engagement_id"),
    }


def is_phase_completed(flow_data: Dict[str, Any], phase: str) -> bool:
    """Check if a specific phase is completed in the flow."""
    phases_completed = flow_data.get("phases_completed", {})
    return phases_completed.get(phase, False)


def get_next_required_phase(
    flow_type: str, current_phase: str, phases_completed: Dict[str, bool]
) -> str:
    """Determine the next required phase based on flow type and completion status."""
    if flow_type == "discovery":
        phase_sequence = [
            "data_import",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_analysis",
        ]

        # Find current phase index
        try:
            current_idx = phase_sequence.index(current_phase)
        except ValueError:
            logger.warning(f"Unknown phase {current_phase}, defaulting to data_import")
            return "data_import"

        # Find next incomplete phase
        for i in range(current_idx + 1, len(phase_sequence)):
            next_phase = phase_sequence[i]
            if not phases_completed.get(next_phase, False):
                return next_phase

        # All phases complete
        return current_phase

    elif flow_type == "collection":
        # Collection flow phases
        if current_phase == "questionnaires":
            return (
                "analysis"
                if not phases_completed.get("analysis", False)
                else "completed"
            )
        return "questionnaires"

    return current_phase


def calculate_flow_progress(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall flow progress statistics."""
    flow_type = flow_data.get("flow_type", "discovery")
    phases_completed = flow_data.get("phases_completed", {})

    if flow_type == "discovery":
        # data_import, field_mapping, data_cleansing, asset_inventory, dependency_analysis, tech_debt_analysis
        total_phases = 6
        completed_count = sum(1 for completed in phases_completed.values() if completed)
    elif flow_type == "collection":
        total_phases = 2  # questionnaires, analysis
        completed_count = sum(1 for completed in phases_completed.values() if completed)
    else:
        total_phases = 1
        completed_count = 1 if flow_data.get("status") == "completed" else 0

    progress_percentage = (
        (completed_count / total_phases * 100) if total_phases > 0 else 0
    )

    return {
        "total_phases": total_phases,
        "completed_phases": completed_count,
        "progress_percentage": round(progress_percentage, 1),
        "is_complete": progress_percentage >= 100,
        "phases_completed": phases_completed,
    }


def format_execution_time(execution_time: float) -> str:
    """Format execution time for logging and response."""
    if execution_time < 1:
        return f"{execution_time * 1000:.0f}ms"
    else:
        return f"{execution_time:.3f}s"


def create_agent_insight(
    agent_name: str, analysis: str, confidence: float, execution_time: float
) -> Dict[str, Any]:
    """Create a standardized agent insight object."""
    return {
        "agent": agent_name,
        "analysis": analysis,
        "confidence": confidence,
        "execution_time": execution_time,
        "timestamp": None,  # Will be set by caller if needed
        "insight_type": "flow_processing",
    }


def validate_flow_continuation_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate flow continuation request data."""
    errors = []
    warnings = []

    # Check user_context if provided
    user_context = request_data.get("user_context", {})
    if user_context and not isinstance(user_context, dict):
        errors.append("user_context must be a dictionary")

    # Validate any additional context data
    if user_context:
        # Check for potential security issues
        suspicious_keys = {"password", "token", "key", "secret"}
        found_suspicious = set(user_context.keys()).intersection(suspicious_keys)
        if found_suspicious:
            warnings.append(
                f"Potentially sensitive keys found: {list(found_suspicious)}"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def sanitize_flow_data_for_logging(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize flow data by removing sensitive information before logging."""
    sensitive_keys = {
        "api_key",
        "password",
        "token",
        "secret",
        "credential",
        "auth",
        "private_key",
        "certificate",
    }

    def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = _sanitize_dict(value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            else:
                sanitized[key] = str(type(value))
        return sanitized

    return _sanitize_dict(flow_data)


def determine_routing_path(flow_type: str, current_phase: str, flow_id: str) -> str:
    """Determine the appropriate routing path based on flow type and phase."""
    if flow_type == "collection":
        return f"/collection/progress/{flow_id}"
    elif flow_type == "discovery":
        # Map phases to their appropriate frontend routes
        phase_routes = {
            "data_import": "/discovery/data-import",
            "field_mapping": "/discovery/attribute-mapping",
            "data_cleansing": "/discovery/data-cleansing",
            "asset_inventory": "/discovery/asset-inventory",
            "dependency_analysis": "/discovery/dependency-analysis",
            "tech_debt_analysis": "/discovery/tech-debt",
        }
        return phase_routes.get(current_phase, "/discovery/overview")
    else:
        return "/discovery/overview"


def extract_error_context(exception: Exception) -> Dict[str, Any]:
    """Extract useful context from an exception for error handling."""
    return {
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "error_module": getattr(exception, "__module__", "unknown"),
        "is_retriable": _is_retriable_error(exception),
    }


def _is_retriable_error(exception: Exception) -> bool:
    """Determine if an error is likely retriable."""
    retriable_error_types = {
        "ConnectionError",
        "TimeoutError",
        "TemporaryFailure",
        "ServiceUnavailable",
    }

    error_type = type(exception).__name__
    error_message = str(exception).lower()

    # Check error type
    if error_type in retriable_error_types:
        return True

    # Check error message for retriable indicators
    retriable_indicators = {
        "timeout",
        "connection",
        "temporary",
        "retry",
        "unavailable",
        "overloaded",
        "rate limit",
    }

    return any(indicator in error_message for indicator in retriable_indicators)
