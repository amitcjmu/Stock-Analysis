"""
Roadmap and timeline endpoints for migration planning.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/roadmap")
async def get_roadmap(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get migration roadmap with comprehensive timeline data.

    Consolidates timeline, phases, milestones, metrics, critical path, and schedule health.
    Replaces legacy /timeline endpoint. Retrieves data from project_timelines and
    timeline_phases tables with multi-tenant scoping.

    Returns:
        - phases: List of timeline phases with milestones and risks
        - metrics: Timeline summary metrics (duration, progress, delays)
        - critical_path: List of phase names on critical path
        - schedule_health: Overall health status with issues and recommendations
    """
    from app.repositories.planning_flow_repository import PlanningFlowRepository
    from app.models.planning import ProjectTimeline
    from sqlalchemy import select, and_
    from uuid import UUID

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    # Convert to UUIDs (per migration 115) - NEVER use integers for tenant IDs
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

    # Get timelines for engagement (directly query with tenant scoping)
    stmt = (
        select(ProjectTimeline)
        .where(
            and_(
                ProjectTimeline.client_account_id == client_account_id,
                ProjectTimeline.engagement_id == engagement_id,
            )
        )
        .order_by(ProjectTimeline.created_at.desc())
    )

    result = await db.execute(stmt)
    timelines = result.scalars().all()

    if not timelines:
        # Return empty state with complete structure for frontend compatibility
        return {
            "phases": [],
            "metrics": {
                "total_duration_weeks": 0,
                "completed_phases": 0,
                "total_phases": 0,
                "overall_progress": 0,
                "delayed_milestones": 0,
                "at_risk_milestones": 0,
            },
            "critical_path": [],
            "schedule_health": {
                "status": "Not Started",
                "issues": [],
                "recommendations": ["Create a project timeline to begin planning"],
            },
            "roadmap_status": "not_started",
        }

    latest_timeline = timelines[0]

    # Get phases for this timeline
    phases_data = await repository.get_phases_by_timeline(
        timeline_id=latest_timeline.id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Get milestones for this timeline
    milestones_data = await repository.get_milestones_by_timeline(
        timeline_id=latest_timeline.id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Calculate metrics
    total_phases = len(phases_data)
    completed_phases = sum(1 for p in phases_data if p.status == "completed")

    # Calculate duration in weeks
    if latest_timeline.overall_start_date and latest_timeline.overall_end_date:
        duration_delta = (
            latest_timeline.overall_end_date - latest_timeline.overall_start_date
        )
        total_duration_weeks = duration_delta.days // 7
    else:
        total_duration_weeks = 0

    # Calculate milestone statuses
    delayed_milestones = sum(1 for m in milestones_data if m.status == "delayed")
    at_risk_milestones = sum(1 for m in milestones_data if m.status == "at_risk")

    # Extract critical path from timeline data
    critical_path_data = latest_timeline.critical_path_data or {}
    critical_path = critical_path_data.get("phases", [])

    # Group milestones by phase
    milestones_by_phase = {}
    for milestone in milestones_data:
        phase_id = str(milestone.phase_id) if milestone.phase_id else "timeline"
        if phase_id not in milestones_by_phase:
            milestones_by_phase[phase_id] = []

        # Use actual_date if available, otherwise planned_date
        milestone_date = (
            milestone.actual_date if milestone.actual_date else milestone.planned_date
        )

        milestones_by_phase[phase_id].append(
            {
                "name": milestone.milestone_name,
                "date": milestone_date.isoformat() if milestone_date else None,
                "status": milestone.status,
                "description": milestone.description or "",
            }
        )

    # Build phases response with milestones and risks
    phases_response = []
    for phase in phases_data:
        phase_id = str(phase.id)
        phase_milestones = milestones_by_phase.get(phase_id, [])

        # Extract risks from blocking_issues
        risks = []
        if phase.blocking_issues:
            for issue in phase.blocking_issues:
                risks.append(
                    {
                        "description": issue.get("description", ""),
                        "impact": issue.get("impact", "Medium"),
                        "mitigation": issue.get("mitigation", ""),
                    }
                )

        phases_response.append(
            {
                "id": phase_id,
                "name": phase.phase_name,
                "start_date": (
                    phase.planned_start_date.isoformat()
                    if phase.planned_start_date
                    else None
                ),
                "end_date": (
                    phase.planned_end_date.isoformat()
                    if phase.planned_end_date
                    else None
                ),
                "status": phase.status.replace(
                    "_", " "
                ).title(),  # Convert to display format
                "progress": (
                    float(phase.progress_percentage) if phase.progress_percentage else 0
                ),
                "dependencies": [
                    str(pid) for pid in (phase.predecessor_phase_ids or [])
                ],
                "phase_number": phase.phase_number,  # Phase sequence number for ordering
                "wave_number": None,  # TODO: Map from wave_id when wave planning integrated
                "is_on_critical_path": phase.is_on_critical_path,  # Critical path flag from DB
                "milestones": phase_milestones,
                "risks": risks,
            }
        )

    # Determine schedule health
    ai_recommendations = latest_timeline.ai_recommendations or {}
    schedule_issues = ai_recommendations.get("issues", [])
    schedule_recommendations = ai_recommendations.get("recommendations", [])

    # Calculate health status
    if delayed_milestones > 0:
        health_status = "Delayed"
    elif at_risk_milestones > 2 or len(schedule_issues) > 3:
        health_status = "At Risk"
    else:
        health_status = "On Track"

    return {
        "phases": phases_response,
        "metrics": {
            "total_duration_weeks": total_duration_weeks,
            "completed_phases": completed_phases,
            "total_phases": total_phases,
            "overall_progress": (
                float(latest_timeline.progress_percentage)
                if latest_timeline.progress_percentage
                else 0
            ),
            "delayed_milestones": delayed_milestones,
            "at_risk_milestones": at_risk_milestones,
        },
        "critical_path": critical_path,
        "schedule_health": {
            "status": health_status,
            "issues": schedule_issues,
            "recommendations": schedule_recommendations,
        },
        "roadmap_status": "active",
    }


@router.put("/roadmap")
async def update_roadmap(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, str]:
    """Update roadmap data."""
    # In a real implementation, this would save to database
    return {"message": "Roadmap updated successfully"}


@router.get("/timeline")
async def get_timeline(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """
    DEPRECATED: Use /api/v1/plan/roadmap instead.

    This endpoint is maintained for backward compatibility but will be removed in a future version.
    It now forwards to the consolidated roadmap logic.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        "DEPRECATED: /api/v1/plan/timeline endpoint called. "
        "Please migrate to /api/v1/plan/roadmap. "
        f"Client: {context.client_account_id}, Engagement: {context.engagement_id}"
    )

    # Forward to consolidated roadmap endpoint
    return await get_roadmap(db=db, context=context)
