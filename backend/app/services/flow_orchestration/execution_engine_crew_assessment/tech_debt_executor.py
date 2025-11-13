"""
Execution Engine - Tech Debt Assessment Executor

Mixin for executing technical debt assessment phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)

logger = get_logger(__name__)


class TechDebtExecutorMixin:
    """Mixin for tech debt assessment phase execution"""

    async def _execute_tech_debt_assessment(
        self,
        agent_pool: Any,
        master_flow: CrewAIFlowStateExtensions,
        phase_input: Dict[str, Any],
        data_repo: Any,
        input_builders: Any,
    ) -> Dict[str, Any]:
        """
        Execute technical debt assessment phase with shared data repository and input builders.

        Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
        Per Qodo Bot: Uses shared instances passed from base.py for performance.
        """
        logger.info("Executing technical debt assessment with persistent agents")

        try:

            # Build phase-specific input
            # CRITICAL FIX (ISSUE-999): Use assessment flow ID, not master flow ID!
            assessment_flow_id = phase_input.get("flow_id", str(master_flow.flow_id))
            crew_inputs = await input_builders.build_tech_debt_input(
                assessment_flow_id, phase_input
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
                agent=(
                    agent._agent if hasattr(agent, "_agent") else agent
                ),  # Unwrap AgentWrapper for CrewAI Task
            )

            # Execute task with inputs
            start_time = time.time()

            # Convert context dict to JSON string (CrewAI expects string context)
            context_str = json.dumps(crew_inputs)

            # CC Phase 3: Setup callback handler for observability
            from app.core.context import RequestContext

            callback_context = RequestContext(
                client_account_id=str(master_flow.client_account_id),
                engagement_id=str(master_flow.engagement_id),
                flow_id=str(master_flow.flow_id),
            )
            callback_handler = CallbackHandlerIntegration.create_callback_handler(
                flow_id=str(master_flow.flow_id),
                context=callback_context,
            )
            callback_handler.setup_callbacks()

            # Register task start
            callback_handler._step_callback(
                {
                    "type": "starting",
                    "status": "starting",
                    "agent": "complexity_analyst",
                    "task": "tech_debt_assessment",
                    "content": f"Starting tech debt assessment with {vuln_count} known vulnerabilities",
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
                    "agent": "complexity_analyst",
                    "task_name": "tech_debt_assessment",
                    "status": "completed",
                    "task_id": "tech_debt_task",
                    "output": parsed_result,
                    "duration": execution_time,
                }
            )

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
