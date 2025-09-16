"""
Flow State Manager Utilities
Helper functions and state builders for FlowStateManager
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


def create_initial_state_structure(
    context: RequestContext, flow_id: str, initial_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Helper function to create initial flow state structure"""
    return {
        "flow_id": flow_id,
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "user_id": str(context.user_id),
        "current_phase": "initialization",
        "status": "running",
        "progress_percentage": 0.0,
        "phase_completion": {
            "data_import": False,
            "field_mapping": False,
            "data_cleansing": False,
            "asset_creation": False,
            "asset_inventory": False,
            "dependency_analysis": False,
            "tech_debt_analysis": False,
        },
        "crew_status": {},
        "raw_data": initial_data.get("raw_data", []),
        "metadata": initial_data.get("metadata", {}),
        "errors": [],
        "warnings": [],
        "agent_insights": [],
        "user_clarifications": [],
        "workflow_log": [],
        "agent_confidences": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


def build_unified_discovery_state(
    context: RequestContext, flow_id: str, child_flow: Any, base_state: Dict[str, Any]
) -> Dict[str, Any]:
    """Helper function to build unified discovery flow state from child flow"""
    validation_results = (
        base_state.get("validation_results")
        or base_state.get("data_validation_results")
        or {}
    )

    return {
        "flow_id": flow_id,
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "user_id": str(context.user_id),
        "current_phase": child_flow.current_phase,
        "status": child_flow.status,  # ADR-012: Use child flow operational status
        "progress_percentage": child_flow.progress_percentage,
        "phase_completion": {
            "data_import": child_flow.data_import_completed or False,
            "field_mapping": child_flow.field_mapping_completed or False,
            "data_cleansing": child_flow.data_cleansing_completed or False,
            "asset_inventory": child_flow.asset_inventory_completed or False,
        },
        "errors": child_flow.error_details or [],
        "validation_results": validation_results,
        "field_mappings": base_state.get("field_mappings", []),
        "raw_data": base_state.get("raw_data", []),
        "agent_insights": base_state.get("agent_insights", []),
        "created_at": (
            child_flow.created_at.isoformat() if child_flow.created_at else None
        ),
        "updated_at": (
            child_flow.updated_at.isoformat() if child_flow.updated_at else None
        ),
    }


def build_phase_transition_log_entry(
    from_phase: str, to_phase: str, context: RequestContext
) -> Dict[str, Any]:
    """Helper function to build phase transition log entry"""
    return {
        "event": "phase_transition",
        "transition_from": from_phase,
        "transition_to": to_phase,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": str(context.user_id),
    }


def build_error_log_entry(
    error_type: str, error_message: str, phase: Optional[str] = None
) -> Dict[str, Any]:
    """Helper function to build error log entry"""
    entry = {
        "event": "error",
        "error": error_type,
        "details": error_message,
        "timestamp": datetime.utcnow().isoformat(),
        "error_logged": True,
    }
    if phase:
        entry["phase"] = phase
    return entry


def build_completion_log_entry(phase: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to build phase completion log entry"""
    return {
        "event": "phase_completed",
        "phase": phase,
        "completed_at": datetime.utcnow().isoformat(),
        "results_summary": results.get("summary", "Phase completed successfully"),
    }


def build_resume_log_entry(checkpoint_id: str, reason: str) -> Dict[str, Any]:
    """Helper function to build flow resume log entry"""
    return {
        "event": "flow_resumed",
        "resumed_from": checkpoint_id,
        "resume_reason": reason,
        "resumed_at": datetime.utcnow().isoformat(),
    }


def sanitize_state_for_storage(state: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize state data for safe storage (remove sensitive information)"""
    sensitive_keys = ["password", "secret", "token", "api_key", "private_key"]
    sanitized_state = state.copy()

    def _sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in d.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = _sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    _sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    return _sanitize_dict(sanitized_state)


def extract_validation_results_safely(base_state: Dict[str, Any]) -> Dict[str, Any]:
    """Safely extract validation results from base state with fallbacks"""
    return (
        base_state.get("validation_results")
        or base_state.get("data_validation_results")
        or {}
    )


def build_recovery_context(
    flow_id: str, error: Exception, context: RequestContext
) -> Dict[str, Any]:
    """Build context for flow recovery operations"""
    return {
        "flow_id": flow_id,
        "client_account_id": str(context.client_account_id),
        "engagement_id": str(context.engagement_id),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "recovery_attempted": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
