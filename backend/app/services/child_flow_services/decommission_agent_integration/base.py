"""
Decommission Agent Integration - Base Module

Common utilities, agent retrieval, and task creation helpers.
ADR Compliance: ADR-015 (TenantScopedAgentPool)
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.services.persistent_agents.agent_pool_constants import (
    DECOMMISSION_PHASE_AGENT_MAPPING,
)

logger = logging.getLogger(__name__)


async def _get_agents_for_phase(
    phase_name: str,
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    flow_id: UUID,
) -> List[Any]:
    """
    Get agents for a decommission phase from TenantScopedAgentPool.

    Args:
        phase_name: Phase to get agents for
        client_account_uuid: Tenant client account ID
        engagement_uuid: Tenant engagement ID
        flow_id: Flow ID for context

    Returns:
        List of unwrapped CrewAI agents

    ADR Compliance:
    - ADR-015: Uses TenantScopedAgentPool.get_or_create_agent()
    """
    agent_types = DECOMMISSION_PHASE_AGENT_MAPPING.get(phase_name, [])
    agents = []

    for agent_type in agent_types:
        try:
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=str(client_account_uuid),
                engagement_id=str(engagement_uuid),
                agent_type=agent_type,
                context_info={
                    "flow_id": str(flow_id),
                    "flow_type": "decommission",
                    "phase": phase_name,
                },
            )
            # Unwrap AgentWrapper to get actual CrewAI Agent (ADR-015)
            actual_agent = agent._agent if hasattr(agent, "_agent") else agent
            agents.append(actual_agent)
            logger.info(f"Retrieved {agent_type} from TenantScopedAgentPool")
        except Exception as e:
            logger.warning(f"Failed to get {agent_type} from pool: {e}")

    return agents


def _create_decommission_task(
    agent: Any,
    task_description: str,
    expected_output: str,
    context_data: Dict[str, Any],
) -> Any:
    """
    Create a CrewAI task for decommission agent.

    Args:
        agent: CrewAI agent instance
        task_description: Task description
        expected_output: Expected output format description
        context_data: Context data for the task

    Returns:
        CrewAI Task instance
    """
    from crewai import Task

    # Build context string from data
    context_str = "\n".join(
        f"- {k}: {v}" for k, v in context_data.items() if v is not None
    )

    return Task(
        description=f"{task_description}\n\nContext:\n{context_str}",
        expected_output=expected_output,
        agent=agent,
    )
