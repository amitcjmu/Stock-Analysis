"""
Admin Flow Management Endpoints

Provides administrative functions for managing stuck or stale flows.
Per Bug #651: Manual cleanup of flows stuck in intermediate phases.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db
from app.core.context import RequestContext, get_current_context

# from app.models.collection_flow import CollectionFlow  # REMOVED - CollectionFlow was removed
try:
    from app.models.collection_flow import CollectionFlow
except ImportError:
    CollectionFlow = None
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/flows/cleanup-stale", response_model=Dict[str, Any])
async def cleanup_stale_flows(
    hours_threshold: int = Query(
        6,
        description="Mark flows as completed if no activity for this many hours",
        ge=1,
        le=168,  # Max 1 week
    ),
    dry_run: bool = Query(
        False,
        description="Preview which flows would be cleaned up without making changes",
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """
    Clean up flows stuck in intermediate phases for extended periods.

    This endpoint identifies flows that haven't been updated in X hours and are still
    in 'running' or 'paused' status, then marks them as 'completed'.

    **Use Cases**:
    - Flows stuck in questionnaire_generation due to stub implementation
    - Flows abandoned by users mid-workflow
    - Flows blocked by transient errors that were never retried

    **Safety**:
    - Tenant-scoped: Only affects flows for the authenticated client_account_id
    - Dry-run mode: Preview changes before applying
    - Configurable threshold: Adjust based on expected flow duration

    **Args**:
    - hours_threshold: Only clean flows older than this (default: 6 hours)
    - dry_run: If True, return list of flows that would be cleaned without changing them

    **Returns**:
    - cleaned_flows: Number of flows marked as completed
    - flow_ids: List of flow IDs that were (or would be) cleaned
    - dry_run: Whether this was a preview or actual cleanup
    """
    logger.info(
        f"Admin cleanup requested: threshold={hours_threshold}h, dry_run={dry_run}, "
        f"client={context.client_account_id}, engagement={context.engagement_id}"
    )

    cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

    # Find stuck collection flows - REMOVED: CollectionFlow was removed
    stuck_collection_flows = []
    if CollectionFlow is not None:
        collection_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.status.in_(["running", "paused"]))
            .where(CollectionFlow.updated_at < cutoff_time)
            .where(CollectionFlow.client_account_id == context.client_account_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
        )
        stuck_collection_flows = collection_result.scalars().all()

    # Find stuck master flows
    master_flow_result = await db.execute(
        select(CrewAIFlowStateExtensions)
        .where(CrewAIFlowStateExtensions.flow_status.in_(["running", "paused"]))
        .where(CrewAIFlowStateExtensions.updated_at < cutoff_time)
        .where(CrewAIFlowStateExtensions.client_account_id == context.client_account_id)
        .where(CrewAIFlowStateExtensions.engagement_id == context.engagement_id)
    )
    stuck_master_flows = master_flow_result.scalars().all()

    if dry_run:
        logger.info(
            f"Dry-run: Found {len(stuck_collection_flows)} stuck collection flows "
            f"and {len(stuck_master_flows)} stuck master flows"
        )
        return {
            "dry_run": True,
            "cleaned_flows": 0,
            "would_clean": len(stuck_collection_flows) + len(stuck_master_flows),
            "collection_flow_ids": [str(f.flow_id) for f in stuck_collection_flows],
            "master_flow_ids": [str(f.flow_id) for f in stuck_master_flows],
            "cutoff_time": cutoff_time.isoformat(),
        }

    # Actually clean up flows - use bulk updates for efficiency
    cleaned_collection_ids = [str(f.flow_id) for f in stuck_collection_flows]
    for flow in stuck_collection_flows:
        logger.info(
            f"Cleaning up stuck collection flow {flow.flow_id} "
            f"(phase: {flow.current_phase}, stale since: {flow.updated_at})"
        )

    if cleaned_collection_ids and CollectionFlow is not None:
        await db.execute(
            update(CollectionFlow)
            .where(CollectionFlow.flow_id.in_(cleaned_collection_ids))
            .values(
                status="completed",
                current_phase="completed",
                updated_at=datetime.utcnow(),
            )
        )

    cleaned_master_ids = [str(f.flow_id) for f in stuck_master_flows]
    for flow in stuck_master_flows:
        logger.info(
            f"Cleaning up stuck master flow {flow.flow_id} "
            f"(phase: {flow.current_phase}, stale since: {flow.updated_at})"
        )

    if cleaned_master_ids:
        await db.execute(
            update(CrewAIFlowStateExtensions)
            .where(CrewAIFlowStateExtensions.flow_id.in_(cleaned_master_ids))
            .values(
                flow_status="completed",
                current_phase="completed",
                updated_at=datetime.utcnow(),
            )
        )

    await db.commit()

    total_cleaned = len(cleaned_collection_ids) + len(cleaned_master_ids)
    logger.info(f"Successfully cleaned up {total_cleaned} stuck flows")

    return {
        "dry_run": False,
        "cleaned_flows": total_cleaned,
        "collection_flow_ids": cleaned_collection_ids,
        "master_flow_ids": cleaned_master_ids,
        "cutoff_time": cutoff_time.isoformat(),
    }
