"""
Wave Planning Service - Wave Logic Module

Contains fallback wave planning logic and application data fetching.
This module provides the mathematical wave grouping algorithm when
the CrewAI agent is unavailable.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def fetch_application_details(
    planning_flow: Any,
    db: AsyncSession,
    client_account_id: UUID = None,
    engagement_id: UUID = None,
) -> List[Dict[str, Any]]:
    """
    Fetch detailed application metadata for selected applications.

    Queries assets table for real app names and joins with sixr_decisions
    for 6R assessment data when available.

    Args:
        planning_flow: Planning flow object with selected_applications
        db: Database session for querying assets and 6R decisions
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for tenant scoping

    Returns:
        List of application metadata dictionaries with real names
    """
    from app.models.asset import Asset
    from app.models.assessment_flow.analysis_models import SixRDecision

    selected_apps = planning_flow.selected_applications or []

    if not selected_apps:
        logger.warning("No selected applications in planning flow")
        return []

    # Convert to UUIDs if strings
    app_uuids = [
        UUID(str(app_id)) if isinstance(app_id, str) else app_id
        for app_id in selected_apps
    ]

    # Query assets with optional 6R decisions
    try:
        # First fetch all assets with tenant scoping
        asset_stmt = select(Asset).where(
            Asset.id.in_(app_uuids),
            Asset.client_account_id == client_account_id,
            Asset.engagement_id == engagement_id,
        )
        asset_result = await db.execute(asset_stmt)
        assets = {asset.id: asset for asset in asset_result.scalars().all()}

        # Then fetch any 6R decisions for these apps
        sixr_stmt = select(SixRDecision).where(
            SixRDecision.application_id.in_(app_uuids)
        )
        sixr_result = await db.execute(sixr_stmt)
        sixr_decisions = {
            decision.application_id: decision
            for decision in sixr_result.scalars().all()
        }

        logger.info(
            f"Fetched {len(assets)} assets and {len(sixr_decisions)} 6R decisions"
        )

        applications = []
        for app_id in app_uuids:
            asset = assets.get(app_id)
            sixr = sixr_decisions.get(app_id)

            if asset:
                app_data = {
                    "id": str(app_id),
                    "name": asset.name or f"Asset {str(app_id)[:8]}",
                    "description": asset.description or "",
                    "complexity": "medium",  # Default
                    "business_criticality": "medium",  # Default
                    "migration_strategy": "rehost",  # Default
                }

                # Enrich with 6R data if available
                if sixr:
                    app_data["migration_strategy"] = sixr.sixr_strategy or "rehost"
                    app_data["confidence_score"] = sixr.confidence_score
                    app_data["estimated_effort"] = sixr.estimated_effort
                    app_data["decision_rationale"] = sixr.decision_rationale

                applications.append(app_data)
            else:
                # Asset not found - use fallback
                logger.warning(f"Asset not found for ID: {app_id}")
                applications.append(
                    {
                        "id": str(app_id),
                        "name": f"Unknown App {str(app_id)[:8]}",
                        "complexity": "medium",
                        "business_criticality": "medium",
                        "migration_strategy": "rehost",
                    }
                )

        return applications

    except Exception as e:
        logger.error(f"Error fetching application details: {e}", exc_info=True)
        # Fall back to basic structure
        return [
            {
                "id": str(app_id),
                "name": f"App {str(app_id)[:8]}",
                "complexity": "medium",
                "business_criticality": "medium",
                "migration_strategy": "rehost",
            }
            for app_id in app_uuids
        ]


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
        applications: List of application metadata with real names
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
        start_idx = (wave_num - 1) * max_apps_per_wave
        end_idx = min(start_idx + max_apps_per_wave, selected_app_count)
        wave_apps = applications[start_idx:end_idx]
        apps_in_wave = len(wave_apps)

        wave_start = start_date + timedelta(days=(wave_num - 1) * wave_duration_days)
        wave_end = wave_start + timedelta(days=wave_duration_days)

        # Determine wave name based on position
        if wave_num == 1:
            wave_name = f"Wave {wave_num} - Initial Migration"
        elif wave_num == wave_count:
            wave_name = f"Wave {wave_num} - Final Migration"
        else:
            wave_name = f"Wave {wave_num} - Secondary Migration"

        # Build application list with real names and metadata
        wave_applications = []
        for app in wave_apps:
            wave_applications.append(
                {
                    "application_id": app.get("id", ""),
                    "application_name": app.get("name", "Unknown App"),
                    "rationale": f"Assigned to wave {wave_num} for migration",
                    "criticality": app.get("business_criticality", "medium"),
                    "complexity": app.get("complexity", "medium"),
                    "migration_strategy": app.get("migration_strategy", "rehost"),
                    "dependency_depth": 0,
                }
            )

        # Compute predominant strategy from apps in this wave
        strategy_counts: Dict[str, int] = {}
        for app in wave_apps:
            strategy = app.get("migration_strategy", "rehost").lower()
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        # Use most common strategy as group default
        predominant_strategy = (
            max(strategy_counts.keys(), key=lambda s: strategy_counts[s])
            if strategy_counts
            else "rehost"
        )

        wave = {
            "wave_id": f"wave_{wave_num}",
            "wave_number": wave_num,
            "wave_name": wave_name,
            "application_count": apps_in_wave,
            "applications": wave_applications,  # Include actual apps with real names
            "start_date": wave_start.isoformat(),
            "end_date": wave_end.isoformat(),
            "duration_days": wave_duration_days,
            "status": "planned",
            "description": f"{wave_name.split(' - ')[1]} containing {apps_in_wave} applications",
            "risk_level": "medium",
            "groups": [
                {
                    "group_id": f"wave_{wave_num}_group_1",
                    "group_name": f"{wave_name.split(' - ')[1]} Group",
                    "application_count": apps_in_wave,
                    "migration_strategy": predominant_strategy,
                    "parallel_execution": True,
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
