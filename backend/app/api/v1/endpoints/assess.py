"""
Assessment API endpoints for 6R analysis, roadmap, and wave planning.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from app.core.context import get_current_context
from app.core.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/roadmap")
async def get_roadmap(
    db: AsyncSession = Depends(get_db), context=Depends(get_current_context)
) -> Dict[str, Any]:
    """Get migration roadmap with waves and phases."""
    # Return demo roadmap data
    current_date = datetime.now()

    roadmap_data = {
        "waves": [
            {
                "wave": "Wave 1",
                "phases": [
                    {
                        "name": "Discovery & Assessment",
                        "start": current_date.strftime("%Y-%m-%d"),
                        "end": (current_date + timedelta(days=14)).strftime("%Y-%m-%d"),
                        "status": "completed",
                    },
                    {
                        "name": "Planning & Design",
                        "start": (current_date + timedelta(days=15)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                        "status": "in-progress",
                    },
                    {
                        "name": "Migration Execution",
                        "start": (current_date + timedelta(days=31)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=60)).strftime("%Y-%m-%d"),
                        "status": "planned",
                    },
                    {
                        "name": "Testing & Validation",
                        "start": (current_date + timedelta(days=61)).strftime(
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
                        "name": "Discovery & Assessment",
                        "start": (current_date + timedelta(days=45)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=59)).strftime("%Y-%m-%d"),
                        "status": "planned",
                    },
                    {
                        "name": "Planning & Design",
                        "start": (current_date + timedelta(days=60)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=75)).strftime("%Y-%m-%d"),
                        "status": "planned",
                    },
                    {
                        "name": "Migration Execution",
                        "start": (current_date + timedelta(days=76)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": (current_date + timedelta(days=105)).strftime(
                            "%Y-%m-%d"
                        ),
                        "status": "planned",
                    },
                    {
                        "name": "Testing & Validation",
                        "start": (current_date + timedelta(days=106)).strftime(
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
        "totalApps": 125,
        "plannedApps": 75,
    }

    return roadmap_data


@router.put("/roadmap")
async def update_roadmap(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context=Depends(get_current_context),
) -> Dict[str, str]:
    """Update migration roadmap."""
    # In a real implementation, this would save to database
    return {"message": "Roadmap updated successfully"}
