"""
Flow Status Sync Debug Endpoints

Provides endpoints for testing and debugging the ADR-012 flow status synchronization system.
These endpoints should be used for development and testing purposes.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.flow_status_sync import FlowStatusSyncService
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

router = APIRouter()


@router.post("/flows/{flow_id}/start-atomic")
async def start_flow_atomic(
    flow_id: str,
    flow_type: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Start a flow with atomic status synchronization

    Tests ADR-012 atomic updates for critical operations
    """
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.start_flow_with_atomic_sync(flow_id, flow_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/pause-atomic")
async def pause_flow_atomic(
    flow_id: str,
    flow_type: str,
    reason: str = "user_requested",
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Pause a flow with atomic status synchronization

    Tests ADR-012 atomic updates for critical operations
    """
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.pause_flow_with_atomic_sync(
            flow_id, flow_type, reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/resume-atomic")
async def resume_flow_atomic(
    flow_id: str,
    flow_type: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Resume a flow with atomic status synchronization

    Tests ADR-012 atomic updates for critical operations
    """
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.resume_flow_with_atomic_sync(flow_id, flow_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/reconcile")
async def reconcile_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Reconcile master flow status using MFO sync agent

    Tests ADR-012 sync agent functionality
    """
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.reconcile_flow_status(flow_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/health-monitor")
async def monitor_flow_health(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Monitor flow health and identify inconsistencies

    Tests ADR-012 health monitoring functionality
    """
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.monitor_flow_health()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/consistency-check")
async def check_flow_consistency(
    flow_id: str,
    flow_type: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Check consistency between master and child flow status

    Tests ADR-012 consistency validation
    """
    try:
        sync_service = FlowStatusSyncService(db, context)
        result = await sync_service.validate_flow_consistency(flow_id, flow_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/recover")
async def recover_from_partial_update(
    flow_id: str,
    flow_type: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Recover from partial status updates

    Tests ADR-012 recovery mechanisms
    """
    try:
        sync_service = FlowStatusSyncService(db, context)
        result = await sync_service.recover_from_partial_update(flow_id, flow_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/operational-status")
async def update_operational_status(
    flow_id: str,
    flow_type: str,
    status: str,
    metadata: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Update operational status via event-driven sync

    Tests ADR-012 event-driven updates for non-critical operations
    """
    try:
        sync_service = FlowStatusSyncService(db, context)
        await sync_service.update_operational_status(
            flow_id, flow_type, status, metadata
        )
        return {"success": True, "message": "Operational status updated via event"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/debug-status")
async def debug_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Debug flow status - shows both master and child flow status

    Useful for debugging ADR-012 implementation
    """
    try:
        from app.repositories.crewai_flow_state_extensions_repository import (
            CrewAIFlowStateExtensionsRepository,
        )
        from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

        # Get master flow status
        master_repo = CrewAIFlowStateExtensionsRepository(
            db, context.client_account_id, context.engagement_id, context.user_id
        )
        master_flow = await master_repo.get_by_flow_id(flow_id)

        # Get child flow status (assuming discovery for now)
        discovery_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id, context.user_id
        )
        child_flow = await discovery_repo.get_by_flow_id(flow_id)

        return {
            "flow_id": flow_id,
            "master_flow": {
                "exists": master_flow is not None,
                "status": master_flow.flow_status if master_flow else None,
                "type": master_flow.flow_type if master_flow else None,
                "updated_at": (
                    master_flow.updated_at.isoformat()
                    if master_flow and master_flow.updated_at
                    else None
                ),
            },
            "child_flow": {
                "exists": child_flow is not None,
                "status": child_flow.status if child_flow else None,
                "phase": child_flow.current_phase if child_flow else None,
                "progress": child_flow.progress_percentage if child_flow else None,
                "updated_at": (
                    child_flow.updated_at.isoformat()
                    if child_flow and child_flow.updated_at
                    else None
                ),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
