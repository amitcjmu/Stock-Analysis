"""
Master Flow Coordination API Endpoints
Task 5.2.1: API endpoints for cross-phase asset queries and master flow analytics
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.api.v1.master_flows_schemas import (
    CrossPhaseAnalyticsResponse,
    DiscoveryFlowResponse,
    MasterFlowCoordinationResponse,
    MasterFlowSummaryResponse,
)
from app.api.v1.master_flows_service import MasterFlowService
from app.core.database import get_db
from app.models import User
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.schemas.asset_schemas import AssetResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper function to get user context with proper authentication
async def get_current_user_context(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Get user context with client_account_id and engagement_id from authenticated user.
    """
    service = UserService(db)
    user_context = await service.get_user_context(current_user)

    return {
        "user_id": str(current_user.id),
        "client_account_id": (
            str(user_context.client.id) if user_context.client else None
        ),
        "engagement_id": (
            str(user_context.engagement.id) if user_context.engagement else None
        ),
    }


# Static routes first (no path parameters)


@router.get("/analytics/cross-phase", response_model=CrossPhaseAnalyticsResponse)
async def get_cross_phase_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> CrossPhaseAnalyticsResponse:
    """Get analytics across all phases and master flows"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        analytics = await asset_repo.get_cross_phase_analytics()
        return CrossPhaseAnalyticsResponse(**analytics)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving cross-phase analytics: {str(e)}"
        )


@router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_master_flows(
    flow_type: Optional[str] = Query(
        None,
        alias="flow_type",  # Accept snake_case from frontend
        description="Filter by flow type (discovery, assessment, planning, execution, etc.)",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[Dict[str, Any]]:
    """Get all active master flows across all flow types"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.get_active_master_flows(flow_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving active master flows: {str(e)}"
        )


@router.get("/coordination/summary", response_model=MasterFlowCoordinationResponse)
async def get_master_flow_coordination_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> MasterFlowCoordinationResponse:
    """Get master flow coordination summary"""

    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    discovery_repo = DiscoveryFlowRepository(
        db, client_account_id, engagement_id, user_id=current_user.get("user_id")
    )

    try:
        summary = await discovery_repo.get_master_flow_coordination_summary()
        return MasterFlowCoordinationResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving coordination summary: {str(e)}"
        )


@router.get("/phase/{phase}/assets", response_model=List[AssetResponse])
async def get_assets_by_phase(
    phase: str,
    current_phase: bool = Query(
        True,
        description="If true, filter by current_phase; if false, filter by source_phase",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[AssetResponse]:
    """Get assets by phase (current or source)"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        if current_phase:
            assets = await asset_repo.get_by_current_phase(phase)
        else:
            assets = await asset_repo.get_by_source_phase(phase)

        return [AssetResponse.from_orm(asset) for asset in assets]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving assets by phase: {str(e)}"
        )


@router.get("/multi-phase/assets", response_model=List[AssetResponse])
async def get_multi_phase_assets(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[AssetResponse]:
    """Get assets that have progressed through multiple phases"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        assets = await asset_repo.get_multi_phase_assets()
        return [AssetResponse.from_orm(asset) for asset in assets]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving multi-phase assets: {str(e)}"
        )


# Dynamic routes (with path parameters) - must come after static routes


@router.get("/{master_flow_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_master_flow(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> List[AssetResponse]:
    """Get all assets for a specific master flow"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        assets = await asset_repo.get_by_master_flow(master_flow_id)
        return [AssetResponse.from_orm(asset) for asset in assets]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving assets: {str(e)}"
        )


@router.get("/{master_flow_id}/summary", response_model=MasterFlowSummaryResponse)
async def get_master_flow_summary(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> MasterFlowSummaryResponse:
    """Get comprehensive summary for a master flow"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    asset_repo = AssetRepository(db, client_account_id)

    try:
        summary = await asset_repo.get_master_flow_summary(master_flow_id)
        return MasterFlowSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving master flow summary: {str(e)}"
        )


@router.get("/{master_flow_id}/discovery-flow", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_by_master(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> DiscoveryFlowResponse:
    """Get discovery flow associated with a master flow"""

    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    discovery_repo = DiscoveryFlowRepository(
        db, client_account_id, engagement_id, user_id=current_user.get("user_id")
    )

    try:
        discovery_flow = await discovery_repo.get_by_master_flow_id(master_flow_id)
        if not discovery_flow:
            raise HTTPException(
                status_code=404, detail="Discovery flow not found for master flow"
            )

        return DiscoveryFlowResponse.from_orm(discovery_flow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving discovery flow: {str(e)}"
        )


@router.post("/{discovery_flow_id}/transition-to-assessment")
async def transition_to_assessment_phase(
    discovery_flow_id: str,
    assessment_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Prepare discovery flow for assessment phase transition"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.transition_to_assessment_phase(
            discovery_flow_id, assessment_flow_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error transitioning to assessment: {str(e)}"
        )


@router.put("/{asset_id}/phase-progression")
async def update_asset_phase_progression(
    asset_id: str,
    new_phase: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Update an asset's phase progression"""

    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.update_asset_phase(asset_id, new_phase)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error updating asset phase: {str(e)}"
        )


@router.delete("/{flow_id}")
async def soft_delete_master_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """
    Soft delete a master flow and mark all its child flows as deleted.
    """
    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=current_user.get("engagement_id"),
        user_id=current_user.get("user_id"),
    )

    try:
        return await service.soft_delete_flow(flow_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting master flow: {str(e)}"
        )
