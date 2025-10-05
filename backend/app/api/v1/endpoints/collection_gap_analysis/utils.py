"""
Utility functions for gap analysis operations.
"""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


async def resolve_collection_flow(
    flow_id: str,
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession,
) -> CollectionFlow:
    """
    Resolve collection flow from flow_id (may be master_flow_id).

    Args:
        flow_id: Either collection_flow.flow_id (business identifier) or master_flow_id
        client_account_id: Tenant client account UUID
        engagement_id: Engagement UUID
        db: Async database session

    Returns:
        CollectionFlow instance

    Raises:
        HTTPException: If flow not found or not accessible
    """
    flow_uuid = UUID(flow_id)

    # Try as collection_flow.flow_id first (business identifier from URL)
    stmt = select(CollectionFlow).where(
        CollectionFlow.flow_id == flow_uuid,
        CollectionFlow.client_account_id == client_account_id,
        CollectionFlow.engagement_id == engagement_id,
    )
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        return collection_flow

    # Try as master_flow_id
    stmt = select(CollectionFlow).where(
        CollectionFlow.master_flow_id == flow_uuid,
        CollectionFlow.client_account_id == client_account_id,
        CollectionFlow.engagement_id == engagement_id,
    )
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if not collection_flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection flow {flow_id} not found or not accessible",
        )

    return collection_flow
