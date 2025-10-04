"""Data loading utilities for gap analysis."""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


async def load_assets(
    selected_asset_ids: List[str],
    client_account_id: str,
    engagement_id: str,
    db: AsyncSession,
) -> List[Asset]:
    """Load REAL assets from database with tenant scoping.

    Args:
        selected_asset_ids: List of asset UUID strings
        client_account_id: Client account ID for scoping
        engagement_id: Engagement ID for scoping
        db: Database session

    Returns:
        List of Asset objects
    """
    asset_uuids = [
        UUID(aid) if isinstance(aid, str) else aid for aid in selected_asset_ids
    ]

    # Convert client_account_id and engagement_id to UUID if they're strings
    client_uuid = (
        UUID(client_account_id)
        if isinstance(client_account_id, str)
        else client_account_id
    )
    engagement_uuid = (
        UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
    )

    stmt = select(Asset).where(
        and_(
            Asset.id.in_(asset_uuids),
            Asset.client_account_id == client_uuid,
            Asset.engagement_id == engagement_uuid,
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def resolve_collection_flow_id(
    flow_id: str,
    db: AsyncSession,
) -> str:
    """
    Resolve the actual collection flow ID from the input flow_id.

    The service might receive either:
    - A master flow ID (needs lookup to find child collection flow)
    - A collection flow ID directly (use as-is)

    Args:
        flow_id: Input flow ID (could be master or collection flow)
        db: Database session

    Returns:
        The UUID string of the child collection flow to use for gap persistence
    """
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

    # First try: Is this already a collection_flow_id?
    stmt = select(CollectionFlow).where(CollectionFlow.id == flow_uuid)
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        logger.debug(f"✅ Input {flow_id} is a collection flow ID (direct match)")
        return str(collection_flow.id)

    # Second try: Is this a master_flow_id? Look up child collection flow
    stmt = select(CollectionFlow).where(CollectionFlow.master_flow_id == flow_uuid)
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        logger.info(
            f"✅ Input {flow_id} is a master flow ID, "
            f"resolved to collection flow {collection_flow.id}"
        )
        return str(collection_flow.id)

    # Fallback: No collection flow found - this will cause FK violation, but be explicit
    logger.error(
        f"❌ Could not resolve collection flow ID from input: {flow_id} "
        f"(not found as collection_flow_id or master_flow_id)"
    )
    # Return original ID to let FK constraint fail with clear error
    return flow_id
