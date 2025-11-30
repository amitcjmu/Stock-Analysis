"""
6R Strategy Enrichment for Wave Plan Data.

Fetches and enriches wave_plan_data applications with 6R strategies
from assets or assessment flows.
"""

import copy
import logging
from typing import Any, Dict, Optional, Set
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def enrich_wave_data_with_6r_strategies(
    db: AsyncSession,
    wave_plan_data: Dict[str, Any],
    client_account_uuid: Optional[UUID],
    engagement_uuid: Optional[UUID],
) -> Dict[str, Any]:
    """
    Enrich wave_plan_data applications with 6R strategies from assets or assessment flows.

    The CrewAI wave planning agent may not include migration_strategy in its output.
    This function fetches 6R decisions from:
    1. assets.six_r_strategy (PRIMARY - wave_plan_data uses asset IDs)
    2. assessment_flows.phase_results (FALLBACK - for canonical app IDs)

    Args:
        db: Async database session
        wave_plan_data: Raw wave plan data that may be missing migration_strategy
        client_account_uuid: Client account UUID for tenant scoping
        engagement_uuid: Engagement UUID for tenant scoping

    Returns:
        Enriched wave_plan_data with migration_strategy populated for each app
    """
    waves = wave_plan_data.get("waves", [])
    if not waves:
        return wave_plan_data

    # Collect all app IDs from wave_plan_data
    all_app_ids = _collect_app_ids(waves)
    if not all_app_ids:
        return wave_plan_data

    # Build lookup of 6R strategies
    sixr_lookup = await _build_sixr_lookup(
        db, all_app_ids, client_account_uuid, engagement_uuid
    )

    if not sixr_lookup:
        logger.info("No 6R strategies found in assets or assessment flows")
        return wave_plan_data

    # Apply enrichment
    enriched_data = _apply_enrichment(wave_plan_data, sixr_lookup)

    return enriched_data


def _collect_app_ids(waves: list) -> Set[str]:
    """Collect all application IDs from wave data."""
    all_app_ids: Set[str] = set()
    for wave in waves:
        for app in wave.get("applications", []):
            app_id = app.get("application_id") or app.get("id")
            if app_id:
                all_app_ids.add(app_id)
    return all_app_ids


async def _build_sixr_lookup(
    db: AsyncSession,
    all_app_ids: Set[str],
    client_account_uuid: Optional[UUID],
    engagement_uuid: Optional[UUID],
) -> Dict[str, str]:
    """Build lookup of 6R strategies from assets and assessment flows."""
    sixr_lookup: Dict[str, str] = {}

    # PRIMARY: Query assets table
    sixr_lookup = await _fetch_from_assets(db, all_app_ids)

    # FALLBACK: Try assessment_flows for missing apps
    missing_apps = all_app_ids - set(sixr_lookup.keys())
    if missing_apps:
        assessment_strategies = await _fetch_from_assessment_flows(
            db, missing_apps, client_account_uuid, engagement_uuid
        )
        sixr_lookup.update(assessment_strategies)

    return sixr_lookup


async def _fetch_from_assets(db: AsyncSession, all_app_ids: Set[str]) -> Dict[str, str]:
    """Fetch 6R strategies from assets table."""
    from app.models.asset import Asset

    sixr_lookup: Dict[str, str] = {}

    try:
        # Convert string IDs to UUIDs for query
        app_uuids = []
        for app_id in all_app_ids:
            try:
                app_uuids.append(UUID(app_id) if isinstance(app_id, str) else app_id)
            except (ValueError, TypeError):
                continue

        if app_uuids:
            asset_stmt = select(Asset.id, Asset.six_r_strategy).where(
                Asset.id.in_(app_uuids),
                Asset.six_r_strategy.isnot(None),
            )
            asset_result = await db.execute(asset_stmt)
            assets = asset_result.all()

            for asset_id, strategy in assets:
                if strategy:
                    sixr_lookup[str(asset_id)] = strategy.lower()

            logger.info(
                f"Built 6R strategy lookup with {len(sixr_lookup)} apps from assets table"
            )
    except Exception as e:
        logger.warning(f"Could not fetch 6R strategies from assets: {e}")

    return sixr_lookup


async def _fetch_from_assessment_flows(
    db: AsyncSession,
    missing_apps: Set[str],
    client_account_uuid: Optional[UUID],
    engagement_uuid: Optional[UUID],
) -> Dict[str, str]:
    """Fetch 6R strategies from assessment flows for missing apps."""
    from app.models.assessment_flow.core_models import AssessmentFlow

    sixr_lookup: Dict[str, str] = {}

    try:
        assessment_stmt = (
            select(AssessmentFlow)
            .where(
                AssessmentFlow.client_account_id == client_account_uuid,
                AssessmentFlow.engagement_id == engagement_uuid,
            )
            .order_by(AssessmentFlow.updated_at.desc())
        )
        assessment_result = await db.execute(assessment_stmt)
        assessment_flows = assessment_result.scalars().all()

        for flow in assessment_flows:
            if not flow.phase_results:
                continue
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
                    if strategy:
                        sixr_lookup[app_id_str] = strategy

        logger.info(f"Added {len(sixr_lookup)} apps from assessment flows (fallback)")
    except Exception as e:
        logger.warning(f"Could not fetch 6R strategies from assessment flows: {e}")

    return sixr_lookup


def _apply_enrichment(
    wave_plan_data: Dict[str, Any], sixr_lookup: Dict[str, str]
) -> Dict[str, Any]:
    """Apply 6R strategy enrichment to wave plan data."""
    enriched_data = copy.deepcopy(wave_plan_data)
    enriched_count = 0

    for wave in enriched_data.get("waves", []):
        for app in wave.get("applications", []):
            # Skip if already has migration_strategy
            if app.get("migration_strategy"):
                continue

            # Look up by application_id or id
            app_id = app.get("application_id") or app.get("id")
            if app_id and app_id in sixr_lookup:
                app["migration_strategy"] = sixr_lookup[app_id]
                enriched_count += 1

    if enriched_count > 0:
        logger.info(f"Enriched {enriched_count} apps with 6R strategies")

    # Log strategy distribution for debugging
    strategy_dist: Dict[str, int] = {}
    for wave in enriched_data.get("waves", []):
        for app in wave.get("applications", []):
            strategy = app.get("migration_strategy", "unknown")
            strategy_dist[strategy] = strategy_dist.get(strategy, 0) + 1
    logger.info(f"6R strategy distribution for resource estimation: {strategy_dist}")

    return enriched_data
