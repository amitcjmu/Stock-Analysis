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
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute risk assessment phase with shared data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        Per Qodo Bot: Uses shared instances passed from base.py for performance.
        """
        logger.info("Executing risk assessment with persistent agents")

        try:

            # Build phase-specific input
            crew_inputs = await input_builders.build_risk_input(
                str(master_flow.flow_id), phase_input
            )

            # Log risk input preparation
            prior_phases = list(crew_inputs.get("previous_phase_results", {}).keys())
            logger.info(f"Built risk input with prior phase results: {prior_phases}")

            # Get agent from pool
            agent = await self._get_agent_for_phase(
                "risk_assessment", agent_pool, master_flow
            )

            # Create task for agent
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Assess migration risks and develop mitigation strategies based on:
- Results from prior phases: {', '.join(prior_phases)}
- 6R strategy evaluation (Rehost, Replatform, Repurchase, Refactor, Retire, Retain)
- Technical, business, and compliance risks
- Environment and infrastructure constraints

Provide a comprehensive risk assessment with:
1. Overall risk score (0-100)
2. Critical risks and impact analysis
3. 6R strategy recommendations
4. Mitigation strategies and contingency plans

Return results as valid JSON with keys: risk_score, critical_risks, six_r_recommendations, mitigation_strategies
""",
                expected_output=(
                    "Comprehensive risk assessment with scores, "
                    "6R recommendations, and mitigation strategies in JSON format"
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

            logger.info(f"✅ Risk assessment completed in {execution_time:.2f}s")

            return {
                "phase": "risk_assessment",
                "status": "completed",
                "agent": "risk_assessor",
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": parsed_result,
                "context_data_available": bool(crew_inputs.get("context_data")),
            }

        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {
                "phase": "risk_assessment",
                "status": "failed",
                "error": str(e),
            }
