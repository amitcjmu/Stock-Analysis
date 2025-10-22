"""
Execution Engine - Dependency Analysis Executor

Mixin for executing dependency analysis phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

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
            crew_inputs = await input_builders.build_dependency_input(
                str(master_flow.flow_id), phase_input
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
            result = await task.execute_async(context=context_str)

            execution_time = time.time() - start_time

            # Parse result (assuming JSON output from agent)
            try:
                parsed_result = (
                    json.loads(result) if isinstance(result, str) else result
                )
            except json.JSONDecodeError:
                parsed_result = {"raw_output": str(result)}

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
