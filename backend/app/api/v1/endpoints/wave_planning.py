"""
Wave Planning API endpoints for migration wave management.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_current_context
from app.core.database import get_db

router = APIRouter()


@router.get("/")
async def get_wave_planning(
    db: AsyncSession = Depends(get_db),
    context = Depends(get_current_context)
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
                "status": "Scheduled"
            },
            {
                "wave": "Wave 2",
                "startDate": (current_date + timedelta(days=45)).strftime("%Y-%m-%d"),
                "targetDate": (current_date + timedelta(days=135)).strftime("%Y-%m-%d"),
                "groups": ["ERP Systems", "Supply Chain", "Customer Service"],
                "apps": 38,
                "status": "Planning"
            },
            {
                "wave": "Wave 3",
                "startDate": (current_date + timedelta(days=90)).strftime("%Y-%m-%d"),
                "targetDate": (current_date + timedelta(days=180)).strftime("%Y-%m-%d"),
                "groups": ["Legacy Systems", "Data Warehouses", "Analytics"],
                "apps": 42,
                "status": "Draft"
            }
        ],
        "summary": {
            "totalWaves": 3,
            "totalApps": 125,
            "totalGroups": 9
        }
    }
    
    return wave_planning_data


@router.put("/")
async def update_wave_planning(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context = Depends(get_current_context)
) -> Dict[str, str]:
    """Update wave planning data."""
    # In a real implementation, this would save to database
    return {"message": "Wave planning updated successfully"}