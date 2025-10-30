"""
Planning flow update endpoint.

Updates wave plan and planning configuration (manual override of AI suggestions).
Supports incremental updates to wave plan data and planning configuration.

Related ADRs:
- ADR-012: Two-Table Pattern (child flow operational state)
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


class UpdateWavePlanRequest(BaseModel):
    """Request model for wave plan update."""

    planning_flow_id: str = Field(..., description="Planning flow UUID")
    wave_plan_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Wave plan data (waves, groups, assignments)"
    )
    planning_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Planning configuration updates"
    )
    ui_state: Optional[Dict[str, Any]] = Field(
        default=None, description="UI state updates"
    )


@router.put("/update-wave-plan")
async def update_wave_plan(
    request: UpdateWavePlanRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Update wave plan (manual override of AI suggestions).

    Allows users to modify AI-generated wave plans, update planning configuration,
    or save UI state. All updates are atomic and tenant-scoped.

    Request Body:
    ```json
    {
        "planning_flow_id": "uuid",
        "wave_plan_data": {
            "waves": [
                {
                    "wave_number": 1,
                    "name": "Wave 1",
                    "applications": ["app-uuid-1", "app-uuid-2"],
                    "start_date": "2025-11-01",
                    "end_date": "2025-12-31"
                }
            ],
            "groups": [...]
        },
        "planning_config": {
            "max_apps_per_wave": 50
        },
        "ui_state": {
            "selected_wave": 1
        }
    }
    ```

    Response:
    ```json
    {
        "status": "updated",
        "planning_flow_id": "uuid",
        "updated_fields": ["wave_plan_data", "planning_config"]
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
        # Parse planning flow ID and convert tenant IDs to UUIDs (per migration 115)
        try:
            planning_flow_uuid = UUID(request.planning_flow_id)
            client_account_uuid = (
                UUID(client_account_id)
                if isinstance(client_account_id, str)
                else client_account_id
            )
            engagement_uuid = (
                UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid UUID format: {str(e)}",
            )

        # Initialize repository with UUIDs
        repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Get planning flow (verify existence and tenant scoping)
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {request.planning_flow_id} not found or access denied",
            )

        # Build update dictionary (only include provided fields)
        update_data = {}
        updated_fields = []

        if request.wave_plan_data is not None:
            update_data["wave_plan_data"] = request.wave_plan_data
            updated_fields.append("wave_plan_data")

        if request.planning_config is not None:
            update_data["planning_config"] = request.planning_config
            updated_fields.append("planning_config")

        if request.ui_state is not None:
            update_data["ui_state"] = request.ui_state
            updated_fields.append("ui_state")

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided for update",
            )

        # Update planning flow (atomic transaction)
        async with db.begin():
            updated_flow = await repo.update_planning_flow(
                planning_flow_id=planning_flow_uuid,
                client_account_id=client_account_uuid,
                engagement_id=engagement_uuid,
                **update_data,
            )
            await db.flush()

        logger.info(
            f"Updated planning flow {request.planning_flow_id}: {updated_fields} "
            f"(client: {client_account_uuid}, engagement: {engagement_uuid})"
        )

        return sanitize_for_json(
            {
                "status": "updated",
                "planning_flow_id": str(updated_flow.planning_flow_id),
                "updated_fields": updated_fields,
                "current_phase": updated_flow.current_phase,
                "phase_status": updated_flow.phase_status,
                "message": "Planning flow updated successfully",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update wave plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update wave plan: {str(e)}",
        )
