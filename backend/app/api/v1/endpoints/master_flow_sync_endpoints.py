"""
Master Flow Synchronization API Endpoints

Provides endpoints for master flow synchronization operations,
addressing Section 8 of the validation checklist.
"""

import logging
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.deps import get_db, get_current_user, get_request_context
from app.core.rbac_utils import (
    COLLECTION_READ_ROLES,
    COLLECTION_WRITE_ROLES,
    require_role,
)
from app.models import User
from app.models.collection_flow import CollectionFlow
from app.models.assessment_flow.core_models import AssessmentFlow
from app.services.master_flow_sync_service import (
    MasterFlowSyncService,
    FlowSyncStatus,
    SyncResult,
)
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/collection/{flow_id}/sync-status")
async def get_collection_sync_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> FlowSyncStatus:
    """
    Get synchronization status for a collection flow.

    Returns detailed information about master-child flow synchronization
    including status matches, progress alignment, and any issues.
    """
    require_role(current_user, COLLECTION_READ_ROLES, "get collection sync status")

    try:
        flow_uuid = UUID(flow_id)

        # Get collection flow
        result = await db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.flow_id == flow_uuid,
                    CollectionFlow.client_account_id == context.client_account_id,
                    CollectionFlow.engagement_id == context.engagement_id,
                )
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Initialize sync service and get status
        sync_service = MasterFlowSyncService(db, context)
        sync_status = await sync_service.synchronize_collection_flow(collection_flow)

        return sync_status

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting collection sync status for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sync status check failed: {str(e)}"
        )


@router.post("/collection/{flow_id}/synchronize")
async def synchronize_collection_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> FlowSyncStatus:
    """
    Force synchronization of a collection flow with its master flow.

    This endpoint actively synchronizes the master flow status, progress,
    and phase information with the current child flow state.
    """
    require_role(current_user, COLLECTION_WRITE_ROLES, "synchronize collection flow")

    try:
        flow_uuid = UUID(flow_id)

        # Get collection flow
        result = await db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.flow_id == flow_uuid,
                    CollectionFlow.client_account_id == context.client_account_id,
                    CollectionFlow.engagement_id == context.engagement_id,
                )
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Perform synchronization
        sync_service = MasterFlowSyncService(db, context)
        sync_status = await sync_service.synchronize_collection_flow(collection_flow)

        # Commit changes
        await db.commit()

        logger.info(f"Collection flow {flow_id} synchronized with master flow")

        return sync_status

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error synchronizing collection flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@router.get("/assessment/{flow_id}/sync-status")
async def get_assessment_sync_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> FlowSyncStatus:
    """Get synchronization status for an assessment flow."""
    require_role(current_user, COLLECTION_READ_ROLES, "get assessment sync status")

    try:
        flow_uuid = UUID(flow_id)

        # Get assessment flow
        result = await db.execute(
            select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.id == flow_uuid,
                    AssessmentFlow.client_account_id == context.client_account_id,
                    AssessmentFlow.engagement_id == context.engagement_id,
                )
            )
        )
        assessment_flow = result.scalar_one_or_none()

        if not assessment_flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get sync status
        sync_service = MasterFlowSyncService(db, context)
        sync_status = await sync_service.synchronize_assessment_flow(assessment_flow)

        return sync_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessment sync status for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Sync status check failed: {str(e)}"
        )


@router.post("/assessment/{flow_id}/synchronize")
async def synchronize_assessment_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> FlowSyncStatus:
    """Force synchronization of an assessment flow with its master flow."""
    require_role(current_user, COLLECTION_WRITE_ROLES, "synchronize assessment flow")

    try:
        flow_uuid = UUID(flow_id)

        # Get assessment flow
        result = await db.execute(
            select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.id == flow_uuid,
                    AssessmentFlow.client_account_id == context.client_account_id,
                    AssessmentFlow.engagement_id == context.engagement_id,
                )
            )
        )
        assessment_flow = result.scalar_one_or_none()

        if not assessment_flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Perform synchronization
        sync_service = MasterFlowSyncService(db, context)
        sync_status = await sync_service.synchronize_assessment_flow(assessment_flow)

        # Commit changes
        await db.commit()

        logger.info(f"Assessment flow {flow_id} synchronized with master flow")

        return sync_status

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error synchronizing assessment flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")


@router.post("/synchronize-all")
async def synchronize_all_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> SyncResult:
    """
    Synchronize all flows for the current tenant.

    This is a comprehensive synchronization operation that checks all
    collection and assessment flows and ensures they're properly
    synchronized with their master flows.
    """
    require_role(current_user, COLLECTION_WRITE_ROLES, "synchronize all flows")

    try:
        # Perform comprehensive synchronization
        sync_service = MasterFlowSyncService(db, context)
        sync_result = await sync_service.synchronize_all_flows()

        logger.info(
            f"Comprehensive flow synchronization completed for tenant {context.client_account_id}: "
            f"{sync_result.flows_synchronized}/{sync_result.flows_processed} flows synchronized"
        )

        return sync_result

    except Exception as e:
        logger.error(f"Error in comprehensive flow synchronization: {e}")
        raise HTTPException(
            status_code=500, detail=f"Comprehensive synchronization failed: {str(e)}"
        )


@router.get("/sync-summary")
async def get_sync_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get synchronization summary for all flows in the current tenant.

    Provides an overview of synchronization status without performing
    actual synchronization operations.
    """
    require_role(current_user, COLLECTION_READ_ROLES, "get sync summary")

    try:
        sync_service = MasterFlowSyncService(db, context)

        # Get all flows
        collection_flows = await sync_service._get_all_collection_flows()
        assessment_flows = await sync_service._get_all_assessment_flows()

        # Quick sync status check (read-only)
        collection_issues = 0
        assessment_issues = 0
        total_flows = len(collection_flows) + len(assessment_flows)

        for flow in collection_flows:
            sync_status = await sync_service.synchronize_collection_flow(flow)
            if not sync_status.is_synchronized:
                collection_issues += 1

        for flow in assessment_flows:
            sync_status = await sync_service.synchronize_assessment_flow(flow)
            if not sync_status.is_synchronized:
                assessment_issues += 1

        # Don't commit - this is read-only
        await db.rollback()

        summary = {
            "tenant_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "total_flows": total_flows,
            "collection_flows": len(collection_flows),
            "assessment_flows": len(assessment_flows),
            "flows_with_sync_issues": collection_issues + assessment_issues,
            "collection_sync_issues": collection_issues,
            "assessment_sync_issues": assessment_issues,
            "overall_sync_health": (
                "healthy"
                if collection_issues + assessment_issues == 0
                else (
                    "needs_attention"
                    if collection_issues + assessment_issues < 3
                    else "critical"
                )
            ),
            "recommendations": [],
        }

        # Add recommendations based on issues found
        if collection_issues > 0:
            summary["recommendations"].append(
                f"Run synchronization for {collection_issues} collection flows"
            )

        if assessment_issues > 0:
            summary["recommendations"].append(
                f"Run synchronization for {assessment_issues} assessment flows"
            )

        if collection_issues + assessment_issues == 0:
            summary["recommendations"].append("All flows are properly synchronized")

        return summary

    except Exception as e:
        logger.error(f"Error getting sync summary: {e}")
        raise HTTPException(status_code=500, detail=f"Sync summary failed: {str(e)}")
