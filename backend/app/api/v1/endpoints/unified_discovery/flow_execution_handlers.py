"""
Flow Execution Handlers for Unified Discovery

Handles flow execution and phase management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery.flow_execution_service import execute_flow_phase

logger = logging.getLogger(__name__)

router = APIRouter()


def _determine_next_phase(discovery_flow: DiscoveryFlow) -> str:
    """
    Determine the next phase to execute based on the current flow state.

    This is a simplified phase determination - in production, this logic
    would be more sophisticated and potentially moved to a service.
    """
    current_phase = discovery_flow.current_phase or "initialization"

    phase_sequence = [
        "initialization",
        "data_collection",
        "analysis",
        "dependency_mapping",
        "recommendations",
        "completed",
    ]

    try:
        current_index = phase_sequence.index(current_phase)
        if current_index < len(phase_sequence) - 1:
            return phase_sequence[current_index + 1]
    except ValueError:
        # Current phase not in sequence, start from beginning
        return "data_collection"

    return None  # Flow is completed


@router.post("/flows/{flow_id}/execute")
async def execute_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Execute the next phase of a discovery flow."""
    try:
        # Query the flow with proper tenant scoping
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        discovery_flow = result.scalar_one_or_none()
        if not discovery_flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")

        # Determine the next phase to execute
        next_phase = _determine_next_phase(discovery_flow)

        if not next_phase:
            return {
                "success": True,
                "message": "Flow execution completed - no more phases to execute",
                "status": "completed",
            }

        # Execute the phase with correct signature
        result = await execute_flow_phase(flow_id, discovery_flow, context, db)

        logger.info(
            safe_log_format(
                "Flow phase executed: flow_id={flow_id}, phase={phase}, success={success}",
                flow_id=mask_id(str(flow_id)),
                phase=next_phase,
                success=result.get("success", False),
            )
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Flow execution failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
