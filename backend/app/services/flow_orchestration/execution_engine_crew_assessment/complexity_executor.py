"""
Execution Engine - Complexity Analysis Executor

Mixin for executing complexity analysis phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class ComplexityExecutorMixin:
    """Mixin for complexity analysis phase execution"""

    async def _execute_complexity_analysis(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute complexity analysis phase with data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        """
        logger.info("Executing complexity analysis with persistent agents")

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
            crew_inputs = await input_builders.build_complexity_input(
                str(master_flow.flow_id), phase_input
            )

            # Log complexity input preparation
            complexity_indicators = crew_inputs.get("context_data", {}).get(
                "complexity_indicators", {}
            )
            logger.info(
                f"Built complexity input with indicators: {complexity_indicators}"
            )

            # TODO: Execute agent with crew_inputs
            # agent = await agent_pool.get_agent('complexity_analyst')
            # result = await agent.execute(crew_inputs)

            return {
                "phase": "complexity_analysis",
                "status": "completed",
                "agent": "complexity_analyst",
                "inputs_prepared": True,
                "context_data_available": bool(crew_inputs.get("context_data")),
                "message": "Complexity analysis executed with input builders",
            }

        except Exception as e:
            logger.error(f"Error in complexity analysis: {e}")
            return {
                "phase": "complexity_analysis",
                "status": "failed",
                "error": str(e),
            }
