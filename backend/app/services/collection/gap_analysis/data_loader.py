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
    Resolve collection flow PRIMARY KEY (id) from business flow_id.

    CRITICAL ARCHITECTURE:
    - Input: flow_id (business identifier from frontend/API)
    - Output: id (PRIMARY KEY for FK relationships)
    - WHY: FK constraints reference collection_flows.id (PK), not flow_id

    The service might receive either:
    - A collection flow_id (business identifier) → returns matching PK
    - A master flow ID → finds child collection flow, returns its PK

    Args:
        flow_id: Input flow ID (business identifier or master flow UUID)
        db: Database session

    Returns:
        The PRIMARY KEY (id) of the child collection flow for FK persistence
    """
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

    # First try: Is this a collection flow_id (business identifier)?
    # Query by flow_id, return id (PK)
    stmt = select(CollectionFlow).where(CollectionFlow.flow_id == flow_uuid)
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        logger.debug(
            f"✅ Input {flow_id} is a collection flow_id (business ID), "
            f"returning PK {collection_flow.id} for FK storage"
        )
        return str(collection_flow.id)  # Return PK for FK relationships

    # Second try: Is this a master_flow_id? Look up child collection flow
    stmt = select(CollectionFlow).where(CollectionFlow.master_flow_id == flow_uuid)
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        logger.info(
            f"✅ Input {flow_id} is a master flow ID, "
            f"resolved to collection flow PK {collection_flow.id} (flow_id: {collection_flow.flow_id})"
        )
        return str(collection_flow.id)  # Return PK for FK relationships

    # Fallback: No collection flow found - raise an error
    message = (
        f"Could not resolve collection flow ID from input: {flow_id} "
        f"(not found as collection_flow_id or master_flow_id)"
    )
    logger.error(f"❌ {message}")
    raise ValueError(message)
