"""
Flow Execution Engine Phase Utilities
Phase navigation and management utilities for flow execution.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.crewai_flows.agents.decision import AgentDecision

logger = get_logger(__name__)


class ExecutionEnginePhaseUtils:
    """Phase utilities for flow execution engine."""

    def __init__(
        self, master_repo: CrewAIFlowStateExtensionsRepository, flow_registry=None
    ):
        self.master_repo = master_repo

        # Validate flow_registry interface
        if flow_registry and not hasattr(flow_registry, "get_flow_config"):
            logger.warning(
                "Provided flow_registry lacks 'get_flow_config'; disabling registry-backed transitions"
            )
            self.flow_registry = None
        else:
            self.flow_registry = flow_registry

        # Cache for flow configurations to improve performance
        self._flow_configs_cache = {}

    async def skip_to_next_phase(
        self, flow_id: str, phase_name: str, decision: AgentDecision
    ) -> Dict[str, Any]:
        """Handle agent skip decision"""
        logger.info(
            f"⏭️ Agent requested skip for phase {phase_name}: {decision.reasoning}"
        )

        # Update flow to mark phase as skipped
        await self.master_repo.update_flow_status(
            flow_id=flow_id,
            status="running",
            phase_data={
                "skipped_phase": phase_name,
                "skip_reason": decision.reasoning,
                "next_phase": decision.next_phase,
            },
        )

        return {
            "phase": phase_name,
            "status": "skipped",
            "reason": decision.reasoning,
            "next_phase": decision.next_phase,
            "agent_action": decision.action.value,
        }

    def get_default_next_phase(self, current_phase: str, flow_type: str = None) -> str:
        """Get default next phase using FlowTypeRegistry"""
        # Use flow registry if flow type is provided
        if flow_type and self.flow_registry:
            try:
                # Check cache first
                if flow_type not in self._flow_configs_cache:
                    self._flow_configs_cache[flow_type] = (
                        self.flow_registry.get_flow_config(flow_type)
                    )

                flow_config = self._flow_configs_cache[flow_type]
                next_phase = flow_config.get_next_phase(current_phase)
                if next_phase:
                    return next_phase
                # If no next phase, flow is complete
                return "completed"
            except Exception as e:
                logger.warning(f"⚠️ Failed to get next phase from registry: {e}")

        # Fallback to hardcoded transitions for backward compatibility (Discovery)
        # Support both legacy and new naming conventions
        phase_transitions = {
            "initialization": "data_import",
            "data_import": "attribute_mapping",
            "field_mapping": "data_cleansing",  # Legacy name support
            "attribute_mapping": "data_cleansing",  # New name
            "data_cleansing": "inventory",
            "asset_creation": "inventory",  # Alternative name
            "inventory": "dependencies",
            "dependencies": "completed",
            "analysis": "completed",  # Legacy name support
        }

        return phase_transitions.get(current_phase, "completed")

    def is_recoverable_error(self, error: Exception) -> bool:
        """
        Determine if an error is recoverable and phase should be retried

        Args:
            error: The exception that occurred

        Returns:
            True if error is recoverable, False otherwise
        """
        recoverable_types = [
            "ConnectionError",
            "TimeoutError",
            "TemporaryFailure",
            "RateLimitError",
        ]

        error_name = type(error).__name__
        return error_name in recoverable_types
