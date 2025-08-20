"""
Flow Execution Engine Crew Utilities
Utility functions for CrewAI flow execution including input/output processing and cleanup.
"""

from typing import Any, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionEngineCrewUtils:
    """Utility methods for CrewAI execution engine."""

    def build_crew_inputs(
        self, master_flow, phase_config, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build inputs for crew execution"""
        crew_inputs = {
            "flow_id": master_flow.flow_id,
            "flow_type": master_flow.flow_type,
            "phase_name": phase_config.name,
            "phase_input": phase_input,
            "flow_state": master_flow.flow_persistence_data or {},
        }

        # Add any phase-specific input formatting
        if hasattr(phase_config, "input_schema"):
            # Apply input schema transformations if defined
            pass

        return crew_inputs

    def process_crew_output(self, crew_result: Any) -> Dict[str, Any]:
        """Process crew execution output into standardized format"""
        if isinstance(crew_result, dict):
            return crew_result
        elif hasattr(crew_result, "to_dict"):
            return crew_result.to_dict()
        elif hasattr(crew_result, "__dict__"):
            return crew_result.__dict__
        else:
            return {"result": str(crew_result)}

    def build_error_response(
        self, phase_name: str, error_message: str, master_flow=None
    ) -> Dict[str, Any]:
        """Build standardized error response"""
        return {
            "phase": phase_name,
            "status": "failed",
            "error": error_message,
            "crew_results": {},
            "flow_id": master_flow.flow_id if master_flow else None,
            "method": "crew_execution_error",
        }
