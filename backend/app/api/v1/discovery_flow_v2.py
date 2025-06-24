"""
Discovery Flow API v2
New API endpoints for discovery flows using fresh database architecture.
Uses CrewAI Flow ID as single source of truth (no session_id confusion).
Follows the Multi-Flow Architecture Implementation Plan.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.services.discovery_flow_service import DiscoveryFlowService, DiscoveryFlowIntegrationService
from app.services.discovery_flow_completion_service import DiscoveryFlowCompletionService
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Discovery Flow v2 - Multi-Flow Architecture"])


# === Pydantic Models ===

class CreateDiscoveryFlowRequest(BaseModel):
    """Request model for creating a new discovery flow"""
    flow_id: str = Field(..., description="CrewAI generated flow ID - single source of truth")
    raw_data: List[Dict[str, Any]] = Field(..., description="Raw imported data")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    import_session_id: Optional[str] = Field(default=None, description="Import session ID for backward compatibility")
    user_id: Optional[str] = Field(default=None, description="User ID")

class UpdatePhaseRequest(BaseModel):
    """Request model for updating phase completion"""
    phase: str = Field(..., description="Phase name (data_import, attribute_mapping, etc.)")
    phase_data: Dict[str, Any] = Field(..., description="Phase-specific data")
    crew_status: Optional[Dict[str, Any]] = Field(default={}, description="CrewAI crew status")
    agent_insights: Optional[List[Dict[str, Any]]] = Field(default=[], description="Agent insights")

class CreateFlowFromCrewAIRequest(BaseModel):
    """Request model for creating flow from CrewAI"""
    crewai_flow_id: str = Field(..., description="CrewAI flow ID")
    crewai_state: Dict[str, Any] = Field(..., description="CrewAI flow state")
    raw_data: List[Dict[str, Any]] = Field(..., description="Raw data")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Metadata")

class SyncCrewAIStateRequest(BaseModel):
    """Request model for syncing CrewAI state"""
    crewai_state: Dict[str, Any] = Field(..., description="CrewAI flow state")
    phase: Optional[str] = Field(default=None, description="Current phase")

class ValidateAssetRequest(BaseModel):
    """Request model for asset validation"""
    validation_status: str = Field(..., description="Validation status")
    validation_results: Optional[Dict[str, Any]] = Field(default={}, description="Validation results")

class DiscoveryFlowResponse(BaseModel):
    """Response model for discovery flow - V2 Clean Architecture"""
    id: str
    flow_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    import_session_id: Optional[str]
    data_import_id: Optional[str]
    flow_name: str
    flow_description: Optional[str]
    status: str
    progress_percentage: float
    phases: Dict[str, bool]
    crewai_persistence_id: Optional[str]
    learning_scope: str
    memory_isolation_level: str
    assessment_ready: bool
    is_mock: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    completed_at: Optional[str]
    migration_readiness_score: float
    next_phase: Optional[str]
    is_complete: bool
    agent_insights: Optional[List[Dict[str, Any]]] = Field(default=[], description="Agent insights for UI bridge")

class DiscoveryAssetResponse(BaseModel):
    """Response model for discovery asset - V2 Clean Architecture"""
    id: str
    discovery_flow_id: str
    client_account_id: str
    engagement_id: str
    asset_name: str
    asset_type: Optional[str]
    asset_subtype: Optional[str]
    raw_data: Dict[str, Any]
    normalized_data: Optional[Dict[str, Any]]
    discovered_in_phase: str
    discovery_method: Optional[str]
    confidence_score: Optional[float]
    migration_ready: bool
    migration_complexity: Optional[str]
    migration_priority: Optional[int]
    asset_status: str
    validation_status: str
    is_mock: bool
    created_at: Optional[str]
    updated_at: Optional[str]

class FlowSummaryResponse(BaseModel):
    """Response model for flow summary - V2 Clean Architecture"""
    flow_id: str
    flow_name: str
    status: str
    next_phase: Optional[str]
    progress_percentage: float
    phases: Dict[str, bool]
    completed_phases: int
    total_phases: int
    assets_summary: Dict[str, Any]
    timestamps: Dict[str, Optional[str]]
    assessment_ready: bool
    migration_readiness_score: float
    is_complete: bool


# === API Endpoints ===

@router.post("/flows", response_model=DiscoveryFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_discovery_flow(
    request: CreateDiscoveryFlowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Create a new discovery flow using CrewAI Flow ID as single source of truth.
    No more session_id confusion.
    """
    try:
        logger.info(f"🚀 Creating discovery flow: {request.flow_id}")
        
        service = DiscoveryFlowService(db, context)
        
        flow = await service.create_discovery_flow(
            flow_id=request.flow_id,
            raw_data=request.raw_data,
            metadata=request.metadata,
            import_session_id=request.import_session_id,
            user_id=request.user_id
        )
        
        logger.info(f"✅ Discovery flow created: {flow.flow_id}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to create discovery flow: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create discovery flow")

