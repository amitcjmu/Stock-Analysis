"""Agent and memory manager setup for gap enhancement."""

import logging
from typing import Any, Tuple

from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


async def setup_agent_and_memory(
    client_account_id: str, engagement_id: str, db_session
) -> Tuple[Any, TenantMemoryManager]:
    """Create persistent agent and memory manager.

    Args:
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db_session: AsyncSession for database operations

    Returns:
        Tuple of (agent, memory_manager)
    """
    # Get single persistent agent for entire run
    logger.debug("🔧 Creating persistent gap_analysis_specialist agent")
    agent = await TenantScopedAgentPool.get_or_create_agent(
        client_id=client_account_id,
        engagement_id=engagement_id,
        agent_type="gap_analysis_specialist",
    )
    logger.info(
        f"✅ Agent created: {agent.role if hasattr(agent, 'role') else 'gap_analysis_specialist'}"
    )

    # Initialize memory manager (fail-safe wrapper below)
    # Per ADR-024: Use TenantMemoryManager with valid database session
    memory_manager = TenantMemoryManager(
        crewai_service=None,  # Not needed for gap enhancement
        database_session=db_session,  # ✅ Pass actual AsyncSession
    )

    return agent, memory_manager
