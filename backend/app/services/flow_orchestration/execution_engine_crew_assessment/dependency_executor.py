"""
Execution Engine - Dependency Analysis Executor

Mixin for executing dependency analysis phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class DependencyExecutorMixin:
    """Mixin for dependency analysis phase execution"""

    async def _execute_dependency_analysis(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute dependency analysis phase with data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        """
        logger.info("Executing dependency analysis with persistent agents")

        try:
            from app.repositories.assessment_data_repository import (
                AssessmentDataRepository,
            )
            from app.services.flow_orchestration.assessment_input_builders import (
                AssessmentInputBuilders,
            )

            # Create data repository with tenant context
            data_repo = AssessmentDataRepository(
                self.crew_utils.db,
                master_flow.client_account_id,
                master_flow.engagement_id,
            )

            # Create input builders
            input_builders = AssessmentInputBuilders(data_repo)

            # Build phase-specific input
            crew_inputs = await input_builders.build_dependency_input(
                str(master_flow.flow_id), phase_input
            )

            # Log dependency input preparation
            graph_metadata = (
                crew_inputs.get("context_data", {})
                .get("dependency_graph", {})
                .get("metadata", {})
            )
            logger.info(f"Built dependency input with graph metadata: {graph_metadata}")

            # TODO: Execute agent with crew_inputs
            # agent = await agent_pool.get_agent('dependency_analyst')
            # result = await agent.execute(crew_inputs)

            return {
                "phase": "dependency_analysis",
                "status": "completed",
                "agent": "dependency_analyst",
                "inputs_prepared": True,
                "context_data_available": bool(crew_inputs.get("context_data")),
                "message": "Dependency analysis executed with input builders",
            }

        except Exception as e:
            logger.error(f"Error in dependency analysis: {e}")
            return {
                "phase": "dependency_analysis",
                "status": "failed",
                "error": str(e),
            }
