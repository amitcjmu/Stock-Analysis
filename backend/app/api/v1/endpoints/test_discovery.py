"""
Test Discovery Endpoints
Provides authentication-free endpoints for testing CMDB import functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from app.api.v1.dependencies import get_crewai_flow_service
from app.core.context import RequestContext, extract_context_from_request
from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test Discovery"])


@router.post("/agent/analysis")
async def test_agent_analysis(
    data: Dict[str, Any],
    request: Request,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Test agent analysis endpoint without authentication.
    
    This endpoint bypasses authentication for testing purposes.
    Use this to debug CMDB import issues.
    """
    try:
        # Get context without authentication
        context = extract_context_from_request(request)
        
        logger.info(f"Test agent analysis request: {data.get('analysis_type', 'unknown')}")
        
        # Call the service directly
        result = await service.agent_analysis(data, context)
        
        return {
            "success": True,
            "analysis_id": f"test_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "data_source_analysis": result,
            "test_mode": True
        }
        
    except Exception as e:
        logger.error(f"Test agent analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test analysis failed: {str(e)}")


@router.post("/flow/run")
async def test_discovery_flow(
    data: Dict[str, Any],
    request: Request,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Test discovery flow initiation without authentication.
    
    This endpoint bypasses authentication for testing purposes.
    """
    try:
        # Get context without authentication
        context = extract_context_from_request(request)
        
        logger.info(f"Test discovery flow request for file: {data.get('filename', 'unknown')}")
        
        # Prepare data_source in the format expected by initiate_discovery_workflow
        data_source = {
            "file_data": data.get("data", []),  # Use 'data' field from request
            "metadata": {
                "filename": data.get("filename", "test_file.csv"),
                "headers": data.get("headers", []),
                "sample_data": data.get("sample_data", []),
                "options": data.get("options", {}),
                "test_mode": True
            }
        }
        
        # Initiate the discovery workflow with correct parameters
        result = await service.initiate_discovery_workflow(
            data_source=data_source,
            context=context
        )
        
        return {
            "success": True,
            "flow_id": result.get("session_id"),
            "session_id": result.get("session_id"),
            "status": "initiated",
            "message": "Test discovery flow started successfully",
            "current_phase": result.get("current_phase", "initialization"),
            "progress_percentage": result.get("progress_percentage", 0),
            "started_at": datetime.utcnow().isoformat(),
            "test_mode": True
        }
        
    except Exception as e:
        logger.error(f"Test discovery flow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test flow initiation failed: {str(e)}")


@router.get("/flow/status")
async def test_flow_status(
    session_id: str,
    request: Request,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Test flow status polling without authentication.
    """
    try:
        # Get context without authentication
        context = extract_context_from_request(request)
        
        logger.info(f"Test flow status request for session: {session_id}")
        
        # Get flow state
        flow_state = await service.get_flow_state_by_session(session_id, context)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail=f"Flow not found: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "flow_status": {
                "status": flow_state.get("status", "unknown"),
                "current_phase": flow_state.get("current_phase", "unknown"),
                "progress_percentage": flow_state.get("progress_percentage", 0),
                "phases_completed": flow_state.get("phases_completed", {}),
                "agent_insights": flow_state.get("agent_insights", []),
                "started_at": flow_state.get("started_at"),
                "estimated_completion": flow_state.get("estimated_completion")
            },
            "test_mode": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test flow status failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test status check failed: {str(e)}")


@router.get("/health")
async def test_health():
    """
    Test endpoint health check.
    """
    return {
        "success": True,
        "service": "Test Discovery Endpoints",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "test_mode": True
    } 