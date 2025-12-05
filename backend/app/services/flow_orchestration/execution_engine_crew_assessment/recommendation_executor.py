"""
Execution Engine - Recommendation Generation Executor

Mixin for executing recommendation generation phase.
Per ADR-024: Uses TenantMemoryManager, CrewAI memory disabled.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)
from app.services.flow_orchestration.execution_engine_crew_assessment.recommendation_validator import (
    validate_recommendation_structure,
)

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
            # CRITICAL FIX (ISSUE-999): Use assessment flow ID, not master flow ID!
            assessment_flow_id = phase_input.get("flow_id", str(master_flow.flow_id))
            crew_inputs = await input_builders.build_recommendation_input(
                assessment_flow_id, phase_input
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

            # ISSUE-999: Extract application list for per-application 6R analysis
            applications = crew_inputs.get("context_data", {}).get("applications", [])
            app_count = len(applications)

            # RETRY-FIX: Check metadata for data issues
            meta = crew_inputs.get("context_data", {}).get("_meta", {})
            all_apps_completed = meta.get("all_apps_completed", False)
            apps_not_found = meta.get("apps_not_found_in_db", [])

            # Skip agent execution if no apps to process
            # Qodo Bot: Normalize early returns into persistable results
            if app_count == 0:
                meta_payload = {
                    "apps_with_existing_decisions": meta.get(
                        "apps_with_existing_decisions", 0
                    ),
                    "apps_not_found_in_db": apps_not_found,
                    "apps_to_process": 0,
                    "all_apps_completed": bool(all_apps_completed),
                    "has_missing_apps": bool(apps_not_found),
                }
                if all_apps_completed:
                    logger.info(
                        f"[RETRY-FIX] All applications already have 6R decisions - "
                        f"skipping agent execution for flow {assessment_flow_id}"
                    )
                    return {
                        "success": True,
                        "skipped": True,
                        "reason": "all_apps_completed",
                        "phase": "recommendation_generation",
                        "results": {
                            "recommendation_generation": {
                                "applications": [],
                                "meta": meta_payload,
                            }
                        },
                    }
                if apps_not_found:
                    logger.error(
                        f"[RETRY-FIX] Cannot retry: {len(apps_not_found)} selected apps "
                        f"not found in canonical_applications table: {apps_not_found}"
                    )
                    return {
                        "success": False,
                        "phase": "recommendation_generation",
                        "results": {
                            "recommendation_generation": {
                                "applications": [],
                                "meta": meta_payload,
                                "error": "data_integrity_error",
                            }
                        },
                    }
                logger.warning(
                    f"[RETRY-FIX] No applications to process for flow {assessment_flow_id}"
                )
                return {
                    "success": False,
                    "phase": "recommendation_generation",
                    "results": {
                        "recommendation_generation": {
                            "applications": [],
                            "meta": meta_payload,
                            "error": "no_apps_to_process",
                        }
                    },
                }

            # Create detailed application list for agent prompt
            app_list_text = "\n".join(
                [
                    f"- {i+1}. {app.get('name', 'Unknown')} "
                    f"(ID: {app.get('id', 'N/A')}, "
                    f"Criticality: {app.get('business_criticality', 'medium')})"
                    for i, app in enumerate(
                        applications[:20]
                    )  # Limit to first 20 for prompt
                ]
            )
            if app_count > 20:
                app_list_text += f"\n... and {app_count - 20} more applications"

            # Create task for agent with per-application 6R requirements
            from crewai import Task
            import time
            import json

            task = Task(
                description=f"""Generate comprehensive migration recommendations with \
PER-APPLICATION 6R strategy analysis.

CRITICAL REQUIREMENT (ISSUE-999): You MUST analyze EACH application individually and \
determine its specific 6R migration strategy.

APPLICATIONS TO ASSESS ({app_count} total):
{app_list_text}

ASSESSMENT PHASES COMPLETED:
- Readiness Assessment: Cloud readiness evaluation
- Complexity Analysis: Technical complexity scoring
- Dependency Analysis: Application dependencies and integration points
- Tech Debt Assessment: Technical debt quantification
- Risk Assessment: Migration risk evaluation
- Business Objectives: {obj_count} objectives

YOUR TASK:
For EACH application listed above, determine:
1. **6R Strategy**: Choose ONE strategy from [rehost, replatform, refactor, rearchitect, replace, retire]
   - rehost: Lift-and-shift with minimal changes
   - replatform: Minor cloud optimizations (e.g., managed databases)
   - refactor: Rearchitect for cloud-native patterns
   - rearchitect: Redesign application architecture
   - replace: Replace with SaaS/COTS solution
   - retire: Decommission if obsolete

2. **Confidence Score**: 0.0-1.0 based on assessment data quality and analysis depth

3. **Reasoning**: 2-3 sentence explanation covering:
   - Technical readiness factors
   - Business criticality considerations
   - Complexity and risk drivers
   - Dependencies and constraints

4. **Estimated Effort**: low/medium/high/very_high

5. **Risk Level**: low/medium/high

RESPONSE FORMAT (CRITICAL - MUST BE VALID JSON):
{{
  "applications": [
    {{
      "application_id": "uuid-from-input",
      "application_name": "Application Name",
      "six_r_strategy": "rehost|replatform|refactor|rearchitect|replace|retire",
      "confidence_score": 0.85,
      "reasoning": "Concise explanation based on assessment results",
      "estimated_effort": "medium",
      "risk_level": "low"
    }}
  ],
  "summary": {{
    "total_applications": {app_count},
    "strategy_distribution": {{"rehost": 5, "refactor": 3, ...}},
    "overall_recommendation": "Brief executive summary",
    "wave_plan": "High-level wave sequencing guidance",
    "modernization_opportunities": "Key modernization recommendations"
  }}
}}

