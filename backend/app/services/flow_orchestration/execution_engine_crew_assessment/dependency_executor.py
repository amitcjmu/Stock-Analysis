"""
Execution Engine - Dependency Analysis Executor

Mixin for executing dependency analysis phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)

logger = get_logger(__name__)


class DependencyExecutorMixin:
    """Mixin for dependency analysis phase execution"""

    async def _execute_dependency_analysis(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute dependency analysis phase with shared data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        Per Qodo Bot: Uses shared instances passed from base.py for performance.
        """
        logger.info("Executing dependency analysis with persistent agents")

        try:

            # Build phase-specific input
            # CRITICAL FIX (ISSUE-999): Use assessment flow ID, not master flow ID!
            assessment_flow_id = phase_input.get("flow_id", str(master_flow.flow_id))
            crew_inputs = await input_builders.build_dependency_input(
                assessment_flow_id, phase_input
            )

            # Log dependency input preparation
            graph_metadata = (
                crew_inputs.get("context_data", {})
                .get("dependency_graph", {})
                .get("metadata", {})
            )
            logger.info(f"Built dependency input with graph metadata: {graph_metadata}")

            # Get agent from pool
            agent = await self._get_agent_for_phase(
                "dependency_analysis", agent_pool, master_flow
            )

            # Create task for agent
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Analyze application and infrastructure dependencies based on:
- Dependency graph metadata: {graph_metadata}
- Application integration points
- Infrastructure dependencies
- Cross-team dependencies

Provide a comprehensive dependency analysis with:
1. Dependency complexity score (0-100)
2. Critical dependencies and impact analysis
3. Circular dependencies and risks
4. Decoupling recommendations

Return results as valid JSON with keys: dependency_score, critical_deps, circular_deps, recommendations
""",
                expected_output=(
                    "Comprehensive dependency analysis with scores, "
                    "critical dependencies, and decoupling recommendations in JSON format"
                ),
                agent=(
                    agent._agent if hasattr(agent, "_agent") else agent
                ),  # Unwrap AgentWrapper for CrewAI Task
            )

            # Execute task with inputs
            start_time = time.time()

            # Convert context dict to JSON string (CrewAI expects string context)
            context_str = json.dumps(crew_inputs)

            # CC Phase 3: Setup callback handler for observability
            callback_handler = CallbackHandlerIntegration.create_callback_handler(
                flow_id=str(master_flow.flow_id),
                context={
                    "client_account_id": str(master_flow.client_account_id),
                    "engagement_id": str(master_flow.engagement_id),
                    "flow_type": "assessment",
                    "phase": "dependency",
                },
            )
            callback_handler.setup_callbacks()

            # Register task start
            callback_handler._step_callback(
                {
                    "type": "starting",
                    "status": "starting",
                    "agent": "dependency_analyst",
                    "task": "dependency_analysis",
                    "content": f"Starting dependency analysis with graph metadata: {graph_metadata}",
                }
            )

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

            # CC Phase 3: Register task completion
            callback_handler._task_completion_callback(
                {
                    "agent": "dependency_analyst",
                    "task_name": "dependency_analysis",
                    "status": "completed",
                    "task_id": "dependency_task",
                    "output": parsed_result,
                    "duration": execution_time,
                }
            )

            logger.info(f"✅ Dependency analysis completed in {execution_time:.2f}s")

            return {
                "phase": "dependency_analysis",
                "status": "completed",
                "agent": "dependency_analyst",
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": parsed_result,
                "context_data_available": bool(crew_inputs.get("context_data")),
            }

        except Exception as e:
            logger.error(f"Error in dependency analysis: {e}")
            return {
                "phase": "dependency_analysis",
                "status": "failed",
                "error": str(e),
            }
