"""
Collection Flow API Endpoints
Provides API interface for the Adaptive Data Collection System (ADCS)

This module serves as the main router/facade for collection flow operations,
delegating to modular components while maintaining 100% backward compatibility.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
    CollectionFlowCreate,
    CollectionFlowResponse,
    CollectionFlowUpdate,
    CollectionGapAnalysisResponse,
    ManageFlowRequest,
)

# Import all modular functions to maintain backward compatibility
from app.api.v1.endpoints import collection_crud

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flows/from-discovery", response_model=CollectionFlowResponse)
async def create_collection_from_discovery(
    discovery_flow_id: str,
    selected_application_ids: List[str],
    collection_strategy: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Create a Collection flow from Discovery results with selected applications.

    This endpoint enables seamless transition from Discovery to Collection,
    allowing users to select applications from the Discovery inventory for
    detailed data collection and gap analysis.

    Args:
        discovery_flow_id: The Discovery flow ID to transition from
        selected_application_ids: List of application IDs to collect data for
        collection_strategy: Optional configuration for collection approach

    Returns:
        CollectionFlowResponse with the created Collection flow details
    """
    return await collection_crud.create_collection_from_discovery(
        discovery_flow_id=discovery_flow_id,
        selected_application_ids=selected_application_ids,
        collection_strategy=collection_strategy,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/ensure", response_model=CollectionFlowResponse)
async def ensure_collection_flow(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Return an active Collection flow for the engagement, or create one via MFO.

    This enables seamless navigation from Discovery to Collection without users
    needing to manually start a flow. It reuses any non-completed flow; if none
    exist, it creates a new one and returns it immediately.
    """
    return await collection_crud.ensure_collection_flow(
        db=db,
        current_user=current_user,
        context=context,
    )


@router.get("/status", response_model=Dict[str, Any])
async def get_collection_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Get collection flow status for current engagement"""
    return await collection_crud.get_collection_status(
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows", response_model=CollectionFlowResponse)
async def create_collection_flow(
    flow_data: CollectionFlowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Create and start a new collection flow"""
    return await collection_crud.create_collection_flow(
        flow_data=flow_data,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.get("/flows/{flow_id}", response_model=CollectionFlowResponse)
async def get_collection_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Get collection flow details"""
    return await collection_crud.get_collection_flow(
        flow_id=flow_id,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.put("/flows/{flow_id}", response_model=CollectionFlowResponse)
async def update_collection_flow(
    flow_id: str,
    update_data: CollectionFlowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Update collection flow (e.g., provide user input, continue flow)"""
    return await collection_crud.update_collection_flow(
        flow_id=flow_id,
        flow_data=update_data,  # Fixed: parameter name should be flow_data
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/{flow_id}/execute")
async def execute_collection_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Execute a collection flow phase through Master Flow Orchestrator.

    This endpoint triggers actual CrewAI execution of the collection flow,
    enabling phase progression and questionnaire generation.
    """
    return await collection_crud.execute_collection_flow(
        flow_id=flow_id,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.get("/flows/{flow_id}/gaps", response_model=List[CollectionGapAnalysisResponse])
async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[CollectionGapAnalysisResponse]:
    """Get gap analysis results for a collection flow"""
    return await collection_crud.get_collection_gaps(
        flow_id=flow_id,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.get(
    "/flows/{flow_id}/questionnaires",
    response_model=List[AdaptiveQuestionnaireResponse],
)
async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for manual collection"""
    return await collection_crud.get_adaptive_questionnaires(
        flow_id=flow_id,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/{flow_id}/questionnaires/{questionnaire_id}/submit")
async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    responses: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire"""
    return await collection_crud.submit_questionnaire_response(
        flow_id=flow_id,
        questionnaire_id=questionnaire_id,
        responses=responses,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.get("/flows/{flow_id}/readiness")
async def get_collection_readiness(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Read-only readiness and quality summary for a collection flow.

    Returns engagement-scoped readiness counts and validator phase scores for
    collection→discovery, plus quality/confidence stored on the flow.
    """
    return await collection_crud.get_collection_readiness(
        flow_id=flow_id,
        db=db,
        current_user=current_user,
        context=context,
    )


# ========================================
# COLLECTION FLOW LIFECYCLE MANAGEMENT
# ========================================


@router.get("/incomplete", response_model=List[CollectionFlowResponse])
async def get_incomplete_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[CollectionFlowResponse]:
    """Get all incomplete collection flows for the current engagement"""
    return await collection_crud.get_incomplete_flows(
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/{flow_id}/continue")
async def continue_flow(
    flow_id: str,
    resume_context: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Continue/resume a paused or incomplete collection flow"""
    return await collection_crud.continue_flow(
        flow_id=flow_id,
        resume_context=resume_context,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.delete("/flows/{flow_id}")
async def delete_flow(
    flow_id: str,
    force: bool = Query(False, description="Force delete even if flow is active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Delete a collection flow and all related data"""
    return await collection_crud.delete_flow(
        flow_id=flow_id,
        force=force,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/cleanup")
async def cleanup_flows(
    expiration_hours: int = Query(
        72, description="Hours after which flows are considered expired"
    ),
    dry_run: bool = Query(
        True, description="Preview cleanup without actually deleting"
    ),
    include_failed: bool = Query(True, description="Include failed flows in cleanup"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Clean up expired collection flows"""
    return await collection_crud.cleanup_flows(
        expiration_hours=expiration_hours,
        dry_run=dry_run,
        include_failed=include_failed,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/batch-delete")
async def batch_delete_flows(
    flow_ids: List[str],
    force: bool = Query(False, description="Force delete even if flows are active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Delete multiple collection flows in batch"""
    return await collection_crud.batch_delete_flows(
        flow_ids=flow_ids,
        force=force,
        db=db,
        current_user=current_user,
        context=context,
    )


# ========================================
# FLOW CONFLICT RESOLUTION ENDPOINTS
# ========================================


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


# Export router for backward compatibility
__all__ = ["router"]
