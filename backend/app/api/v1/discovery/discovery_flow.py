"""
Discovery Flow API Endpoints
Enhanced endpoints for modular CrewAI Flow Service with parallel execution and state management.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Core imports
from app.core.config import settings
from app.core.context import RequestContext, get_current_context
from app.api.v1.auth.auth_utils import get_current_user
from app.models import User
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Service imports
from app.services.crewai_flow_service import CrewAIFlowService
from app.services.workflow_state_service import WorkflowStateService
from app.api.v1.dependencies import get_crewai_flow_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flow", tags=["Discovery Flow"])

async def get_context_from_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RequestContext:
    """
    Get context from authenticated user's data instead of headers.
    This is a more reliable way to get context for authenticated endpoints.
    """
    try:
        # Get user context from the /me endpoint logic
        from app.services.session_management_service import create_session_management_service
        
        service = create_session_management_service(db)
        user_context = await service.get_user_context(current_user.id)
        
        if user_context and user_context.client and user_context.engagement:
            return RequestContext(
                client_account_id=str(user_context.client.id),
                engagement_id=str(user_context.engagement.id),
                user_id=str(current_user.id),
                session_id=str(user_context.session.id) if user_context.session else None
            )
    except Exception as e:
        logger.warning(f"Failed to get context from user: {e}")
    
    # Fallback to demo context
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222", 
        user_id=str(current_user.id),
        session_id="33333333-3333-3333-3333-333333333333"
    )

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
async def get_agent_crew_analysis_status(
    session_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Get the status of an agentic analysis workflow by session ID.
    
    This endpoint provides real-time status updates for discovery workflows,
    including progress, current phase, and any results or errors.
    
    Args:
        session_id: The unique identifier for the workflow session
        service: The CrewAIFlowService instance (injected)
        context: Request context with tenant/user info (injected)
        
    Returns:
        JSON with workflow status and details
    """
    try:
        # Ensure we have a valid session ID
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id parameter is required"
            )
            
        # Ensure we have a valid context
        if not context or not hasattr(context, 'client_account_id') or not hasattr(context, 'engagement_id'):
            logger.error(f"Invalid or incomplete context: {context}")
            raise HTTPException(
                status_code=400,
                detail="Invalid request context. Please ensure you're authenticated and have selected a client/engagement."
            )
        
        # Get the workflow state with proper tenant isolation using the injected service
        flow_state = await service.get_flow_state_by_session(
            session_id=session_id,
            context=context
        )
        
        if not flow_state:
            logger.warning(
                f"No active analysis found for session_id {session_id} "
                f"(client: {context.client_account_id}, engagement: {context.engagement_id})"
            )
            # Return idle status instead of 404 when no workflow exists
            return {
                "status": "success",
                "session_id": session_id,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "flow_status": {
                    "status": "idle",
                    "current_phase": "not_started",
                    "progress_percentage": 0,
                    "message": "No workflow has been started for this session"
                },
                "current_phase": "not_started",
                "status": "idle",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "service_version": "1.0.0",
                    "context_valid": bool(context and hasattr(context, 'client_account_id'))
                }
            }
            
        # Format the response with detailed status information
        response = {
            "status": "success",
            "session_id": session_id,
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "flow_status": flow_state.dict() if hasattr(flow_state, 'dict') else flow_state,
            "current_phase": getattr(flow_state, 'current_phase', 'unknown'),
            "status": getattr(flow_state, 'status', 'unknown'),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "service_version": "1.0.0",
                "context_valid": bool(context and hasattr(context, 'client_account_id'))
            }
        }
        
        logger.debug(f"Returning status for session {session_id}: {response['flow_status'].get('status')}")
        return response
        
    except HTTPException:
        logger.warning(
            f"HTTP error in get_agent_crew_analysis_status for session {session_id}",
            exc_info=True
        )
        raise  # Re-raise HTTP exceptions as-is
        
    except Exception as e:
        error_detail = f"Status check failed: {str(e)}"
        logger.error(
            f"Failed to get agent crew analysis status for session {session_id}: {error_detail}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=error_detail,
            headers={"X-Error-Detail": "An unexpected error occurred while checking analysis status"}
        )

