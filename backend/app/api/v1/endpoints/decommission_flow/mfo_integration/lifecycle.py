"""
Decommission Flow MFO Integration - Lifecycle Operations

Handles lifecycle operations (pause, resume) for decommission flows.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format
from .queries import get_decommission_status_via_mfo

logger = logging.getLogger(__name__)


async def resume_decommission_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    phase: str | None,
    user_input: Dict[str, Any] | None,  # Fixed per CodeRabbit: Add user_input parameter
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Resume paused decommission flow (updates both master and child tables atomically).

    Per ADR-012: Syncs both master flow (lifecycle) and child flow (operational state)
    to ensure consistent resume behavior.

    Args:
        flow_id: Decommission flow UUID
        client_account_id: Client account UUID for multi-tenant isolation
        engagement_id: Engagement UUID for multi-tenant isolation
        phase: Optional phase to resume from (if None, continues from current)
        user_input: Optional user input data for resuming execution
        db: Database session

    Returns:
        Dict with updated unified state

    Raises:
        ValueError: If flow not found or not in paused state
        SQLAlchemyError: If database operations fail
    """
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
                .where(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    DecommissionFlow.client_account_id == client_account_id,
                    DecommissionFlow.engagement_id == engagement_id,
                )
            )

            result = await db.execute(query)
            row = result.first()

            if not row:
                raise ValueError(f"Decommission flow {flow_id} not found")

            master_flow, child_flow = row

            # Validate flow is in paused state
            if master_flow.flow_status != "paused":
                raise ValueError(
                    f"Flow {flow_id} cannot be resumed - current status: "
                    f"{master_flow.flow_status}"
                )

            # Resume master flow (lifecycle)
            master_flow.flow_status = "running"

            # Resume child flow (operational state)
            # NOTE: Per DecommissionFlow model, status uses phase names (decommission_planning, etc.)
            # This is intentional - see CheckConstraint in core_models.py lines 45-48
            # If specific phase requested, update current_phase
            if phase:
                child_flow.current_phase = phase
                child_flow.status = phase  # Status tracks phase for decommission flows
            else:
                # Restore status to current phase
                child_flow.status = child_flow.current_phase

            # Update runtime_state with resume timestamp and user input
            runtime_state = child_flow.runtime_state or {}
            runtime_state["resumed_at"] = datetime.utcnow().isoformat()
            # Fixed per CodeRabbit: Store user_input if provided
            if user_input:
                runtime_state["resume_user_input"] = user_input
            child_flow.runtime_state = runtime_state

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Resumed decommission flow via MFO: flow_id={flow_id}",
                flow_id=str(flow_id),
            )
        )

        # Return updated unified state
        return await get_decommission_status_via_mfo(
            flow_id, db, client_account_id, engagement_id
        )

    except ValueError:
        # Re-raise validation errors
        raise
    except SQLAlchemyError as e:
        logger.error(
            safe_log_format(
                "Database error resuming decommission flow: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to resume decommission flow: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise


async def pause_decommission_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Pause decommission flow (updates both master and child tables atomically).

    Per ADR-012: Syncs both master flow (lifecycle) and child flow (operational state)
    to ensure consistent pause behavior.

    Args:
        flow_id: Decommission flow UUID
        client_account_id: Client account UUID for multi-tenant isolation
        engagement_id: Engagement UUID for multi-tenant isolation
        db: Database session

    Returns:
        Dict with updated unified state

    Raises:
        ValueError: If flow not found or not in running state
        SQLAlchemyError: If database operations fail
    """
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
                .where(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    DecommissionFlow.client_account_id == client_account_id,
                    DecommissionFlow.engagement_id == engagement_id,
                )
            )

            result = await db.execute(query)
            row = result.first()

            if not row:
                raise ValueError(f"Decommission flow {flow_id} not found")

            master_flow, child_flow = row

            # Validate flow is in running state
            if master_flow.flow_status not in ["running", "initialized"]:
                raise ValueError(
                    f"Flow {flow_id} cannot be paused - current status: "
                    f"{master_flow.flow_status}"
                )

            # Pause master flow (lifecycle)
            master_flow.flow_status = "paused"

            # Update child flow operational status
            # Store current status before pausing
            runtime_state = child_flow.runtime_state or {}
            runtime_state["paused_at"] = datetime.utcnow().isoformat()
            runtime_state["status_before_pause"] = child_flow.status
            child_flow.runtime_state = runtime_state
            # Fixed per Qodo: Set child flow status to "paused" for consistency
            child_flow.status = "paused"

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Paused decommission flow via MFO: flow_id={flow_id}",
                flow_id=str(flow_id),
            )
        )

        # Return updated unified state
        return await get_decommission_status_via_mfo(
            flow_id, db, client_account_id, engagement_id
        )

    except ValueError:
        # Re-raise validation errors
        raise
    except SQLAlchemyError as e:
        logger.error(
            safe_log_format(
                "Database error pausing decommission flow: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to pause decommission flow: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise


async def cancel_decommission_flow(
    flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Cancel decommission flow (marks as failed/deleted in both master and child tables).

    Per ADR-012: Syncs both master flow (lifecycle) and child flow (operational state)
    to ensure consistent cancellation behavior.

    Args:
        flow_id: Decommission flow UUID
        client_account_id: Client account UUID for multi-tenant isolation
        engagement_id: Engagement UUID for multi-tenant isolation
        db: Database session

    Returns:
        Dict with updated unified state

    Raises:
        ValueError: If flow not found
        SQLAlchemyError: If database operations fail
    """
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
                .where(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    DecommissionFlow.client_account_id == client_account_id,
                    DecommissionFlow.engagement_id == engagement_id,
                )
            )

            result = await db.execute(query)
            row = result.first()

            if not row:
                raise ValueError(f"Decommission flow {flow_id} not found")

            master_flow, child_flow = row

            # Fixed per CodeRabbit: Capture status BEFORE modification
            runtime_state = child_flow.runtime_state or {}
            runtime_state["status_before_cancel"] = child_flow.status
            runtime_state["cancelled_at"] = datetime.utcnow().isoformat()

            # Cancel master flow (lifecycle) - mark as deleted
            master_flow.flow_status = "deleted"

            # Cancel child flow (operational state)
            child_flow.status = "failed"

            # Apply runtime_state changes
            child_flow.runtime_state = runtime_state

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Cancelled decommission flow via MFO: flow_id={flow_id}",
                flow_id=str(flow_id),
            )
        )

        # Fixed per CodeRabbit: Return unified state consistent with resume/pause
        return await get_decommission_status_via_mfo(
            flow_id, db, client_account_id, engagement_id
        )

    except ValueError:
        # Re-raise validation errors
        raise
    except SQLAlchemyError as e:
        logger.error(
            safe_log_format(
                "Database error cancelling decommission flow: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to cancel decommission flow: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
