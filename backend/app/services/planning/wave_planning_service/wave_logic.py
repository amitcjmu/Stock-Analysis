"""
Wave Planning Service - Wave Logic Module

Contains fallback wave planning logic and application data fetching.
This module provides the mathematical wave grouping algorithm when
the CrewAI agent is unavailable.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def fetch_application_details(planning_flow: Any) -> List[Dict[str, Any]]:
    """
    Fetch detailed application metadata for selected applications.

    Args:
        planning_flow: Planning flow object with selected_applications

    Returns:
        List of application metadata dictionaries

    TODO: Query assessment_flows table for real application details
    """
    # For now, return basic structure from selected_applications
    selected_apps = planning_flow.selected_applications or []

    applications = []
    for app_id in selected_apps:
        # In production, query Asset table and join with assessment data
        applications.append(
            {
                "id": str(app_id),
                "name": f"Application {app_id}",
                "complexity": "medium",  # From assessment
                "business_criticality": "medium",  # From assessment
                "migration_strategy": "rehost",  # From assessment 6R decision
            }
        )

    return applications


async def fetch_application_dependencies(planning_flow: Any) -> List[Dict[str, Any]]:
    """
    Fetch application dependencies for dependency graph analysis.

    Args:
        planning_flow: Planning flow object

    Returns:
        List of application dependency relationships

    TODO: Query dependencies table
    """
    # For now, return empty list (no dependencies)
    return []


def generate_fallback_wave_plan(
    applications: List[Dict[str, Any]], config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a simple wave plan as fallback when CrewAI agent fails.

    This is the original simple math-based implementation that divides
    applications into waves based on max_apps_per_wave configuration.

    Args:
        applications: List of application metadata
        config: Wave planning configuration with:
            - max_apps_per_wave: Maximum applications per wave (default: 50)
            - wave_duration_limit_days: Duration per wave in days (default: 90)

    Returns:
        Wave plan data structure with waves, groups, and summary
    """
    selected_app_count = len(applications)
    max_apps_per_wave = config.get("max_apps_per_wave", 50)
    wave_duration_days = config.get("wave_duration_limit_days", 90)

    # Calculate number of waves needed
    wave_count = max(
        1, (selected_app_count + max_apps_per_wave - 1) // max_apps_per_wave
    )

    waves = []
    start_date = datetime.now(timezone.utc)

    for wave_num in range(1, wave_count + 1):
        # Calculate applications for this wave
        remaining_apps = selected_app_count - (wave_num - 1) * max_apps_per_wave
        apps_in_wave = min(max_apps_per_wave, remaining_apps)

        wave_start = start_date + timedelta(days=(wave_num - 1) * wave_duration_days)
        wave_end = wave_start + timedelta(days=wave_duration_days)

        wave = {
            "wave_id": f"wave_{wave_num}",
            "wave_number": wave_num,
            "wave_name": f"Wave {wave_num}",
            "application_count": apps_in_wave,
            "start_date": wave_start.isoformat(),
            "end_date": wave_end.isoformat(),
            "duration_days": wave_duration_days,
            "status": "planned",
            "description": f"Migration wave {wave_num} with {apps_in_wave} applications",
            "groups": [
                {
                    "group_id": f"wave_{wave_num}_group_1",
                    "group_name": f"Wave {wave_num} - Primary Group",
                    "application_count": apps_in_wave,
                    "migration_strategy": "lift_and_shift",
                }
            ],
        }
        waves.append(wave)

    # Generate summary
    summary = {
        "total_waves": wave_count,
        "total_apps": selected_app_count,
        "total_groups": wave_count,
        "estimated_duration_days": wave_count * wave_duration_days,
        "planning_date": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "max_apps_per_wave": max_apps_per_wave,
            "wave_duration_days": wave_duration_days,
        },
    }

    return {
        "waves": waves,
        "groups": [group for wave in waves for group in wave["groups"]],
        "summary": summary,
        "metadata": {
            "generated_by": "fallback_wave_planning",
            "version": "1.0.0",
            "generation_method": "simple_grouping",
        },
    }
