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

            # Get agent from pool (reuses complexity_analyst per mapping)
            agent = await self._get_agent_for_phase(
                "tech_debt_assessment", agent_pool, master_flow
            )

            # Create task for agent
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Assess technical debt for applications based on:
- Known vulnerabilities: {vuln_count} identified
- Code quality metrics and outdated libraries
- Security compliance gaps
- Maintenance burden indicators

Provide a comprehensive technical debt assessment with:
1. Overall tech debt score (0-100)
2. Critical security vulnerabilities
3. Modernization requirements
4. Remediation roadmap

Return results as valid JSON with keys: tech_debt_score, vulnerabilities, modernization, remediation
""",
                expected_output=(
                    "Comprehensive technical debt assessment with scores, "
                    "vulnerabilities, and remediation roadmap in JSON format"
                ),
                agent=agent,
            )

            # Execute task with inputs
            start_time = time.time()

            result = await task.execute_async(context=crew_inputs)

            execution_time = time.time() - start_time

            # Parse result (assuming JSON output from agent)
            try:
                parsed_result = (
                    json.loads(result) if isinstance(result, str) else result
                )
            except json.JSONDecodeError:
                parsed_result = {"raw_output": str(result)}

            logger.info(f"✅ Tech debt assessment completed in {execution_time:.2f}s")

            return {
                "phase": "tech_debt_assessment",
                "status": "completed",
                "agent": "complexity_analyst",  # Reuse complexity agent
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": parsed_result,
                "context_data_available": bool(crew_inputs.get("context_data")),
            }

        except Exception as e:
            logger.error(f"Error in tech debt assessment: {e}")
            return {
                "phase": "tech_debt_assessment",
                "status": "failed",
                "error": str(e),
            }