Use all available assessment data from previous phases to make informed decisions. \
Base recommendations on EVIDENCE from the assessment results, not assumptions.
""",
                expected_output=(
                    "JSON object with per-application 6R strategies and comprehensive summary. "
                    "MUST include 'applications' array with all required fields for each application."
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

            # Bug #1168 Fix: Use master_flow.flow_id (NOT assessment_flow_id) for callbacks
            # The master_flow.flow_id is the FK-valid ID for agent_task_history table.
            # Other executors (readiness, complexity, dependency, tech_debt, risk) already use this pattern.
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

            # Generate unique task ID for this execution (prevents ID collisions)
            import uuid

            task_id = str(uuid.uuid4())

            # Register task start
            callback_handler._step_callback(
                {
                    "type": "starting",
                    "status": "starting",
                    "agent": "recommendation_generator",
                    "task": "recommendation_generation",
                    "task_id": task_id,
                    "content": (
                        f"Starting 6R recommendation generation for {app_count} "
                        f"applications with {obj_count} business objectives"
                    ),
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
            # Strip markdown code blocks if present (common LLM output format)
            if isinstance(result_str, str):
                result_str = result_str.strip()
                # Remove ```json and ``` wrappers
                if result_str.startswith("```json"):
                    result_str = result_str[7:]  # Remove ```json
                elif result_str.startswith("```"):
                    result_str = result_str[3:]  # Remove ```
                if result_str.endswith("```"):
                    result_str = result_str[:-3]  # Remove trailing ```
                result_str = result_str.strip()

            try:
                parsed_result = (
                    json.loads(result_str)
                    if isinstance(result_str, str)
                    else result_str
                )
            except json.JSONDecodeError as e:
                logger.error(
                    f"[ISSUE-999] Failed to parse recommendation agent output as JSON: {e}"
                )
                # CRITICAL: Fail fast - abort downstream processing on parse failure
                callback_handler._task_completion_callback(
                    {
                        "agent": "recommendation_generator",
                        "task_name": "recommendation_generation",
                        "status": "failed",
                        "task_id": task_id,
                        "error": str(e),
                        "output": {"raw_output": result_str},
                        "duration": execution_time,
                    }
                )
                return {
                    "phase": "recommendation_generation",
                    "status": "failed",
                    "agent": "recommendation_generator",
                    "inputs_prepared": True,
                    "execution_time_seconds": execution_time,
                    "results": {"raw_output": result_str, "parse_error": str(e)},
                    "context_data_available": bool(crew_inputs.get("context_data")),
                    "applications_assessed": 0,
                    "total_applications": app_count,
                    "assets_updated": False,
                    "assets_updated_count": 0,
                }

            # Per ADR-029: Sanitize LLM output to remove NaN/Infinity before JSON serialization
            parsed_result = sanitize_for_json(parsed_result)

            # ISSUE-999: Validate per-application recommendations structure
            validation_result = validate_recommendation_structure(
                parsed_result, app_count
            )

            # CC Phase 3: Register task completion
            callback_handler._task_completion_callback(
                {
                    "agent": "recommendation_generator",
                    "task_name": "recommendation_generation",
                    "status": (
                        "completed"
                        if validation_result["is_valid"]
                        else "completed_with_warnings"
                    ),
                    "task_id": task_id,  # Use the unique task_id generated earlier
                    "output": parsed_result,
                    "duration": execution_time,
                }
            )

            logger.info(
                f"[ISSUE-999] ✅ Recommendation generation completed in {execution_time:.2f}s - "
                f"{validation_result['applications_with_6r']} of {app_count} applications have 6R strategies"
            )

            # ISSUE-999: Update assets table with 6R recommendations
            assets_updated_count = await self._update_assets_with_recommendations(
                parsed_result=parsed_result,
                assessment_flow_id=assessment_flow_id,
                master_flow=master_flow,
            )

            # ISSUE-999: Structure results for phase_results storage
            structured_result = {
                "recommendation_generation": {
                    "applications": parsed_result.get("applications", []),
                    "summary": parsed_result.get("summary", {}),
                    "total_applications_assessed": validation_result[
                        "applications_with_6r"
                    ],
                    "total_applications_expected": app_count,
                    "execution_time_seconds": execution_time,
                    "validation": validation_result,
                    "assets_updated_count": assets_updated_count,  # ISSUE-999: Track asset updates
                    "metadata": {
                        "timestamp": time.time(),
                        "agent": "recommendation_generator",
                        "flow_id": assessment_flow_id,
                    },
                }
            }

            return {
                "phase": "recommendation_generation",
                "status": "completed",
                "agent": "recommendation_generator",
                "inputs_prepared": True,
                "execution_time_seconds": execution_time,
                "results": structured_result,  # Structured for phase_results
                "context_data_available": bool(crew_inputs.get("context_data")),
                "applications_assessed": validation_result["applications_with_6r"],
                "total_applications": app_count,
                "assets_updated": assets_updated_count
                > 0,  # ISSUE-999: Flag for asset updates
                "assets_updated_count": assets_updated_count,  # ISSUE-999: Number of assets updated
            }

        except Exception as e:
            logger.error(f"Error in recommendation generation: {e}")
            return {
                "phase": "recommendation_generation",
                "status": "failed",
                "error": str(e),
            }
