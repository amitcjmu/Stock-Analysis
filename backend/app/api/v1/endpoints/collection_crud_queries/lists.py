"""
Collection Flow List Operations
Bulk operations for retrieving multiple flows.
"""

import logging
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
)
from app.schemas.collection_flow import (
    CollectionFlowResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def get_incomplete_flows(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    limit: int = 50,
) -> List[CollectionFlowResponse]:
    """Get incomplete collection flows for current engagement.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context
        limit: Maximum number of flows to return

    Returns:
        List of incomplete collection flows
    """
    try:
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.in_(
                    [
                        # Per ADR-012: Use lifecycle states instead of phase values
                        CollectionFlowStatus.INITIALIZED.value,
                        CollectionFlowStatus.RUNNING.value,
                        CollectionFlowStatus.PAUSED.value,
                        CollectionFlowStatus.FAILED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(limit)
        )
        flows = result.scalars().all()

        return [
            collection_serializers.serialize_collection_flow(flow) for flow in flows
        ]

    except Exception as e:
        logger.error(safe_log_format("Error getting incomplete flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def get_all_flows(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    limit: int = 50,
) -> List[CollectionFlowResponse]:
    """Get all collection flows for current engagement (including completed ones).
    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context
        limit: Maximum number of flows to return
    Returns:
        List of all collection flows
    """
    try:
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(limit)
        )
        flows = result.scalars().all()
        return [
            collection_serializers.serialize_collection_flow(flow) for flow in flows
        ]
    except Exception as e:
        logger.error(safe_log_format("Error getting all flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
