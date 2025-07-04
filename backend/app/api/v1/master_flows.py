"""
Master Flow Coordination API Endpoints
Task 5.2.1: API endpoints for cross-phase asset queries and master flow analytics
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.schemas.asset_schemas import AssetResponse
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Helper function to get demo context for testing
async def get_current_user_context(user_id: str = Depends(get_current_user_id)):
    """
    Get user context with client_account_id and engagement_id.
    Uses demo values for testing purposes.
    """
    return {
        "user_id": user_id,
        "client_account_id": "11111111-1111-1111-1111-111111111111",
        "engagement_id": "22222222-2222-2222-2222-222222222222"
    }

router = APIRouter(prefix="/master-flows", tags=["Master Flow Coordination"])


class MasterFlowSummaryResponse(BaseModel):
    """Master flow summary response model"""
    master_flow_id: str
    total_assets: int
    phases: Dict[str, int]
    asset_types: Dict[str, int]
    strategies: Dict[str, int]
    status_distribution: Dict[str, int]


class CrossPhaseAnalyticsResponse(BaseModel):
    """Cross-phase analytics response model"""
    master_flows: Dict[str, Dict[str, Any]]
    phase_transitions: Dict[str, int]
    quality_by_phase: Dict[str, Dict[str, Any]]


class MasterFlowCoordinationResponse(BaseModel):
    """Master flow coordination summary response"""
    total_discovery_flows: int
    flows_with_master_coordination: int
    unique_master_flows: int
    coordination_percentage: float
    phase_distribution: Dict[str, int]


class DiscoveryFlowResponse(BaseModel):
    """Simple discovery flow response for master flow API"""
    id: str
    flow_id: str
    client_account_id: str
    engagement_id: str
    flow_name: Optional[str] = None
    status: str
    progress_percentage: float
    master_flow_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/{master_flow_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_master_flow(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
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
        raise HTTPException(status_code=500, detail=f"Error retrieving assets: {str(e)}")


@router.get("/{master_flow_id}/summary", response_model=MasterFlowSummaryResponse)
async def get_master_flow_summary(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
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
        raise HTTPException(status_code=500, detail=f"Error retrieving master flow summary: {str(e)}")


@router.get("/{master_flow_id}/discovery-flow", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_by_master(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
) -> DiscoveryFlowResponse:
    """Get discovery flow associated with a master flow"""
    
    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")
    
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    discovery_repo = DiscoveryFlowRepository(db, client_account_id, engagement_id, user_id=current_user.get("user_id"))
    
    try:
        discovery_flow = await discovery_repo.get_by_master_flow_id(master_flow_id)
        if not discovery_flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found for master flow")
        
        return DiscoveryFlowResponse.from_orm(discovery_flow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving discovery flow: {str(e)}")


@router.get("/analytics/cross-phase", response_model=CrossPhaseAnalyticsResponse)
async def get_cross_phase_analytics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
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
        raise HTTPException(status_code=500, detail=f"Error retrieving cross-phase analytics: {str(e)}")


@router.get("/coordination/summary", response_model=MasterFlowCoordinationResponse)
async def get_master_flow_coordination_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
) -> MasterFlowCoordinationResponse:
    """Get master flow coordination summary"""
    
    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")
    
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    discovery_repo = DiscoveryFlowRepository(db, client_account_id, engagement_id, user_id=current_user.get("user_id"))
    
    try:
        summary = await discovery_repo.get_master_flow_coordination_summary()
        return MasterFlowCoordinationResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving coordination summary: {str(e)}")


@router.get("/phase/{phase}/assets", response_model=List[AssetResponse])
async def get_assets_by_phase(
    phase: str,
    current_phase: bool = Query(True, description="If true, filter by current_phase; if false, filter by source_phase"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
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
        raise HTTPException(status_code=500, detail=f"Error retrieving assets by phase: {str(e)}")


@router.get("/multi-phase/assets", response_model=List[AssetResponse])
async def get_multi_phase_assets(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
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
        raise HTTPException(status_code=500, detail=f"Error retrieving multi-phase assets: {str(e)}")


@router.post("/{discovery_flow_id}/transition-to-assessment")
async def transition_to_assessment_phase(
    discovery_flow_id: str,
    assessment_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Prepare discovery flow for assessment phase transition"""
    
    client_account_id = current_user.get("client_account_id")
    engagement_id = current_user.get("engagement_id")
    
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    discovery_repo = DiscoveryFlowRepository(db, client_account_id, engagement_id, user_id=current_user.get("user_id"))
    
    try:
        success = await discovery_repo.transition_to_assessment_phase(discovery_flow_id, assessment_flow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Discovery flow not found or transition failed")
        
        return {
            "success": True,
            "discovery_flow_id": discovery_flow_id,
            "assessment_flow_id": assessment_flow_id,
            "message": "Discovery flow prepared for assessment phase transition"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transitioning to assessment phase: {str(e)}")


@router.put("/{asset_id}/phase-progression")
async def update_asset_phase_progression(
    asset_id: int,
    new_phase: str,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Update asset phase progression with tracking"""
    
    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    asset_repo = AssetRepository(db, client_account_id)
    
    try:
        success = await asset_repo.update_phase_progression(asset_id, new_phase, notes)
        
        if not success:
            raise HTTPException(status_code=404, detail="Asset not found or update failed")
        
        return {
            "success": True,
            "asset_id": asset_id,
            "new_phase": new_phase,
            "notes": notes,
            "message": "Asset phase progression updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating phase progression: {str(e)}")


@router.delete("/{flow_id}")
async def delete_master_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """Delete a master flow and all associated data"""
    
    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    # Special handling for placeholder flows
    if flow_id.startswith("placeholder-"):
        logger.info(f"Deleting placeholder flow {flow_id}")
        return {
            "success": True,
            "flow_id": flow_id,
            "message": "Placeholder flow deleted successfully"
        }
    
    # Import the repository for master flow operations
    from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
    
    extensions_repo = CrewAIFlowStateExtensionsRepository(db, client_account_id)
    
    try:
        # Delete from master flow table (this should cascade to related tables)
        success = await extensions_repo.delete_master_flow(flow_id)
        
        if success:
            await db.commit()
            logger.info(f"✅ Master flow {flow_id} deleted successfully")
            return {
                "success": True,
                "flow_id": flow_id,
                "message": "Master flow deleted successfully"
            }
        else:
            logger.warning(f"Master flow {flow_id} not found or already deleted")
            return {
                "success": True,
                "flow_id": flow_id,
                "message": "Flow not found or already deleted"
            }
            
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to delete master flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}") 