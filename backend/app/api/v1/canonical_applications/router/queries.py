"""
Database query logic for canonical applications.

Handles readiness queries, unmapped asset queries, and related database operations.
"""

import logging
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset.models import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)

logger = logging.getLogger(__name__)


async def get_readiness_stats(
    db: AsyncSession,
    app_ids: List[UUID],
    client_account_id: UUID,
    engagement_id: UUID,
) -> Dict[UUID, Dict[str, int]]:
    """
    Query asset readiness stats for canonical applications.

    Args:
        db: Database session
        app_ids: List of canonical application IDs
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        Map of canonical_app_id -> {linked_asset_count, ready_asset_count}
    """
    # Query to get asset readiness stats per canonical app
    # JOIN: CollectionFlowApplication -> Asset
    # GROUP BY: canonical_application_id
    # COUNT: total assets, ready assets
    # CC FIX: Must check BOTH discovery_status AND assessment_readiness to match
    # backend validation in verify_applications_ready_for_assessment()
    readiness_query = (
        select(
            CollectionFlowApplication.canonical_application_id,
            func.count(Asset.id).label("linked_asset_count"),
            func.sum(
                case(
                    (
                        and_(
                            Asset.discovery_status == "completed",
                            Asset.assessment_readiness == "ready",
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("ready_asset_count"),
        )
        .join(
            Asset,
            and_(
                Asset.id == CollectionFlowApplication.asset_id,
                Asset.client_account_id == client_account_id,
                Asset.engagement_id == engagement_id,
            ),
        )
        .where(
            CollectionFlowApplication.canonical_application_id.in_(app_ids),
            CollectionFlowApplication.client_account_id == client_account_id,
            CollectionFlowApplication.engagement_id == engagement_id,
        )
        .group_by(CollectionFlowApplication.canonical_application_id)
    )

    readiness_result = await db.execute(readiness_query)
    readiness_rows = readiness_result.all()

    # Build readiness map: canonical_app_id -> {linked_count, ready_count}
    return {
        row.canonical_application_id: {
            "linked_asset_count": row.linked_asset_count or 0,
            "ready_asset_count": row.ready_asset_count or 0,
        }
        for row in readiness_rows
    }


def calculate_readiness_metadata(
    linked_count: int, ready_count: int
) -> Tuple[str, List[str], List[str]]:
    """
    Calculate readiness status, blockers, and recommendations.

    Args:
        linked_count: Total assets linked to canonical application
        ready_count: Assets ready for assessment

    Returns:
        Tuple of (readiness_status, blockers, recommendations)
    """
    not_ready_count = linked_count - ready_count

    # Determine overall readiness status
    if linked_count == 0:
        readiness_status = "not_ready"  # No assets = not ready
        blockers = ["No assets linked to this application"]
        recommendations = ["Complete Collection Flow to gather application data"]
    elif ready_count == linked_count:
        readiness_status = "ready"  # All assets ready
        blockers = []
        recommendations = []
    elif ready_count > 0:
        readiness_status = "partial"  # Some ready, some not
        blockers = [f"{not_ready_count} asset(s) not ready for assessment"]
        recommendations = [
            "Complete discovery and data collection for remaining assets"
        ]
    else:
        readiness_status = "not_ready"  # None ready
        blockers = ["Assets require discovery completion and data collection"]
        recommendations = ["Run Collection Flow to gather missing data"]

    return readiness_status, blockers, recommendations


async def get_unmapped_assets(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    search: str | None = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Query for non-application assets and their mapping status.

    Issue #1197: Optimized with batch queries to avoid N+1 pattern.
    After bootstrap, assets with application_name will have junction records.

    Args:
        db: Database session
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID
        search: Optional search term for asset name

    Returns:
        Tuple of (unmapped_assets_data, unmapped_total_count)
    """
    # Query for non-application assets
    unmapped_base_query = select(Asset).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
        Asset.asset_type != "application",  # Exclude applications
    )

    # Apply search filter if provided
    if search and search.strip():
        search_term = f"%{search.strip().lower()}%"
        unmapped_base_query = unmapped_base_query.where(
            func.lower(Asset.name).like(search_term)
        )

    # Count unmapped assets
    unmapped_count_query = select(func.count()).select_from(
        unmapped_base_query.subquery()
    )
    unmapped_count_result = await db.execute(unmapped_count_query)
    unmapped_total = unmapped_count_result.scalar() or 0

    # Fetch unmapped assets with pagination
    unmapped_query = unmapped_base_query.order_by(Asset.created_at.desc())

    unmapped_result = await db.execute(unmapped_query)
    unmapped_assets = unmapped_result.scalars().all()

    if not unmapped_assets:
        return [], unmapped_total

    # Issue #1197: Batch query all mappings to avoid N+1 pattern
    asset_ids = [asset.id for asset in unmapped_assets]

    batch_mappings_query = (
        select(
            CollectionFlowApplication.asset_id,
            CollectionFlowApplication.canonical_application_id,
            CanonicalApplication.canonical_name,
        )
        .join(
            CanonicalApplication,
            CanonicalApplication.id
            == CollectionFlowApplication.canonical_application_id,
        )
        .where(
            CollectionFlowApplication.asset_id.in_(asset_ids),
            CollectionFlowApplication.client_account_id == client_account_id,
            CollectionFlowApplication.engagement_id == engagement_id,
        )
    )

    batch_mappings_result = await db.execute(batch_mappings_query)
    batch_mappings = batch_mappings_result.all()

    # Build lookup dictionary: asset_id -> (canonical_app_id, canonical_name)
    mappings_by_asset: Dict[UUID, Tuple[UUID, str]] = {}
    for mapping in batch_mappings:
        mappings_by_asset[mapping.asset_id] = (
            mapping.canonical_application_id,
            mapping.canonical_name,
        )

    # Build response data using batch-fetched mappings
    unmapped_assets_data = []
    for asset in unmapped_assets:
        mapping = mappings_by_asset.get(asset.id)

        unmapped_assets_data.append(
            {
                "is_unmapped_asset": True,  # Flag to identify unmapped assets
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "asset_type": asset.asset_type,
                "mapped_to_application_id": (str(mapping[0]) if mapping else None),
                "mapped_to_application_name": (mapping[1] if mapping else None),
                "discovery_status": asset.discovery_status,
                "assessment_readiness": asset.assessment_readiness,
            }
        )

    return unmapped_assets_data, unmapped_total
