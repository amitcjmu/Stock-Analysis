"""
Roadmap and timeline endpoints for migration planning.

ARCHITECTURE NOTE:
Timeline data is DERIVED from wave_plan_data in planning_flows table.
This ensures Timeline and Wave Planning pages show consistent data from single source of truth.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def _calculate_wave_progress(wave: Dict[str, Any]) -> float:
    """Calculate progress percentage based on wave status."""
    status = wave.get("status", "planned").lower()
    if status == "completed":
        return 100.0
    elif status in ("in_progress", "in-progress"):
        return 50.0
    elif status == "blocked":
        return 25.0
    return 0.0


def _map_wave_status_to_phase_status(status: str) -> str:
    """Map wave status to timeline phase status."""
    status_lower = status.lower() if status else "planned"
    mapping = {
        "completed": "Completed",
        "in_progress": "In Progress",
        "in-progress": "In Progress",
        "blocked": "Delayed",
        "planned": "Not Started",
    }
    return mapping.get(status_lower, "Not Started")


def _generate_wave_milestones(wave: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate milestones for a wave (start, go-live)."""
    milestones = []
    wave_name = wave.get("wave_name", f"Wave {wave.get('wave_number', 1)}")
    status = wave.get("status", "planned").lower()

    # Wave Start milestone
    if wave.get("start_date"):
        milestone_status = (
            "Completed"
            if status in ("completed", "in_progress", "in-progress")
            else "Pending"
        )
        milestones.append(
            {
                "name": f"{wave_name} Start",
                "date": wave.get("start_date"),
                "status": milestone_status,
                "description": f"Kick-off for {wave_name}",
            }
        )

    # Wave Go-Live milestone
    if wave.get("end_date"):
        milestone_status = "Completed" if status == "completed" else "Pending"
        if status == "blocked":
            milestone_status = "At Risk"
        milestones.append(
            {
                "name": f"{wave_name} Go-Live",
                "date": wave.get("end_date"),
                "status": milestone_status,
                "description": f"Production deployment for {wave_name}",
            }
        )

    return milestones


