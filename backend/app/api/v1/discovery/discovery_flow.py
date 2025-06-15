"""
Discovery Flow API Endpoints
Enhanced endpoints for modular CrewAI Flow Service with parallel execution and state management.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the modular service
from app.services.crewai_flow_service import crewai_flow_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flow", tags=["Discovery Flow"])

# Request/Response Models
class DiscoveryFlowRequest(BaseModel):
    """Request model for Discovery flow execution."""
    headers: List[str] = Field(..., description="CMDB data headers")
    sample_data: List[Dict[str, Any]] = Field(..., description="Sample CMDB records")
    filename: Optional[str] = Field("unknown", description="Source filename")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options")

class FlowStatusResponse(BaseModel):
    """Response model for flow status."""
    flow_id: str
    status: str
    current_phase: Optional[str]
    progress_percentage: Optional[float]
    started_at: Optional[str]
    duration_seconds: Optional[float]

# Main Discovery Flow Endpoints

# Alias for frontend polling: /agent/crew/analysis/status?session_id=...
from fastapi import Request

@router.get("/agent/crew/analysis/status")
async def get_agent_crew_analysis_status(session_id: str, request: Request):
    """
    Alias endpoint for agentic analysis status polling via session_id.
    Returns flow status for the given session.
    """
    try:
        flow_state = crewai_flow_service.get_flow_state_by_session(session_id)
        if not flow_state:
            raise HTTPException(status_code=404, detail=f"No active analysis found for session_id {session_id}")
        # Compose a minimal status response compatible with frontend expectations
        return {
            "status": "success",
            "flow_status": flow_state.dict() if hasattr(flow_state, 'dict') else flow_state,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent crew analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/run")
async def run_discovery_flow(request: DiscoveryFlowRequest):
    """
    Execute complete Discovery phase workflow with enhanced parallel processing.
    
    **Features:**
    - Input validation and data quality assessment
    - AI-powered field mapping with pattern recognition
    - Intelligent asset classification with confidence scoring
    - Parallel execution for optimal performance
    - Comprehensive readiness assessment
    
    **Process Flow:**
    1. Input validation and data quality checks
    2. Data validation using AI analysis
    3. Parallel execution: Field mapping + Asset classification
    4. Migration readiness assessment
    5. Structured results with recommendations
    """
    try:
        # Convert request to service format
        cmdb_data = {
            "headers": request.headers,
            "sample_data": request.sample_data,
            "filename": request.filename,
            "options": request.options
        }
        
        # Execute discovery flow
        result = await crewai_flow_service.run_discovery_flow(cmdb_data)
        
        return {
            "status": "success",
            "message": "Discovery flow completed successfully",
            "flow_result": result,
            "next_steps": {
                "ready_for_assessment": result.get("ready_for_assessment", False),
                "recommended_actions": [
                    "Review field mappings and update if needed",
                    "Validate asset classifications",
                    "Proceed to Assessment phase if readiness score > 8.0"
                ]
            }
        }
        
    except ValueError as e:
        logger.error(f"Discovery flow validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    
    except Exception as e:
        logger.error(f"Discovery flow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/health")
async def get_flow_service_health():
    """
    Get comprehensive health status of the Discovery Flow Service.
    
    **Returns:**
    - Service status and version
    - Component availability (LLM, agents, handlers)
    - Configuration summary
    - Performance capabilities
    """
    try:
        health_status = crewai_flow_service.get_health_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service_details": health_status,
            "capabilities": {
                "async_crew_execution": True,
                "parallel_processing": True,
                "enhanced_parsing": True,
                "input_validation": True,
                "state_management": True,
                "retry_logic": True,
                "fallback_support": True,
                "modular_architecture": True
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "fallback_available": True
        }

@router.get("/status/{flow_id}")
async def get_flow_status(flow_id: str):
    """
    Get detailed status of a specific Discovery flow.
    
    **Returns:**
    - Current phase and progress percentage
    - Component completion status
    - Execution metrics and timing
    - Results (if completed)
    """
    try:
        status = crewai_flow_service.get_flow_status(flow_id)
        
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        return {
            "status": "success",
            "flow_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.get("/active")
async def get_active_flows():
    """
    Get summary of all currently active Discovery flows.
    
    **Returns:**
    - Total active flows count
    - Flows grouped by current phase
    - Individual flow summaries with progress
    """
    try:
        active_flows = crewai_flow_service.get_active_flows()
        
        return {
            "status": "success",
            "active_flows": active_flows,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get active flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve active flows: {str(e)}")

@router.get("/metrics")
async def get_performance_metrics():
    """
    Get comprehensive performance metrics for the Discovery Flow Service.
    
    **Returns:**
    - Execution performance statistics
    - Flow completion rates and timing
    - Handler-specific metrics
    - Resource utilization data
    """
    try:
        metrics = crewai_flow_service.get_performance_metrics()
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

# Individual Component Endpoints for Testing/Debugging
@router.post("/validate-data")
async def validate_data_only(request: DiscoveryFlowRequest):
    """
    Execute only data validation phase for testing purposes.
    
    **Use Cases:**
    - Quick data quality assessment
    - Testing data structure before full flow
    - Debugging validation issues
    """
    try:
        cmdb_data = {
            "headers": request.headers,
            "sample_data": request.sample_data,
            "filename": request.filename
        }
        
        # Use validation handler directly
        validation_handler = crewai_flow_service.validation_handler
        validation_handler.validate_input_data(cmdb_data)
        quality_metrics = validation_handler.assess_data_quality(cmdb_data)
        
        return {
            "status": "success",
            "validation_result": {
                "input_validation": "passed",
                "data_quality_metrics": quality_metrics,
                "ready_for_full_flow": quality_metrics.get("overall_quality_score", 0) > 5.0
            }
        }
        
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"Data validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@router.post("/cleanup")
async def cleanup_resources():
    """
    Clean up expired flows and free resources.
    
    **Use Cases:**
    - Manual resource cleanup
    - Performance optimization
    - Debugging memory issues
    """
    try:
        cleaned_count = crewai_flow_service.cleanup_resources()
        
        return {
            "status": "success",
            "message": f"Cleanup completed: {cleaned_count} flows cleaned",
            "cleaned_flows": cleaned_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Resource cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Configuration and Debugging Endpoints
@router.get("/config")
async def get_service_configuration():
    """
    Get current service configuration and settings.
    
    **Returns:**
    - Timeout configurations
    - Retry settings
    - LLM parameters
    - Handler configurations
    """
    try:
        config_summary = crewai_flow_service.config.get_summary()
        
        return {
            "status": "success",
            "configuration": config_summary,
            "service_version": "2.0.0",
            "modular_architecture": True
        }
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@router.get("/capabilities")
async def get_service_capabilities():
    """
    Get detailed service capabilities and feature availability.
    
    **Returns:**
    - Available features and enhancements
    - Handler capabilities
    - AI agent availability
    - Performance optimizations
    """
    try:
        health = crewai_flow_service.get_health_status()
        
        capabilities = {
            "discovery_workflow": {
                "parallel_execution": True,
                "retry_logic": True,
                "enhanced_parsing": True,
                "input_validation": True,
                "state_management": True
            },
            "ai_capabilities": {
                "llm_available": health["components"]["llm_available"],
                "agents_available": health["components"]["agents_created"],
                "intelligent_field_mapping": True,
                "asset_classification": True,
                "data_validation": True
            },
            "performance_features": {
                "async_execution": True,
                "parallel_processing": True,
                "configurable_timeouts": True,
                "automatic_fallbacks": True,
                "memory_management": True
            },
            "integration_features": {
                "modular_architecture": True,
                "rest_api": True,
                "structured_responses": True,
                "comprehensive_logging": True
            }
        }
        
        return {
            "status": "success",
            "capabilities": capabilities,
            "service_details": health
        }
        
    except Exception as e:
        logger.error(f"Capabilities check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Capabilities error: {str(e)}")

# Export router
__all__ = ["router"] 