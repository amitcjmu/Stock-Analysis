"""
Planning flow retrigger endpoint.

Retriggers wave planning with updated configuration parameters.
Allows users to regenerate wave plans with new migration start dates,
wave sizes, or duration limits.

Related ADRs:
- ADR-012: Two-Table Pattern (child flow operational state)
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

from .shared_utils import (
    parse_tenant_uuids,
    schedule_wave_planning_task,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class RetriggerWavePlanRequest(BaseModel):
    """Request model for retriggering wave planning with updated configuration."""

    migration_start_date: Optional[str] = Field(
        default=None,
        description="Updated migration start date in ISO format (YYYY-MM-DD)",
    )
    max_apps_per_wave: Optional[int] = Field(
        default=None, description="Maximum applications per wave"
    )
    wave_duration_limit_days: Optional[int] = Field(
        default=None, description="Wave duration in days"
    )


@router.post("/retrigger/{planning_flow_id}")
async def retrigger_wave_planning(
    planning_flow_id: str,
    request: RetriggerWavePlanRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Retrigger wave planning with updated configuration.

    Updates planning configuration (migration_start_date, max_apps_per_wave, etc.)
    and re-executes wave planning to regenerate the wave plan with new parameters.

    This endpoint is useful when:
    - User wants to change the migration start date
    - Resource constraints require adjusting max apps per wave
    - Wave duration needs to be modified

    The existing wave plan will be replaced with a newly generated plan.
    Wave planning runs in the background - poll status endpoint for completion.

    Path Parameters:
        planning_flow_id: Planning flow UUID

    Request Body:
    ```json
    {
        "migration_start_date": "2025-03-01",
        "max_apps_per_wave": 30,
        "wave_duration_limit_days": 60
    }
    ```

    Response:
    ```json
    {
        "status": "in_progress",
        "planning_flow_id": "uuid",
        "message": "Wave planning retriggered - poll status endpoint for completion"
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
        # Parse and validate UUIDs using shared utility
        planning_flow_uuid, client_account_uuid, engagement_uuid = parse_tenant_uuids(
            client_account_id, engagement_id, planning_flow_id
        )

        # Initialize repository
        repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Get existing planning flow
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {planning_flow_id} not found or access denied",
            )

        # Build updated planning config from existing + new values
        existing_config = planning_flow.planning_config or {}
        updated_config = existing_config.copy()

        # Per Qodo Bot: Use `is not None` for consistent optional param checks
        if request.migration_start_date is not None:
            updated_config["migration_start_date"] = request.migration_start_date
        if request.max_apps_per_wave is not None:
            updated_config["max_apps_per_wave"] = request.max_apps_per_wave
        if request.wave_duration_limit_days is not None:
            updated_config["wave_duration_limit_days"] = (
                request.wave_duration_limit_days
            )

        # Update planning flow config
        await repo.update_planning_flow(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            planning_config=updated_config,
        )

        # Reset phase status to indicate re-execution
        await repo.update_phase_status(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            current_phase="wave_planning",
            phase_status="in_progress",
        )

        await db.commit()

        # Launch background task with proper lifecycle management (Qodo Bot fix)
        schedule_wave_planning_task(
            planning_flow_id=planning_flow_uuid,
            context=context,
            planning_config=updated_config,
        )

        return sanitize_for_json(
            {
                "status": "in_progress",
                "planning_flow_id": str(planning_flow_uuid),
                "updated_config": updated_config,
                "message": (
                    "Wave planning retriggered with updated configuration. "
                    "Poll status endpoint for completion."
                ),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrigger wave planning: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrigger wave planning: {str(e)}",
        )
