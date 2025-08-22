"""
Flow Execution Engine State Utilities
State management and data conversion utilities for flow execution.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)

logger = get_logger(__name__)


class ExecutionEngineStateUtils:
    """State utilities for flow execution engine."""

    def __init__(
        self, master_repo: CrewAIFlowStateExtensionsRepository, context: RequestContext
    ):
        self.master_repo = master_repo
        self.context = context

    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get current flow state for agent context"""
        try:
            # Try to get discovery flow state if this is a discovery flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if master_flow and master_flow.flow_type == "discovery":
                # Import discovery state utilities
                from app.services.crewai_flows.flow_state_bridge import FlowStateBridge

                # Create bridge and get state
                bridge = FlowStateBridge(self.context)
                discovery_state = await bridge.recover_flow_state(flow_id)

                if discovery_state:
                    # Convert to dict for agent processing
                    return {
                        "flow_id": discovery_state.flow_id,
                        "status": discovery_state.status,
                        "current_phase": discovery_state.current_phase,
                        "completed_phases": discovery_state.completed_phases or [],
                        "raw_data": discovery_state.raw_data or [],
                        "processed_data": discovery_state.processed_data or [],
                        "field_mappings": discovery_state.field_mappings or {},
                        "metadata": discovery_state.metadata or {},
                    }

            # Fallback to basic flow info
            if master_flow:
                # Extract current phase from persistence data or use get_current_phase method
                current_phase = None
                if hasattr(master_flow, "get_current_phase"):
                    current_phase = master_flow.get_current_phase()
                elif master_flow.flow_persistence_data and isinstance(
                    master_flow.flow_persistence_data, dict
                ):
                    current_phase = master_flow.flow_persistence_data.get(
                        "current_phase"
                    )

                return {
                    "flow_id": master_flow.flow_id,
                    "flow_type": master_flow.flow_type,
                    "status": master_flow.flow_status,
                    "current_phase": current_phase,
                    "persistence_data": master_flow.flow_persistence_data or {},
                }

            return None

        except Exception as e:
            logger.warning(f"⚠️ Failed to get flow state for {flow_id}: {e}")
            return None

    def ensure_json_serializable(self, obj: Any) -> Any:
        """
        Ensure object is JSON serializable for database storage

        Args:
            obj: Object to make serializable

        Returns:
            JSON-serializable version of object
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self.ensure_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self.ensure_json_serializable(item) for item in obj]
        else:
            # Convert unknown types to string
            return str(obj)
