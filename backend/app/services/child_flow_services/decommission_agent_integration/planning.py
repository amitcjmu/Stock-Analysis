"""
Decommission Agent Integration - Planning Phase Module

Handles execution of decommission planning phase with CrewAI agents.
ADR Compliance: ADR-015, ADR-024, ADR-029, ADR-031
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)
from app.utils.json_sanitization import sanitize_for_json

from .base import _create_decommission_task, _get_agents_for_phase
from .fallbacks import _generate_fallback_planning_result
from .learning import _store_decommission_learnings

logger = logging.getLogger(__name__)


async def execute_decommission_planning_with_agents(
    master_flow_id: UUID,
    child_flow_id: UUID,
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    system_ids: List[str],
    decommission_strategy: Optional[Dict[str, Any]],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Execute decommission planning phase using CrewAI agents.

    ADR Compliance:
    - ADR-015: TenantScopedAgentPool for agents
    - ADR-024: create_crew() with memory=False
    - ADR-029: sanitize_for_json on output
    - ADR-031: CallbackHandlerIntegration for observability

    Args:
        master_flow_id: Master flow UUID (FK to crewai_flow_state_extensions)
        child_flow_id: Child flow UUID for reference
        client_account_uuid: Tenant client account ID
        engagement_uuid: Tenant engagement ID
        system_ids: List of system IDs to decommission
        decommission_strategy: Strategy configuration
        db: Database session

    Returns:
        Decommission planning result
    """
    phase_name = "decommission_planning"

    # Get agents from TenantScopedAgentPool (ADR-015)
    agents = await _get_agents_for_phase(
        phase_name, client_account_uuid, engagement_uuid, child_flow_id
    )

    if not agents:
        logger.warning("No agents available for decommission_planning, using fallback")
        return _generate_fallback_planning_result(system_ids)

    # Create callback handler for observability (ADR-031)
    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id=str(master_flow_id),
        context=None,
        metadata={
            "client_account_id": str(client_account_uuid),
            "engagement_id": str(engagement_uuid),
            "child_flow_id": str(child_flow_id),
            "flow_type": "decommission",
            "phase": phase_name,
            "system_count": len(system_ids),
        },
    )
    callback_handler.setup_callbacks()

    # Create tasks for each agent
    tasks = []

    # Task 1: System dependency analysis
    if len(agents) > 0:
        tasks.append(
            _create_decommission_task(
                agent=agents[0],
                task_description=(
                    "Analyze system dependencies and identify impact zones for the systems "
                    "being decommissioned. Create a comprehensive dependency map showing "
                    "upstream and downstream system relationships."
                ),
                expected_output=(
                    "JSON object with: dependency_map (list of dependencies), "
                    "impact_zones (affected systems), risk_assessment (risk level and factors)"
                ),
                context_data={
                    "system_ids": system_ids,
                    "system_count": len(system_ids),
                    "strategy": decommission_strategy,
                },
            )
        )

    # Task 2: Dependency mapping (if second agent available)
    if len(agents) > 1:
        tasks.append(
            _create_decommission_task(
                agent=agents[1],
                task_description=(
                    "Map complex system relationships and integration points. "
                    "Create a visual dependency graph and identify critical paths "
                    "that could cause cascade failures during decommissioning."
                ),
                expected_output=(
                    "JSON object with: integration_points (list of integrations), "
                    "critical_paths (ordered list of dependencies), "
                    "cascade_risk_factors (potential cascade points)"
                ),
                context_data={
                    "system_ids": system_ids,
                    "system_count": len(system_ids),
                },
            )
        )

    # Create crew using factory (ADR-024)
    from app.services.crewai_flows.config.crew_factory import create_crew

    crew = create_crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
    )

    # Register task start
    task_id = f"decommission_planning_{master_flow_id}"
    callback_handler._step_callback(
        {
            "type": "starting",
            "status": "starting",
            "agent": "decommission_system_analyst",
            "task": "decommission_planning",
            "task_id": task_id,
            "content": f"Analyzing {len(system_ids)} systems for decommissioning",
        }
    )

    # Execute crew
    try:
        start_time = time.time()
        result = await asyncio.to_thread(crew.kickoff)
        execution_time = time.time() - start_time

        # Parse result (ADR-029)
        result_str = result.raw if hasattr(result, "raw") else str(result)

        try:
            from app.utils.json_sanitization import safe_parse_llm_json

            parsed_result = safe_parse_llm_json(result_str)
            if not parsed_result:
                parsed_result = _generate_fallback_planning_result(system_ids)
        except Exception as e:
            logger.error(f"Failed to parse planning result: {e}")
            parsed_result = _generate_fallback_planning_result(system_ids)

        # Sanitize for JSON (ADR-029)
        parsed_result = sanitize_for_json(parsed_result)

        # Mark task completion
        callback_handler._task_completion_callback(
            {
                "agent": "decommission_system_analyst",
                "task_name": "decommission_planning",
                "status": "completed",
                "task_id": task_id,
                "output": parsed_result,
                "duration": execution_time,
            }
        )

        # Store learnings (ADR-024)
        await _store_decommission_learnings(
            phase_name, parsed_result, client_account_uuid, engagement_uuid, db
        )

        logger.info(f"Decommission planning completed in {execution_time:.2f}s")

        return {
            "status": "success",
            "phase": phase_name,
            "execution_type": "crewai_adr015",
            "result": parsed_result,
            "execution_time": execution_time,
        }

    except Exception as e:
        logger.error(f"Decommission planning failed: {e}", exc_info=True)
        callback_handler._task_completion_callback(
            {
                "agent": "decommission_system_analyst",
                "task_name": "decommission_planning",
                "status": "failed",
                "task_id": task_id,
                "error": str(e),
            }
        )
        return {
            "status": "failed",
            "phase": phase_name,
            "error": str(e),
            "result": _generate_fallback_planning_result(system_ids),
        }
