"""
Planning flow status retrieval endpoint.

Retrieves current status and progress of planning flows.
Returns operational state from child flow (planning_flows table).

Related ADRs:
- ADR-012: Flow Status Management Separation (Two-Table Pattern)
"""

import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.utils.json_sanitization import sanitize_for_json

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_canonical_to_strategy_map(phase_results: Dict[str, Any]) -> Dict[str, str]:
    """Build mapping of canonical app ID to 6R strategy from phase results."""
    recommendation_gen = phase_results.get("recommendation_generation", {})
    results = recommendation_gen.get("results", {})
    rec_gen_inner = results.get("recommendation_generation", {})
    applications = rec_gen_inner.get("applications", [])

    canonical_to_strategy = {}
    for app_data in applications:
        canonical_app_id = str(app_data.get("application_id", ""))
        strategy = app_data.get("six_r_strategy")
        if canonical_app_id and strategy:
            canonical_to_strategy[canonical_app_id] = strategy

    return canonical_to_strategy


def _map_assets_to_strategies(
    flow: Any, canonical_to_strategy: Dict[str, str]
) -> Dict[str, str]:
    """Map asset IDs to strategies using application_asset_groups."""
    sixr_lookup: Dict[str, str] = {}
    app_asset_groups: list[Any] = flow.application_asset_groups or []

    for group in app_asset_groups:
        canonical_id = str(group.get("canonical_application_id", ""))
        strategy = canonical_to_strategy.get(canonical_id)
        if strategy:
            asset_ids = group.get("asset_ids", [])
            for asset_id in asset_ids:
                sixr_lookup[str(asset_id)] = strategy

    return sixr_lookup


def _apply_strategies_to_waves(
    wave_plan_data: Dict[str, Any], sixr_lookup: Dict[str, str]
) -> int:
    """Apply 6R strategies to wave applications, return count enriched."""
    enriched_count = 0
    for wave in wave_plan_data.get("waves", []):
        for app in wave.get("applications", []):
            app_id = app.get("application_id")
            if app_id and not app.get("migration_strategy"):
                strategy = sixr_lookup.get(str(app_id))
                if strategy:
                    app["migration_strategy"] = strategy
                    enriched_count += 1
    return enriched_count


def _build_wave_app_entry(
    app_id: str, app_data: Dict[str, Any], rationale: str
) -> Dict[str, Any]:
    """Build a single wave application entry dict."""
    return {
        "application_id": app_id,
        "application_name": app_data.get("name", f"App {app_id[:8]}..."),
        "rationale": rationale,
        "criticality": app_data.get("criticality", "medium"),
        "complexity": app_data.get("complexity", "medium"),
        "migration_strategy": app_data.get("migration_strategy", "rehost"),
        "dependency_depth": 0,
    }


def _get_assigned_app_ids(waves: list) -> set:
    """Extract app IDs already assigned to waves."""
    assigned = set()
    for wave in waves:
        for app in wave.get("applications", []):
            app_id = app.get("application_id") or app.get("id")
            if app_id:
                assigned.add(str(app_id))
    return assigned


