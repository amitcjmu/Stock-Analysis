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
    """Response model for discovery flow"""
    id: str
    flow_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    current_phase: str
    progress_percentage: float
    status: str
    phase_completion: Dict[str, bool]
    raw_data: List[Dict[str, Any]]
    field_mappings: Optional[Dict[str, Any]]
    cleaned_data: Dict[str, Any]
    asset_inventory: Optional[Dict[str, Any]]
    dependencies: Optional[Dict[str, Any]]
    tech_debt: Optional[Dict[str, Any]]
    crew_status: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    assessment_ready: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]

class DiscoveryAssetResponse(BaseModel):
    """Response model for discovery asset"""
    id: str
    discovery_flow_id: str
    asset_name: str
    asset_type: str
    asset_subtype: Optional[str]
    asset_data: Dict[str, Any]
    discovered_in_phase: str
    discovery_method: Optional[str]
    quality_score: float
    validation_status: str
    confidence_score: float
    tech_debt_score: float
    six_r_recommendation: Optional[str]
    migration_ready: bool
    created_at: Optional[str]
    updated_at: Optional[str]

class FlowSummaryResponse(BaseModel):
    """Response model for flow summary"""
    flow_id: str
    status: str
    current_phase: str
    progress_percentage: float
    phase_completion: Dict[str, bool]
    completed_phases: int
    total_phases: int
    assets: Dict[str, Any]
    timestamps: Dict[str, Optional[str]]
    assessment_ready: bool
    crew_status: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]


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

@router.delete("/flows/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Delete discovery flow and all associated assets"""
    try:
        logger.info(f"🗑️ Deleting discovery flow: {flow_id}")
        
        service = DiscoveryFlowService(db, context)
        deleted = await service.delete_flow(flow_id)
        
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Discovery flow not found: {flow_id}")
        
        logger.info(f"✅ Discovery flow deleted: {flow_id}")
        
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
            "assessment_handoff_preparation"
        ]
    } 