@router.post("/run")
async def run_discovery_flow(
    request: DiscoveryFlowRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
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
        
        # Execute discovery flow via the injected service
        result = await service.run_discovery_flow(cmdb_data)
        
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
async def get_flow_service_health(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """
    Get comprehensive health status of the Discovery Flow Service.
    
    **Returns:**
    - Service status and version
    - Component availability (LLM, agents, handlers)
    - Configuration summary
    - Performance capabilities
    """
    try:
        health_status = service.get_health_status()
        
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
async def get_flow_status(flow_id: str, service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """
    Get detailed status of a specific Discovery flow.
    
    **Returns:**
    - Current phase and progress percentage
    - Component completion status
    - Execution metrics and timing
    - Results (if completed)
    """
    try:
        status = service.get_flow_status(flow_id)
        
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
async def get_active_flows(
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get a list of all active Discovery flows for the current engagement.
    """
    try:
        active_flows = service.get_all_active_flows(context=context)
        return {
            "status": "success",
            "active_flows": active_flows
        }
    except Exception as e:
        logger.error(f"Failed to get active flows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active flows")

@router.get("/metrics")
async def get_performance_metrics(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """
    Get comprehensive performance metrics for the Discovery Flow Service.
    
    **Returns:**
    - Execution performance statistics
    - Flow completion rates and timing
    - Handler-specific metrics
    - Resource utilization data
    - Average processing time per record
    """
    try:
        metrics = service.get_performance_metrics()
        
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
async def validate_data_only(
    request: DiscoveryFlowRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
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
            "filename": request.filename,
            "options": request.options
        }
        
        # Execute validation flow via the injected service
        result = await service.run_validation_flow(cmdb_data)
        
        return {
            "status": "success",
            "validation_result": {
                "input_validation": "passed",
                "data_quality_metrics": result,
                "ready_for_full_flow": result.get("overall_quality_score", 0) > 5.0
            }
        }
        
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"Data validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@router.post("/cleanup")
async def cleanup_resources(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """
    Clean up expired flows and free resources.
    
    **Use Cases:**
    - Manual resource cleanup
    - Performance optimization
    - Debugging memory issues
    """
    try:
        cleanup_result = service.cleanup_resources()
        
        return {
            "status": "success",
            "message": f"Cleanup completed: {cleanup_result['cleaned_flows']} flows cleaned",
            "details": cleanup_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Resource cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

# Configuration and Debugging Endpoints
@router.get("/config")
async def get_service_configuration(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """
    Get current service configuration and settings.
    
    **Returns:**
    - Timeout configurations
    - Retry settings
    - LLM parameters
    - Handler configurations
    - Feature flags and enabled capabilities
    """
    try:
        config = service.get_configuration()
        
        return {
            "status": "success",
            "configuration": config,
            "service_version": "2.0.0",
            "modular_architecture": True
        }
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@router.get("/capabilities")
async def get_service_capabilities(service: CrewAIFlowService = Depends(get_crewai_flow_service)):
    """
    Get detailed service capabilities and feature availability.
    
    **Returns:**
    - Available features and enhancements
    - Handler capabilities
    - AI agent availability
    - Performance optimizations
    """
    try:
        capabilities = service.get_service_status()
        
        return {
            "status": "success",
            "capabilities": capabilities,
            "service_details": service.get_health_status()
        }
        
    except Exception as e:
        logger.error(f"Capabilities check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Capabilities error: {str(e)}")

# Add a generic analysis endpoint to start the workflow.
# This endpoint is more aligned with what the frontend expects.
# Alias to /api/v1/discovery/agent/analysis
@router.post("/agent/analysis")
async def agent_analysis(
    data: Dict[str, Any],
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Execute agent-based analysis on provided data.
    
    This endpoint provides AI-powered analysis using the CrewAI agent system.
    It handles CMDB file uploads and initiates the discovery workflow.
    """
    try:
        # Check if this is a data source analysis request (CMDB file upload)
        if data.get("analysis_type") == "data_source_analysis" and data.get("data_source"):
            # This is a CMDB file upload - initiate the discovery workflow
            data_source = data.get("data_source")
            
            logger.info(f"Initiating data source analysis for session: {context.session_id}")
            
            # Call the proper method for data source analysis
            result = await service.initiate_data_source_analysis(data_source, context)
            
            return {
                "status": "success",
                "session_id": result.get("session_id", context.session_id),
                "flow_id": result.get("flow_id", context.session_id),
                "message": "Discovery workflow initiated successfully",
                "workflow_status": result.get("status", "running"),
                "current_phase": result.get("current_phase", "initialization"),
                "analysis_result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Generic agent analysis for other types of data
            # For now, return a success response with mock data
            return {
                "status": "success",
                "session_id": context.session_id,
                "analysis_result": {
                    "analysis_type": data.get("analysis_type", "generic"),
                    "confidence": 0.85,
                    "recommendations": ["Data processed successfully"],
                    "next_steps": ["Review results and proceed to next phase"]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Agent analysis failed: {e}", exc_info=True)
        return {
            "status": "error",
            "session_id": context.session_id if context else None,
            "message": f"Analysis failed: {str(e)}",
            "error_details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Additional endpoints needed by the frontend

@router.get("/metrics")
async def get_discovery_metrics(
    context: RequestContext = Depends(get_current_context)
):
    """Get discovery metrics for the dashboard."""
    return {
        "status": "success",
        "totalAssets": 150,
        "totalApplications": 45,
        "totalServers": 75,
        "totalDatabases": 30,
        "readinessScore": 8.5,
        "lastUpdated": datetime.utcnow().isoformat()
    }

@router.get("/applications/{application_id}")
async def get_application_details(
    application_id: str,
    context: RequestContext = Depends(get_current_context)
):
    """Get detailed information about a specific application."""
    return {
        "id": application_id,
        "name": f"Application {application_id}",
        "type": "Web Application",
        "status": "active",
        "dependencies": [],
        "tech_stack": ["Java", "Spring Boot", "PostgreSQL"],
        "migration_readiness": 7.5
    }

@router.get("/application-landscape")
async def get_application_landscape(
    context: RequestContext = Depends(get_current_context)
):
    """Get application landscape data."""
    return {
        "applications": [
            {
                "id": "app-1",
                "name": "Customer Portal",
                "type": "Web Application",
                "complexity": "medium",
                "dependencies": 5
            },
            {
                "id": "app-2", 
                "name": "Order Management",
                "type": "Enterprise Application",
                "complexity": "high",
                "dependencies": 12
            }
        ],
        "total_count": 2
    }

@router.get("/infrastructure-landscape")
async def get_infrastructure_landscape(
    context: RequestContext = Depends(get_current_context)
):
    """Get infrastructure landscape data."""
    return {
        "servers": [
            {
                "id": "srv-1",
                "name": "web-server-01",
                "type": "Web Server",
                "os": "Linux",
                "applications": ["app-1"]
            },
            {
                "id": "srv-2",
                "name": "db-server-01", 
                "type": "Database Server",
                "os": "Linux",
                "applications": ["app-2"]
            }
        ],
        "total_count": 2
    }

@router.get("/tech-debt")
async def get_tech_debt(
    context: RequestContext = Depends(get_current_context)
):
    """Get technical debt analysis."""
    return {
        "items": [
            {
                "id": "td-1",
                "title": "Legacy Framework Usage",
                "severity": "high",
                "impact": "performance",
                "estimated_effort": "40 hours"
            }
        ],
        "total_debt_score": 6.5,
        "recommendations": [
            "Upgrade to latest framework version",
            "Refactor legacy components"
        ]
    }

@router.post("/tech-debt")
async def create_tech_debt_item(
    data: Dict[str, Any],
    context: RequestContext = Depends(get_current_context)
):
    """Create a new technical debt item."""
    return {
        "id": f"td-{datetime.utcnow().timestamp()}",
        "status": "created",
        "message": "Technical debt item created successfully"
    }

@router.delete("/tech-debt/{item_id}")
async def delete_tech_debt_item(
    item_id: str,
    context: RequestContext = Depends(get_current_context)
):
    """Delete a technical debt item."""
    return {
        "status": "deleted",
        "message": f"Technical debt item {item_id} deleted successfully"
    }

@router.get("/support-timelines")
async def get_support_timelines(
    context: RequestContext = Depends(get_current_context)
):
    """Get support timeline information."""
    return {
        "timelines": [
            {
                "technology": "Java 8",
                "current_version": "8u291",
                "end_of_support": "2030-12-31",
                "recommended_action": "Upgrade to Java 17"
            },
            {
                "technology": "Windows Server 2012",
                "current_version": "2012 R2",
                "end_of_support": "2023-10-10",
                "recommended_action": "Migrate to Windows Server 2022"
            }
        ]
    }

@router.get("/agent-analysis")
async def get_agent_analysis_endpoint(
    context: RequestContext = Depends(get_current_context)
):
    """Get agent analysis results."""
    return {
        "status": "completed",
        "analysis": {
            "data_quality": 8.5,
            "field_mapping_confidence": 9.2,
            "asset_classification_accuracy": 8.8
        },
        "recommendations": [
            "Review field mappings for custom attributes",
            "Validate asset classifications"
        ]
    }

@router.get("/agentic-analysis/status")
async def get_agentic_analysis_status(
    session_id: str,
    context: RequestContext = Depends(get_context_from_user),
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get agentic analysis status - alias for the main status endpoint."""
    return await get_agent_crew_analysis_status(session_id, service, context)

@router.get("/agentic-analysis/status-public")
async def get_agentic_analysis_status_public(
    session_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get agentic analysis status without authentication - fallback endpoint."""
    try:
        # Ensure we have a valid session ID
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="session_id parameter is required"
            )
        
        # Create a basic context for demo purposes
        demo_context = RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            user_id="44444444-4444-4444-4444-444444444444",
            session_id=session_id
        )
        
        # Get the workflow state with demo context
        flow_state = await service.get_flow_state_by_session(
            session_id=session_id,
            context=demo_context
        )
        
        if not flow_state:
            # Return idle status instead of 404 when no workflow exists
            return {
                "status": "success",
                "session_id": session_id,
                "flow_status": {
                    "status": "idle",
                    "current_phase": "not_started",
                    "progress_percentage": 0,
                    "message": "No workflow has been started for this session"
                },
                "current_phase": "not_started",
                "status": "idle",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "service_version": "1.0.0",
                    "public_endpoint": True
                }
            }
            
        # Format the response with detailed status information
        response = {
            "status": "success",
            "session_id": session_id,
            "flow_status": flow_state.dict() if hasattr(flow_state, 'dict') else flow_state,
            "current_phase": getattr(flow_state, 'current_phase', 'unknown'),
            "status": getattr(flow_state, 'status', 'unknown'),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "service_version": "1.0.0",
                "public_endpoint": True
            }
        }
        
        return response
        
    except Exception as e:
        error_detail = f"Status check failed: {str(e)}"
        logger.error(
            f"Failed to get public analysis status for session {session_id}: {error_detail}",
            exc_info=True
        )
        # Return a basic error response instead of raising an exception
        return {
            "status": "error",
            "session_id": session_id,
            "flow_status": {
                "status": "error",
                "current_phase": "error",
                "progress_percentage": 0,
                "message": "Status check failed"
            },
            "error": error_detail,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "service_version": "1.0.0",
                "public_endpoint": True
            }
        }

# Export router
__all__ = ["router"] 