"""
Wave Planning Service - Wave Logic Module

Contains fallback wave planning logic and application data fetching.
This module provides the mathematical wave grouping algorithm when
the CrewAI agent is unavailable.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
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

    Data sources (in priority order):
    1. assessment_flows.phase_results['recommendation_generation'] - Primary 6R source
    2. assets.six_r_strategy - 6R strategy stored directly on asset
    3. Default fallback

    NOTE: Legacy SixRDecision table is NOT used per new architecture where
    6R decisions are stored in phase_results JSONB.

    Args:
        planning_flow: Planning flow object with selected_applications
        db: Database session for querying assets and assessment flows
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for tenant scoping

    Returns:
        List of application metadata dictionaries with real names and 6R strategies
    """
    from app.models.asset import Asset

    selected_apps = planning_flow.selected_applications or []

    if not selected_apps:
        logger.warning("No selected applications in planning flow")
        return []

    # Convert to UUIDs if strings
    app_uuids = [
        UUID(str(app_id)) if isinstance(app_id, str) else app_id
        for app_id in selected_apps
    ]

    try:
        # Fetch all assets with tenant scoping (includes six_r_strategy column)
        asset_stmt = select(Asset).where(
            Asset.id.in_(app_uuids),
            Asset.client_account_id == client_account_id,
            Asset.engagement_id == engagement_id,
        )
        asset_result = await db.execute(asset_stmt)
        assets = {asset.id: asset for asset in asset_result.scalars().all()}

        # Fetch 6R decisions from assessment_flows.phase_results (PRIMARY SOURCE)
        sixr_from_assessment = await _fetch_sixr_from_assessment(
            db, client_account_id, engagement_id
        )

        logger.info(f"Fetched {len(assets)} assets for wave planning")

        # Build application list
        applications = _build_applications_list(app_uuids, assets, sixr_from_assessment)

        # Log strategy distribution for debugging
        _log_strategy_distribution(applications)

        return applications

    except Exception as e:
        logger.error(f"Error fetching application details: {e}", exc_info=True)
        # Fall back to basic structure
        return _build_fallback_applications(app_uuids)


async def _fetch_sixr_from_assessment(
    db: AsyncSession,
    client_account_id: Optional[UUID],
    engagement_id: Optional[UUID],
) -> Dict[str, Dict[str, Any]]:
    """Fetch 6R decisions from assessment flow phase_results."""
    from app.models.assessment_flow.core_models import AssessmentFlow

    sixr_from_assessment: Dict[str, Dict[str, Any]] = {}

    try:
        assessment_stmt = (
            select(AssessmentFlow)
            .where(
                AssessmentFlow.client_account_id == client_account_id,
                AssessmentFlow.engagement_id == engagement_id,
            )
            .order_by(AssessmentFlow.updated_at.desc())
        )
        assessment_result = await db.execute(assessment_stmt)
        assessment_flows = assessment_result.scalars().all()

        for flow in assessment_flows:
            _extract_sixr_from_flow(flow, sixr_from_assessment)

        logger.info(f"Fetched {len(sixr_from_assessment)} 6R decisions from assessment")
    except Exception as assess_err:
        logger.warning(f"Could not fetch 6R from assessment_flows: {assess_err}")

    return sixr_from_assessment


def _extract_sixr_from_flow(flow: Any, sixr_lookup: Dict[str, Dict[str, Any]]) -> None:
    """Extract 6R decisions from a single assessment flow into lookup dict."""
    if not flow.phase_results:
        return

    rec_gen = flow.phase_results.get("recommendation_generation", {})
    results = rec_gen.get("results", {})
    inner_rec = results.get("recommendation_generation", {})
    applications_data = inner_rec.get("applications", [])

    for app_data in applications_data:
        app_id_str = app_data.get("id") or app_data.get("application_id")
        if app_id_str and app_id_str not in sixr_lookup:
            strategy = (
                app_data.get("six_r_strategy", "")
                or app_data.get("strategy", "")
                or app_data.get("migration_strategy", "")
            ).lower()
            sixr_lookup[app_id_str] = {
                "strategy": strategy,
                "confidence": app_data.get("confidence_score")
                or app_data.get("confidence"),
                "rationale": app_data.get("reasoning")
                or app_data.get("rationale")
                or app_data.get("decision_rationale"),
                "estimated_effort": app_data.get("estimated_effort"),
                "risk_level": app_data.get("risk_level"),
            }


