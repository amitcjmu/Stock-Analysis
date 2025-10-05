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
    CollectionFlowCreate,
    CollectionFlowResponse,
    CollectionFlowUpdate,
    CollectionApplicationSelectionRequest,
)

# Import all modular functions to maintain backward compatibility
from app.api.v1.endpoints import collection_crud
from app.api.v1.endpoints.collection_batch_operations import (
    cleanup_flows as batch_cleanup_flows,
    batch_delete_flows as batch_delete,
)
from app.api.v1.endpoints.collection_applications import update_flow_applications
from app.api.v1.endpoints.collection_transition import router as transition_router
from app.api.v1.endpoints.collection_conflict_resolution import (
    router as conflict_resolution_router,
)
from app.api.v1.endpoints.collection_questionnaires import (
    router as questionnaires_router,
)
from app.api.v1.endpoints.collection_bulk_import import process_bulk_import

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


@router.get("/flows", response_model=List[CollectionFlowResponse])
async def get_all_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[CollectionFlowResponse]:
    """Get all collection flows for the current engagement (including completed ones)"""
    return await collection_crud.get_all_flows(
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
        flow_update=update_data,  # Fixed: parameter name should be flow_update
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


@router.get("/flows/{flow_id}/gaps", response_model=List[Dict[str, Any]])
async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[Dict[str, Any]]:
    """Get gap analysis results for a collection flow"""
    return await collection_crud.get_collection_gaps(
        flow_id=flow_id,
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


@router.post("/flows/{flow_id}/applications", response_model=Dict[str, Any])
async def update_collection_flow_applications(
    flow_id: str,
    request_data: CollectionApplicationSelectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Update collection flow with selected applications for questionnaire generation.

    This endpoint allows users to specify which applications should be included
    in a collection flow, enabling targeted questionnaire generation and gap analysis.

    SECURITY: Validates that all selected applications belong to the current user's engagement.
    """
    return await update_flow_applications(
        flow_id=flow_id,
        request_data=request_data,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/bulk-import")
async def bulk_import_collection_data(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Process bulk CSV import for Collection flow.

    This endpoint:
    1. Validates the Collection flow exists and is in correct state
    2. Validates the CSV file using ImportStorageHandler
    3. Processes each row through the Collection questionnaire system
    4. Creates/updates assets in the database
    5. Triggers gap analysis for all imported assets

    Args:
        flow_id: The Collection flow ID to import data into
        file_path: Path to the uploaded CSV file
        asset_type: Type of assets being imported (applications/servers/databases/devices)

    Returns:
        Dict with import results including processed count and any errors
    """
    # Extract parameters from request body
    flow_id = request.get("flow_id")
    asset_type = request.get("asset_type", "applications")
    csv_data = request.get("csv_data", [])

    # Validate required parameters
    if not flow_id:
        raise HTTPException(
            status_code=400, detail="flow_id is required for bulk import operation"
        )

    # Process directly with CSV data if provided, otherwise use file_path
    if csv_data:
        return await process_bulk_import(
            flow_id=flow_id,
            file_path=None,
            csv_data=csv_data,
            asset_type=asset_type,
            db=db,
            current_user=current_user,
            context=context,
        )
    else:
        # Legacy path for file-based import
        file_path = request.get("file_path")
        return await process_bulk_import(
            flow_id=flow_id,
            file_path=file_path,
            csv_data=None,
            asset_type=asset_type,
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


@router.post("/flows/{flow_id}/rerun-gap-analysis")
async def rerun_gap_analysis(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Re-run gap analysis for a collection flow.

    Re-computes gap summary and regenerates questionnaires based on
    current application selection and collection progress.

    Returns:
        202 Accepted with estimated completion time and polling information
    """
    return await collection_crud.rerun_gap_analysis(
        flow_id=flow_id,
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
    return await batch_cleanup_flows(
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
    """Batch delete multiple collection flows"""
    return await batch_delete(
        flow_ids=flow_ids,
        force=force,
        db=db,
        current_user=current_user,
        context=context,
    )


# Include modular routers
router.include_router(questionnaires_router)
router.include_router(conflict_resolution_router)
router.include_router(transition_router)

# Export router for backward compatibility
__all__ = ["router"]
