"""
Unified Discovery Flow API Endpoints
Consolidates all discovery flow API endpoints into a single, consistent interface.

Replaces:
- backend/app/api/v1/discovery/discovery_flow.py
- Multiple competing API implementations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context
from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-discovery", tags=["Unified Discovery Flow"])

# Request/Response Models
class InitializeFlowRequest(BaseModel):
    client_account_id: str
    engagement_id: str
    user_id: str
    raw_data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)

class FlowStatusResponse(BaseModel):
    flow_id: str
    session_id: str
    status: str
    current_phase: str
    progress_percentage: float
    phase_completion: Dict[str, bool]
    crew_status: Dict[str, Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[str]
    started_at: Optional[str]
    updated_at: str

@router.post("/flow/initialize")
async def initialize_discovery_flow(
    request: InitializeFlowRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Initialize a new unified discovery flow"""
    try:
        logger.info(f"🚀 Initializing unified discovery flow for client {request.client_account_id}")
        
        if not request.raw_data:
            raise HTTPException(status_code=400, detail="Raw data is required")
        
        # Create CrewAI service
        crewai_service = CrewAIFlowService()
        
        # Generate session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create unified discovery flow
        flow = create_unified_discovery_flow(
            session_id=session_id,
            client_account_id=request.client_account_id,
            engagement_id=request.engagement_id,
            user_id=request.user_id,
            raw_data=request.raw_data,
            metadata=request.metadata,
            crewai_service=crewai_service,
            context=context
        )
        
        # Execute flow in background
        background_tasks.add_task(_execute_flow_background, flow, context)
        
        return {
            "status": "success",
            "message": "Unified discovery flow initialized successfully",
            "flow_id": flow.state.flow_id,
            "session_id": session_id,
            "current_phase": "initialization",
            "progress_percentage": 0.0
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize discovery flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize discovery flow: {str(e)}")

@router.get("/flow/status/{session_id}")
async def get_flow_status(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a discovery flow"""
    try:
        # Implementation placeholder
        return {
            "flow_id": session_id,
            "session_id": session_id,
            "status": "running",
            "current_phase": "field_mapping",
            "progress_percentage": 25.0,
            "phase_completion": {},
            "crew_status": {},
            "errors": [],
            "warnings": [],
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow status: {str(e)}")

@router.post("/flow/execute/{phase}")
async def execute_flow_phase(
    phase: str,
    request: Dict[str, Any],
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Execute a specific phase of the discovery flow"""
    try:
        session_id = request.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        logger.info(f"🔄 Executing phase {phase} for session {session_id}")
        
        # Implementation placeholder - integrate with unified flow
        return {
            "status": "success",
            "message": f"Phase {phase} execution started",
            "session_id": session_id,
            "phase": phase,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute phase {phase}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute phase {phase}: {str(e)}")

@router.get("/flow/health")
async def get_flow_health():
    """Get health status of the unified discovery flow system"""
    try:
        from app.services.crewai_flows.unified_discovery_flow import CREWAI_FLOW_AVAILABLE
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "crewai_available": CREWAI_FLOW_AVAILABLE,
            "system_info": {
                "unified_flow_active": True,
                "api_version": "1.0"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/flow/active")
async def get_active_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get all active discovery flows (compatibility endpoint for Enhanced Discovery Dashboard)"""
    try:
        logger.info(f"🔍 Getting active flows for client: {context.client_account_id}")
        
        # This is a compatibility endpoint for the Enhanced Discovery Dashboard
        # It returns mock data in the expected format until we implement full flow tracking
        return {
            "success": True,
            "message": "Active flows retrieved successfully",
            "flow_details": [],  # Empty for now - will be populated when flows are running
            "total_flows": 0,
            "active_flows": 0,
            "completed_flows": 0,
            "failed_flows": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get active flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active flows: {str(e)}")

async def _execute_flow_background(flow, context: RequestContext):
    """Execute the complete discovery flow in background"""
    try:
        logger.info(f"🔄 Starting background execution of flow: {flow.state.session_id}")
        
        # Execute the flow using CrewAI Flow patterns
        result = flow.kickoff()
        
        logger.info(f"✅ Flow execution completed: {flow.state.session_id}")
        
    except Exception as e:
        logger.error(f"❌ Background flow execution failed: {e}")
        flow.state.add_error("background_execution", str(e))
        flow.state.status = "failed" 