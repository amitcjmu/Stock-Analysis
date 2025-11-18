"""
Flow Execution Engine Collection Crew - Base Class
Main class and phase execution orchestration.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class ExecutionEngineCollectionCrews:
    """Collection flow persistent agent execution handlers."""

    def __init__(self, crew_utils):
        self.crew_utils = crew_utils

    async def execute_collection_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute collection flow phase using persistent agents"""
        logger.info(
            f"🔄 Executing collection phase '{phase_config.name}' with persistent agents"
        )

        try:
            # Import utils to prepare phase_input with correct flow IDs
            from .utils import prepare_phase_input

            # CRITICAL FIX (Issue #1067): Prepare phase_input with correct flow IDs
            # Following MFO Two-Table Flow ID pattern (matching discovery flow)
            await prepare_phase_input(master_flow, phase_input)

            # Initialize persistent agent pool for this tenant
            from .utils import initialize_collection_agent_pool

            agent_pool = await initialize_collection_agent_pool(master_flow)

            # Map phase names to execution methods
            from .utils import map_collection_phase_name

            mapped_phase = map_collection_phase_name(phase_config.name)

            # Execute the phase with persistent agents
            result = await self._execute_collection_mapped_phase(
                mapped_phase, agent_pool, phase_input
            )

            # Add metadata about persistent agent usage
            result["agent_pool_info"] = {
                "agent_pool_type": "TenantScopedAgentPool" if agent_pool else "none",
                "client_account_id": str(master_flow.client_account_id),
                "engagement_id": str(master_flow.engagement_id),
            }

            logger.info(
                f"✅ Collection phase '{phase_config.name}' completed with persistent agents"
            )
            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "persistent_agent_execution",
                "agents_used": result.get("agents", [result.get("agent")]),
            }

        except Exception as e:
            logger.error(f"❌ Collection phase failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return self.crew_utils.build_error_response(
                phase_config.name, str(e), master_flow
            )

    async def _execute_collection_mapped_phase(
        self, mapped_phase: str, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mapped collection phase with appropriate agents"""
        from .phase_handlers import (
            execute_platform_detection,
            execute_automated_collection,
            execute_gap_analysis,
            execute_questionnaire_generation,
            execute_manual_collection,
            execute_generic_collection_phase,
        )

        phase_methods = {
            "platform_detection": execute_platform_detection,
            "automated_collection": execute_automated_collection,
            "gap_analysis": execute_gap_analysis,
            "questionnaire_generation": execute_questionnaire_generation,
            "manual_collection": execute_manual_collection,
        }

        method = phase_methods.get(mapped_phase, execute_generic_collection_phase)
        return await method(agent_pool, phase_input)
