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

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
    agent_pool: type,  # TenantScopedAgentPool class reference (has class methods)
    applications: List[Dict[str, Any]],
    dependencies: List[Dict[str, Any]],
    config: Dict[str, Any],
    master_flow_id: UUID,  # CRITICAL: FK to crewai_flow_state_extensions for agent_task_history
    planning_flow_id: UUID,  # Child flow ID for context/logging only
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
        agent_pool: TenantScopedAgentPool class reference (has class methods)
        applications: List of application metadata
        dependencies: List of application dependencies
        config: Wave planning configuration
        master_flow_id: Master flow UUID (FK to crewai_flow_state_extensions)
        planning_flow_id: Planning flow UUID for context/logging
        client_account_uuid: Tenant client account ID
        engagement_uuid: Tenant engagement ID
        db: Database session for TenantMemoryManager

    Returns:
        Wave plan data structure

    ADR Compliance:
    - ADR-015: Uses TenantScopedAgentPool.get_or_create_agent() class method
    - ADR-024: memory=False, use TenantMemoryManager for learning
    - ADR-029: sanitize_for_json on parsed result
    - ADR-031: CallbackHandlerIntegration wrapping
    """
    # Step 1: Get CrewAI agent from TenantScopedAgentPool (ADR-015 compliant)
    # Use class method to get persistent agent instead of agent_registry metadata
    try:
        agent = await TenantScopedAgentPool.get_or_create_agent(
            client_id=str(client_account_uuid),
            engagement_id=str(engagement_uuid),
            agent_type="wave_planning_specialist",
            context_info={
                "flow_id": str(planning_flow_id),
                "flow_type": "planning",
            },
        )
        logger.info(
            f"Retrieved wave_planning_specialist agent from TenantScopedAgentPool "
            f"for client {client_account_uuid}"
        )
    except Exception as e:
        logger.warning(
            f"Failed to get agent from TenantScopedAgentPool: {e}, using fallback logic"
        )
        from .wave_logic import generate_fallback_wave_plan

        return generate_fallback_wave_plan(applications, config)

    # Step 2: Create callback handler for observability (ADR-031)
    # CRITICAL: Use master_flow_id (not planning_flow_id) for agent_task_history FK constraint
    # The FK requires flow_id to exist in crewai_flow_state_extensions (master flow table)
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id=str(master_flow_id),  # FK to crewai_flow_state_extensions
        context=None,  # No RequestContext available in this context
        metadata={
            "client_account_id": str(client_account_uuid),
            "engagement_id": str(engagement_uuid),
            "planning_flow_id": str(planning_flow_id),  # Child flow ID for reference
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

    # Step 4: Create Crew using factory (ADR-015 + ADR-024 compliant)
    # ADR-015: Agent comes from TenantScopedAgentPool (persistent, not created per call)
    # ADR-024: create_crew() sets memory=False by default (use TenantMemoryManager instead)
    # CRITICAL: Use create_crew() from factory, NOT direct Crew() instantiation
    from app.services.crewai_flows.config.crew_factory import create_crew

    # Unwrap AgentWrapper to get the actual CrewAI Agent (ADR-015)
    # TenantScopedAgentPool returns AgentWrapper for Pydantic v2 compatibility,
    # but Crew expects BaseAgent instances
    actual_agent = agent._agent if hasattr(agent, "_agent") else agent

    # Use factory-created crew which applies ADR-024 defaults (memory=False)
    crew = create_crew(
        agents=[actual_agent],
        tasks=[task],
        verbose=True,
    )

    # Step 5: Register task start
    # Use master_flow_id for task tracking (consistent with callback handler)
    task_id = f"wave_planning_{master_flow_id}"
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

    # Step 6: Execute crew using persistent agent
    try:
        start_time = time.time()

        # Execute crew synchronously in a thread (CrewAI kickoff is blocking)
        # This is the correct async pattern used throughout the codebase
        import asyncio

        result = await asyncio.to_thread(crew.kickoff)

        execution_time = time.time() - start_time

        # Step 7: Extract and parse result (ADR-029)
        # CrewOutput has .raw attribute with the final answer text
        if hasattr(result, "raw"):
            result_str = result.raw
        elif hasattr(result, "result"):
            result_str = result.result
        else:
            result_str = str(result) if not isinstance(result, str) else result

        logger.info(
            f"Wave planning agent completed. Output length: {len(result_str)} chars"
        )

        # Parse JSON from LLM output using ADR-029 compliant parser
        try:
            from app.utils.json_sanitization import safe_parse_llm_json

            parsed_result = safe_parse_llm_json(result_str)

            if not parsed_result or "waves" not in parsed_result:
                logger.warning("Agent output missing 'waves' key, using fallback")
                from .wave_logic import generate_fallback_wave_plan

                parsed_result = generate_fallback_wave_plan(applications, config)
            else:
                # ADR-035: Validate and enrich waves with applications if missing
                # LLM output may be truncated (16KB limit) or missing applications
                parsed_result = _validate_and_enrich_wave_applications(
                    parsed_result, applications
                )
        except Exception as e:
            logger.error(f"Failed to parse agent output as JSON: {e}")
            logger.debug(f"Raw output (truncated): {result_str[:500]}...")
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


def _validate_and_enrich_wave_applications(
    parsed_result: Dict[str, Any],
    applications: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate and enrich wave applications if missing or incomplete.

    Per ADR-035, LLM output may be truncated due to 16KB limit, causing
    the applications array within waves to be missing or incomplete.
    This function:
    1. Checks if each wave has an applications array
    2. If missing, distributes input applications across waves using application_count
    3. Enriches application data with name, criticality, complexity, migration_strategy

    Args:
        parsed_result: Parsed LLM output with waves structure
        applications: Input applications list from planning flow

    Returns:
        Enriched wave plan with applications populated in each wave
    """
    waves = parsed_result.get("waves", [])

    # Check if any wave is missing applications
    waves_missing_apps = [
        w
        for w in waves
        if not w.get("applications") or len(w.get("applications", [])) == 0
    ]

    if not waves_missing_apps:
        logger.info("All waves have applications - no enrichment needed")
        return parsed_result

    logger.warning(
        f"{len(waves_missing_apps)} of {len(waves)} waves missing applications - enriching"
    )

    # Track which apps have been assigned
    assigned_app_ids = set()

    # First pass: collect already-assigned apps from waves that have them
    for wave in waves:
        wave_apps = wave.get("applications", [])
        for app in wave_apps:
            app_id = app.get("application_id") or app.get("id")
            if app_id:
                assigned_app_ids.add(str(app_id))

    # Get unassigned applications
    unassigned_apps = [
        app for app in applications if str(app.get("id", "")) not in assigned_app_ids
    ]

    # Distribute unassigned apps to waves missing applications
    app_index = 0
    for wave in waves:
        if not wave.get("applications") or len(wave.get("applications", [])) == 0:
            # Use application_count from wave metadata, or estimate
            app_count = wave.get("application_count", 0)
            if app_count == 0:
                # Estimate based on remaining apps and remaining waves
                remaining_waves_missing = len(
                    [w for w in waves if not w.get("applications")]
                )
                app_count = max(
                    1, len(unassigned_apps) // max(1, remaining_waves_missing)
                )

            # Assign apps to this wave
            wave_applications = []
            for _ in range(min(app_count, len(unassigned_apps) - app_index)):
                if app_index >= len(unassigned_apps):
                    break

                app = unassigned_apps[app_index]
                app_id = str(app.get("id", ""))

                wave_applications.append(
                    {
                        "application_id": app_id,
                        "application_name": app.get("name")
                        or app.get("application_name")
                        or f"App {app_id[:8]}...",
                        "rationale": f"Assigned to wave {wave.get('wave_number', 'N/A')} during enrichment",
                        "criticality": app.get("business_criticality", "medium"),
                        "complexity": app.get("complexity", "medium"),
                        "migration_strategy": app.get("migration_strategy")
                        or app.get("six_r_strategy", "rehost"),
                        "dependency_depth": 0,
                    }
                )
                app_index += 1

            wave["applications"] = wave_applications
            wave["application_count"] = len(wave_applications)

            logger.info(
                f"Enriched wave {wave.get('wave_number')} with {len(wave_applications)} applications"
            )

    # Handle any remaining apps by adding to the last wave
    if app_index < len(unassigned_apps) and waves:
        last_wave = waves[-1]
        if "applications" not in last_wave:
            last_wave["applications"] = []
        for app in unassigned_apps[app_index:]:
            app_id = str(app.get("id", ""))
            last_wave["applications"].append(
                {
                    "application_id": app_id,
                    "application_name": app.get("name")
                    or app.get("application_name")
                    or f"App {app_id[:8]}...",
                    "rationale": "Assigned to final wave during enrichment",
                    "criticality": app.get("business_criticality", "medium"),
                    "complexity": app.get("complexity", "medium"),
                    "migration_strategy": app.get("migration_strategy")
                    or app.get("six_r_strategy", "rehost"),
                    "dependency_depth": 0,
                }
            )
        last_wave["application_count"] = len(last_wave["applications"])

    return parsed_result


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
        # Initialize TenantMemoryManager (ADR-024)
        # crewai_service can be None when not using CrewAI built-in memory
        memory_manager = TenantMemoryManager(crewai_service=None, database_session=db)

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
            pattern_type="WAVE_PLANNING_OPTIMIZATION",
            pattern_data=learning_data,
        )

        logger.info("Stored wave planning learnings via TenantMemoryManager")

    except Exception as e:
        logger.warning(f"Failed to store wave planning learnings: {e}")
        # Non-critical failure, continue execution