def _derive_phases_from_waves(waves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Derive timeline phases from wave_plan_data.waves.

    Each wave becomes a timeline phase with:
    - Dates from wave start_date/end_date
    - Milestones for start and go-live
    - Dependencies based on wave_number sequence
    """
    phases = []

    for i, wave in enumerate(waves):
        wave_number = wave.get("wave_number", i + 1)
        wave_id = wave.get("wave_id", f"wave-{wave_number}")

        # Calculate dependencies (previous wave must complete first)
        dependencies = []
        if i > 0:
            prev_wave = waves[i - 1]
            prev_id = prev_wave.get(
                "wave_id", f"wave-{prev_wave.get('wave_number', i)}"
            )
            dependencies.append(prev_id)

        # Generate milestones for this wave
        milestones = _generate_wave_milestones(wave)

        # Extract risks from wave risk_level
        risks = []
        risk_level = wave.get("risk_level", "low")
        if risk_level and risk_level.lower() in ("high", "medium"):
            risks.append(
                {
                    "description": f"Wave {wave_number} has {risk_level} risk level",
                    "impact": risk_level.title(),
                    "mitigation": "Monitor closely and have contingency plans ready",
                }
            )

        phase = {
            "id": wave_id,
            "name": wave.get("wave_name", f"Wave {wave_number}"),
            "start_date": wave.get("start_date"),
            "end_date": wave.get("end_date"),
            "status": _map_wave_status_to_phase_status(wave.get("status", "planned")),
            "progress": _calculate_wave_progress(wave),
            "dependencies": dependencies,
            "wave_number": wave_number,
            "phase_number": wave_number,
            "is_on_critical_path": i == 0
            or wave.get("risk_level", "").lower() == "high",
            "milestones": milestones,
            "risks": risks,
            # Include application count for context
            "application_count": wave.get(
                "application_count", len(wave.get("applications", []))
            ),
        }
        phases.append(phase)

    return phases


def _calculate_timeline_metrics(
    phases: List[Dict[str, Any]], waves: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate timeline metrics from derived phases."""
    if not phases:
        return {
            "total_duration_weeks": 0,
            "completed_phases": 0,
            "total_phases": 0,
            "overall_progress": 0,
            "delayed_milestones": 0,
            "at_risk_milestones": 0,
        }

    # Calculate duration
    start_dates = [p["start_date"] for p in phases if p.get("start_date")]
    end_dates = [p["end_date"] for p in phases if p.get("end_date")]

    total_duration_weeks = 0
    if start_dates and end_dates:
        try:
            earliest_start = min(datetime.fromisoformat(d) for d in start_dates)
            latest_end = max(datetime.fromisoformat(d) for d in end_dates)
            total_duration_weeks = (latest_end - earliest_start).days // 7
        except (ValueError, TypeError):
            pass

    # Count phases by status
    completed_phases = sum(1 for p in phases if p["status"] == "Completed")
    total_phases = len(phases)

    # Calculate overall progress
    if total_phases > 0:
        overall_progress = sum(p["progress"] for p in phases) / total_phases
    else:
        overall_progress = 0

    # Count milestone statuses
    all_milestones = []
    for phase in phases:
        all_milestones.extend(phase.get("milestones", []))

    delayed_milestones = sum(1 for m in all_milestones if m.get("status") == "At Risk")
    at_risk_milestones = delayed_milestones  # Same for derived data

    return {
        "total_duration_weeks": total_duration_weeks,
        "completed_phases": completed_phases,
        "total_phases": total_phases,
        "overall_progress": round(overall_progress, 1),
        "delayed_milestones": delayed_milestones,
        "at_risk_milestones": at_risk_milestones,
    }


def _identify_critical_path(phases: List[Dict[str, Any]]) -> List[str]:
    """Identify critical path phases (sequential dependent phases)."""
    return [p["name"] for p in phases if p.get("is_on_critical_path")]


def _calculate_schedule_health(
    phases: List[Dict[str, Any]], metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate schedule health status, issues, and recommendations."""
    issues = []
    recommendations = []

    # Check for blocked/delayed phases
    blocked_phases = [p for p in phases if p["status"] == "Delayed"]
    if blocked_phases:
        issues.append(f"{len(blocked_phases)} wave(s) are blocked or delayed")
        recommendations.append("Address blocking issues to prevent schedule slip")

    # Check for at-risk milestones
    if metrics["at_risk_milestones"] > 0:
        issues.append(f"{metrics['at_risk_milestones']} milestone(s) at risk")
        recommendations.append("Review at-risk milestones and assign mitigation owners")

    # Check for low progress
    if metrics["total_phases"] > 0 and metrics["overall_progress"] < 20:
        recommendations.append("Consider accelerating initial phases to build momentum")

    # Determine status
    if len(blocked_phases) > 0:
        status = "Delayed"
    elif metrics["at_risk_milestones"] > 2 or len(issues) > 2:
        status = "At Risk"
    elif metrics["total_phases"] == 0:
        status = "Not Started"
    else:
        status = "On Track"

    if not recommendations:
        recommendations.append("Continue monitoring progress against milestones")

    return {
        "status": status,
        "issues": issues,
        "recommendations": recommendations,
    }


@router.get("/roadmap")
async def get_roadmap(
    planning_flow_id: Optional[str] = Query(
        None, description="Planning flow ID to derive timeline from wave data"
    ),
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, Any]:
    """
    Get migration roadmap with timeline data DERIVED from wave_plan_data.

    Now derives timeline phases from planning_flows.wave_plan_data to ensure
    consistency between Timeline and Wave Planning pages.

    Args:
        planning_flow_id: Optional planning flow UUID to fetch specific wave data

    Returns:
        - phases: Timeline phases derived from waves with milestones and risks
        - metrics: Timeline summary metrics (duration, progress, delays)
        - critical_path: List of phase names on critical path
        - schedule_health: Overall health status with issues and recommendations
    """
    from app.models.planning import PlanningFlow
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

    # Build query for planning flow with wave data
    conditions = [
        PlanningFlow.client_account_id == client_account_uuid,
        PlanningFlow.engagement_id == engagement_uuid,
    ]

    # If planning_flow_id provided, filter by it
    if planning_flow_id:
        try:
            planning_flow_uuid = UUID(planning_flow_id)
            conditions.append(PlanningFlow.planning_flow_id == planning_flow_uuid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid planning_flow_id format: {planning_flow_id}")

    stmt = (
        select(PlanningFlow)
        .where(and_(*conditions))
        .order_by(PlanningFlow.created_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    planning_flow = result.scalar_one_or_none()

    # Extract wave_plan_data
    wave_plan_data = {}
    if planning_flow:
        wave_plan_data = planning_flow.wave_plan_data or {}

    waves = wave_plan_data.get("waves", [])

    if not waves:
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
                "recommendations": [
                    "Complete wave planning to generate timeline phases"
                ],
            },
            "roadmap_status": "not_started",
        }

    # Derive timeline phases from wave data
    phases = _derive_phases_from_waves(waves)

    # Calculate metrics
    metrics = _calculate_timeline_metrics(phases, waves)

    # Identify critical path
    critical_path = _identify_critical_path(phases)

    # Calculate schedule health
    schedule_health = _calculate_schedule_health(phases, metrics)

    logger.info(
        f"Timeline derived from wave_plan_data: {len(phases)} phases, "
        f"{metrics['total_duration_weeks']} weeks duration"
    )

    return {
        "phases": phases,
        "metrics": metrics,
        "critical_path": critical_path,
        "schedule_health": schedule_health,
        "roadmap_status": "active" if phases else "not_started",
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
    # Log deprecation without exposing tenant identifiers (security: redact PII)
    logger.warning(
        "DEPRECATED: /api/v1/plan/timeline endpoint called. "
        "Please migrate to /api/v1/plan/roadmap."
    )

    # Forward to consolidated roadmap endpoint
    return await get_roadmap(db=db, context=context)
