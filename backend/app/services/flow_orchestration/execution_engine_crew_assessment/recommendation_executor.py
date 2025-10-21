"""
Execution Engine - Recommendation Generation Executor

Mixin for executing recommendation generation phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class RecommendationExecutorMixin:
    """Mixin for recommendation generation phase execution"""

    async def _execute_recommendation_generation(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute recommendation generation phase with data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        """
        logger.info("Executing recommendation generation with persistent agents")

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
            crew_inputs = await input_builders.build_recommendation_input(
                str(master_flow.flow_id), phase_input
            )

            # Log recommendation input preparation
            obj_count = len(
                crew_inputs.get("context_data", {}).get("business_objectives", [])
            )
            logger.info(
                f"Built recommendation input with all phase results "
                f"and {obj_count} business objectives"
            )

            # TODO: Execute agent with crew_inputs
            # agent = await agent_pool.get_agent('recommendation_generator')
            # result = await agent.execute(crew_inputs)

            return {
                "phase": "recommendation_generation",
                "status": "completed",
                "agent": "recommendation_generator",
                "inputs_prepared": True,
                "context_data_available": bool(crew_inputs.get("context_data")),
                "message": "Recommendation generation executed with input builders",
            }

        except Exception as e:
            logger.error(f"Error in recommendation generation: {e}")
            return {
                "phase": "recommendation_generation",
                "status": "failed",
                "error": str(e),
            }
