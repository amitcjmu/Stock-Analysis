"""
Persistent agent management for Discovery Flow Execution Engine.
Contains agent pool initialization and error handling methods.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class PersistentAgentsMixin:
    """Mixin class containing persistent agent management methods for discovery flows."""

    async def _initialize_discovery_agent_pool(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> Any:
        """Initialize persistent agent pool for the tenant with ServiceRegistry support"""
        # Import here to avoid circular dependencies
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
            client_id=str(master_flow.client_account_id),
            engagement_id=str(master_flow.engagement_id),
        )

        if agent_pool is not None:
            logger.info(
                f"🏊 Initialized agent pool for tenant {master_flow.client_account_id}"
            )
            return agent_pool
        else:
            logger.error("❌ Agent pool initialization returned None")
            raise RuntimeError("Failed to initialize agent pool")

    async def _execute_phase_with_agent_pool(
        self, phase_config, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the specific phase using the agent pool"""
        mapped_phase = self._map_discovery_phase_name(phase_config.name)
        logger.info(
            f"🗺️ Mapped phase '{phase_config.name}' to '{mapped_phase}' for agent execution"
        )

        result = await self._execute_discovery_mapped_phase(
            mapped_phase, agent_pool, phase_input
        )

        logger.info(
            f"✅ Discovery phase '{mapped_phase}' completed using persistent agents"
        )

        return {
            "phase": phase_config.name,
            "status": "completed",
            "crew_results": result,
            "method": "persistent_agent_execution",
            "agents_used": result.get("agents", [result.get("agent")]),
        }

    def _handle_pydantic_validation_error(
        self, error: ValueError, phase_config, master_flow: CrewAIFlowStateExtensions
    ) -> Dict[str, Any]:
        """Handle Pydantic validation errors during agent initialization"""
        if "object has no field" in str(error):
            logger.error(
                f"❌ Pydantic field validation error in agent creation: {error}"
            )
            logger.error(
                "🔧 Hint: This is likely a CrewAI/Pydantic v2 compatibility issue"
            )
            logger.error("🔧 Check AgentWrapper implementation in agent_config.py")
            return self.crew_utils.build_error_response(
                phase_config.name,
                f"Agent creation failed due to Pydantic v2 compatibility: {str(error)}",
                master_flow,
            )
        else:
            logger.error(
                f"❌ ValueError in discovery phase '{phase_config.name}': {error}"
            )
            return self.crew_utils.build_error_response(
                phase_config.name, str(error), master_flow
            )

    def _handle_general_agent_error(
        self, error: Exception, phase_config, master_flow: CrewAIFlowStateExtensions
    ) -> Dict[str, Any]:
        """Handle general errors during agent initialization"""
        logger.error(f"❌ Discovery phase '{phase_config.name}' failed: {error}")
        logger.error(f"❌ Exception type: {type(error).__name__}")
        import traceback

        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        return self.crew_utils.build_error_response(
            phase_config.name, str(error), master_flow
        )
