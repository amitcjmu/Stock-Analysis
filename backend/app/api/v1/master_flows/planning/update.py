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


async def _sync_waves_to_timeline(
    repo: PlanningFlowRepository,
    planning_flow_id: UUID,
    client_account_id: UUID,
    engagement_id: UUID,
    wave_plan_data: Dict[str, Any],
) -> None:
    """
    Synchronize wave plan data to timeline tables.

    Creates or updates ProjectTimeline and TimelinePhase records based on wave data.
    This ensures the Roadmap page can display wave planning information.

    Args:
        repo: PlanningFlowRepository instance
        planning_flow_id: Planning flow UUID
        client_account_id: Client account UUID
        engagement_id: Engagement UUID
        wave_plan_data: Wave plan data containing waves array
    """
    from datetime import datetime, timezone

    from sqlalchemy import delete

    from app.models.planning import TimelinePhase

    waves = wave_plan_data.get("waves", [])
    if not waves:
        logger.debug("No waves in wave_plan_data, skipping timeline sync")
        return

    # Get or create timeline for this planning flow
    timeline = await repo.get_timeline_by_planning_flow(
        planning_flow_id=planning_flow_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    if not timeline:
        # Create new timeline
        # Calculate overall start/end dates from waves
        start_dates = [
            datetime.fromisoformat(w["start_date"])
            for w in waves
            if w.get("start_date")
        ]
        end_dates = [
            datetime.fromisoformat(w["end_date"]) for w in waves if w.get("end_date")
        ]

        # Use UTC now for timezone-aware comparison
        now_utc = datetime.now(timezone.utc)
        overall_start = min(start_dates) if start_dates else now_utc
        overall_end = max(end_dates) if end_dates else now_utc

        timeline = await repo.create_timeline(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            planning_flow_id=planning_flow_id,
            timeline_name="Migration Timeline",
            overall_start_date=overall_start,
            overall_end_date=overall_end,
        )
        logger.info(
            f"Created timeline {timeline.id} for planning_flow {planning_flow_id}"
        )

    # Delete existing phases for this timeline to avoid duplicates
    # This is safe because phases are recreation from wave data
    delete_stmt = delete(TimelinePhase).where(TimelinePhase.timeline_id == timeline.id)
    await repo.db.execute(delete_stmt)
    logger.debug(f"Deleted existing phases for timeline {timeline.id}")

    # Map wave status to timeline phase status
    # Constraint: not_started, in_progress, on_hold, completed, cancelled
    # Wave statuses: Planned, In Progress, Completed, Blocked
    wave_to_phase_status = {
        "planned": "not_started",
        "Planned": "not_started",
        "in_progress": "in_progress",
        "In Progress": "in_progress",
        "completed": "completed",
        "Completed": "completed",
        "blocked": "on_hold",
        "Blocked": "on_hold",
    }

    # Sync waves to timeline phases
    for wave in waves:
        wave_number = wave.get("wave_number", 1)
        phase_name = wave.get("wave_name", f"Wave {wave_number}")
        start_date_str = wave.get("start_date")
        end_date_str = wave.get("end_date")
        wave_status = wave.get("status", "planned")
        # Map wave status to valid timeline phase status
        status = wave_to_phase_status.get(wave_status, "not_started")

        if not start_date_str or not end_date_str:
            logger.warning(
                f"Wave {wave_number} missing start/end dates, skipping phase creation"
            )
            continue

        # Create timeline phase for this wave
        await repo.create_timeline_phase(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            timeline_id=timeline.id,
            phase_number=wave_number,
            phase_name=phase_name,
            planned_start_date=datetime.fromisoformat(start_date_str),
            planned_end_date=datetime.fromisoformat(end_date_str),
            status=status,
        )
        logger.debug(f"Created timeline phase for wave {wave_number}: {phase_name}")

    logger.info(f"Synced {len(waves)} waves to timeline {timeline.id}")


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
                detail=f"Planning flow {request.planning_flow_id} not found",
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

        # Update planning flow (repository manages transaction atomically)
        updated_flow = await repo.update_planning_flow(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            **update_data,
        )

        # Sync wave plan to timeline tables if wave_plan_data was updated
        if request.wave_plan_data is not None:
            await _sync_waves_to_timeline(
                repo=repo,
                planning_flow_id=planning_flow_uuid,
                client_account_id=client_account_uuid,
                engagement_id=engagement_uuid,
                wave_plan_data=request.wave_plan_data,
            )

        await db.commit()

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
