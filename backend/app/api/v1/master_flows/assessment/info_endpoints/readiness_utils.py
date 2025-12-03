"""
Readiness data utilities for assessment endpoints.

Helper functions for refreshing and calculating readiness data.
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from ..uuid_utils import ensure_uuid

logger = logging.getLogger(__name__)


async def refresh_readiness_for_groups(
    db: AsyncSession,
    application_groups: list,
    client_account_id: Any,
    engagement_id: Any,
) -> list:
    """
    Refresh readiness_summary and asset details for pre-computed application groups.

    Pre-computed groups stored in the database may have stale readiness data
    (e.g., all zeros) because assets were marked as ready AFTER the flow was created.
    This function queries the current asset state and updates the readiness data.

    Args:
        db: Database session
        application_groups: List of pre-computed application group dicts
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        Updated application groups with fresh readiness data
    """
    if not application_groups:
        return application_groups

    # Collect all asset IDs from all groups
    all_asset_ids = []
    for group in application_groups:
        asset_ids = group.get("asset_ids", [])
        all_asset_ids.extend(asset_ids)

    if not all_asset_ids:
        return application_groups

    # Query current asset state for all assets
    assets_query = select(
        Asset.id,
        Asset.asset_name,
        Asset.name,
        Asset.asset_type,
        Asset.environment,
        Asset.assessment_readiness,
        Asset.assessment_readiness_score,
    ).where(
        Asset.id.in_([ensure_uuid(aid) for aid in all_asset_ids]),
        Asset.client_account_id == ensure_uuid(client_account_id),
        Asset.engagement_id == ensure_uuid(engagement_id),
    )
    assets_result = await db.execute(assets_query)
    assets_rows = assets_result.all()

    # Build lookup by asset_id
    asset_lookup = {}
    for row in assets_rows:
        asset_lookup[str(row.id)] = {
            "asset_id": str(row.id),
            "asset_name": row.asset_name or row.name or "Unknown Asset",
            "asset_type": row.asset_type,
            "environment": row.environment,
            "assessment_readiness": row.assessment_readiness or "not_ready",
            "assessment_readiness_score": (
                float(row.assessment_readiness_score)
                if row.assessment_readiness_score is not None
                else None
            ),
        }

    # Update each group with fresh readiness data
    updated_groups = []
    for group in application_groups:
        group_asset_ids = group.get("asset_ids", [])

        # Calculate fresh readiness summary
        ready_count = 0
        not_ready_count = 0
        in_progress_count = 0
        scores = []
        assets_list = []

        for aid in group_asset_ids:
            aid_str = str(aid)
            if aid_str in asset_lookup:
                asset_info = asset_lookup[aid_str]
                readiness = asset_info["assessment_readiness"]

                # Count by readiness status
                if readiness == "ready":
                    ready_count += 1
                elif readiness == "in_progress":
                    in_progress_count += 1
                else:
                    not_ready_count += 1

                # Collect score for average
                if asset_info["assessment_readiness_score"] is not None:
                    score = asset_info["assessment_readiness_score"]
                    if 0.0 <= score <= 1.0:
                        scores.append(score)

                # Build asset detail
                assets_list.append(asset_info)
            else:
                # Asset not found - mark as not_ready
                not_ready_count += 1
                assets_list.append(
                    {
                        "asset_id": aid_str,
                        "asset_name": "Unknown Asset",
                        "asset_type": None,
                        "environment": None,
                        "assessment_readiness": "not_ready",
                        "assessment_readiness_score": None,
                    }
                )

        # Calculate average score
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Update group with fresh data
        updated_group = dict(group)  # Copy to avoid mutating original
        updated_group["readiness_summary"] = {
            "ready": ready_count,
            "not_ready": not_ready_count,
            "in_progress": in_progress_count,
            "avg_completeness_score": avg_score,
        }
        updated_group["assets"] = assets_list
        updated_groups.append(updated_group)

    logger.info(
        f"Refreshed readiness data for {len(updated_groups)} application groups "
        f"({len(all_asset_ids)} total assets)"
    )
    return updated_groups
