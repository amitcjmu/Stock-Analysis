"""
Flow Intelligence Knowledge Base - Utility Functions
Helper functions for flow processing and navigation
"""

from typing import Any, Dict, List, Optional

from .flow_intelligence_definitions import FLOW_DEFINITIONS
from .flow_intelligence_enums import ActionType, FlowType


def get_flow_definition(flow_type: FlowType) -> Dict[str, Any]:
    """Get complete flow definition including all phases and criteria"""
    return FLOW_DEFINITIONS.get(flow_type, {})


def get_phase_definition(flow_type: FlowType, phase_id: str) -> Dict[str, Any]:
    """Get specific phase definition with success criteria and actions"""
    flow_def = get_flow_definition(flow_type)
    phases = flow_def.get("phases", [])

    for phase in phases:
        if phase["id"] == phase_id:
            return phase

    return {}


def get_next_phase(flow_type: FlowType, current_phase: str) -> Optional[str]:
    """Get the next phase in the flow sequence"""
    flow_def = get_flow_definition(flow_type)
    phases = flow_def.get("phases", [])

    for i, phase in enumerate(phases):
        if phase["id"] == current_phase and i + 1 < len(phases):
            return phases[i + 1]["id"]

    return None


def get_navigation_path(
    flow_type: FlowType,
    phase_id: str,
    flow_id: str,
    action_type: ActionType = ActionType.USER_ACTION,
) -> str:
    """Get the navigation path for a specific phase and action type"""
    phase_def = get_phase_definition(flow_type, phase_id)

    if not phase_def:
        # FIXED: Always include flow_id in overview paths to maintain routing context
        return f"/{flow_type.value}/overview/{flow_id}"

    base_path = phase_def.get("navigation_path", f"/{flow_type.value}/{phase_id}")

    # Substitute flow_id in path template or add as parameter for non-parametric paths
    if "{flow_id}" in base_path:
        return base_path.format(flow_id=flow_id)
    else:
        # For paths that don't expect flow_id in path (like data import)
        # Only data_import phase should not have flow_id in path
        if phase_id == "data_import":
            if "?" in base_path:
                return f"{base_path}&flow_id={flow_id}"
            else:
                return base_path
        else:
            # All other phases must carry flow_id in the path
            return f"{base_path}/{flow_id}"


def get_validation_services(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get list of validation services for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("validation_services", [])


def get_success_criteria(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get success criteria for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("success_criteria", [])


def get_user_actions(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get user actions required for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("user_actions", [])


def get_system_actions(flow_type: FlowType, phase_id: str) -> List[str]:
    """Get system actions required for a specific phase"""
    phase_def = get_phase_definition(flow_type, phase_id)
    return phase_def.get("system_actions", [])
