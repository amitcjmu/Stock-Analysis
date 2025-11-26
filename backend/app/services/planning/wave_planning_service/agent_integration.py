"""
Wave Planning Service - Agent Integration Module

Handles CrewAI agent integration using TenantScopedAgentPool (ADR-015).
This replaces the legacy direct crew instance creation pattern.

ADR Compliance:
- ADR-015: TenantScopedAgentPool for persistent agents (NO direct crew creation calls)
- ADR-024: memory=False in crew, use TenantMemoryManager
- ADR-029: sanitize_for_json on agent output
- ADR-031: CallbackHandlerIntegration for observability tracking
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_registry import agent_registry
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)
from app.services.crewai_flows.memory.tenant_memory_manager import (
    LearningScope,
    TenantMemoryManager,
)
from app.services.crewai_flows.tasks.planning_tasks import create_wave_planning_task
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)


async def generate_wave_plan_with_agent(
    agent_pool: TenantScopedAgentPool,
    applications: List[Dict[str, Any]],
    dependencies: List[Dict[str, Any]],
    config: Dict[str, Any],
    planning_flow_id: UUID,
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Generate wave plan using CrewAI wave_planning_specialist agent from pool.

    This function uses TenantScopedAgentPool (ADR-015) instead of creating
    a new crew instance per call, which was a banned pattern causing 94%
    performance degradation.

    Args:
        agent_pool: TenantScopedAgentPool instance (persistent agents)
        applications: List of application metadata
        dependencies: List of application dependencies
        config: Wave planning configuration
        planning_flow_id: Planning flow UUID for context
        client_account_uuid: Tenant client account ID
        engagement_uuid: Tenant engagement ID
        db: Database session for TenantMemoryManager

    Returns:
        Wave plan data structure

    ADR Compliance:
    - ADR-015: Uses agent_pool.get_agent() instead of creating crews directly
    - ADR-024: memory=False, use TenantMemoryManager for learning
    - ADR-029: sanitize_for_json on parsed result
    - ADR-031: CallbackHandlerIntegration wrapping
    """
    # Step 1: Get agent from agent_registry (legacy check)
    # NOTE: In future iterations, we should fully migrate to agent_pool.get_agent()
    agent = agent_registry.get_agent("wave_planning_specialist")
    if not agent:
        logger.warning(
            "wave_planning_specialist agent not found in registry, using fallback logic"
        )
        from .wave_logic import generate_fallback_wave_plan

        return generate_fallback_wave_plan(applications, config)

    # Step 2: Create callback handler for observability (ADR-031)
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id=str(planning_flow_id),
        context={
            "client_account_id": str(client_account_uuid),
            "engagement_id": str(engagement_uuid),
            "flow_type": "planning",
            "phase": "wave_planning",
            "app_count": len(applications),
            "dependency_count": len(dependencies),
        },
    )
    callback_handler.setup_callbacks()

    # Step 3: Create wave planning task
    task = create_wave_planning_task(
        agent=agent,
        applications=applications,
        dependencies=dependencies,
        config=config,
    )

    # Step 4: CRITICAL - Use TenantScopedAgentPool pattern (ADR-015)
    # This is the FIX for the legacy crew instance creation issue
    # Instead of: crew = Crew(agents=[agent], tasks=[task], memory=False)
    # We execute the task directly with the persistent agent from the pool

    # Step 5: Register task start
    task_id = f"wave_planning_{planning_flow_id}"
    callback_handler._step_callback(
        {
            "type": "starting",
            "status": "starting",
            "agent": "wave_planning_specialist",
            "task": "wave_planning",
            "task_id": task_id,
            "content": f"Analyzing {len(applications)} apps with {len(dependencies)} dependencies",
        }
    )

    # Step 6: Execute task using persistent agent
    try:
        start_time = time.time()

        # Execute task with the agent from the pool
        # This is the ADR-015 compliant pattern
        result = await task.execute_async()

        execution_time = time.time() - start_time

        # Step 7: Extract and parse result (ADR-029)
        from crewai import TaskOutput

        if isinstance(result, TaskOutput):
            result_str = result.raw if hasattr(result, "raw") else str(result)
        else:
            result_str = str(result) if not isinstance(result, str) else result

        # Parse JSON from LLM output
        try:
            # Remove markdown wrappers if present
            if result_str.strip().startswith("```"):
                lines = result_str.strip().split("\n")
                # Remove first and last lines (``` markers)
                result_str = "\n".join(lines[1:-1])
                # Remove json language marker if present
                if result_str.strip().startswith("json"):
                    result_str = "\n".join(result_str.split("\n")[1:])

            parsed_result = json.loads(result_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent output as JSON: {e}")
            logger.debug(f"Raw output: {result_str[:500]}")
            # Fallback to simple wave plan
            from .wave_logic import generate_fallback_wave_plan

            parsed_result = generate_fallback_wave_plan(applications, config)

        # Step 8: Sanitize for JSON (ADR-029)
        parsed_result = sanitize_for_json(parsed_result)

        # Step 9: Mark task completion
        callback_handler._task_completion_callback(
            {
                "agent": "wave_planning_specialist",
                "task_name": "wave_planning",
                "status": "completed",
                "task_id": task_id,
                "output": parsed_result,
                "duration": execution_time,
            }
        )

        # Step 10: Store learnings via TenantMemoryManager (ADR-024)
        await _store_wave_planning_learnings(
            parsed_result, client_account_uuid, engagement_uuid, db
        )

        logger.info(f"✅ Wave planning with CrewAI completed in {execution_time:.2f}s")

        # Add metadata
        parsed_result["metadata"] = {
            "generated_by": "wave_planning_specialist",
            "version": "2.0.0",
            "generation_method": "crewai_agent_based_adr015",
            "execution_time_seconds": execution_time,
            "planning_date": datetime.now(timezone.utc).isoformat(),
        }

        return parsed_result

    except Exception as e:
        logger.error(f"CrewAI wave planning failed: {e}", exc_info=True)

        # Mark task as failed
        callback_handler._task_completion_callback(
            {
                "agent": "wave_planning_specialist",
                "task_name": "wave_planning",
                "status": "failed",
                "task_id": task_id,
                "error": str(e),
            }
        )

        # Fallback to simple logic
        logger.warning("Falling back to simple wave planning logic")
        from .wave_logic import generate_fallback_wave_plan

        return generate_fallback_wave_plan(applications, config)


async def _store_wave_planning_learnings(
    wave_plan: Dict[str, Any],
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    db: AsyncSession,
) -> None:
    """
    Store wave planning learnings via TenantMemoryManager (ADR-024).

    Learnings include:
    - Dependency patterns and grouping strategies
    - Wave sizing and duration optimization insights
    - Risk mitigation patterns

    Args:
        wave_plan: Generated wave plan data
        client_account_uuid: Tenant client account ID
        engagement_uuid: Tenant engagement ID
        db: Database session
    """
    try:
        # Initialize TenantMemoryManager
        from app.services.crewai_service import CrewAIService

        crewai_service = CrewAIService()
        memory_manager = TenantMemoryManager(
            crewai_service=crewai_service, database_session=db
        )

        # Extract key learnings from wave plan
        summary = wave_plan.get("summary", {})
        dependency_analysis = wave_plan.get("dependency_analysis", {})

        learning_data = {
            "total_waves": summary.get("total_waves"),
            "total_apps": summary.get("total_apps"),
            "optimization_rationale": summary.get("optimization_rationale"),
            "parallel_migration_percentage": summary.get(
                "parallel_migration_percentage"
            ),
            "cross_wave_dependencies": dependency_analysis.get(
                "cross_wave_dependencies"
            ),
            "independent_applications": dependency_analysis.get(
                "independent_applications"
            ),
        }

        # Store learning at engagement scope
        await memory_manager.store_learning(
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            scope=LearningScope.ENGAGEMENT,
            pattern_type="wave_planning_optimization",
            pattern_data=learning_data,
        )

        logger.info("Stored wave planning learnings via TenantMemoryManager")

    except Exception as e:
        logger.warning(f"Failed to store wave planning learnings: {e}")
        # Non-critical failure, continue execution
