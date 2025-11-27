"""
Decommission Agent Integration - Data Migration Phase Module

Handles execution of data migration phase with CrewAI agents.
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
from .fallbacks import _generate_fallback_migration_result
from .learning import _store_decommission_learnings

logger = logging.getLogger(__name__)


async def execute_data_migration_with_agents(
    master_flow_id: UUID,
    child_flow_id: UUID,
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    system_ids: List[str],
    retention_policies: Optional[Dict[str, Any]],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Execute data migration phase using CrewAI agents.

    ADR Compliance: Same as execute_decommission_planning_with_agents
    """
    phase_name = "data_migration"

    agents = await _get_agents_for_phase(
        phase_name, client_account_uuid, engagement_uuid, child_flow_id
    )

    if not agents:
        logger.warning("No agents available for data_migration, using fallback")
        return _generate_fallback_migration_result(system_ids)

    callback_handler = CallbackHandlerIntegration.create_callback_handler(
        flow_id=str(master_flow_id),
        context=None,
        metadata={
            "client_account_id": str(client_account_uuid),
            "engagement_id": str(engagement_uuid),
            "child_flow_id": str(child_flow_id),
            "flow_type": "decommission",
            "phase": phase_name,
        },
    )
    callback_handler.setup_callbacks()

    tasks = []

    # Task 1: Data retention analysis
    if len(agents) > 0:
        tasks.append(
            _create_decommission_task(
                agent=agents[0],
                task_description=(
                    "Analyze data retention requirements for the systems being decommissioned. "
                    "Determine retention periods based on regulatory requirements (GDPR, SOX, HIPAA). "
                    "Create archival policies for each data category."
                ),
                expected_output=(
                    "JSON object with: retention_policies (per data type), "
                    "archival_plan (timeline and locations), compliance_checklist"
                ),
                context_data={
                    "system_ids": system_ids,
                    "existing_policies": retention_policies,
                },
            )
        )

    # Task 2: Compliance validation
    if len(agents) > 1:
        tasks.append(
            _create_decommission_task(
                agent=agents[1],
                task_description=(
                    "Validate that all data migration activities meet regulatory compliance. "
                    "Create audit trail documentation and verify secure disposal procedures."
                ),
                expected_output=(
                    "JSON object with: compliance_status, audit_trail, "
                    "required_approvals, compliance_gaps"
                ),
                context_data={
                    "system_ids": system_ids,
                },
            )
        )

    from app.services.crewai_flows.config.crew_factory import create_crew

    crew = create_crew(agents=agents, tasks=tasks, verbose=True)

    task_id = f"data_migration_{master_flow_id}"
    callback_handler._step_callback(
        {
            "type": "starting",
            "status": "starting",
            "agent": "decommission_data_retention",
            "task": "data_migration",
            "task_id": task_id,
        }
    )

    try:
        start_time = time.time()
        result = await asyncio.to_thread(crew.kickoff)
        execution_time = time.time() - start_time

        result_str = result.raw if hasattr(result, "raw") else str(result)

        try:
            from app.utils.json_sanitization import safe_parse_llm_json

            parsed_result = safe_parse_llm_json(result_str)
            if not parsed_result:
                parsed_result = _generate_fallback_migration_result(system_ids)
        except Exception:
            parsed_result = _generate_fallback_migration_result(system_ids)

        parsed_result = sanitize_for_json(parsed_result)

        callback_handler._task_completion_callback(
            {
                "agent": "decommission_data_retention",
                "task_name": "data_migration",
                "status": "completed",
                "task_id": task_id,
                "duration": execution_time,
            }
        )

        await _store_decommission_learnings(
            phase_name, parsed_result, client_account_uuid, engagement_uuid, db
        )

        return {
            "status": "success",
            "phase": phase_name,
            "execution_type": "crewai_adr015",
            "result": parsed_result,
            "execution_time": execution_time,
        }

    except Exception as e:
        logger.error(f"Data migration phase failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "phase": phase_name,
            "error": str(e),
            "result": _generate_fallback_migration_result(system_ids),
        }
