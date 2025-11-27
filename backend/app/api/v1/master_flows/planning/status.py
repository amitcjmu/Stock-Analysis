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
