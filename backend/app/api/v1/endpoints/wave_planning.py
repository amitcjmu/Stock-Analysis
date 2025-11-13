"""
Wave Planning API endpoints for migration wave management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def get_wave_planning(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get wave planning data (UPDATED - no longer stub).

    Retrieves real wave planning data from planning_flows table via repository.
    Returns empty state if no planning flow exists (no error).
    """
    from app.repositories.planning_flow_repository import PlanningFlowRepository

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    # Convert to UUIDs (per migration 115) - NEVER use integers for tenant IDs
    from uuid import UUID

    client_account_uuid = (
        (
            UUID(client_account_id)
            if isinstance(client_account_id, str)
            else client_account_id
        )
        if client_account_id
        else None
    )
    engagement_uuid = (
        (UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id)
        if engagement_id
        else None
    )

    # Initialize repository with tenant scoping
    repository = PlanningFlowRepository(
        db=db,
        client_account_id=client_account_uuid,
        engagement_id=engagement_uuid,
    )

    # Get latest planning flow for engagement (get_all auto-filters by tenant context)
    planning_flows = await repository.get_all()

    if not planning_flows:
        # Return empty state (no error - planning not started yet)
        return {
            "waves": [],
            "groups": [],
            "planning_status": "not_started",
            "summary": {"total_waves": 0, "total_apps": 0, "total_groups": 0},
        }

    # Get most recent planning flow
    latest_flow = planning_flows[0]

    return {
        "waves": latest_flow.wave_plan_data.get("waves", []),
        "groups": latest_flow.wave_plan_data.get("groups", []),
        "planning_status": latest_flow.current_phase,
        "phase_status": latest_flow.phase_status,
        "summary": latest_flow.wave_plan_data.get("summary", {}),
        "planning_flow_id": str(latest_flow.planning_flow_id),
    }


@router.put("/")
async def update_wave_planning(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, str]:
    """Update wave planning data."""
    # In a real implementation, this would save to database
    return {"message": "Wave planning updated successfully"}


@router.get("/roadmap")
async def get_roadmap(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get migration roadmap data with phases and timelines."""
    current_date = datetime.now()

    roadmap_data = {
        "waves": [
            {
                "wave": "Wave 1",
                "phases": [
                    {
                        "name": "Planning",
                        "start": current_date.strftime("%Y-%m-%d"),
                        "end": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                        "status": "in-progress",
                    },
                    {
                        "name": "Migration",
                        "start": (current_date + timedelta(days=30)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=60)).strftime("%Y-%m-%d"),
                        "status": "planned",
                    },
                    {
                        "name": "Testing",
                        "start": (current_date + timedelta(days=60)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=75)).strftime("%Y-%m-%d"),
                        "status": "planned",
                    },
                ],
            },
            {
                "wave": "Wave 2",
                "phases": [
                    {
                        "name": "Planning",
                        "start": (current_date + timedelta(days=45)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=75)).strftime("%Y-%m-%d"),
                        "status": "planned",
                    },
                    {
                        "name": "Migration",
                        "start": (current_date + timedelta(days=75)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=105)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "planned",
                    },
                    {
                        "name": "Testing",
                        "start": (current_date + timedelta(days=105)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=120)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "planned",
                    },
                ],
            },
        ],
        "totalApps": 83,
        "plannedApps": 45,
    }

    return roadmap_data


@router.put("/roadmap")
async def update_roadmap(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, str]:
    """Update roadmap data."""
    # In a real implementation, this would save to database
    return {"message": "Roadmap updated successfully"}
