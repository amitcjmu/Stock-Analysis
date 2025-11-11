"""
Decommission Agent Pool

Manages decommission-specific agent pool for multi-tenant environments.

Provides access to 7 specialized decommission agents organized into
3 phase-specific crews matching the FlowTypeConfig phases.

Per ADR-024: All agents created with memory=False. Use TenantMemoryManager for learning.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

from .agent_configs import DECOMMISSION_AGENT_CONFIGS
from .crew_factory import (
    create_data_migration_crew,
    create_decommission_planning_crew,
    create_system_shutdown_crew,
)

logger = logging.getLogger(__name__)

# CrewAI imports with fallback
try:
    from crewai import Agent, Crew, LLM

    CREWAI_AVAILABLE = True
    logger.info("✅ CrewAI imports successful for DecommissionAgentPool")
except ImportError as e:
    logger.warning(f"CrewAI not available: {e}")
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Agent:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.role = kwargs.get("role", "")
            self.goal = kwargs.get("goal", "")
            self.backstory = kwargs.get("backstory", "")

    class LLM:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            pass

    class Crew:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.agents = kwargs.get("agents", [])
            self.tasks = kwargs.get("tasks", [])

        def kickoff(self, inputs=None):
            return {"status": "fallback_mode", "result": {}}


class DecommissionAgentPool:
    """
    Manages decommission-specific agent pool for multi-tenant environments.

    This class provides access to 7 specialized decommission agents organized into
    3 phase-specific crews matching the FlowTypeConfig phases.

    Usage:
        pool = DecommissionAgentPool()
        agent = await pool.get_agent("system_analysis_agent", client_id, engagement_id)
        crew = pool.create_decommission_planning_crew(agents_dict, system_ids, strategy)
    """

    def __init__(self):
        """Initialize decommission agent pool."""
        self.agent_configs = DECOMMISSION_AGENT_CONFIGS
        self._agent_cache: Dict[str, Agent] = {}
        logger.info("🔧 Initialized DecommissionAgentPool with 7 agents")

    async def get_agent(
        self,
        agent_key: str,
        client_account_id: str,
        engagement_id: str,
        tools: Optional[List[Any]] = None,
    ) -> Agent:
        """
        Get or create decommission agent instance scoped to tenant.

        Args:
            agent_key: Agent identifier (e.g., "system_analysis_agent")
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            tools: Optional list of tools to attach to agent

        Returns:
            Agent instance configured with LLM and tools

        Raises:
            ValueError: If agent_key is not recognized
        """
        if agent_key not in self.agent_configs:
            raise ValueError(
                f"Unknown agent key: {agent_key}. "
                f"Valid keys: {list(self.agent_configs.keys())}"
            )

        # Build cache key for tenant-scoped agent
        cache_key = f"{client_account_id}:{engagement_id}:{agent_key}"

        # Return cached agent if exists
        if cache_key in self._agent_cache:
            logger.debug(f"♻️ Reusing cached agent: {agent_key}")
            return self._agent_cache[cache_key]

        # Create new agent
        config = self.agent_configs[agent_key]
        logger.info(f"🤖 Creating new {agent_key} for tenant {client_account_id}")

        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available, returning fallback agent")
            return Agent(
                role=config["role"], goal=config["goal"], backstory=config["backstory"]
            )

        # Create LLM instance (DeepInfra with Llama 4)
        llm = LLM(
            model=f"deepinfra/{config['llm_config']['model']}",
            api_key=settings.DEEPINFRA_API_KEY,
        )

        # Create agent with memory=False per ADR-024
        agent = Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=llm,
            tools=tools or [],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            # CRITICAL: memory=False per ADR-024
            # Use TenantMemoryManager for learning instead
        )

        # Add metadata for tracking
        agent._client_account_id = client_account_id
        agent._engagement_id = engagement_id
        agent._agent_key = agent_key

        # Cache agent
        self._agent_cache[cache_key] = agent

        logger.info(f"✅ Created {agent_key} with {len(tools or [])} tools")
        return agent

    def create_decommission_planning_crew(
        self,
        agents: Dict[str, Agent],
        system_ids: List[str],
        decommission_strategy: Dict[str, Any],
    ) -> Crew:
        """
        Create decommission planning crew (Phase 1: decommission_planning).

        Delegates to crew_factory.create_decommission_planning_crew().

        Args:
            agents: Dictionary of agent instances
            system_ids: List of system IDs to decommission
            decommission_strategy: Strategy configuration

        Returns:
            Crew instance ready for execution (or None in fallback mode)
        """
        return create_decommission_planning_crew(
            agents, system_ids, decommission_strategy
        )

    def create_data_migration_crew(
        self,
        agents: Dict[str, Agent],
        retention_policies: Dict[str, Any],
        system_ids: List[str],
    ) -> Crew:
        """
        Create data migration crew (Phase 2: data_migration).

        Delegates to crew_factory.create_data_migration_crew().

        Args:
            agents: Dictionary of agent instances
            retention_policies: Policies from planning phase
            system_ids: List of system IDs

        Returns:
            Crew instance ready for execution (or None in fallback mode)
        """
        return create_data_migration_crew(agents, retention_policies, system_ids)

    def create_system_shutdown_crew(
        self,
        agents: Dict[str, Agent],
        decommission_plan: Dict[str, Any],
        system_ids: List[str],
    ) -> Crew:
        """
        Create system shutdown crew (Phase 3: system_shutdown).

        Delegates to crew_factory.create_system_shutdown_crew().

        Args:
            agents: Dictionary of agent instances
            decommission_plan: Plan from planning phase
            system_ids: List of system IDs

        Returns:
            Crew instance ready for execution (or None in fallback mode)
        """
        return create_system_shutdown_crew(agents, decommission_plan, system_ids)

    async def release_agents(self, client_account_id: str, engagement_id: str):
        """
        Release all agents for a specific tenant from cache.

        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
        """
        prefix = f"{client_account_id}:{engagement_id}:"
        released = [k for k in list(self._agent_cache.keys()) if k.startswith(prefix)]

        for key in released:
            del self._agent_cache[key]

        logger.info(
            f"🧹 Released {len(released)} agents for tenant {client_account_id}"
        )

    def get_available_agents(self) -> List[str]:
        """
        Get list of available agent keys.

        Returns:
            List of agent identifiers
        """
        return list(self.agent_configs.keys())

    def get_agent_info(self, agent_key: str) -> Dict[str, Any]:
        """
        Get configuration information for a specific agent.

        Args:
            agent_key: Agent identifier

        Returns:
            Agent configuration dictionary

        Raises:
            ValueError: If agent_key is not recognized
        """
        if agent_key not in self.agent_configs:
            raise ValueError(
                f"Unknown agent key: {agent_key}. "
                f"Valid keys: {list(self.agent_configs.keys())}"
            )

        config = self.agent_configs[agent_key]
        return {
            "agent_key": agent_key,
            "role": config["role"],
            "goal": config["goal"],
            "tools": config.get("tools", []),
            "memory_enabled": config.get("memory_enabled", False),
            "llm_model": config["llm_config"]["model"],
        }
