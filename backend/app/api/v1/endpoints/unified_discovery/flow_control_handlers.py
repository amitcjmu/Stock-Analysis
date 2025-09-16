"""
Flow Control Handlers for Unified Discovery

Handles flow control operations: pause, resume, delete, and retry.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.client_account import User
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.utils.flow_constants.flow_states import FlowStatus

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_flow_id(flow_id: str) -> None:
    """Validate that flow_id is a valid UUID format."""
    try:
        uuid.UUID(flow_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flow ID format: {flow_id}. Must be a valid UUID.",
        )


@router.post("/flows/{flow_id}/pause")
async def pause_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Pause a running discovery flow."""
    _validate_flow_id(flow_id)

    try:
        logger.info(safe_log_format("Pausing flow: {flow_id}", flow_id=flow_id))

        # Check if flow is archived before pausing
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Guard against deleted flows
        if flow.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot process deleted flow")

        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.pause_flow(flow_id)

        return {
            "success": True,
            "flow_id": flow_id,
            "status": "paused",
            "result": result,
        }

    except Exception as e:
        logger.error(safe_log_format("Failed to pause flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/resume")
async def resume_flow(
    flow_id: str,
    phase_input: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused discovery flow."""
    _validate_flow_id(flow_id)

    try:
        logger.info(safe_log_format("Resuming flow: {flow_id}", flow_id=flow_id))

        # Get the flow's current state
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Guard against deleted flows
        if flow.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot process deleted flow")

        if flow.status not in ["paused", "waiting_for_approval", "failed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Flow cannot be resumed from status: {flow.status}",
            )

        # Resume through orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.resume_flow(flow_id, phase_input or {})

        return {
            "success": True,
            "flow_id": flow_id,
            "status": "resumed",
            "current_phase": flow.current_phase,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to resume flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flows/{flow_id}")
async def delete_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Delete a discovery flow."""
    _validate_flow_id(flow_id)

    try:
        logger.info(safe_log_format("Deleting flow: {flow_id}", flow_id=flow_id))

        # First check if the flow exists and belongs to the current context
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Soft delete by updating status
        flow.status = FlowStatus.ARCHIVED.value
        flow.updated_at = datetime.now(timezone.utc)

        await db.commit()

        # Also update CrewAI Flow State if it exists
        master_stmt = (
            update(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                )
            )
            .values(
                flow_status=FlowStatus.ARCHIVED.value,
                updated_at=datetime.now(timezone.utc),
            )
        )

        await db.execute(master_stmt)
        await db.commit()

        return {
            "success": True,
            "flow_id": flow_id,
            "message": "Flow deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to delete flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/retry")
async def retry_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Retry a failed discovery flow phase."""
    _validate_flow_id(flow_id)

    try:
        logger.info(safe_log_format("Retrying flow: {flow_id}", flow_id=flow_id))

        # Get the flow's current state
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Guard against deleted flows
        if flow.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot process deleted flow")

        if flow.status not in ["failed", "error"]:
            raise HTTPException(
                status_code=400,
                detail=f"Flow cannot be retried from status: {flow.status}",
            )

        # Retry through orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.retry_phase(flow_id, flow.current_phase)

        return {
            "success": True,
            "flow_id": flow_id,
            "phase_retried": flow.current_phase,
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to retry flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
