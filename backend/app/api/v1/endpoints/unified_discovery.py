"""
Unified Discovery Flow API - Master Flow Orchestrator Integration

This endpoint provides the proper architectural flow as shown in the DFD:
File upload → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow

ARCHITECTURAL FIX: This ensures all discovery flows go through the Master Flow Orchestrator
instead of bypassing it with direct CrewAI flow creation.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.flow_configs import initialize_all_flows

logger = logging.getLogger(__name__)
router = APIRouter()

class FlowInitializationRequest(BaseModel):
    """Request model for flow initialization"""
    flow_name: Optional[str] = None
    raw_data: Optional[List[Dict[str, Any]]] = None
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class FlowInitializationResponse(BaseModel):
    """Response model for flow initialization"""
    success: bool
    flow_id: Optional[str] = None
    flow_name: Optional[str] = None
    status: str
    message: str
    error: Optional[str] = None


@router.post("/flow/initialize", response_model=FlowInitializationResponse)
async def initialize_discovery_flow(
    request: FlowInitializationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowInitializationResponse:
    """
    Initialize a Discovery Flow through Master Flow Orchestrator.
    
    This is the proper architectural endpoint as shown in the DFD:
    Frontend → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow
    
    Args:
        request: Flow initialization request with raw data and configuration
        db: Database session
        context: Request context with tenant information
        
    Returns:
        FlowInitializationResponse with flow_id and status
    """
    try:
        logger.info(f"🎯 Initializing Discovery Flow via Master Flow Orchestrator")
        logger.info(f"🔍 Client: {context.client_account_id}, Engagement: {context.engagement_id}, User: {context.user_id}")
        logger.info(f"🔍 Raw data count: {len(request.raw_data) if request.raw_data else 0}")
        
        # Ensure flow configurations are initialized
        initialize_all_flows()
        
        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Prepare configuration
        configuration = request.configuration or {}
        configuration.update({
            "source": "unified_discovery_api",
            "initialization_timestamp": datetime.utcnow().isoformat()
        })
        
        # Prepare initial state with raw data
        initial_state = {
            "raw_data": request.raw_data or [],
            "metadata": request.metadata or {}
        }
        
        # Create discovery flow through orchestrator
        logger.info(f"🚀 Creating discovery flow through Master Flow Orchestrator...")
        flow_result = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=request.flow_name or f"Discovery Flow {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            configuration=configuration,
            initial_state=initial_state
        )
        
        # Extract flow_id from result tuple
        if isinstance(flow_result, tuple) and len(flow_result) >= 1:
            flow_id = flow_result[0]
            flow_details = flow_result[1] if len(flow_result) > 1 else {}
            
            logger.info(f"✅ Discovery flow created successfully: {flow_id}")
            
            return FlowInitializationResponse(
                success=True,
                flow_id=flow_id,
                flow_name=request.flow_name or flow_details.get("flow_name"),
                status="initialized",
                message=f"Discovery flow initialized successfully with automatic kickoff"
            )
        else:
            logger.error(f"❌ Unexpected flow creation result: {flow_result}")
            return FlowInitializationResponse(
                success=False,
                status="failed",
                message="Flow creation returned unexpected result",
                error="Invalid flow creation response"
            )
            
    except Exception as e:
        logger.error(f"❌ Discovery flow initialization failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return FlowInitializationResponse(
            success=False,
            status="failed",
            message="Discovery flow initialization failed",
            error=str(e)
        )


@router.get("/flow/{flow_id}/status")
async def get_discovery_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get discovery flow status through Master Flow Orchestrator.
    
    This ensures consistent status reporting across all flow types.
    """
    try:
        logger.info(f"🔍 Getting discovery flow status: {flow_id}")
        
        # Ensure flow configurations are initialized
        initialize_all_flows()
        
        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Get flow status
        status = await orchestrator.get_flow_status(flow_id)
        
        logger.info(f"✅ Retrieved flow status for {flow_id}: {status.get('status', 'unknown')}")
        return status
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow status for {flow_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/flow/{flow_id}/pause")
async def pause_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Pause a discovery flow through Master Flow Orchestrator."""
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.pause_flow(flow_id)
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"❌ Failed to pause flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/{flow_id}/resume")
async def resume_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Resume a discovery flow through Master Flow Orchestrator."""
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.resume_flow(flow_id)
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"❌ Failed to resume flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flow/{flow_id}")
async def delete_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Delete a discovery flow through Master Flow Orchestrator."""
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.delete_flow(flow_id)
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"❌ Failed to delete flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))