def _build_applications_list(
    app_uuids: List[UUID],
    assets: Dict[UUID, Any],
    sixr_from_assessment: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Build the applications list from assets and 6R data."""
    applications = []

    for app_id in app_uuids:
        asset = assets.get(app_id)
        app_id_str = str(app_id)
        sixr_data = sixr_from_assessment.get(app_id_str, {})

        if asset:
            app_data = _build_app_from_asset(asset, app_id_str, sixr_data)
        else:
            logger.warning(f"Asset not found for ID: {app_id}")
            app_data = _build_fallback_app(app_id_str, sixr_data)

        applications.append(app_data)

    return applications


def _build_app_from_asset(
    asset: Any, app_id_str: str, sixr_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Build application data from an asset with 6R enrichment."""
    # Priority: assessment phase_results > asset.six_r_strategy > default
    migration_strategy = (
        sixr_data.get("strategy")
        or (asset.six_r_strategy.lower() if asset.six_r_strategy else None)
        or "rehost"
    )

    app_data = {
        "id": app_id_str,
        "name": asset.name or f"Asset {app_id_str[:8]}",
        "description": asset.description or "",
        "complexity": getattr(asset, "complexity", None) or "medium",
        "business_criticality": getattr(asset, "criticality", None) or "medium",
        "migration_strategy": migration_strategy,
    }

    # Enrich with additional 6R data if available
    if sixr_data.get("confidence"):
        app_data["confidence_score"] = sixr_data["confidence"]
    if sixr_data.get("rationale"):
        app_data["decision_rationale"] = sixr_data["rationale"]
    if sixr_data.get("estimated_effort"):
        app_data["estimated_effort"] = sixr_data["estimated_effort"]

    return app_data


def _build_fallback_app(app_id_str: str, sixr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build fallback application data when asset not found."""
    migration_strategy = sixr_data.get("strategy") or "rehost"
    return {
        "id": app_id_str,
        "name": f"Unknown App {app_id_str[:8]}",
        "complexity": "medium",
        "business_criticality": "medium",
        "migration_strategy": migration_strategy,
    }


def _build_fallback_applications(app_uuids: List[UUID]) -> List[Dict[str, Any]]:
    """Build fallback application list when main fetch fails."""
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


def _log_strategy_distribution(applications: List[Dict[str, Any]]) -> None:
    """Log the distribution of migration strategies."""
    strategy_dist: Dict[str, int] = {}
    for app in applications:
        strategy = app.get("migration_strategy", "unknown")
        strategy_dist[strategy] = strategy_dist.get(strategy, 0) + 1
    logger.info(f"6R strategy distribution for wave planning: {strategy_dist}")


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
            - migration_start_date: ISO date string for migration start (default: today)

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

    # Use user-provided migration_start_date if available, otherwise default to today
    migration_start_date_str = config.get("migration_start_date")
    if migration_start_date_str:
        try:
            # Parse ISO date string (YYYY-MM-DD or full ISO timestamp)
            if "T" in migration_start_date_str:
                start_date = datetime.fromisoformat(
                    migration_start_date_str.replace("Z", "+00:00")
                )
            else:
                # Date-only format, add timezone
                start_date = datetime.strptime(
                    migration_start_date_str, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            logger.info(f"Using user-provided migration start date: {start_date}")
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Invalid migration_start_date '{migration_start_date_str}': {e}, "
                f"using current date"
            )
            start_date = datetime.now(timezone.utc)
    else:
        start_date = datetime.now(timezone.utc)
        logger.info("No migration_start_date provided, using current date")

    for wave_num in range(1, wave_count + 1):
        wave = _build_wave(
            wave_num,
            wave_count,
            applications,
            max_apps_per_wave,
            wave_duration_days,
            start_date,
            selected_app_count,
        )
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


def _build_wave(
    wave_num: int,
    wave_count: int,
    applications: List[Dict[str, Any]],
    max_apps_per_wave: int,
    wave_duration_days: int,
    start_date: datetime,
    selected_app_count: int,
) -> Dict[str, Any]:
    """Build a single wave structure."""
    # Calculate applications for this wave
    start_idx = (wave_num - 1) * max_apps_per_wave
    end_idx = min(start_idx + max_apps_per_wave, selected_app_count)
    wave_apps = applications[start_idx:end_idx]
    apps_in_wave = len(wave_apps)

    wave_start = start_date + timedelta(days=(wave_num - 1) * wave_duration_days)
    wave_end = wave_start + timedelta(days=wave_duration_days)

    # Determine wave name based on position
    wave_name = _get_wave_name(wave_num, wave_count)

    # Build application list
    wave_applications = [
        {
            "application_id": app.get("id", ""),
            "application_name": app.get("name", "Unknown App"),
            "rationale": f"Assigned to wave {wave_num} for migration",
            "criticality": app.get("business_criticality", "medium"),
            "complexity": app.get("complexity", "medium"),
            "migration_strategy": app.get("migration_strategy", "rehost"),
            "dependency_depth": 0,
        }
        for app in wave_apps
    ]

    # Compute predominant strategy
    predominant_strategy = _compute_predominant_strategy(wave_apps)

    return {
        "wave_id": f"wave_{wave_num}",
        "wave_number": wave_num,
        "wave_name": wave_name,
        "application_count": apps_in_wave,
        "applications": wave_applications,
        "start_date": wave_start.isoformat(),
        "end_date": wave_end.isoformat(),
        "duration_days": wave_duration_days,
        "status": "planned",
        "description": f"{wave_name.split(' - ')[1]} containing {apps_in_wave} apps",
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


def _get_wave_name(wave_num: int, wave_count: int) -> str:
    """Get the display name for a wave based on its position."""
    if wave_num == 1:
        return f"Wave {wave_num} - Initial Migration"
    elif wave_num == wave_count:
        return f"Wave {wave_num} - Final Migration"
    return f"Wave {wave_num} - Secondary Migration"


def _compute_predominant_strategy(wave_apps: List[Dict[str, Any]]) -> str:
    """Compute the most common migration strategy in a wave."""
    strategy_counts: Dict[str, int] = {}
    for app in wave_apps:
        strategy = app.get("migration_strategy", "rehost").lower()
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

    if not strategy_counts:
        return "rehost"

    return max(strategy_counts.keys(), key=lambda s: strategy_counts[s])
