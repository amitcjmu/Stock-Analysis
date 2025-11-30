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

    Selection Priority (to ensure best user experience):
    1. Most recent completed flow with wave data
    2. Most recent flow with any wave data (regardless of status)
    3. Most recent flow (for in-progress planning)
    """
    from sqlalchemy import select

    from app.models.planning import PlanningFlow

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

    if not client_account_uuid or not engagement_uuid:
        return {
            "waves": [],
            "groups": [],
            "planning_status": "not_started",
            "summary": {"total_waves": 0, "total_apps": 0, "total_groups": 0},
        }

    # Query directly with proper ordering (created_at DESC) instead of using get_all()
    # which doesn't guarantee ordering
    stmt = (
        select(PlanningFlow)
        .where(
            PlanningFlow.client_account_id == client_account_uuid,
            PlanningFlow.engagement_id == engagement_uuid,
        )
        .order_by(PlanningFlow.created_at.desc())
    )
    result = await db.execute(stmt)
    planning_flows = result.scalars().all()

    if not planning_flows:
        # Return empty state (no error - planning not started yet)
        return {
            "waves": [],
            "groups": [],
            "planning_status": "not_started",
            "summary": {"total_waves": 0, "total_apps": 0, "total_groups": 0},
        }

    # Selection priority:
    # 1. Most recent completed flow with wave data
    # 2. Most recent flow with any wave data
    # 3. Most recent flow overall
    best_flow = None

    # First pass: find completed flow with wave data
    for flow in planning_flows:
        wave_data = flow.wave_plan_data or {}
        waves = wave_data.get("waves", [])
        if flow.phase_status == "completed" and waves:
            best_flow = flow
            break

    # Second pass: find any flow with wave data
    if not best_flow:
        for flow in planning_flows:
            wave_data = flow.wave_plan_data or {}
            waves = wave_data.get("waves", [])
            if waves:
                best_flow = flow
                break

    # Fallback: use most recent flow
    if not best_flow:
        best_flow = planning_flows[0]

    wave_data = best_flow.wave_plan_data or {}
    return {
        "waves": wave_data.get("waves", []),
        "groups": wave_data.get("groups", []),
        "planning_status": best_flow.current_phase,
        "phase_status": best_flow.phase_status,
        "summary": wave_data.get("summary", {}),
        "planning_flow_id": str(best_flow.planning_flow_id),
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


@router.get("/flows")
async def list_planning_flows(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """
    List all planning flows for the current engagement.

    Returns a list of planning flow summaries for the "Available Planning Flows" UI.
    Results are ordered by created_at DESC (most recent first).
    """
    from typing import List

    from sqlalchemy import select

    from app.models.planning import PlanningFlow

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    # Convert to UUIDs (per migration 115)
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

    if not client_account_uuid or not engagement_uuid:
        return {"flows": [], "total": 0}

    # Query with proper ordering
    stmt = (
        select(PlanningFlow)
        .where(
            PlanningFlow.client_account_id == client_account_uuid,
            PlanningFlow.engagement_id == engagement_uuid,
        )
        .order_by(PlanningFlow.created_at.desc())
    )
    result = await db.execute(stmt)
    planning_flows = result.scalars().all()

    # Build flow summaries
    flow_summaries: List[Dict[str, Any]] = []
    for flow in planning_flows:
        wave_data = flow.wave_plan_data or {}
        waves = wave_data.get("waves", [])
        total_apps = sum(w.get("application_count", 0) for w in waves)

        flow_summaries.append(
            {
                "planning_flow_id": str(flow.planning_flow_id),
                "current_phase": flow.current_phase,
                "phase_status": flow.phase_status,
                "wave_count": len(waves),
                "application_count": total_apps,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
            }
        )

    return {"flows": flow_summaries, "total": len(flow_summaries)}


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
