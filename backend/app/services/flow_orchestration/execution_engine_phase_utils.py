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
        self.flow_registry = flow_registry

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

    def get_default_next_phase(self, current_phase: str) -> str:
        """Get default next phase using FlowTypeRegistry"""
        # This would ideally come from flow configuration
        phase_transitions = {
            "initialization": "data_import",
            "data_import": "field_mapping",
            "field_mapping": "data_cleansing",
            "data_cleansing": "asset_creation",
            "asset_creation": "analysis",
            "analysis": "completed",
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
