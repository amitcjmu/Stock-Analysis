"""
Query helper functions for assessment endpoints.

Provides reusable database query logic for assessment flows.
"""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.models.assessment_flow import AssessmentFlow
from .uuid_utils import ensure_uuid


async def get_assessment_flow(
    db: AsyncSession,
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
) -> AssessmentFlow:
    """
    Get assessment flow with tenant scoping and master_flow_id fallback.

    Args:
        db: Database session
        flow_id: Flow ID (can be master_flow_id or legacy id)
        client_account_id: Client account ID for tenant scoping
        engagement_id: Engagement ID for tenant scoping

    Returns:
        AssessmentFlow instance

    Raises:
        HTTPException: If flow not found or validation fails
    """
    # Validate context
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    if not engagement_id:
        raise HTTPException(status_code=400, detail="Engagement ID required")

    # Query with master_flow_id first, fallback to id for legacy flows
    query = select(AssessmentFlow).where(
        sa.or_(
            AssessmentFlow.master_flow_id == UUID(flow_id),
            AssessmentFlow.id == UUID(flow_id),
        ),
        AssessmentFlow.client_account_id == ensure_uuid(client_account_id),
        AssessmentFlow.engagement_id == ensure_uuid(engagement_id),
    )
    result = await db.execute(query)
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(status_code=404, detail="Assessment flow not found")

    return flow


def get_asset_ids(flow: AssessmentFlow) -> list:
    """
    Get asset IDs from flow with semantic field fallback.

    Args:
        flow: AssessmentFlow instance

    Returns:
        List of asset IDs (may be empty)
    """
    # Use new semantic field with fallback to deprecated field
    return flow.selected_asset_ids or flow.selected_application_ids or []


async def get_collection_flow_id(flow: AssessmentFlow) -> Optional[UUID]:
    """
    Extract collection_flow_id from flow metadata.

    Args:
        flow: AssessmentFlow instance

    Returns:
        Collection flow ID UUID or None if not available
    """
    if not flow.flow_metadata or not isinstance(flow.flow_metadata, dict):
        return None

    source_collection = flow.flow_metadata.get("source_collection", {})
    if not isinstance(source_collection, dict):
        return None

    collection_flow_id_str = source_collection.get("collection_flow_id")
    if not collection_flow_id_str:
        return None

    return UUID(collection_flow_id_str)
