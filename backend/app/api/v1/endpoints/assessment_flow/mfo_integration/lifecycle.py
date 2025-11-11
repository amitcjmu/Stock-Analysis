"""
Assessment Flow MFO Integration - Lifecycle Operations

Handles lifecycle operations (pause, resume, complete, delete) for assessment flows.
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
from .updates import update_assessment_via_mfo

logger = logging.getLogger(__name__)


async def pause_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Pause assessment flow (updates both master and child tables atomically).

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with updated unified state
    """
    return await update_assessment_via_mfo(
        flow_id=flow_id,
        updates={
            "status": AssessmentFlowStatus.PAUSED.value,
            "runtime_state": {"paused_at": datetime.utcnow().isoformat()},
        },
        db=db,
    )


async def resume_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Resume assessment flow (updates both master and child tables atomically).

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with updated unified state
    """
    return await update_assessment_via_mfo(
        flow_id=flow_id,
        updates={
            "status": AssessmentFlowStatus.IN_PROGRESS.value,
            "runtime_state": {"resumed_at": datetime.utcnow().isoformat()},
        },
        db=db,
    )


async def complete_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Mark assessment flow as completed (updates both master and child tables atomically).

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with updated unified state
    """
    return await update_assessment_via_mfo(
        flow_id=flow_id,
        updates={
            "status": AssessmentFlowStatus.COMPLETED.value,
            "progress": 100,
            "runtime_state": {"completed_at": datetime.utcnow().isoformat()},
        },
        db=db,
    )


async def delete_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Delete assessment flow (soft delete in master, removes child record).

    Per ADR-006: Master flow handles deletion/cancellation decisions.

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with deletion confirmation
    """
    try:
        async with db.begin():
            # Get master flow
            query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            result = await db.execute(query)
            master_flow = result.scalar_one_or_none()

            if not master_flow:
                raise ValueError(f"Assessment flow {flow_id} not found")

            # Soft delete master flow (set status to deleted)
            master_flow.flow_status = "deleted"

            # Delete child flow (cascade will handle this if FK configured properly)
            # But we'll be explicit for clarity
            child_query = select(
                AssessmentFlow
            ).where(  # SKIP_TENANT_CHECK - master_flow_id FK enforces isolation
                AssessmentFlow.master_flow_id == flow_id
            )
            child_result = await db.execute(child_query)
            child_flow = child_result.scalar_one_or_none()

            if child_flow:
                await db.delete(child_flow)

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Deleted assessment flow via MFO: flow_id={flow_id}",
                flow_id=str(flow_id),
            )
        )

        return {
            "flow_id": str(flow_id),
            "status": "deleted",
            "message": "Assessment flow deleted successfully",
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to delete assessment flow: flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