@router.get("/flows/active", response_model=Dict[str, Any])
async def get_active_discovery_flows_v2(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get active discovery flows for Enhanced Discovery Dashboard - V2 API.
    
    For platform admin users, this returns flows across all authorized clients.
    For regular users, this returns flows for their current client context.
    
    This replaces the legacy V1 endpoint that used WorkflowState.
    """
    try:
        logger.info(f"🔍 V2: Getting active discovery flows for user: {context.user_id}, client: {context.client_account_id}")
        
        # Check if user is platform admin
        from app.models.rbac import UserRole, ClientAccess
        from app.models.client_account import ClientAccount, Engagement
        from sqlalchemy import select, and_
        
        user_role_query = select(UserRole).where(UserRole.user_id == context.user_id)
        user_roles_result = await db.execute(user_role_query)
        user_roles = user_roles_result.scalars().all()
        
        is_platform_admin = any(role.role_name in ['platform_admin', 'Platform Administrator'] for role in user_roles)
        
        flows = []
        authorized_client_ids = []
        
        if is_platform_admin:
            logger.info(f"🔑 Platform admin detected - querying across all authorized clients")
            
            # Get authorized client IDs for platform admin
            client_access_query = select(ClientAccess.client_account_id).where(
                and_(
                    ClientAccess.user_profile_id == context.user_id,
                    ClientAccess.is_active == True
                )
            )
            client_access_result = await db.execute(client_access_query)
            authorized_client_ids = [str(cid) for cid in client_access_result.scalars().all()]
            
            logger.info(f"👥 Found {len(authorized_client_ids)} authorized clients for admin")
            
            if authorized_client_ids:
                # Get flows for all authorized clients using V2 DiscoveryFlowService
                for client_id in authorized_client_ids:
                    try:
                        # Create context for each client
                        client_context = RequestContext(
                            client_account_id=client_id,
                            engagement_id=context.engagement_id,
                            user_id=context.user_id
                        )
                        flow_service = DiscoveryFlowService(db, client_context)
                        client_flows = await flow_service.get_active_flows()
                        flows.extend(client_flows)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to get flows for client {client_id}: {e}")
                        continue
        else:
            # Regular user: Get flows for current client context only
            logger.info(f"👤 Regular user - querying for client: {context.client_account_id}")
            
            if not context.client_account_id:
                logger.warning("⚠️ No client context available for regular user")
                return {
                    "success": True,
                    "total_flows": 0,
                    "active_flows": 0,
                    "flow_details": [],
                    "is_platform_admin": False,
                    "authorized_clients": 0,
                    "message": "No client context available"
                }
            
            # Use V2 DiscoveryFlowService for regular users
            flow_service = DiscoveryFlowService(db, context)
            flows = await flow_service.get_active_flows()
            authorized_client_ids = [context.client_account_id]
        
        logger.info(f"📊 Found {len(flows)} active flows in database")
        
        # Process flows for frontend compatibility
        flow_details = []
        for flow in flows:
            try:
                # Get client and engagement names
                client_name = "Unknown Client"
                engagement_name = "Unknown Engagement"
                
                # Query client name
                if flow.client_account_id:
                    client_result = await db.execute(
                        select(ClientAccount).where(ClientAccount.id == flow.client_account_id)
                    )
                    client = client_result.scalar_one_or_none()
                    if client:
                        client_name = client.name
                
                # Query engagement name  
                if flow.engagement_id:
                    engagement_result = await db.execute(
                        select(Engagement).where(Engagement.id == flow.engagement_id)
                    )
                    engagement = engagement_result.scalar_one_or_none()
                    if engagement:
                        engagement_name = engagement.name
                
                flow_detail = {
                    "flow_id": str(flow.flow_id),
                    "client_id": str(flow.client_account_id),
                    "client_name": client_name,
                    "engagement_id": str(flow.engagement_id),
                    "engagement_name": engagement_name,
                    "status": flow.status,
                    "current_phase": flow.current_phase,
                    "progress": flow.progress_percentage,
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                    "phases": getattr(flow, 'phases', {}) or {},
                    "errors": getattr(flow, 'errors', []) or [],
                    "warnings": getattr(flow, 'warnings', []) or [],
                    "agent_insights": getattr(flow, 'agent_insights', []) or []
                }
                flow_details.append(flow_detail)
                
            except Exception as e:
                logger.error(f"Error processing flow {getattr(flow, 'flow_id', 'unknown')}: {str(e)}")
                continue
        
        # Calculate summary statistics
        total_flows = len(flow_details)
        active_flows = len([f for f in flow_details if f["status"] in ["running", "active"]])
        completed_flows = len([f for f in flow_details if f["status"] == "completed"])
        failed_flows = len([f for f in flow_details if f["status"] == "failed"])
        
        logger.info(f"📈 V2 Flow summary: {total_flows} total, {active_flows} active, {completed_flows} completed, {failed_flows} failed")
        
        return {
            "success": True,
            "message": f"Active discovery flows retrieved successfully via V2 API ({'platform-wide' if is_platform_admin else 'client-specific'})",
            "flow_details": flow_details,
            "total_flows": total_flows,
            "active_flows": active_flows,
            "completed_flows": completed_flows,
            "failed_flows": failed_flows,
            "is_platform_admin": is_platform_admin,
            "authorized_clients": len(authorized_client_ids),
            "api_version": "2.0",
            "timestamp": "2025-01-27T16:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"❌ V2: Failed to get active discovery flows: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get active discovery flows: {str(e)}")

@router.get("/flows/{flow_id}", response_model=DiscoveryFlowResponse)
async def get_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get discovery flow by CrewAI Flow ID (single source of truth)"""
    try:
        logger.info(f"📋 Getting discovery flow: {flow_id}")
        
        service = DiscoveryFlowService(db, context)
        flow = await service.get_flow_by_id(flow_id)
        
        if not flow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Discovery flow not found: {flow_id}")
        
        logger.info(f"✅ Discovery flow retrieved: {flow_id}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get discovery flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get discovery flow")

@router.get("/flows/import-session/{import_session_id}", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_by_import_session(
    import_session_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get discovery flow by import session ID (for backward compatibility)"""
    try:
        logger.info(f"📋 Getting discovery flow by import session: {import_session_id}")
        
        service = DiscoveryFlowService(db, context)
        flow = await service.get_flow_by_import_session(import_session_id)
        
        if not flow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Discovery flow not found for import session: {import_session_id}")
        
        logger.info(f"✅ Discovery flow retrieved by import session: {import_session_id} -> {flow.flow_id}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get discovery flow by import session {import_session_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get discovery flow")

@router.put("/flows/{flow_id}/phase", response_model=DiscoveryFlowResponse)
async def update_phase_completion(
    flow_id: str,
    request: UpdatePhaseRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Update phase completion and store results"""
    try:
        logger.info(f"🔄 Updating phase completion: {flow_id}, phase: {request.phase}")
        
        service = DiscoveryFlowService(db, context)
        
        flow = await service.update_phase_completion(
            flow_id=flow_id,
            phase=request.phase,
            phase_data=request.phase_data,
            crew_status=request.crew_status,
            agent_insights=request.agent_insights
        )
        
        logger.info(f"✅ Phase completion updated: {flow_id}, phase: {request.phase}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to update phase completion for {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update phase completion")

@router.post("/flows/{flow_id}/complete", response_model=DiscoveryFlowResponse)
async def complete_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Complete discovery flow and prepare assessment handoff package"""
    try:
        logger.info(f"🏁 Completing discovery flow: {flow_id}")
        
        service = DiscoveryFlowService(db, context)
        flow = await service.complete_discovery_flow(flow_id)
        
        logger.info(f"✅ Discovery flow completed: {flow_id}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to complete discovery flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete discovery flow")

@router.get("/flows", response_model=List[DiscoveryFlowResponse])
async def get_discovery_flows(
    status_filter: Optional[str] = Query(None, description="Filter by status (active, completed, failed)"),
    limit: int = Query(10, description="Limit number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get discovery flows for the current client/engagement"""
    try:
        logger.info(f"📋 Getting discovery flows, status: {status_filter}, limit: {limit}")
        
        service = DiscoveryFlowService(db, context)
        
        if status_filter == "active":
            flows = await service.get_active_flows()
        elif status_filter == "completed":
            flows = await service.get_completed_flows(limit)
        else:
            # Get both active and completed flows
            active_flows = await service.get_active_flows()
            completed_flows = await service.get_completed_flows(limit)
            flows = active_flows + completed_flows
        
        logger.info(f"✅ Found {len(flows)} discovery flows")
        return [DiscoveryFlowResponse(**flow.to_dict()) for flow in flows]
        
    except Exception as e:
        logger.error(f"❌ Failed to get discovery flows: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get discovery flows")

@router.get("/flows/{flow_id}/summary", response_model=FlowSummaryResponse)
async def get_flow_summary(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get comprehensive summary of the discovery flow"""
    try:
        logger.info(f"📊 Getting flow summary: {flow_id}")
        
        service = DiscoveryFlowService(db, context)
        summary = await service.get_flow_summary(flow_id)
        
        logger.info(f"✅ Flow summary generated: {flow_id}")
        return FlowSummaryResponse(**summary)
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to get flow summary for {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get flow summary")

@router.get("/flows/{flow_id}/assets", response_model=List[DiscoveryAssetResponse])
async def get_flow_assets(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get all assets for a discovery flow"""
    try:
        logger.info(f"📦 Getting assets for flow: {flow_id}")
        
        service = DiscoveryFlowService(db, context)
        assets = await service.get_flow_assets(flow_id)
        
        logger.info(f"✅ Found {len(assets)} assets for flow: {flow_id}")
        return [DiscoveryAssetResponse(**asset.to_dict()) for asset in assets]
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to get assets for flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get flow assets")

@router.get("/assets/type/{asset_type}", response_model=List[DiscoveryAssetResponse])
async def get_assets_by_type(
    asset_type: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get assets by type for the current client/engagement"""
    try:
        logger.info(f"📦 Getting assets by type: {asset_type}")
        
        service = DiscoveryFlowService(db, context)
        assets = await service.get_assets_by_type(asset_type)
        
        logger.info(f"✅ Found {len(assets)} assets of type: {asset_type}")
        return [DiscoveryAssetResponse(**asset.to_dict()) for asset in assets]
        
    except Exception as e:
        logger.error(f"❌ Failed to get assets by type {asset_type}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get assets by type")

@router.put("/assets/{asset_id}/validate", response_model=DiscoveryAssetResponse)
async def validate_asset(
    asset_id: str,
    request: ValidateAssetRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Update asset validation status and results"""
    try:
        logger.info(f"🔍 Validating asset: {asset_id}")
        
        service = DiscoveryFlowService(db, context)
        
        asset = await service.validate_asset(
            asset_id=uuid.UUID(asset_id),
            validation_status=request.validation_status,
            validation_results=request.validation_results
        )
        
        logger.info(f"✅ Asset validation updated: {asset_id}")
        return DiscoveryAssetResponse(**asset.to_dict())
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to validate asset {asset_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate asset")

@router.delete("/flows/{flow_id}", response_model=Dict[str, Any])
async def delete_discovery_flow(
    flow_id: str,
    force_delete: bool = Query(False, description="Force deletion even if flow is active"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Delete discovery flow with comprehensive cleanup using V2 cleanup service"""
    try:
        logger.info(f"🗑️ Deleting discovery flow: {flow_id}")
        
        # Import V2 cleanup service
        from app.services.discovery_flow_cleanup_service_v2 import create_discovery_flow_cleanup_service_v2
        
        cleanup_service = create_discovery_flow_cleanup_service_v2(db, context)
        cleanup_result = await cleanup_service.delete_flow_with_cleanup(
            flow_id=flow_id,
            force_delete=force_delete,
            cleanup_options={
                "reason": "user_requested",
                "delete_discovery_assets": True,
                "delete_created_assets": True,
                "clean_data_imports": True,
                "create_audit": True
            }
        )
        
        if not cleanup_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=cleanup_result.get("error", "Failed to delete discovery flow")
            )
        
        logger.info(f"✅ Discovery flow deleted with cleanup: {flow_id}")
        return cleanup_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete discovery flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete discovery flow")


# === CrewAI Integration Endpoints ===

@router.post("/crewai/create-flow", response_model=DiscoveryFlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow_from_crewai(
    request: CreateFlowFromCrewAIRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Create discovery flow from CrewAI flow initialization.
    Bridges CrewAI flow state with new database architecture.
    """
    try:
        logger.info(f"🔗 Creating discovery flow from CrewAI: {request.crewai_flow_id}")
        
        integration_service = DiscoveryFlowIntegrationService(db, context)
        
        flow = await integration_service.create_flow_from_crewai(
            crewai_flow_id=request.crewai_flow_id,
            crewai_state=request.crewai_state,
            raw_data=request.raw_data,
            metadata=request.metadata
        )
        
        logger.info(f"✅ Discovery flow created from CrewAI: {flow.flow_id}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to create flow from CrewAI: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create flow from CrewAI")

@router.put("/flows/{flow_id}/sync-crewai", response_model=DiscoveryFlowResponse)
async def sync_crewai_state(
    flow_id: str,
    request: SyncCrewAIStateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Sync CrewAI flow state with discovery flow database.
    Maintains hybrid persistence as described in the implementation plan.
    """
    try:
        logger.info(f"🔄 Syncing CrewAI state for flow: {flow_id}")
        
        integration_service = DiscoveryFlowIntegrationService(db, context)
        
        flow = await integration_service.sync_crewai_state(
            flow_id=flow_id,
            crewai_state=request.crewai_state,
            phase=request.phase
        )
        
        logger.info(f"✅ CrewAI state synced for flow: {flow_id}")
        return DiscoveryFlowResponse(**flow.to_dict())
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to sync CrewAI state for {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync CrewAI state")


# === Asset Creation Bridge ===

@router.post("/flows/{flow_id}/create-assets", response_model=Dict[str, Any])
async def create_assets_from_discovery(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Create assets in main inventory from discovery flow results.
    Critical bridge for completing inventory phase and handoff to assessment.
    """
    try:
        logger.info(f"🏗️ Creating assets from discovery flow: {flow_id}")
        
        # Import the service here to avoid circular imports
        from app.services.asset_creation_bridge_service import AssetCreationBridgeService
        
        bridge_service = AssetCreationBridgeService(db, context)
        result = await bridge_service.create_assets_from_discovery(
            discovery_flow_id=uuid.UUID(flow_id),
            user_id=uuid.UUID(context.user_id) if context.user_id else None
        )
        
        logger.info(f"✅ Asset creation completed for flow: {flow_id}")
        return result
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to create assets from discovery flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create assets from discovery")


# === Flow Completion & Assessment Handoff ===

@router.get("/flows/{flow_id}/validation", response_model=Dict[str, Any])
async def validate_flow_completion_readiness(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Validate if a discovery flow is ready for completion and assessment handoff"""
    try:
        logger.info(f"🔍 Validating completion readiness for flow: {flow_id}")
        
        completion_service = DiscoveryFlowCompletionService(db, context)
        validation_results = await completion_service.validate_flow_completion_readiness(
            uuid.UUID(flow_id)
        )
        
        logger.info(f"✅ Flow validation completed: {flow_id}")
        return validation_results
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to validate flow completion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate flow completion")

@router.get("/flows/{flow_id}/assessment-ready-assets", response_model=Dict[str, Any])
async def get_assessment_ready_assets(
    flow_id: str,
    migration_ready: Optional[bool] = Query(None, description="Filter by migration readiness"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence score"),
    validation_status: Optional[str] = Query(None, description="Filter by validation status"),
    migration_complexity: Optional[str] = Query(None, description="Filter by migration complexity"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get assets that are ready for assessment with optional filtering"""
    try:
        logger.info(f"🔍 Getting assessment-ready assets for flow: {flow_id}")
        
        # Build filters
        filters = {}
        if migration_ready is not None:
            filters["migration_ready"] = migration_ready
        if asset_type:
            filters["asset_type"] = asset_type
        if min_confidence is not None:
            filters["min_confidence"] = min_confidence
        if validation_status:
            filters["validation_status"] = validation_status
        if migration_complexity:
            filters["migration_complexity"] = migration_complexity
        
        completion_service = DiscoveryFlowCompletionService(db, context)
        assets_data = await completion_service.get_assessment_ready_assets(
            uuid.UUID(flow_id),
            filters if filters else None
        )
        
        logger.info(f"✅ Retrieved assessment-ready assets for flow: {flow_id}")
        return assets_data
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to get assessment-ready assets: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get assessment-ready assets")

class GenerateAssessmentPackageRequest(BaseModel):
    """Request model for generating assessment package"""
    selected_asset_ids: Optional[List[str]] = Field(default=None, description="Optional list of specific asset IDs to include")

@router.post("/flows/{flow_id}/assessment-package", response_model=Dict[str, Any])
async def generate_assessment_package(
    flow_id: str,
    request: GenerateAssessmentPackageRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Generate a comprehensive assessment package for handoff to assessment phase"""
    try:
        logger.info(f"🎯 Generating assessment package for flow: {flow_id}")
        
        completion_service = DiscoveryFlowCompletionService(db, context)
        assessment_package = await completion_service.generate_assessment_package(
            uuid.UUID(flow_id),
            request.selected_asset_ids
        )
        
        logger.info(f"✅ Assessment package generated for flow: {flow_id}")
        return assessment_package
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to generate assessment package: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate assessment package")

class CompleteDiscoveryFlowRequest(BaseModel):
    """Request model for completing discovery flow"""
    selected_asset_ids: Optional[List[str]] = Field(default=None, description="Optional list of specific asset IDs to include in assessment")

@router.post("/flows/{flow_id}/complete-with-assessment", response_model=Dict[str, Any])
async def complete_discovery_flow_with_assessment(
    flow_id: str,
    request: CompleteDiscoveryFlowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Complete discovery flow and generate assessment package for handoff"""
    try:
        logger.info(f"🎯 Completing discovery flow with assessment: {flow_id}")
        
        completion_service = DiscoveryFlowCompletionService(db, context)
        
        # First validate flow readiness
        validation_results = await completion_service.validate_flow_completion_readiness(
            uuid.UUID(flow_id)
        )
        
        if not validation_results["is_ready"]:
            raise ValueError(f"Flow not ready for completion: {validation_results['errors']}")
        
        # Generate assessment package
        assessment_package = await completion_service.generate_assessment_package(
            uuid.UUID(flow_id),
            request.selected_asset_ids
        )
        
        # Complete the flow
        completion_result = await completion_service.complete_discovery_flow(
            uuid.UUID(flow_id),
            assessment_package
        )
        
        logger.info(f"✅ Discovery flow completed with assessment: {flow_id}")
        return completion_result
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Failed to complete discovery flow: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to complete discovery flow")

# === Health Check ===

@router.get("/health", dependencies=[])
async def health_check():
    """Health check endpoint for discovery flow v2 API - no context required"""
    return {
        "status": "healthy",
        "service": "discovery-flows-v2",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "api_version": "v2",
        "features": [
            "crewai_flow_id_as_single_source_of_truth",
            "multi_tenant_isolation",
            "phase_completion_tracking",
            "asset_normalization",
            "crewai_integration",
            "assessment_handoff_preparation",
            "asset_creation_bridge",
            "flow_completion_validation",
            "assessment_ready_asset_selection",
            "assessment_package_generation",
            "migration_wave_planning",
            "six_r_strategy_recommendations"
        ]
    } 