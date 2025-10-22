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
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute readiness assessment phase with shared data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        Per Qodo Bot: Uses shared instances passed from base.py for performance.
        """
        logger.info("Executing readiness assessment with persistent agents")

        try:

            # Build phase-specific input
            crew_inputs = await input_builders.build_readiness_input(
                str(master_flow.flow_id), phase_input
            )

            # Log readiness input preparation
            app_count = len(crew_inputs.get("context_data", {}).get("applications", []))
            logger.info(f"Built readiness input with {app_count} applications")

            # Get agent from pool
            agent = await self._get_agent_for_phase(
                "readiness_assessment", agent_pool, master_flow
            )

            # Create task for agent
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Assess migration readiness for applications based on:
- Application metadata: {app_count} applications
- Technology stacks and architecture standards
- Current environment details

Provide a comprehensive readiness assessment with:
1. Overall readiness score (0-100)
2. Blockers and critical issues
3. Recommendations for addressing gaps
4. Cloud provider recommendations

Return results as valid JSON with keys: readiness_score, blockers, recommendations, cloud_providers
""",
                expected_output=(
                    "Comprehensive readiness assessment with scores, "
                    "blockers, and recommendations in JSON format"
                ),
                agent=agent,
            )

            # Execute task with inputs
            start_time = time.time()

            # Convert context dict to JSON string (CrewAI expects string context)
            context_str = json.dumps(crew_inputs)
            result = await task.execute_async(context=context_str)

            execution_time = time.time() - start_time

            # Parse result (assuming JSON output from agent)
            try:
                parsed_result = (
                    json.loads(result) if isinstance(result, str) else result
                )
            except json.JSONDecodeError:
                parsed_result = {"raw_output": str(result)}

            logger.info(f"✅ Readiness assessment completed in {execution_time:.2f}s")

            return {
                "phase": "readiness_assessment",
                "status": "completed",
                "agent": "readiness_assessor",
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": parsed_result,
                "context_data_available": bool(crew_inputs.get("context_data")),
            }

        except Exception as e:
            logger.error(f"Error in readiness assessment: {e}")
            return {
                "phase": "readiness_assessment",
                "status": "failed",
                "error": str(e),
            }