def _distribute_apps_to_wave(
    wave: Dict[str, Any],
    unassigned_app_ids: list,
    app_index: int,
    app_lookup: Dict[str, Any],
    total_remaining_waves: int,
) -> int:
    """Distribute apps to a single wave missing applications. Returns new app_index."""
    app_count = wave.get("application_count", 0)
    if app_count == 0:
        app_count = max(1, len(unassigned_app_ids) // max(1, total_remaining_waves))

    wave_applications = []
    for _ in range(min(app_count, len(unassigned_app_ids) - app_index)):
        if app_index >= len(unassigned_app_ids):
            break

        app_id = unassigned_app_ids[app_index]
        app_data = app_lookup.get(app_id, {})
        rationale = f"Assigned to wave {wave.get('wave_number', 'N/A')}"
        wave_applications.append(_build_wave_app_entry(app_id, app_data, rationale))
        app_index += 1

    wave["applications"] = wave_applications
    wave["application_count"] = len(wave_applications)
    return app_index


async def enrich_wave_plan_with_sixr_strategies(
    wave_plan_data: Dict[str, Any],
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """
    Enrich wave plan applications with 6R strategies from assessment flows.

    This handles backwards compatibility for wave plans generated before
    migration_strategy was added to the wave application data structure.

    Uses the same enrichment logic as applications.py endpoint to get
    6R strategies from assessment_flows.phase_results.

    Args:
        wave_plan_data: Wave plan data from planning flow
        db: Database session
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        Enriched wave plan data with migration_strategy populated
    """
    from app.models.assessment_flow import AssessmentFlow

    if not wave_plan_data or "waves" not in wave_plan_data:
        return wave_plan_data

    # Query assessment flows for this tenant/engagement
    try:
        result = await db.execute(
            select(AssessmentFlow).where(
                AssessmentFlow.client_account_id == client_account_id,
                AssessmentFlow.engagement_id == engagement_id,
                AssessmentFlow.phase_results.isnot(None),
            )
        )
        flows = result.scalars().all()

        # Build lookup dict: asset_id -> six_r_strategy
        sixr_lookup: Dict[str, str] = {}

        for flow in flows:
            phase_results: Dict[str, Any] = flow.phase_results or {}
            canonical_to_strategy = _build_canonical_to_strategy_map(phase_results)
            flow_lookup = _map_assets_to_strategies(flow, canonical_to_strategy)
            sixr_lookup.update(flow_lookup)

        # Apply strategies to wave applications
        enriched_count = _apply_strategies_to_waves(wave_plan_data, sixr_lookup)

        if enriched_count > 0:
            logger.info(
                f"Enriched {enriched_count} apps with 6R strategies from assessment flows"
            )

    except Exception as e:
        logger.warning(f"Failed to enrich wave plan with 6R strategies: {e}")

    return wave_plan_data


def _build_app_lookup_from_assets(assets: list) -> Dict[str, Dict[str, Any]]:
    """Build lookup dict from Asset objects."""
    app_lookup = {}
    for asset in assets:
        app_lookup[str(asset.id)] = {
            "id": str(asset.id),
            "name": asset.application_name or asset.asset_name or str(asset.id)[:8],
            "criticality": getattr(asset, "business_criticality", "medium") or "medium",
            "complexity": getattr(asset, "complexity", "medium") or "medium",
            "migration_strategy": getattr(asset, "six_r_strategy", None),
            "tech_stack": getattr(asset, "technology_stack", None),
        }
    return app_lookup


def _add_remaining_apps_to_last_wave(
    waves: list, unassigned_app_ids: list, app_index: int, app_lookup: Dict[str, Any]
) -> None:
    """Add any remaining unassigned apps to the last wave."""
    if app_index >= len(unassigned_app_ids) or not waves:
        return

    last_wave = waves[-1]
    if "applications" not in last_wave:
        last_wave["applications"] = []

    for app_id in unassigned_app_ids[app_index:]:
        app_data = app_lookup.get(app_id, {})
        last_wave["applications"].append(
            _build_wave_app_entry(app_id, app_data, "Assigned to final wave")
        )
    last_wave["application_count"] = len(last_wave["applications"])


async def _populate_missing_wave_applications(
    wave_plan_data: Dict[str, Any],
    selected_applications: list,
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[str, Any]:
    """
    Populate missing applications arrays in waves from selected_applications.

    Per ADR-035, LLM output may be truncated causing waves to have
    application_count but no applications array. This function fetches
    application details from the Asset table and populates missing arrays.
    """
    from app.models.asset.models import Asset

    waves = wave_plan_data.get("waves", [])
    if not waves:
        return wave_plan_data

    # Check if any wave is missing applications
    waves_missing_apps = [
        w for w in waves if not w.get("applications") or not w.get("applications")
    ]
    if not waves_missing_apps:
        return wave_plan_data

    logger.info(
        f"Populating missing applications for {len(waves_missing_apps)} of {len(waves)} waves"
    )

    app_id_strs = [str(app_id) for app_id in selected_applications]
    if not app_id_strs:
        logger.warning("No selected_applications to populate waves with")
        return wave_plan_data

    try:
        # Build UUID list for query (skip invalid UUIDs)
        app_uuids = []
        for app_id in app_id_strs:
            try:
                app_uuids.append(UUID(app_id))
            except ValueError:
                continue

        # Query Asset table for application details
        result = await db.execute(
            select(Asset).where(
                Asset.client_account_id == client_account_id,
                Asset.engagement_id == engagement_id,
                Asset.id.in_(app_uuids),
            )
        )
        assets = result.scalars().all()

        # Build lookups using helpers
        app_lookup = _build_app_lookup_from_assets(assets)
        assigned_app_ids = _get_assigned_app_ids(waves)
        unassigned_app_ids = [
            app_id for app_id in app_id_strs if app_id not in assigned_app_ids
        ]

        # Distribute apps to waves missing applications
        app_index = 0
        for wave in waves:
            if not wave.get("applications"):
                remaining_waves = len([w for w in waves if not w.get("applications")])
                app_index = _distribute_apps_to_wave(
                    wave, unassigned_app_ids, app_index, app_lookup, remaining_waves
                )

        # Handle remaining apps by adding to last wave
        _add_remaining_apps_to_last_wave(
            waves, unassigned_app_ids, app_index, app_lookup
        )

        logger.info("Successfully populated missing wave applications")

    except Exception as e:
        logger.warning(f"Failed to populate missing wave applications: {e}")

    return wave_plan_data


@router.get("/status/{planning_flow_id}")
async def get_planning_status(
    planning_flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    Get current planning flow status and progress.

    Returns operational state from planning_flows table including:
    - Current phase and phase status
    - Wave plan data
    - Resource allocation data
    - Timeline data
    - Cost estimation data
    - UI state

    Response:
    ```json
    {
        "planning_flow_id": "uuid",
        "master_flow_id": "uuid",
        "current_phase": "wave_planning",
        "phase_status": "completed",
        "wave_plan_data": {...},
        "resource_allocation_data": {...},
        "timeline_data": {...},
        "cost_estimation_data": {...},
        "ui_state": {...},
        "created_at": "2025-10-29T12:00:00",
        "updated_at": "2025-10-29T12:30:00"
    }
    ```
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    try:
        # Parse planning flow ID
        try:
            planning_flow_uuid = UUID(planning_flow_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid planning flow UUID format"
            )

        # Convert client_account_id and engagement_id to UUIDs (per migration 115)
        # All tenant IDs are UUIDs - NEVER convert to integers
        try:
            client_account_uuid = (
                UUID(client_account_id)
                if isinstance(client_account_id, str)
                else client_account_id
            )
            engagement_uuid = (
                UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
            )

            if not client_account_uuid or not engagement_uuid:
                raise ValueError(
                    "Both client_account_id and engagement_id are required"
                )
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid UUID format for client_account_id or engagement_id: {str(e)}",
            )

        # Initialize repository with UUIDs
        repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Get planning flow (with tenant scoping verification)
        planning_flow = await repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        if not planning_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Planning flow {planning_flow_id} not found or access denied",
            )

        logger.debug(
            f"Retrieved planning flow status: {planning_flow_id} "
            f"(client: {client_account_uuid}, engagement: {engagement_uuid})"
        )

        # Enrich wave plan data with 6R strategies (backwards compatibility)
        enriched_wave_plan = await enrich_wave_plan_with_sixr_strategies(
            planning_flow.wave_plan_data or {},
            db,
            client_account_uuid,
            engagement_uuid,
        )

        # Also populate missing applications arrays in waves from selected_applications
        # This handles cases where agent output was truncated (ADR-035) or missing apps
        enriched_wave_plan = await _populate_missing_wave_applications(
            enriched_wave_plan,
            planning_flow.selected_applications or [],
            db,
            client_account_uuid,
            engagement_uuid,
        )

        # Return complete planning flow state
        return sanitize_for_json(
            {
                "planning_flow_id": str(planning_flow.planning_flow_id),
                "master_flow_id": str(planning_flow.master_flow_id),
                "current_phase": planning_flow.current_phase,
                "phase_status": planning_flow.phase_status,
                "wave_plan_data": enriched_wave_plan,
                "resource_allocation_data": planning_flow.resource_allocation_data,
                "timeline_data": planning_flow.timeline_data,
                "cost_estimation_data": planning_flow.cost_estimation_data,
                "agent_execution_log": planning_flow.agent_execution_log,
                "ui_state": planning_flow.ui_state,
                "created_at": planning_flow.created_at.isoformat(),
                "updated_at": planning_flow.updated_at.isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve planning flow status: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve planning flow status: {str(e)}",
        )
