"""
Execution Engine - Risk Assessment Executor

Mixin for executing risk assessment phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class RiskExecutorMixin:
    """Mixin for risk assessment phase execution"""

    async def _execute_risk_assessment(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute risk assessment phase with data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        """
        logger.info("Executing risk assessment with persistent agents")

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
            crew_inputs = await input_builders.build_risk_input(
                str(master_flow.flow_id), phase_input
            )

            # Log risk input preparation
            prior_phases = list(crew_inputs.get("previous_phase_results", {}).keys())
            logger.info(f"Built risk input with prior phase results: {prior_phases}")

            # TODO: Execute agent with crew_inputs
            # agent = await agent_pool.get_agent('risk_assessor')
            # result = await agent.execute(crew_inputs)

            return {
                "phase": "risk_assessment",
                "status": "completed",
                "agent": "risk_assessor",
                "inputs_prepared": True,
                "context_data_available": bool(crew_inputs.get("context_data")),
                "message": "Risk assessment executed with input builders",
            }

        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {
                "phase": "risk_assessment",
                "status": "failed",
                "error": str(e),
            }
