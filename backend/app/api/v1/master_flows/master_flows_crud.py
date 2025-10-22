"""
Master Flow CRUD Operations API Endpoints
Basic CRUD operations for master flows and related entities
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.master_flows_schemas import DiscoveryFlowResponse, MasterFlowResponse
from app.api.v1.master_flows_service import MasterFlowService
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User
from app.repositories.asset_repository import AssetRepository
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.schemas.asset_schemas import AssetResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{flow_id}", response_model=MasterFlowResponse)
async def get_master_flow_by_id(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
    current_user: User = Depends(get_current_user),
) -> MasterFlowResponse:
    """
    Get master flow by ID (Bug #676 fix).

    Returns 404 if flow not found, instead of 405 Method Not Allowed.
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    try:
        # Validate UUID format
        try:
            UUID(flow_id)  # Validate format only
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="Invalid flow ID format (must be UUID)"
            )

        # Get master flow repository with tenant scoping
        flow_repo = CrewAIFlowStateExtensionsRepository(
            db=db,
            client_account_id=str(client_account_id),
            engagement_id=str(engagement_id) if engagement_id else None,
        )

        # Get flow by ID (tenant-scoped query)
        master_flow = await flow_repo.get_by_flow_id(flow_id)

        if not master_flow:
            raise HTTPException(
                status_code=404,
                detail=f"Master flow {flow_id} not found",
            )

        # Return response using Pydantic model
        return MasterFlowResponse.from_orm(master_flow)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving master flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving master flow: {str(e)}"
        )


@router.get("/{master_flow_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_master_flow(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> List[AssetResponse]:
    """Get all assets for a specific master flow"""

    client_account_id = context.client_account_id
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


@router.get("/{master_flow_id}/discovery-flow", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_by_master(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
    current_user: User = Depends(get_current_user),
) -> DiscoveryFlowResponse:
    """Get discovery flow associated with a master flow"""

    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    discovery_repo = DiscoveryFlowRepository(
        db, client_account_id, engagement_id, user_id=str(current_user.id)
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
    context: RequestContext = Depends(get_current_context_dependency),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Prepare discovery flow for assessment phase transition"""

    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=context.engagement_id,
        user_id=str(current_user.id),
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
    context: RequestContext = Depends(get_current_context_dependency),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update an asset's phase progression"""

    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=context.engagement_id,
        user_id=str(current_user.id),
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
    context: RequestContext = Depends(get_current_context_dependency),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Soft delete a master flow and mark all its child flows as deleted.
    """
    client_account_id = context.client_account_id
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")

    service = MasterFlowService(
        db=db,
        client_account_id=client_account_id,
        engagement_id=context.engagement_id,
        user_id=str(current_user.id),
    )

    try:
        return await service.soft_delete_flow(flow_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting master flow: {str(e)}"
        )
