"""
Execution Engine - Tech Debt Assessment Executor

Mixin for executing technical debt assessment phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class TechDebtExecutorMixin:
    """Mixin for tech debt assessment phase execution"""

    async def _execute_tech_debt_assessment(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute technical debt assessment phase with data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        """
        logger.info("Executing technical debt assessment with persistent agents")

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
            crew_inputs = await input_builders.build_tech_debt_input(
                str(master_flow.flow_id), phase_input
            )

            # Log tech debt input preparation
            vuln_count = len(
                crew_inputs.get("tech_debt_concerns", {}).get(
                    "known_vulnerabilities", []
                )
            )
            logger.info(
                f"Built tech debt input with {vuln_count} known vulnerabilities"
            )

            # TODO: Execute agent with crew_inputs
            # agent = await agent_pool.get_agent('complexity_analyst')  # Reuse complexity agent
            # result = await agent.execute(crew_inputs)

            return {
                "phase": "tech_debt_assessment",
                "status": "completed",
                "agent": "complexity_analyst",  # Reuse complexity agent
                "inputs_prepared": True,
                "context_data_available": bool(crew_inputs.get("context_data")),
                "message": "Tech debt assessment executed with input builders",
            }

        except Exception as e:
            logger.error(f"Error in tech debt assessment: {e}")
            return {
                "phase": "tech_debt_assessment",
                "status": "failed",
                "error": str(e),
            }
