"""
Planning flow status retrieval endpoint.

Retrieves current status and progress of planning flows.
Returns operational state from child flow (planning_flows table).

Related ADRs:
- ADR-012: Flow Status Management Separation (Two-Table Pattern)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status/{planning_flow_id}")
async def get_planning_status(
    planning_flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Get current planning flow status and progress.

    Returns operational state from planning_flows table including:
    - Current phase and phase status
    - Wave plan data
    - Resource allocation data
    - Timeline data
    - Cost estimation data
    - UI state

    Response:
    ```json
    {
        "planning_flow_id": "uuid",
        "master_flow_id": "uuid",
        "current_phase": "wave_planning",
        "phase_status": "completed",
        "wave_plan_data": {...},
        "resource_allocation_data": {...},
        "timeline_data": {...},
        "cost_estimation_data": {...},
        "ui_state": {...},
        "created_at": "2025-10-29T12:00:00",
        "updated_at": "2025-10-29T12:30:00"
    }
    ```
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        # Parse planning flow ID
        try:
            planning_flow_uuid = UUID(planning_flow_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid planning flow UUID format"
            )

        # Initialize repository
        repo = PlanningFlowRepository(
            db=db,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id),
        )

        # Get planning flow (with tenant scoping verification)
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {planning_flow_id} not found or access denied",
            )

        logger.debug(
            f"Retrieved planning flow status: {planning_flow_id} "
            f"(client: {client_account_id}, engagement: {engagement_id})"
        )

        # Return complete planning flow state
        return sanitize_for_json(
            {
                "planning_flow_id": str(planning_flow.planning_flow_id),
                "master_flow_id": str(planning_flow.master_flow_id),
                "current_phase": planning_flow.current_phase,
                "phase_status": planning_flow.phase_status,
                "wave_plan_data": planning_flow.wave_plan_data,
                "resource_allocation_data": planning_flow.resource_allocation_data,
                "timeline_data": planning_flow.timeline_data,
                "cost_estimation_data": planning_flow.cost_estimation_data,
                "agent_execution_log": planning_flow.agent_execution_log,
                "ui_state": planning_flow.ui_state,
                "created_at": planning_flow.created_at.isoformat(),
                "updated_at": planning_flow.updated_at.isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve planning flow status: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve planning flow status: {str(e)}",
        )
