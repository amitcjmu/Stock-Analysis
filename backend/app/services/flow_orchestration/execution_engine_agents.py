"""
Flow Execution Engine Agent Handlers
Agent decision making and handling utilities for flow phase execution.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.crewai_flows.agents.decision import AgentDecision
from app.services.crewai_flows.agents.decision.base import PhaseAction
from app.services.crewai_flows.agents.decision.phase_transition import (
    PhaseTransitionAgent,
)

logger = get_logger(__name__)


class ExecutionEngineAgentHandlers:
    """Agent decision handlers for flow execution engine."""

    def __init__(
        self,
        master_repo: CrewAIFlowStateExtensionsRepository,
        phase_transition_agent: PhaseTransitionAgent,
    ):
        self.master_repo = master_repo
        self.phase_transition_agent = phase_transition_agent

    async def get_agent_decision(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_name: str,
        phase_input: Dict[str, Any],
        flow_state: Optional[Dict[str, Any]] = None,
        get_default_next_phase_func=None,
    ) -> AgentDecision:
        """Get agent decision for phase execution"""
        try:
            # Create agent context
            agent_context = {
                "flow_id": master_flow.flow_id,
                "flow_type": master_flow.flow_type,
                "current_phase": phase_name,
                "phase_input": phase_input,
                "flow_state": flow_state or {},
                "flow_history": master_flow.flow_persistence_data or {},
            }

            # Get decision from phase transition agent
            decision = await self.phase_transition_agent.get_decision(agent_context)

            return decision

        except Exception as e:
            logger.warning(f"⚠️ Agent decision failed for phase {phase_name}: {e}")
            # Return default decision on agent failure
            default_next_phase = (
                get_default_next_phase_func(phase_name)
                if get_default_next_phase_func
                else phase_name
            )
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=default_next_phase,
                confidence=0.0,
                reasoning=f"Agent decision failed, proceeding with default: {str(e)}",
                metadata={},
            )

    async def log_agent_decision(
        self, flow_id: str, phase_name: str, decision: AgentDecision
    ):
        """Log agent decision for audit purposes - best effort, don't fail phase on logging errors"""
        try:
            decision_log = {
                "flow_id": flow_id,
                "phase": phase_name,
                "action": decision.action.value,
                "next_phase": decision.next_phase,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "metadata": decision.metadata,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Store in flow phase data - best effort
            try:
                await self.master_repo.update_flow_status(
                    flow_id=flow_id,
                    status="running",  # Keep current status
                    phase_data={"agent_decisions": [decision_log]},
                )
            except Exception as update_err:
                # OCC conflicts and other update errors should not fail the phase
                logger.warning(
                    f"⚠️ Non-critical: Failed to persist agent decision due to concurrent update: {update_err}"
                )
                # Continue without raising - logging is not critical to phase execution

            logger.info(
                f"🤖 Agent Decision for {phase_name}: {decision.action.value} -> "
                f"{decision.next_phase} (confidence: {decision.confidence:.2f})"
            )

        except Exception as e:
            # Catch all exceptions to ensure logging never fails a phase
            logger.warning(f"⚠️ Non-critical: Failed to log agent decision: {e}")

    async def handle_agent_pause(
        self, flow_id: str, phase_name: str, decision: AgentDecision
    ) -> Dict[str, Any]:
        """Handle agent pause decision"""
        logger.info(
            f"⏸️ Agent requested pause for phase {phase_name}: {decision.reasoning}"
        )

        # Update flow status to paused
        await self.master_repo.update_flow_status(
            flow_id=flow_id,
            status="paused",
            phase_data={
                "pause_reason": decision.reasoning,
                "pause_metadata": decision.metadata,
                "paused_at": datetime.utcnow().isoformat(),
            },
        )

        return {
            "phase": phase_name,
            "status": "paused",
            "reason": decision.reasoning,
            "agent_decision": {
                "action": decision.action.value,
                "next_phase": decision.next_phase,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "metadata": decision.metadata,
            },
        }

    async def get_post_execution_decision(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_name: str,
        phase_result: Dict[str, Any],
        flow_state: Optional[Dict[str, Any]] = None,
        get_default_next_phase_func=None,
    ) -> AgentDecision:
        """Get agent decision after phase execution"""
        try:
            # Create post-execution context
            agent_context = {
                "flow_id": master_flow.flow_id,
                "flow_type": master_flow.flow_type,
                "phase_name": phase_name,  # Fixed: was "completed_phase"
                "phase_result": phase_result,
                "flow_state": flow_state or {},
                "flow_history": master_flow.flow_persistence_data or {},
            }

            # Get decision from phase transition agent
            decision = await self.phase_transition_agent.get_post_execution_decision(
                agent_context
            )

            # Log decision if it differs from default
            default_next_phase = (
                get_default_next_phase_func(phase_name)
                if get_default_next_phase_func
                else phase_name
            )
            if decision.next_phase != default_next_phase:
                logger.info(
                    f"🤖 Post-execution override: {phase_name} -> {decision.next_phase} "
                    f"(reasoning: {decision.reasoning})"
                )

            return decision

        except Exception as e:
            logger.warning(f"⚠️ Post-execution agent decision failed: {e}")
            # Return default decision
            default_next_phase = (
                get_default_next_phase_func(phase_name)
                if get_default_next_phase_func
                else phase_name
            )
            return AgentDecision(
                action=PhaseAction.PROCEED,
                next_phase=default_next_phase,
                confidence=0.0,
                reasoning=f"Post-execution decision failed, using default: {str(e)}",
                metadata={},
            )
