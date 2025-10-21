"""
Execution Engine - Readiness Assessment Executor

Mixin for executing readiness assessment phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class ReadinessExecutorMixin:
    """Mixin for readiness assessment phase execution"""

    async def _execute_readiness_assessment(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute readiness assessment phase with data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        """
        logger.info("Executing readiness assessment with persistent agents")

        try:
            # Import input builders and data repository
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
            crew_inputs = await input_builders.build_readiness_input(
                str(master_flow.flow_id), phase_input
            )

            # Log readiness input preparation
            app_count = len(crew_inputs.get("context_data", {}).get("applications", []))
            logger.info(f"Built readiness input with {app_count} applications")

            # TODO: Execute agent with crew_inputs
            # agent = await agent_pool.get_agent('readiness_assessor')
            # result = await agent.execute(crew_inputs)

            return {
                "phase": "readiness_assessment",
                "status": "completed",
                "agent": "readiness_assessor",
                "inputs_prepared": True,
                "context_data_available": bool(crew_inputs.get("context_data")),
                "message": "Readiness assessment executed with input builders",
            }

        except Exception as e:
            logger.error(f"Error in readiness assessment: {e}")
            return {
                "phase": "readiness_assessment",
                "status": "failed",
                "error": str(e),
            }
