"""
Collection Flow Update Operations
Handles update operations for collection flows.
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from fastapi import HTTPException
from app.models import User
from app.models.collection_flow import CollectionFlow
from app.schemas.collection_flow import CollectionFlowUpdate

logger = logging.getLogger(__name__)


async def update_collection_flow(
    flow_id: str,
    flow_update: CollectionFlowUpdate,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Update an existing collection flow."""
    try:
        # Validate flow_id format before querying
        try:
            flow_uuid = UUID(flow_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail=f"Invalid flow ID format: {flow_id}"
            )

        # Fetch the flow by flow_id (not id) with proper multi-tenant validation
        result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_uuid)
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
            .options(selectinload(CollectionFlow.questionnaire_responses))
        )
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=404, detail=f"Collection flow {flow_id} not found"
            )

        # Update fields if provided
        # Note: CollectionFlowUpdate doesn't have a status field
        # Status updates should be handled through action field or separate endpoints

        if flow_update.collection_config is not None:
            flow.collection_config = {
                **flow.collection_config,
                **flow_update.collection_config,
            }

        if flow_update.automation_tier is not None:
            flow.automation_tier = flow_update.automation_tier

        # Update metadata
        flow.updated_at = datetime.utcnow()
        # Note: collection_flows table doesn't have updated_by column

        await db.commit()
        await db.refresh(flow)

        # Build proper CollectionFlowResponse
        from app.api.v1.endpoints import collection_serializers

        return collection_serializers.build_collection_flow_response(flow)

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update collection flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update collection flow: {e}"
        )
