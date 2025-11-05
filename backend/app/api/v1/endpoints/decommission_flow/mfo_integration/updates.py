"""
Decommission Flow MFO Integration - Update Operations

Handles update operations for decommission flows through Master Flow Orchestrator.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format
from .queries import get_decommission_status_via_mfo

logger = logging.getLogger(__name__)


async def update_decommission_phase_via_mfo(
    flow_id: UUID,
    phase_name: str,
    phase_status: str,
    phase_data: Optional[Dict[str, Any]],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Update decommission flow phase through MFO coordination.

    Maintains consistency across master + child tables using atomic transactions.
    Syncs master flow status based on child flow phase progression.

    Per ADR-012:
    - Child flow updates: Operational changes (phase, progress, status transitions)
    - Master flow updates: Lifecycle changes (running → paused → completed)

    CRITICAL: This function updates both master and child flows atomically to
    ensure state consistency.

    Args:
        flow_id: Decommission flow UUID
        phase_name: Phase to update (decommission_planning, data_migration, system_shutdown)
        phase_status: New phase status (pending, running, completed, failed)
        phase_data: Optional additional data to store in runtime_state
        db: Database session

    Returns:
        Dict with updated unified state

    Raises:
        ValueError: If flow not found or invalid phase/status
        SQLAlchemyError: If database operations fail
    """
    # Validate phase name
    valid_phases = ["decommission_planning", "data_migration", "system_shutdown"]
    if phase_name not in valid_phases:
        raise ValueError(
            f"Invalid phase_name: {phase_name}. "
            f"Must be one of: {', '.join(valid_phases)}"
        )

    # Validate phase status
    valid_statuses = ["pending", "running", "completed", "failed"]
    if phase_status not in valid_statuses:
        raise ValueError(
            f"Invalid phase_status: {phase_status}. "
            f"Must be one of: {', '.join(valid_statuses)}"
        )

    try:
        async with db.begin():
            # Get both master and child flows
            query = (
                select(CrewAIFlowStateExtensions, DecommissionFlow)
                .join(
                    DecommissionFlow,
                    DecommissionFlow.master_flow_id
                    == CrewAIFlowStateExtensions.flow_id,
                )
                .where(CrewAIFlowStateExtensions.flow_id == flow_id)
            )

            result = await db.execute(query)
            row = result.first()

            if not row:
                raise ValueError(f"Decommission flow {flow_id} not found")

            master_flow, child_flow = row

            # Update child flow phase-specific status column
            phase_status_col = f"{phase_name}_status"
            setattr(child_flow, phase_status_col, phase_status)

            # Update timestamp if phase completed
            if phase_status == "completed":
                phase_completed_col = f"{phase_name}_completed_at"
                setattr(child_flow, phase_completed_col, datetime.utcnow())

                # Advance current_phase to next phase
                phase_progression = {
                    "decommission_planning": "data_migration",
                    "data_migration": "system_shutdown",
                    "system_shutdown": "completed",
                }
                next_phase = phase_progression.get(phase_name)
                if next_phase:
                    child_flow.current_phase = next_phase

            # Update runtime_state if phase_data provided
            if phase_data:
                runtime_state = child_flow.runtime_state or {}
                runtime_state[f"{phase_name}_data"] = phase_data
                runtime_state["last_updated"] = datetime.utcnow().isoformat()
                child_flow.runtime_state = runtime_state

            # Sync master flow status based on child flow state
            # Per ADR-012: Master flow reflects high-level lifecycle
            if phase_status == "failed":
                master_flow.flow_status = "failed"
                child_flow.status = "failed"
            elif child_flow.current_phase == "completed":
                # All phases complete
                master_flow.flow_status = "completed"
                child_flow.status = "completed"
            elif phase_status == "running":
                # Flow actively processing
                master_flow.flow_status = "running"
                child_flow.status = phase_name  # Status matches current phase
            elif (
                phase_status == "completed" and child_flow.current_phase != "completed"
            ):
                # Phase complete but flow continues
                master_flow.flow_status = "running"
                child_flow.status = child_flow.current_phase

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Updated decommission phase via MFO: flow_id={flow_id}, "
                "phase={phase}, status={status}",
                flow_id=str(flow_id),
                phase=phase_name,
                status=phase_status,
            )
        )

        # Fixed per Qodo: Pass tenant identifiers for multi-tenancy security
        return await get_decommission_status_via_mfo(
            flow_id,
            db,
            client_account_id=child_flow.client_account_id,
            engagement_id=child_flow.engagement_id,
        )

    except ValueError:
        # Re-raise validation errors
        raise
    except SQLAlchemyError as e:
        logger.error(
            safe_log_format(
                "Database error updating decommission phase via MFO: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update decommission phase via MFO: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
