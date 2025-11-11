"""
Assessment Flow MFO Integration - Update Operations

Handles update operations for assessment flows through Master Flow Orchestrator.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    AssessmentFlow,
    AssessmentFlowStatus,
)
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format
from .queries import get_assessment_status_via_mfo

logger = logging.getLogger(__name__)


async def update_assessment_via_mfo(
    flow_id: UUID,
    updates: Dict[str, Any],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Update assessment flow through MFO coordination.

    Maintains consistency across master + child tables using atomic transactions.

    Per ADR-012:
    - Child flow updates: Operational changes (phase, progress, status transitions)
    - Master flow updates: Lifecycle changes (running → paused → completed)

    Args:
        flow_id: Assessment flow UUID
        updates: Dict with fields to update (status, current_phase, progress, etc.)
        db: Database session

    Returns:
        Dict with updated unified state

    Raises:
        ValueError: If flow not found or invalid state transition
    """
    try:
        async with db.begin():
            # Get both master and child flows
            query = (
                select(CrewAIFlowStateExtensions, AssessmentFlow)
                .join(
                    AssessmentFlow,
                    AssessmentFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id,
                )
                .where(CrewAIFlowStateExtensions.flow_id == flow_id)
            )

            result = await db.execute(query)
            row = result.first()

            if not row:
                raise ValueError(f"Assessment flow {flow_id} not found")

            master_flow, child_flow = row

            # Update child flow (operational state)
            if "status" in updates:
                child_flow.status = updates["status"]
            if "current_phase" in updates:
                child_flow.current_phase = updates["current_phase"]
            if "progress" in updates:
                child_flow.progress = updates["progress"]
            if "phase_progress" in updates:
                child_flow.phase_progress = updates["phase_progress"]
            if "runtime_state" in updates:
                child_flow.runtime_state = {
                    **(child_flow.runtime_state or {}),
                    **updates["runtime_state"],
                }

            # Update master flow (lifecycle state) if needed
            # Per ADR-012: Synchronize terminal states
            if child_flow.status == AssessmentFlowStatus.COMPLETED.value:
                master_flow.flow_status = "completed"
                child_flow.completed_at = datetime.utcnow()
            elif child_flow.status == AssessmentFlowStatus.FAILED.value:
                master_flow.flow_status = "failed"
            elif child_flow.status == AssessmentFlowStatus.PAUSED.value:
                master_flow.flow_status = "paused"
            elif child_flow.status == AssessmentFlowStatus.IN_PROGRESS.value:
                master_flow.flow_status = "running"

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Updated assessment flow via MFO: flow_id={flow_id}, updates={updates}",
                flow_id=str(flow_id),
                updates=str(updates.keys()),
            )
        )

        # Return updated unified state
        return await get_assessment_status_via_mfo(flow_id, db)

    except ValueError:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update assessment via MFO: flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
