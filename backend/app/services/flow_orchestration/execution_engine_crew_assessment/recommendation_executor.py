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
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute recommendation generation phase with shared data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        Per Qodo Bot: Uses shared instances passed from base.py for performance.
        """
        logger.info("Executing recommendation generation with persistent agents")

        try:

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

            # Get agent from pool
            agent = await self._get_agent_for_phase(
                "recommendation_generation", agent_pool, master_flow
            )

            # Create task for agent
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Generate comprehensive migration recommendations based on:
- All assessment phase results (readiness, complexity, dependencies, tech debt, risk)
- Business objectives: {obj_count} objectives
- 6R strategy recommendations
- Technical and business constraints

Synthesize all assessments to provide:
1. Recommended migration strategy per application
2. Wave planning and sequencing
3. Technology modernization opportunities
4. Resource requirements and timeline estimates
5. Success criteria and KPIs

Return results as valid JSON with keys: migration_strategy, wave_plan, modernization, resources, success_criteria
""",
                expected_output=(
                    "Comprehensive migration recommendations with strategy, "
                    "wave plan, and success criteria in JSON format"
                ),
                agent=(
                    agent._agent if hasattr(agent, "_agent") else agent
                ),  # Unwrap AgentWrapper for CrewAI Task
            )

            # Execute task with inputs
            start_time = time.time()

            # Convert context dict to JSON string (CrewAI expects string context)
            context_str = json.dumps(crew_inputs)

            # CRITICAL FIX: task.execute_async() returns concurrent.futures.Future (threading)
            # Must use asyncio.wrap_future() to convert to awaitable asyncio.Future
            import asyncio

            future = task.execute_async(context=context_str)
            result = await asyncio.wrap_future(future)

            execution_time = time.time() - start_time

            # Extract string result from TaskOutput object (CrewAI returns TaskOutput, not string)
            from crewai import TaskOutput
            from app.utils.json_sanitization import sanitize_for_json

            if isinstance(result, TaskOutput):
                # TaskOutput has .raw attribute containing the actual string result
                result_str = result.raw if hasattr(result, "raw") else str(result)
            else:
                result_str = str(result) if not isinstance(result, str) else result

            # Parse result (assuming JSON output from agent)
            try:
                parsed_result = (
                    json.loads(result_str)
                    if isinstance(result_str, str)
                    else result_str
                )
            except json.JSONDecodeError:
                parsed_result = {"raw_output": result_str}

            # Per ADR-029: Sanitize LLM output to remove NaN/Infinity before JSON serialization
            parsed_result = sanitize_for_json(parsed_result)

            logger.info(
                f"✅ Recommendation generation completed in {execution_time:.2f}s"
            )

            return {
                "phase": "recommendation_generation",
                "status": "completed",
                "agent": "recommendation_generator",
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": parsed_result,
                "context_data_available": bool(crew_inputs.get("context_data")),
            }

        except Exception as e:
            logger.error(f"Error in recommendation generation: {e}")
            return {
                "phase": "recommendation_generation",
                "status": "failed",
                "error": str(e),
            }
