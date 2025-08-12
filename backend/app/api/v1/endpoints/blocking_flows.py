"""
Simple Blocking Flows Endpoint

Lightweight endpoint to check for flows blocking data import.
Replaces the over-engineered flow recovery system.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.logging import get_logger
from app.services.flow_orchestration.simple_blocking_check import SimpleBlockingCheck

logger = get_logger(__name__)
router = APIRouter()


class BlockingFlow(BaseModel):
    """Simple blocking flow info"""

    flow_id: str
    phase: str
    status: str
    progress: float
    is_blocking: bool
    reason: str


class BlockingFlowsResponse(BaseModel):
    """Response with blocking flows"""

    blocking_flows: List[BlockingFlow]
    count: int
    can_import: bool


@router.get("/check", response_model=BlockingFlowsResponse)
async def check_blocking_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Check for flows blocking data import.

    Only returns flows in early phases where asset collection is incomplete.
    Flows in dependency_analysis or later are NOT blocking.
    """
    checker = SimpleBlockingCheck(db, context)

    blocking_flows = await checker.get_blocking_flows()
    can_import = await checker.can_import_data()

    return BlockingFlowsResponse(
        blocking_flows=[
            BlockingFlow(
                flow_id=flow["flow_id"],
                phase=flow["phase"],
                status=flow["status"],
                progress=flow.get("progress", 0.0),
                is_blocking=flow.get("is_blocking", True),
                reason=flow.get("reason", "Flow incomplete"),
            )
            for flow in blocking_flows
        ],
        count=len(blocking_flows),
        can_import=can_import,
    )


@router.delete("/{flow_id}")
async def cancel_blocking_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Cancel a blocking flow.

    Simple cancellation - just marks the flow as cancelled.
    """
    checker = SimpleBlockingCheck(db, context)

    success = await checker.mark_flow_cancelled(flow_id)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to cancel flow {flow_id}")

    return {"success": True, "message": f"Flow {flow_id} cancelled successfully"}
