"""
Collection Batch Operations
Handles batch operations for collection flows including cleanup and batch deletion.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.core.context import RequestContext
from app.models import User
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


async def cleanup_flows(
    expiration_hours: int,
    dry_run: bool,
    include_failed: bool,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Clean up expired collection flows."""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=expiration_hours)

        # Build query for expired flows
        conditions = [
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.updated_at < cutoff_time,
        ]

        # Include specific statuses
        status_conditions = [CollectionFlow.status.in_(["pending", "in_progress"])]
        if include_failed:
            status_conditions.append(CollectionFlow.status == "failed")

        conditions.append(and_(*status_conditions))

        # Get flows to clean up
        result = await db.execute(
            select(CollectionFlow)
            .where(*conditions)
            .options(selectinload(CollectionFlow.questionnaire_responses))
        )
        flows = result.scalars().all()

        if dry_run:
            return {
                "dry_run": True,
                "flows_to_cleanup": len(flows),
                "flows": [
                    {
                        "id": str(flow.flow_id),
                        "status": flow.status,
                        "created_at": flow.created_at.isoformat(),
                        "updated_at": flow.updated_at.isoformat(),
                    }
                    for flow in flows
                ],
            }

        # Delete flows
        deleted_count = 0
        for flow in flows:
            db.delete(flow)
            deleted_count += 1

        await db.commit()

        return {
            "dry_run": False,
            "flows_deleted": deleted_count,
            "message": f"Successfully cleaned up {deleted_count} expired flows",
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to cleanup flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup flows: {e}")


async def batch_delete_flows(
    flow_ids: List[str],
    force: bool,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Batch delete multiple collection flows."""
    try:
        if not flow_ids:
            raise HTTPException(status_code=400, detail="No flow IDs provided")

        # Get all flows
        result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id.in_(flow_ids))
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .options(selectinload(CollectionFlow.questionnaire_responses))
        )
        flows = result.scalars().all()

        if len(flows) != len(flow_ids):
            found_ids = {str(flow.flow_id) for flow in flows}
            missing_ids = set(flow_ids) - found_ids
            if missing_ids:
                logger.warning(f"Some flows not found: {missing_ids}")

        # Check if any flows are active
        if not force:
            active_flows = [
                flow for flow in flows if flow.status in ["in_progress", "processing"]
            ]
            if active_flows:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete {len(active_flows)} active flows without force flag",
                )

        # Delete flows
        deleted_count = 0
        deleted_ids = []

        for flow in flows:
            db.delete(flow)
            deleted_count += 1
            deleted_ids.append(str(flow.flow_id))

        await db.commit()

        logger.info(
            f"Batch deleted {deleted_count} collection flows for engagement {context.engagement_id}"
        )

        return {
            "deleted_count": deleted_count,
            "deleted_ids": deleted_ids,
            "message": f"Successfully deleted {deleted_count} collection flows",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to batch delete flows: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to batch delete flows: {e}"
        )
