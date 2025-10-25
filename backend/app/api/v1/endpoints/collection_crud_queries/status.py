"""
Collection Flow Status Operations
Basic status and flow retrieval operations.
"""

import logging
from typing import Any, Dict
from uuid import UUID

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


async def get_collection_status(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Get collection flow status for current engagement.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with collection status information
    """
    try:
        # Get active collection flow - use first() to handle multiple rows
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                        CollectionFlowStatus.FAILED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(1)  # Ensure we only get one row
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            return collection_serializers.build_no_active_flow_response()

        return collection_serializers.build_collection_status_response(collection_flow)

    except Exception as e:
        logger.error(safe_log_format("Error getting collection status: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Get collection flow by ID with authorization.

    Args:
        flow_id: Collection flow ID (can be either flow_id or id column)
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Collection flow details

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # Bug #799 Fix: Check both flow_id and id columns for flexible lookup
        flow_uuid = UUID(flow_id)
        result = await db.execute(
            select(CollectionFlow).where(
                (CollectionFlow.flow_id == flow_uuid)
                | (CollectionFlow.id == flow_uuid),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            logger.warning(
                safe_log_format(
                    "Collection flow not found: flow_id={flow_id}, "
                    "engagement_id={engagement_id}",
                    flow_id=flow_id,
                    engagement_id=context.engagement_id,
                )
            )
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Collection flow not found",
                    "flow_id": flow_id,
                    "message": "The requested collection flow does not exist or has been deleted",
                },
            )

        # Query actual application count and list from collection_flow_applications table
        from sqlalchemy import func
        from app.models.canonical_applications.collection_flow_app import (
            CollectionFlowApplication,
        )

        app_count_result = await db.execute(
            select(func.count(CollectionFlowApplication.id)).where(
                CollectionFlowApplication.collection_flow_id == collection_flow.flow_id
            )
        )
        app_count = app_count_result.scalar() or 0

        # Query full application details for UUID-based frontend lookups (Issue #762)
        apps_result = await db.execute(
            select(CollectionFlowApplication).where(
                CollectionFlowApplication.collection_flow_id == collection_flow.flow_id
            )
        )
        applications = apps_result.scalars().all()

        # Build applications list with asset_id and application_name
        applications_data = [
            {
                "asset_id": str(app.asset_id) if app.asset_id else None,
                "application_name": app.application_name,
            }
            for app in applications
        ]

        # Build collection_metrics with actual data
        collection_metrics = {
            "platforms_detected": app_count,
            "data_collected": app_count,  # Assume all apps have data collected
            "gaps_resolved": 0,  # Default since resolution tracking isn't implemented
        }

        return collection_serializers.serialize_collection_flow(
            collection_flow,
            collection_metrics=collection_metrics,
            applications=applications_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error getting collection flow: flow_id={flow_id}, error={e}",
                flow_id=flow_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
