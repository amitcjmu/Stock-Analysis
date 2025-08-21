"""
Plan API endpoints for migration planning, including roadmaps and wave planning.
"""

from datetime import datetime, timedelta
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


@router.get("/")
async def get_plan_overview(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get plan overview with high-level planning metrics."""
    current_date = datetime.now()

    overview_data = {
        "summary": {
            "totalApps": 83,
            "plannedApps": 45,
            "totalWaves": 3,
            "completedPhases": 2,
            "upcomingMilestones": 4,
        },
        "nextMilestone": {
            "name": "Wave 1 Migration Start",
            "date": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": "Begin migration activities for Wave 1 applications",
        },
        "recentActivity": [
            {
                "date": current_date.strftime("%Y-%m-%d"),
                "activity": "Wave planning completed",
                "description": "Finalized application grouping for all waves",
            },
            {
                "date": (current_date - timedelta(days=2)).strftime("%Y-%m-%d"),
                "activity": "Roadmap updated",
                "description": "Timeline adjustments based on resource availability",
            },
        ],
    }

    return overview_data


@router.get("/waveplanning")
async def get_wave_planning(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get wave planning data with waves and groups."""
    current_date = datetime.now()

    wave_planning_data = {
        "waves": [
            {
                "wave": "Wave 1",
                "startDate": current_date.strftime("%Y-%m-%d"),
                "targetDate": (current_date + timedelta(days=90)).strftime("%Y-%m-%d"),
                "groups": ["Finance Apps", "HR Systems", "Email & Collaboration"],
                "apps": 45,
                "status": "Scheduled",
            },
            {
                "wave": "Wave 2",
                "startDate": (current_date + timedelta(days=45)).strftime("%Y-%m-%d"),
                "targetDate": (current_date + timedelta(days=135)).strftime("%Y-%m-%d"),
                "groups": ["ERP Systems", "Supply Chain", "Customer Service"],
                "apps": 38,
                "status": "Planning",
            },
            {
                "wave": "Wave 3",
                "startDate": (current_date + timedelta(days=90)).strftime("%Y-%m-%d"),
                "targetDate": (current_date + timedelta(days=180)).strftime("%Y-%m-%d"),
                "groups": ["Legacy Systems", "Data Warehouses", "Analytics"],
                "apps": 42,
                "status": "Draft",
            },
        ],
        "summary": {"totalWaves": 3, "totalApps": 125, "totalGroups": 9},
    }

    return wave_planning_data


@router.put("/waveplanning")
async def update_wave_planning(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, str]:
    """Update wave planning data."""
    # In a real implementation, this would save to database
    return {"message": "Wave planning updated successfully"}


@router.get("/timeline")
async def get_timeline(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get migration timeline data with phases, milestones, and scheduling information."""
    current_date = datetime.now()

    timeline_data = {
        "phases": [
            {
                "id": "phase-1",
                "name": "Discovery & Assessment",
                "start_date": current_date.strftime("%Y-%m-%d"),
                "end_date": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                "status": "In Progress",
                "progress": 75,
                "dependencies": [],
                "milestones": [
                    {
                        "name": "Application Discovery Complete",
                        "date": (current_date + timedelta(days=14)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "Completed",
                        "description": "All applications identified and catalogued",
                    },
                    {
                        "name": "Dependency Analysis",
                        "date": (current_date + timedelta(days=25)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "In Progress",
                        "description": "Complete dependency mapping between applications",
                    },
                ],
                "risks": [
                    {
                        "description": "Legacy system discovery taking longer than expected",
                        "impact": "Medium",
                        "mitigation": "Allocate additional resources to discovery team",
                    }
                ],
            },
            {
                "id": "phase-2",
                "name": "Migration Planning",
                "start_date": (current_date + timedelta(days=20)).strftime("%Y-%m-%d"),
                "end_date": (current_date + timedelta(days=50)).strftime("%Y-%m-%d"),
                "status": "Not Started",
                "progress": 0,
                "dependencies": ["phase-1"],
                "milestones": [
                    {
                        "name": "Wave Planning Complete",
                        "date": (current_date + timedelta(days=35)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "Pending",
                        "description": "Applications grouped into migration waves",
                    },
                    {
                        "name": "Resource Planning",
                        "date": (current_date + timedelta(days=45)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "Pending",
                        "description": "Team assignments and resource allocation finalized",
                    },
                ],
                "risks": [
                    {
                        "description": "Resource availability constraints",
                        "impact": "High",
                        "mitigation": "Negotiate additional team members or extend timeline",
                    }
                ],
            },
            {
                "id": "phase-3",
                "name": "Wave 1 Migration",
                "start_date": (current_date + timedelta(days=45)).strftime("%Y-%m-%d"),
                "end_date": (current_date + timedelta(days=90)).strftime("%Y-%m-%d"),
                "status": "Not Started",
                "progress": 0,
                "dependencies": ["phase-2"],
                "milestones": [
                    {
                        "name": "Infrastructure Preparation",
                        "date": (current_date + timedelta(days=55)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "Pending",
                        "description": "Target cloud infrastructure ready for migration",
                    },
                    {
                        "name": "Pilot Migration Complete",
                        "date": (current_date + timedelta(days=70)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "Pending",
                        "description": "First batch of applications successfully migrated",
                    },
                    {
                        "name": "Wave 1 Go-Live",
                        "date": (current_date + timedelta(days=85)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "Pending",
                        "description": "All Wave 1 applications live in production",
                    },
                ],
                "risks": [
                    {
                        "description": "Data migration complexity higher than anticipated",
                        "impact": "High",
                        "mitigation": "Implement additional data validation checkpoints",
                    }
                ],
            },
        ],
        "metrics": {
            "total_duration_weeks": 13,
            "completed_phases": 0,
            "total_phases": 3,
            "overall_progress": 25,
            "delayed_milestones": 0,
            "at_risk_milestones": 2,
        },
        "critical_path": [
            "Discovery & Assessment",
            "Migration Planning",
            "Wave 1 Migration",
            "Wave 2 Migration",
            "Validation & Cutover",
        ],
        "schedule_health": {
            "status": "On Track",
            "issues": [
                "Legacy system documentation incomplete",
                "Pending stakeholder approval for cloud architecture",
            ],
            "recommendations": [
                "Schedule additional discovery sessions for undocumented systems",
                "Expedite architecture review process with stakeholders",
                "Consider parallel workstreams to reduce timeline impact",
            ],
        },
    }

    return timeline_data
