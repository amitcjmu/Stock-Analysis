"""
Collection Flow Delete Command Operations
Delete operations for collection flows including single flow deletion,
cleanup of old flows, and batch deletion operations.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import (
    COLLECTION_DELETE_ROLES,
    require_role,
)
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
)

logger = logging.getLogger(__name__)


async def delete_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    force: bool = False,
) -> Dict[str, Any]:
    """Delete a collection flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context
        force: Force delete even if flow is active

    Returns:
        Dictionary with deletion status

    Raises:
        HTTPException: If flow not found or deletion fails
    """
    require_role(current_user, COLLECTION_DELETE_ROLES, "delete collection flows")

    try:
        # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
        flow_uuid = UUID(flow_id)
        result = await db.execute(
            select(CollectionFlow).where(
                (CollectionFlow.flow_id == flow_uuid)
                | (CollectionFlow.id == flow_uuid),
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        await db.delete(collection_flow)
        await db.commit()

        logger.info(
            safe_log_format(
                "Deleted collection flow: flow_id={flow_id}",
                flow_id=flow_id,
            )
        )

        return {
            "status": "success",
            "message": "Collection flow deleted successfully",
            "flow_id": flow_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error deleting collection flow: flow_id={flow_id}, error={e}",
                flow_id=flow_id,
                e=e,
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def cleanup_flows(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
    days_old: int = 30,
) -> Dict[str, Any]:
    """Clean up old completed/failed collection flows.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context
        days_old: Days old threshold for cleanup

    Returns:
        Dictionary with cleanup results

    Raises:
        HTTPException: If cleanup fails
    """
    require_role(current_user, COLLECTION_DELETE_ROLES, "cleanup collection flows")

    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

        # Find flows to clean up
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.in_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.FAILED.value,
                    ]
                ),
                CollectionFlow.updated_at < cutoff_date,
            )
        )
        flows_to_delete = result.scalars().all()

        deleted_count = 0
        for flow in flows_to_delete:
            await db.delete(flow)
            deleted_count += 1

        await db.commit()

        logger.info(
            safe_log_format(
                "Cleaned up {count} collection flows older than {days} days",
                count=deleted_count,
                days=days_old,
            )
        )

        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} flows",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        logger.error(safe_log_format("Error cleaning up flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def batch_delete_flows(
    flow_ids: List[str],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Delete multiple collection flows in batch.

    Args:
        flow_ids: List of collection flow IDs
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with batch deletion results

    Raises:
        HTTPException: If batch deletion fails
    """
    require_role(current_user, COLLECTION_DELETE_ROLES, "delete collection flows")

    try:
        deleted_flows = []
        failed_deletions = []

        for flow_id in flow_ids:
            try:
                # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
                flow_uuid = UUID(flow_id)
                result = await db.execute(
                    select(CollectionFlow).where(
                        (CollectionFlow.flow_id == flow_uuid)
                        | (CollectionFlow.id == flow_uuid),
                        CollectionFlow.client_account_id == context.client_account_id,
                        CollectionFlow.engagement_id == context.engagement_id,
                    )
                )
                collection_flow = result.scalar_one_or_none()

                if collection_flow:
                    await db.delete(collection_flow)
                    deleted_flows.append(flow_id)
                else:
                    failed_deletions.append(
                        {"flow_id": flow_id, "reason": "Flow not found"}
                    )

            except Exception as e:
                failed_deletions.append({"flow_id": flow_id, "reason": str(e)})

        await db.commit()

        logger.info(
            safe_log_format(
                "Batch deleted {count} collection flows",
                count=len(deleted_flows),
            )
        )

        return {
            "status": "success",
            "message": f"Deleted {len(deleted_flows)} flows",
            "deleted_flows": deleted_flows,
            "failed_deletions": failed_deletions,
            "total_requested": len(flow_ids),
            "total_deleted": len(deleted_flows),
            "total_failed": len(failed_deletions),
        }

    except Exception as e:
        logger.error(safe_log_format("Error in batch delete flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
