"""
Master Flow Coordination API Endpoints
Task 5.2.1: API endpoints for cross-phase asset queries and master flow analytics
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.schemas.asset_schemas import AssetResponse
from pydantic import BaseModel
from datetime import datetime
from app.api.v1.auth.auth_utils import get_current_user
from app.models import User
from app.api.v1.endpoints.context.services.user_service import UserService

logger = logging.getLogger(__name__)

# Helper function to get user context with proper authentication
async def get_current_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user context with client_account_id and engagement_id from authenticated user.
    """
    service = UserService(db)
    user_context = await service.get_user_context(current_user)
    
    return {
        "user_id": str(current_user.id),
        "client_account_id": str(user_context.client.id) if user_context.client else None,
        "engagement_id": str(user_context.engagement.id) if user_context.engagement else None
    }

router = APIRouter(tags=["Master Flow Coordination"])


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
    flow_type_distribution: Dict[str, int]
    master_flow_references: Dict[str, int]
    assessment_readiness: Dict[str, int]
    coordination_metrics: Dict[str, float]
    error: Optional[str] = None


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


# Static routes first (no path parameters)

@router.get("/analytics/cross-phase", response_model=CrossPhaseAnalyticsResponse)
async def get_cross_phase_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context)
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


@router.get("/active", response_model=List[Dict[str, Any]])
async def get_active_master_flows(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context)
) -> List[Dict[str, Any]]:
    """Get all active master flows across all flow types"""
    
    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    try:
        from sqlalchemy import select, and_, or_
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        
        # Query for active master flows
        stmt = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.client_account_id == client_account_id,
                CrewAIFlowStateExtensions.flow_status.notin_(["deleted", "cancelled", "child_flows_deleted"])
            )
        ).order_by(CrewAIFlowStateExtensions.created_at.desc())
        
        result = await db.execute(stmt)
        master_flows = result.scalars().all()
        
        # Convert to response format
        active_flows = []
        for flow in master_flows:
            active_flows.append({
                "master_flow_id": str(flow.flow_id),
                "flow_type": flow.flow_type,
                "flow_name": flow.flow_name,
                "status": flow.flow_status,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                "configuration": flow.flow_configuration or {}
            })
        
        logger.info(f"Found {len(active_flows)} active master flows")
        return active_flows
        
    except Exception as e:
        logger.error(f"Error retrieving active master flows: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving active master flows: {str(e)}")


@router.get("/coordination/summary", response_model=MasterFlowCoordinationResponse)
async def get_master_flow_coordination_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context)
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
    current_user: dict = Depends(get_current_user_context)
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
    current_user: dict = Depends(get_current_user_context)
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


# Dynamic routes (with path parameters) - must come after static routes

@router.get("/{master_flow_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_master_flow(
    master_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context)
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
    current_user: dict = Depends(get_current_user_context)
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
    current_user: dict = Depends(get_current_user_context)
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


@router.post("/{discovery_flow_id}/transition-to-assessment")
async def transition_to_assessment_phase(
    discovery_flow_id: str,
    assessment_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_context)
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
    current_user: dict = Depends(get_current_user_context)
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
    current_user: dict = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Mark master flow and all child flows as deleted (soft delete).
    Maintains complete audit trail for troubleshooting.
    """
    
    client_account_id = current_user.get("client_account_id")
    if not client_account_id:
        raise HTTPException(status_code=400, detail="Client account ID required")
    
    from sqlalchemy import select, update
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.flow_deletion_audit import FlowDeletionAudit
    import uuid as uuid_lib
    import time
    
    start_time = time.time()
    
    try:
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id
        
        # Get the master flow
        stmt = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_uuid,
            CrewAIFlowStateExtensions.client_account_id == client_account_id
        )
        result = await db.execute(stmt)
        master_flow = result.scalar_one_or_none()
        
        if not master_flow:
            # Try to find and delete child flows directly
            child_stmt = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.client_account_id == client_account_id
            )
            child_result = await db.execute(child_stmt)
            child_flow = child_result.scalar_one_or_none()
            
            if child_flow:
                # This is a child flow ID, mark it as deleted
                child_flow.status = "deleted"
                child_flow.updated_at = datetime.utcnow()
                
                # Create audit record
                duration_ms = int((time.time() - start_time) * 1000)
                audit_record = FlowDeletionAudit.create_audit_record(
                    flow_id=str(flow_uuid),
                    client_account_id=str(client_account_id),
                    engagement_id=str(child_flow.engagement_id),
                    user_id=current_user.get("user_id"),
                    deletion_type="user_requested",
                    deletion_method="api",
                    deleted_by=current_user.get("user_id"),
                    deletion_reason="Direct child flow deletion",
                    data_deleted={"flow_type": "discovery", "status": child_flow.status},
                    deletion_impact={"soft_delete": True},
                    cleanup_summary={"child_flow_deleted": True},
                    deletion_duration_ms=duration_ms
                )
                db.add(audit_record)
                await db.commit()
                
                return {
                    "success": True,
                    "flow_id": flow_id,
                    "message": "Child flow marked as deleted",
                    "audit_id": str(audit_record.id)
                }
            
            return {
                "success": False,
                "flow_id": flow_id,
                "message": "Flow not found"
            }
        
        # Prepare deletion data
        deletion_data = {
            "flow_type": master_flow.flow_type,
            "flow_name": master_flow.flow_name,
            "previous_status": master_flow.flow_status,
            "child_flows": []
        }
        
        # Mark all child flows as deleted
        child_flows_deleted = 0
        
        # Mark discovery flows
        discovery_update = update(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id == flow_uuid,
            DiscoveryFlow.status != "deleted"
        ).values(
            status="deleted",
            updated_at=datetime.utcnow()
        )
        discovery_result = await db.execute(discovery_update)
        child_flows_deleted += discovery_result.rowcount
        deletion_data["child_flows"].append({"type": "discovery", "count": discovery_result.rowcount})
        
        # TODO: Add similar updates for AssessmentFlow, PlanningFlow, ExecutionFlow when implemented
        
        # Mark master flow as having deleted children
        master_flow.flow_status = "child_flows_deleted"
        master_flow.flow_persistence_data = master_flow.flow_persistence_data or {}
        master_flow.flow_persistence_data["deletion_timestamp"] = datetime.utcnow().isoformat()
        master_flow.flow_persistence_data["deleted_by"] = current_user.get("user_id")
        
        # Create comprehensive audit record
        duration_ms = int((time.time() - start_time) * 1000)
        audit_record = FlowDeletionAudit.create_audit_record(
            flow_id=str(flow_uuid),
            client_account_id=str(client_account_id),
            engagement_id=str(master_flow.engagement_id),
            user_id=current_user.get("user_id"),
            deletion_type="user_requested",
            deletion_method="api",
            deleted_by=current_user.get("user_id"),
            deletion_reason="Master flow deletion requested",
            data_deleted=deletion_data,
            deletion_impact={
                "master_flow_status_updated": True,
                "child_flows_deleted": child_flows_deleted,
                "soft_delete": True
            },
            cleanup_summary={
                "master_flow_updated": True,
                "child_flows_marked_deleted": child_flows_deleted
            },
            deletion_duration_ms=duration_ms
        )
        db.add(audit_record)
        
        await db.commit()
        
        logger.info(f"✅ Master flow {flow_id} and {child_flows_deleted} child flows marked as deleted")
        
        return {
            "success": True,
            "flow_id": flow_id,
            "message": f"Master flow and {child_flows_deleted} child flows marked as deleted",
            "child_flows_deleted": child_flows_deleted,
            "audit_id": str(audit_record.id)
        }
            
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to delete master flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}")