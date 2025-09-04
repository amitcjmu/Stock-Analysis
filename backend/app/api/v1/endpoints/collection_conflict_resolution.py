"""
Collection Flow Conflict Resolution Endpoints
Handles stuck flows, phase advancement, and flow management operations.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import ManageFlowRequest
from app.api.v1.endpoints import collection_crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flows/fix-stuck")
async def fix_stuck_collection_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Fix collection flows stuck in platform_detection phase.

    This endpoint identifies collection flows that have completed platform detection
    but are stuck waiting for the next phase to be triggered. It automatically
    advances them to the automated_collection phase.
    """
    from app.api.v1.endpoints.collection_phase_progression import (
        fix_stuck_collection_flows as fix_flows,
    )

    return await fix_flows(db, current_user, context)


@router.post("/flows/{flow_id}/advance/{target_phase}")
async def advance_collection_flow_phase(
    flow_id: str,
    target_phase: str,
    force: bool = Query(False, description="Force advancement ignoring prerequisites"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Manually advance a collection flow to a specific phase.

    Valid target phases: automated_collection, gap_analysis, questionnaire_generation,
    manual_collection, data_validation, finalization
    """
    from app.api.v1.endpoints.collection_phase_progression import (
        advance_collection_flow_phase as advance_phase,
    )

    return await advance_phase(flow_id, target_phase, force, db, current_user, context)


@router.get("/flows/stuck-analysis")
async def get_stuck_collection_flows_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Analyze collection flows that might be stuck without making changes."""
    from app.api.v1.endpoints.collection_phase_progression import (
        get_stuck_collection_flows_analysis as get_analysis,
    )

    return await get_analysis(db, current_user, context)


@router.get("/flows/analysis")
async def analyze_existing_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Analyze existing collection flows to resolve creation conflicts.

    This endpoint is called when a 409 conflict occurs during flow creation
    to provide users with options for handling existing flows.
    """
    from app.api.v1.endpoints.collection_flow_lifecycle import (
        CollectionFlowLifecycleManager,
    )

    lifecycle_manager = CollectionFlowLifecycleManager(db, context)
    return await lifecycle_manager.analyze_existing_flows(str(current_user.id))


@router.post("/flows/manage")
async def manage_existing_flow(
    request: ManageFlowRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Manage existing flows (cancel, complete, etc.) to resolve conflicts.

    Actions:
    - 'cancel_flow': Cancel a specific flow (requires flow_id)
    - 'cancel_multiple': Cancel multiple flows (requires flow_ids)
    - 'complete_flow': Mark a flow as complete (requires flow_id)
    - 'cancel_stale': Cancel all stale flows
    - 'auto_complete': Auto-complete eligible flows
    """
    from app.api.v1.endpoints.collection_flow_lifecycle import (
        CollectionFlowLifecycleManager,
    )

    lifecycle_manager = CollectionFlowLifecycleManager(db, context)

    if request.action == "cancel_flow":
        if not request.flow_id:
            raise HTTPException(
                status_code=400,
                detail="flow_id is required for 'cancel_flow' action",
            )
        return await collection_crud.delete_flow(
            flow_id=request.flow_id,
            force=True,
            db=db,
            current_user=current_user,
            context=context,
        )
    elif request.action == "cancel_multiple":
        if not request.flow_ids:
            raise HTTPException(
                status_code=400,
                detail="flow_ids is required for 'cancel_multiple' action",
            )
        return await collection_crud.batch_delete_flows(
            flow_ids=request.flow_ids,
            force=True,
            db=db,
            current_user=current_user,
            context=context,
        )
    elif request.action == "complete_flow":
        if not request.flow_id:
            raise HTTPException(
                status_code=400,
                detail="flow_id is required for 'complete_flow' action",
            )
        return await lifecycle_manager.complete_single_flow(request.flow_id)
    elif request.action == "cancel_stale":
        return await lifecycle_manager.cancel_stale_flows()
    elif request.action == "auto_complete":
        return await lifecycle_manager.auto_complete_eligible_flows()
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid action '{request.action}'. Valid actions are: "
                "cancel_flow, cancel_multiple, complete_flow, "
                "cancel_stale, auto_complete"
            ),
        )
