"""
Execution Engine - Complexity Analysis Executor

Mixin for executing complexity analysis phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class ComplexityExecutorMixin:
    """Mixin for complexity analysis phase execution"""

    async def _execute_complexity_analysis(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute complexity analysis phase with shared data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        Per Qodo Bot: Uses shared instances passed from base.py for performance.
        """
        logger.info("Executing complexity analysis with persistent agents")

        try:

            # Build phase-specific input
            crew_inputs = await input_builders.build_complexity_input(
                str(master_flow.flow_id), phase_input
            )

            # Log complexity input preparation
            complexity_indicators = crew_inputs.get("context_data", {}).get(
                "complexity_indicators", {}
            )
            logger.info(
                f"Built complexity input with indicators: {complexity_indicators}"
            )

            # Get agent from pool
            agent = await self._get_agent_for_phase(
                "complexity_analysis", agent_pool, master_flow
            )

            # Create task for agent
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Analyze migration complexity for applications based on:
- Application architecture and technology stacks
- Component complexity indicators: {complexity_indicators}
- Integration points and dependencies
- Customization and technical debt levels

Provide a comprehensive complexity analysis with:
1. Overall complexity score (0-100)
2. Component-level complexity breakdown
3. Integration complexity assessment
4. Modernization opportunities

Return results as valid JSON with keys: complexity_score, components, integrations, modernization
""",
                expected_output=(
                    "Comprehensive complexity analysis with scores, "
                    "component breakdown, and modernization opportunities in JSON format"
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

            logger.info(f"✅ Complexity analysis completed in {execution_time:.2f}s")

            return {
                "phase": "complexity_analysis",
                "status": "completed",
                "agent": "complexity_analyst",
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": parsed_result,
                "context_data_available": bool(crew_inputs.get("context_data")),
            }

        except Exception as e:
            logger.error(f"Error in complexity analysis: {e}")
            return {
                "phase": "complexity_analysis",
                "status": "failed",
                "error": str(e),
            }
