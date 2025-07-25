"""
Navigation Decision Tool

Tool for making intelligent navigation and routing decisions.
"""

import json
import logging
from typing import Any, Dict

try:
    from crewai.tools import BaseTool

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class BaseTool:
        name: str = "fallback_tool"
        description: str = "Fallback tool when CrewAI not available"

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def _run(self, *args, **kwargs):
            return "CrewAI not available - using fallback"


from app.knowledge_bases.flow_intelligence_knowledge import (
    FlowType,
    get_navigation_path,
    get_next_phase,
    get_user_actions,
)

logger = logging.getLogger(__name__)


class NavigationDecisionTool(BaseTool):
    """Tool for making intelligent navigation and routing decisions"""

    name: str = "navigation_decision_maker"
    description: str = "Makes intelligent routing decisions based on flow analysis and validation results, providing specific actionable guidance"

    def _run(self, flow_status: str, validation_results: str, flow_type: str) -> str:
        """Make intelligent navigation decision with actionable guidance"""
        try:
            status_data = (
                json.loads(flow_status) if isinstance(flow_status, str) else flow_status
            )
            validation_data = (
                json.loads(validation_results)
                if isinstance(validation_results, str)
                else validation_results
            )

            flow_id = status_data.get("flow_id")
            current_phase = status_data.get("current_phase", "data_import")

            # Make routing decision based on validation results
            decision = self._make_routing_decision(
                flow_id, flow_type, current_phase, status_data, validation_data
            )

            return json.dumps(decision)

        except Exception as e:
            logger.error(f"Navigation decision failed: {e}")
            return json.dumps(
                {
                    "routing_decision": "/discovery/overview",
                    "user_guidance": f"Navigation error: {str(e)}",
                    "action_type": "error",
                    "confidence": 0.0,
                }
            )

    def _make_routing_decision(
        self,
        flow_id: str,
        flow_type: str,
        current_phase: str,
        status_data: Dict,
        validation_data: Dict,
    ) -> Dict[str, Any]:
        """Make intelligent routing decision"""
        try:
            # Handle not_found flows first
            if current_phase == "not_found" or status_data.get("status") == "not_found":
                return {
                    "routing_decision": "/discovery/cmdb-import",
                    "user_guidance": "The discovery flow was not found. Please start a new discovery flow by uploading your data.",
                    "action_type": "user_action",
                    "confidence": 1.0,
                    "next_actions": [
                        "Navigate to the CMDB Import page",
                        "Click on 'Upload Data' button",
                        "Select your CMDB or asset data file (CSV/Excel)",
                        "Wait for the upload to complete",
                    ],
                    "completion_status": "flow_not_found",
                }

            flow_type_enum = FlowType(flow_type)

            # Check if current phase is valid
            if validation_data.get("phase_valid", False):
                # Phase is complete, move to next phase
                next_phase = get_next_phase(flow_type_enum, current_phase)

                if next_phase:
                    # Move to next phase
                    navigation_path = get_navigation_path(
                        flow_type_enum, next_phase, flow_id
                    )
                    user_actions = get_user_actions(flow_type_enum, next_phase)

                    return {
                        "routing_decision": navigation_path,
                        "user_guidance": f"Phase '{current_phase}' completed successfully. Continue to {next_phase}: {user_actions[0] if user_actions else 'Review and proceed'}",
                        "action_type": "user_action",
                        "confidence": 0.9,
                        "next_phase": next_phase,
                        "completion_status": "phase_complete",
                    }
                else:
                    # Flow complete
                    return {
                        "routing_decision": f"/{flow_type}/results?flow_id={flow_id}",
                        "user_guidance": f"All phases of the {flow_type} flow have been completed successfully. Review the results and proceed to the next workflow.",
                        "action_type": "navigation",
                        "confidence": 0.95,
                        "completion_status": "flow_complete",
                    }
            else:
                # Phase is not complete, provide specific guidance
                issues = validation_data.get("issues", [])
                specific_issue = validation_data.get("specific_issue", "Unknown issue")
                user_action_needed = validation_data.get(
                    "user_action_needed", "Review and fix issues"
                )

                # Route to current phase for user action
                navigation_path = get_navigation_path(
                    flow_type_enum, current_phase, flow_id
                )

                return {
                    "routing_decision": navigation_path,
                    "user_guidance": f"ISSUE: {specific_issue}. ACTION NEEDED: {user_action_needed}",
                    "action_type": "user_action",
                    "confidence": 0.85,
                    "issues": issues,
                    "completion_status": "action_required",
                    "specific_issue": specific_issue,
                }

        except Exception as e:
            logger.error(f"Routing decision failed: {e}")
            return {
                "routing_decision": f"/{flow_type}/overview?flow_id={flow_id}",
                "user_guidance": f"Unable to determine next steps: {str(e)}",
                "action_type": "error",
                "confidence": 0.0,
            }
