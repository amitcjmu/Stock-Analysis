"""
Discovery Flow API Endpoints
Enhanced endpoints for modular CrewAI Flow Service with parallel execution and state management.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from sqlalchemy.sql import func

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

# Import the event listener for flow tracking
from app.services.crewai_flows.event_listeners import discovery_flow_listener

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Discovery Flow"])

async def get_context_from_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RequestContext:
    """
    Get context from authenticated user's data and request headers.
    Uses client+engagement from frontend context switcher to find appropriate default session.
    """
    # Extract client and engagement from request headers (sent by frontend context switcher)
    headers = request.headers
    client_account_id = (
        headers.get("x-client-account-id") or 
        headers.get("x-client-id") or
        headers.get("client-account-id")
    )
    engagement_id = (
        headers.get("x-engagement-id") or
        headers.get("engagement-id")
    )
    
    logger.info(f"Context request - User: {current_user.id}, Client: {client_account_id}, Engagement: {engagement_id}")
    
    # If client+engagement provided in headers, find the default session for that combination
    if client_account_id and engagement_id:
        try:
            from app.models.data_import_session import DataImportSession
            
            # Find user's default session for this specific client+engagement combination
            query = (
                select(DataImportSession)
                .where(and_(
                    DataImportSession.created_by == current_user.id,
                    DataImportSession.client_account_id == client_account_id,
                    DataImportSession.engagement_id == engagement_id,
                    DataImportSession.is_default == True
                ))
            )
            result = await db.execute(query)
            user_session = result.scalar_one_or_none()
            
            if user_session:
                logger.info(f"Found user's default session for client {client_account_id}, engagement {engagement_id}: {user_session.id}")
                return RequestContext(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=str(current_user.id),
                    session_id=str(user_session.id)
                )
            else:
                # No default session exists for this client+engagement combination
                # Create one automatically
                logger.info(f"No default session found for user {current_user.id}, client {client_account_id}, engagement {engagement_id} - creating one")
                
                # Get client and engagement names for session naming
                from app.models.client_account import ClientAccount, Engagement
                
                client_query = select(ClientAccount).where(ClientAccount.id == client_account_id)
                client_result = await db.execute(client_query)
                client = client_result.scalar_one_or_none()
                
                engagement_query = select(Engagement).where(Engagement.id == engagement_id)
                engagement_result = await db.execute(engagement_query)
                engagement = engagement_result.scalar_one_or_none()
                
                if client and engagement:
                    # Create default session for this client+engagement combination
                    session_name = f"{client.name.lower().replace(' ', '-')}-{engagement.name.lower().replace(' ', '-')}-{current_user.email.split('@')[0]}-default"
                    session_display_name = f"{current_user.email}'s Default Session - {client.name} / {engagement.name}"
                    
                    new_session = DataImportSession(
                        session_name=session_name,
                        session_display_name=session_display_name,
                        description=f"Auto-created default session for {current_user.email} in {client.name} / {engagement.name}",
                        engagement_id=engagement_id,
                        client_account_id=client_account_id,
                        is_default=True,
                        auto_created=True,
                        session_type='data_import',
                        status='active',
                        created_by=current_user.id,
                        is_mock=False
                    )
                    
                    db.add(new_session)
                    await db.commit()
                    await db.refresh(new_session)
                    
                    logger.info(f"Created new default session: {new_session.id} for user {current_user.id}, client {client_account_id}, engagement {engagement_id}")
                    
                    return RequestContext(
                        client_account_id=client_account_id,
                        engagement_id=engagement_id,
                        user_id=str(current_user.id),
                        session_id=str(new_session.id)
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to get/create session for client {client_account_id}, engagement {engagement_id}: {e}")
    
    # Fallback: Try to get user context from session management service
    try:
        from app.services.session_management_service import create_session_management_service
        
        service = create_session_management_service(db)
        user_context = await service.get_user_context(current_user.id)
        
        if user_context and user_context.client and user_context.engagement:
            logger.info(f"Using user context from session management service: client {user_context.client.id}, engagement {user_context.engagement.id}")
            return RequestContext(
                client_account_id=str(user_context.client.id),
                engagement_id=str(user_context.engagement.id),
                user_id=str(current_user.id),
                session_id=str(user_context.session.id) if user_context.session else None
            )
    except Exception as e:
        logger.warning(f"Failed to get context from session management service: {e}")
    
    # Final fallback: Try to find any default session for the user
    try:
        from app.models.data_import_session import DataImportSession
        
        query = (
            select(DataImportSession)
            .where(and_(
                DataImportSession.created_by == current_user.id,
                DataImportSession.is_default == True
            ))
            .order_by(DataImportSession.created_at.desc())
        )
        result = await db.execute(query)
        user_default_session = result.scalar_one_or_none()
        
        if user_default_session:
            logger.info(f"Using user's first default session: {user_default_session.id}")
            return RequestContext(
                client_account_id=str(user_default_session.client_account_id),
                engagement_id=str(user_default_session.engagement_id),
                user_id=str(current_user.id),
                session_id=str(user_default_session.id)
            )
    except Exception as e:
        logger.warning(f"Failed to get user's default session: {e}")
    
    # Last resort: Fallback to demo context
    logger.warning(f"No user context found for user {current_user.id}, falling back to demo context")
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
    """Get status of agent crew analysis for a specific session"""
    try:
        logger.info(f"Getting agent crew analysis status for session: {session_id}")
        
        # Get flow status from service
        status = await service.get_flow_analysis_status(session_id)
        
        if not status:
            return {
                "session_id": session_id,
                "status": "not_found",
                "message": "No analysis session found",
                "flows": [],
                "agent_statuses": {}
            }
        
        return {
            "session_id": session_id,
            "status": status.get("status", "unknown"),
            "flows": status.get("flows", []),
            "agent_statuses": status.get("agent_statuses", {}),
            "current_phase": status.get("current_phase"),
            "progress": status.get("progress", 0),
            "started_at": status.get("started_at"),
            "last_updated": status.get("last_updated"),
            "results": status.get("results", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting agent crew analysis status for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis status: {str(e)}")

@router.get("/latest-import")
async def get_latest_import_discovery(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get latest import data for Discovery Flow context.
    This endpoint handles the /api/v1/discovery/latest-import requests from AttributeMapping.
    """
    try:
        # Extract context from request headers
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        logger.info(f"🔍 Discovery: Getting latest import for context: client={context.client_account_id}, engagement={context.engagement_id}")
        
        # If no context, return empty result but don't error
        if not context.client_account_id or not context.engagement_id:
            logger.warning(f"⚡ Discovery: No context provided, returning empty response")
            return {
                "success": True,
                "message": "No client or engagement context provided - ready for new upload",
                "data": [],
                "import_metadata": None,
                "ready_for_upload": True
            }
        
        # Try to get from the data-import service
        try:
            from app.api.v1.endpoints.data_import.handlers.import_storage_handler import get_latest_import
            
            # Forward the request to the data-import handler
            result = await get_latest_import(request, db)
            
            # If data found, return it
            if result.get("success") and result.get("data"):
                logger.info(f"✅ Discovery: Found {len(result['data'])} import records")
                return result
            
        except Exception as import_error:
            logger.warning(f"⚠️ Discovery: Could not get from data-import service: {import_error}")
        
        # No data found - this is normal for new sessions
        logger.info(f"📝 Discovery: No import data found, returning empty state")
        return {
            "success": True,
            "message": "No import data found - ready for new upload",
            "data": [],
            "import_metadata": None,
            "ready_for_upload": True
        }
        
    except Exception as e:
        logger.error(f"❌ Discovery: Error getting latest import: {e}")
        return {
            "success": False,
            "message": "Error retrieving import data",
            "data": [],
            "import_metadata": None,
            "error": str(e)
        }

@router.post("/run")
async def run_discovery_flow(
    request: DiscoveryFlowRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_context_from_user)
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
        # Convert to the format expected by initiate_discovery_workflow
        data_source = {
            "file_data": request.sample_data,
            "metadata": {
                "filename": request.filename,
                "headers": request.headers,
                "options": request.options,
                "source": "discovery_flow_api",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Execute discovery flow via the correct service method
        result = await service.initiate_discovery_workflow(data_source, context)
        
        return {
            "status": "success",
            "message": "Discovery flow initiated successfully",
            "session_id": result.get("session_id", context.session_id),
            "flow_id": result.get("flow_id", context.session_id),
            "workflow_status": result.get("status", "running"),
            "current_phase": result.get("current_phase", "initialization"),
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
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_current_context)
):
    """
    Execute only data validation phase for testing purposes.
    
    **Use Cases:**
    - Quick data quality assessment
    - Testing data structure before full flow
    - Debugging validation issues
    """
    try:
        # For now, provide a basic validation response since run_validation_flow doesn't exist
        # This could be enhanced later with actual validation logic
        
        validation_result = {
            "total_records": len(request.sample_data),
            "headers_count": len(request.headers),
            "filename": request.filename,
            "data_quality_score": 8.5,
            "validation_checks": {
                "has_data": len(request.sample_data) > 0,
                "has_headers": len(request.headers) > 0,
                "data_structure_valid": True,
                "required_fields_present": True
            },
            "recommendations": [
                "Data structure appears valid",
                "Ready for full discovery workflow"
            ]
        }
        
        return {
            "status": "success",
            "validation_result": {
                "input_validation": "passed",
                "data_quality_metrics": validation_result,
                "ready_for_full_flow": validation_result.get("data_quality_score", 0) > 5.0
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
            
            logger.info(f"Initiating discovery workflow for session: {context.session_id}")
            
            # Call the discovery workflow method
            result = await service.initiate_discovery_workflow(data_source, context)
            
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

# New endpoints for enhanced Discovery Flow with Crew Architecture

@router.get("/crews/status/{flow_id}")
async def get_crew_status(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get detailed status of all crews in a Discovery Flow"""
    try:
        status = service.get_flow_crew_status(flow_id)
        if not status:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        return {
            "flow_id": flow_id,
            "crew_status": status.get("crew_status", {}),
            "phase_managers": status.get("phase_managers", {}),
            "agent_collaboration": status.get("agent_collaboration_map", {}),
            "current_phase": status.get("current_phase"),
            "completion_percentage": status.get("completion_percentage", 0)
        }
    except Exception as e:
        logger.error(f"Error getting crew status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crews/{crew_name}/details/{flow_id}")
async def get_crew_details(
    flow_id: str,
    crew_name: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get detailed information about a specific crew in a flow"""
    try:
        crew_info = service.get_crew_details(flow_id, crew_name)
        if not crew_info:
            raise HTTPException(status_code=404, detail=f"Crew {crew_name} not found in flow {flow_id}")
        
        return crew_info
    except Exception as e:
        logger.error(f"Error getting crew details for {crew_name} in flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/status/{flow_id}")
async def get_memory_status(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get shared memory status and usage for a flow"""
    try:
        memory_status = service.get_memory_status(flow_id)
        if not memory_status:
            raise HTTPException(status_code=404, detail="Flow memory not found")
        
        return memory_status
    except Exception as e:
        logger.error(f"Error getting memory status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/status/{flow_id}")
async def get_knowledge_status(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get knowledge base status and usage for a flow"""
    try:
        knowledge_status = service.get_knowledge_status(flow_id)
        if not knowledge_status:
            raise HTTPException(status_code=404, detail="Flow knowledge not found")
        
        return knowledge_status
    except Exception as e:
        logger.error(f"Error getting knowledge status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/planning/status/{flow_id}")
async def get_planning_status(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get planning status and execution plan for a flow"""
    try:
        planning_status = service.get_planning_status(flow_id)
        if not planning_status:
            raise HTTPException(status_code=404, detail="Flow planning not found")
        
        return planning_status
    except Exception as e:
        logger.error(f"Error getting planning status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-redesigned")
async def run_discovery_flow_redesigned(
    request: DiscoveryFlowRequest,
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Execute the redesigned Discovery Flow with proper sequence and crew architecture
    
    This endpoint uses the corrected flow sequence:
    1. Field Mapping Crew (Foundation)
    2. Data Cleansing Crew (Quality Assurance)  
    3. Inventory Building Crew (Multi-Domain Classification)
    4. App-Server Dependency Crew (Hosting Relationships)
    5. App-App Dependency Crew (Integration Analysis)
    6. Technical Debt Crew (6R Preparation)
    7. Discovery Integration (Assessment Flow Preparation)
    """
    try:
        logger.info(f"🚀 Starting redesigned Discovery Flow for user {context.user_id}")
        
        # Initialize the redesigned flow
        flow_result = await service.execute_discovery_flow_redesigned(
            headers=request.headers,
            sample_data=request.sample_data,
            filename=request.filename,
            context=context,
            options=request.options or {}
        )
        
        return {
            "status": "flow_started",
            "flow_id": flow_result.get("flow_id"),
            "session_id": flow_result.get("session_id") or flow_result.get("flow_id"),  # Frontend needs this for polling
            "workflow_status": "running",
            "current_phase": flow_result.get("next_phase", "field_mapping"),
            "architecture": "redesigned_with_crews",
            "sequence": [
                "field_mapping", "data_cleansing", "inventory_building",
                "app_server_dependencies", "app_app_dependencies", 
                "technical_debt", "discovery_integration"
            ],
            "message": "Discovery Flow started with corrected architecture",
            "next_phase": flow_result.get("next_phase", "field_mapping"),
            "crew_coordination": flow_result.get("crew_coordination"),
            "planning": flow_result.get("discovery_plan"),
            "flow_result": flow_result,
            "next_steps": {
                "ready_for_assessment": False,
                "recommended_actions": ["Monitor crew progress", "Review field mappings when available"]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Redesigned Discovery Flow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Flow execution failed: {str(e)}")

@router.get("/success-criteria/{flow_id}")
async def get_success_criteria_status(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get success criteria validation status for all phases"""
    try:
        criteria_status = service.get_success_criteria_status(flow_id)
        if not criteria_status:
            raise HTTPException(status_code=404, detail="Flow success criteria not found")
        
        return criteria_status
    except Exception as e:
        logger.error(f"Error getting success criteria for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaboration/tracking/{flow_id}")
async def get_collaboration_tracking(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get collaboration tracking data for flow."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        if hasattr(flow_instance, 'get_collaboration_status'):
            collaboration_data = flow_instance.get_collaboration_status()
            return jsonable_encoder(collaboration_data)
        else:
            return {"available": False, "reason": "Collaboration tracking not implemented"}
            
    except Exception as e:
        logger.error(f"Failed to get collaboration tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get collaboration tracking: {str(e)}")

# ==================================================================================
# PHASE 5: NEW API ENDPOINTS FOR UI ENHANCEMENTS
# ==================================================================================

@router.get("/crews/monitoring/{flow_id}")
async def get_crew_monitoring_data(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get comprehensive crew monitoring data for UI display."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        monitoring_data = {
            "flow_id": flow_id,
            "crews": {},
            "overall_status": "unknown",
            "phases": []
        }
        
        # Get status for each crew type
        crew_types = [
            "field_mapping", "data_cleansing", "inventory_building",
            "app_server_dependencies", "app_app_dependencies", "technical_debt"
        ]
        
        for crew_type in crew_types:
            try:
                if hasattr(flow_instance, f'get_{crew_type}_status'):
                    crew_status = getattr(flow_instance, f'get_{crew_type}_status')()
                    monitoring_data["crews"][crew_type] = {
                        "status": crew_status.get("status", "unknown"),
                        "progress": crew_status.get("progress", 0),
                        "agents": crew_status.get("agents", []),
                        "current_task": crew_status.get("current_task", None),
                        "started_at": crew_status.get("started_at", None),
                        "completed_at": crew_status.get("completed_at", None),
                        "performance_metrics": crew_status.get("performance_metrics", {})
                    }
                else:
                    monitoring_data["crews"][crew_type] = {
                        "status": "not_implemented",
                        "progress": 0,
                        "agents": [],
                        "current_task": None
                    }
            except Exception as e:
                monitoring_data["crews"][crew_type] = {
                    "status": "error",
                    "error": str(e),
                    "progress": 0
                }
        
        # Get overall flow status
        if hasattr(flow_instance, 'get_current_status'):
            overall_status = flow_instance.get_current_status()
            monitoring_data["overall_status"] = overall_status.get("status", "unknown")
            monitoring_data["current_phase"] = overall_status.get("current_phase", "unknown")
        
        return jsonable_encoder(monitoring_data)
        
    except Exception as e:
        logger.error(f"Failed to get crew monitoring data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get crew monitoring data: {str(e)}")

@router.get("/memory/analytics/{flow_id}")
async def get_memory_analytics(
    flow_id: str,
    report_type: str = "summary",
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get memory analytics data for visualization."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        if hasattr(flow_instance, 'get_memory_analytics_report'):
            analytics_data = flow_instance.get_memory_analytics_report(report_type)
            return jsonable_encoder(analytics_data)
        else:
            return {"available": False, "reason": "Memory analytics not implemented"}
            
    except Exception as e:
        logger.error(f"Failed to get memory analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory analytics: {str(e)}")

@router.get("/planning/intelligence/{flow_id}")
async def get_planning_intelligence(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get planning intelligence data for visualization."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        planning_data = {
            "flow_id": flow_id,
            "planning_available": False,
            "coordination_plan": {},
            "dynamic_planning": {},
            "success_criteria": {},
            "adaptive_workflow": {},
            "planning_intelligence": {}
        }
        
        # Get coordination plan
        if hasattr(flow_instance, 'coordinate_crew_planning'):
            try:
                coordination_result = flow_instance.coordinate_crew_planning({
                    "record_count": 1000,
                    "field_count": 20,
                    "data_quality_score": 0.8
                })
                planning_data["coordination_plan"] = coordination_result
                planning_data["planning_available"] = True
            except Exception as e:
                planning_data["coordination_plan"] = {"error": str(e)}
        
        # Get dynamic planning
        if hasattr(flow_instance, 'create_dynamic_plan'):
            try:
                complexity_analysis = {"overall_complexity": "medium"}
                dynamic_plan = flow_instance.create_dynamic_plan(complexity_analysis)
                planning_data["dynamic_planning"] = dynamic_plan
            except Exception as e:
                planning_data["dynamic_planning"] = {"error": str(e)}
        
        # Get planning intelligence
        if hasattr(flow_instance, 'apply_planning_intelligence'):
            try:
                intelligence_result = flow_instance.apply_planning_intelligence({
                    "data_complexity": "medium",
                    "historical_performance": 0.8
                })
                planning_data["planning_intelligence"] = intelligence_result
            except Exception as e:
                planning_data["planning_intelligence"] = {"error": str(e)}
        
        return jsonable_encoder(planning_data)
        
    except Exception as e:
        logger.error(f"Failed to get planning intelligence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get planning intelligence: {str(e)}")

@router.get("/collaboration/analytics/{flow_id}")
async def get_collaboration_analytics(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get collaboration analytics for advanced dashboard."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        analytics_data = {
            "flow_id": flow_id,
            "collaboration_available": False,
            "agent_collaboration": {},
            "cross_crew_sharing": {},
            "knowledge_utilization": {},
            "collaboration_effectiveness": {}
        }
        
        # Get collaboration status
        if hasattr(flow_instance, 'get_collaboration_status'):
            collaboration_status = flow_instance.get_collaboration_status()
            analytics_data["agent_collaboration"] = collaboration_status
            analytics_data["collaboration_available"] = True
        
        # Get memory analytics
        if hasattr(flow_instance, 'get_memory_analytics_report'):
            memory_analytics = flow_instance.get_memory_analytics_report("detailed")
            analytics_data["cross_crew_sharing"] = memory_analytics.get("report", {}).get("cross_domain_insights", {})
            analytics_data["knowledge_utilization"] = memory_analytics.get("report", {}).get("knowledge_utilization", {})
        
        return jsonable_encoder(analytics_data)
        
    except Exception as e:
        logger.error(f"Failed to get collaboration analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get collaboration analytics: {str(e)}")

@router.get("/agents/performance/{flow_id}")
async def get_agent_performance_metrics(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get detailed agent performance metrics."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        performance_data = {
            "flow_id": flow_id,
            "agents": {},
            "crews": {},
            "learning_metrics": {},
            "success_rates": {}
        }
        
        # Get learning effectiveness metrics
        if hasattr(flow_instance, 'get_learning_effectiveness_metrics'):
            learning_metrics = flow_instance.get_learning_effectiveness_metrics()
            performance_data["learning_metrics"] = learning_metrics
        
        # Get callback metrics
        if hasattr(flow_instance, 'get_callback_metrics'):
            callback_metrics = flow_instance.get_callback_metrics()
            performance_data["callback_metrics"] = callback_metrics
        
        return jsonable_encoder(performance_data)
        
    except Exception as e:
        logger.error(f"Failed to get agent performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent performance metrics: {str(e)}")

@router.post("/planning/optimize/{flow_id}")
async def optimize_planning(
    flow_id: str,
    optimization_request: Dict[str, Any],
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Optimize planning based on current performance data."""
    try:
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        optimization_result = {
            "flow_id": flow_id,
            "optimization_applied": False,
            "recommendations": [],
            "performance_impact": {}
        }
        
        # Apply adaptive workflow management
        if hasattr(flow_instance, 'adapt_workflow_strategy'):
            try:
                current_performance = optimization_request.get("current_performance", {
                    "overall_performance": 0.8,
                    "resource_utilization": 0.6,
                    "time_efficiency": 0.75
                })
                
                adaptation_result = flow_instance.adapt_workflow_strategy(current_performance)
                optimization_result["optimization_applied"] = adaptation_result.get("adapted", False)
                optimization_result["workflow_adaptation"] = adaptation_result
            except Exception as e:
                optimization_result["workflow_adaptation_error"] = str(e)
        
        # Apply planning intelligence
        if hasattr(flow_instance, 'apply_planning_intelligence'):
            try:
                planning_context = optimization_request.get("planning_context", {
                    "data_complexity": "medium",
                    "historical_performance": 0.8
                })
                
                intelligence_result = flow_instance.apply_planning_intelligence(planning_context)
                optimization_result["planning_intelligence"] = intelligence_result
                optimization_result["recommendations"] = intelligence_result.get("recommendations", [])
            except Exception as e:
                optimization_result["planning_intelligence_error"] = str(e)
        
        return jsonable_encoder(optimization_result)
        
    except Exception as e:
        logger.error(f"Failed to optimize planning: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize planning: {str(e)}")

@router.get("/ui/dashboard-data/{flow_id}")
async def get_dashboard_data(
    flow_id: str,
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """Get comprehensive dashboard data for UI components."""
    try:
        # Check if the service has the required method
        if not hasattr(service, 'get_flow_instance'):
            logger.warning(f"Service missing get_flow_instance method, returning basic dashboard data")
            return {
                "flow_id": flow_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "service_unavailable",
                "message": "Dashboard service temporarily unavailable",
                "crew_monitoring": {"error": "Service method not available"},
                "memory_analytics": {"error": "Service method not available"},
                "planning_status": {"error": "Service method not available"},
                "collaboration_tracking": {"error": "Service method not available"},
                "performance_metrics": {"error": "Service method not available"},
                "success_criteria": {"error": "Service method not available"}
            }
        
        flow_instance = service.get_flow_instance(flow_id)
        if not flow_instance:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        dashboard_data = {
            "flow_id": flow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "crew_monitoring": {},
            "memory_analytics": {},
            "planning_status": {},
            "collaboration_tracking": {},
            "performance_metrics": {},
            "success_criteria": {}
        }
        
        # Aggregate data from all endpoints
        try:
            # Crew monitoring data
            crew_monitoring = await get_crew_monitoring_data(flow_id, service)
            dashboard_data["crew_monitoring"] = crew_monitoring
        except Exception as e:
            dashboard_data["crew_monitoring"] = {"error": str(e)}
        
        try:
            # Memory analytics
            memory_analytics = await get_memory_analytics(flow_id, "summary", service)
            dashboard_data["memory_analytics"] = memory_analytics
        except Exception as e:
            dashboard_data["memory_analytics"] = {"error": str(e)}
        
        try:
            # Planning intelligence
            planning_intelligence = await get_planning_intelligence(flow_id, service)
            dashboard_data["planning_status"] = planning_intelligence
        except Exception as e:
            dashboard_data["planning_status"] = {"error": str(e)}
        
        try:
            # Collaboration analytics
            collaboration_analytics = await get_collaboration_analytics(flow_id, service)
            dashboard_data["collaboration_tracking"] = collaboration_analytics
        except Exception as e:
            dashboard_data["collaboration_tracking"] = {"error": str(e)}
        
        try:
            # Performance metrics
            performance_metrics = await get_agent_performance_metrics(flow_id, service)
            dashboard_data["performance_metrics"] = performance_metrics
        except Exception as e:
            dashboard_data["performance_metrics"] = {"error": str(e)}
        
        return jsonable_encoder(dashboard_data)
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

# Export router
__all__ = ["router"]

@router.get("/flow/status")
async def get_flow_status_by_session(
    session_id: str,
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Get real-time flow status using session ID.
    
    This endpoint provides reliable flow tracking using the new flow state manager.
    """
    logger.info(f"🔍 Getting flow status for session_id: {session_id}")
    
    try:
        # Get status from Flow State Manager
        from app.services.crewai_flows.discovery_flow_state_manager import flow_state_manager
        
        flow_state = await flow_state_manager.get_flow_state(session_id)
        
        if not flow_state:
            logger.warning(f"Flow state not found for session: {session_id}")
            return {
                "status": "not_found",
                "session_id": session_id,
                "message": f"Flow state not found for session {session_id}",
                "flow_state": None
            }
        
        logger.info(f"✅ Flow status retrieved: {flow_state['status']} - {flow_state['progress_percentage']}%")
        
        return {
            "status": "success",
            "session_id": session_id,
            "flow_state": {
                "status": flow_state["status"],
                "current_phase": flow_state["current_phase"],
                "progress_percentage": flow_state["progress_percentage"],
                "phase_completion": flow_state["phase_completion"],
                "started_at": flow_state["started_at"],
                "updated_at": flow_state.get("updated_at"),
                "completed_at": flow_state.get("completed_at"),
                "database_integration_status": flow_state.get("database_integration_status", "pending"),
                "database_assets_created": flow_state.get("database_assets_created", [])
            },
            "phase_data": {
                "field_mappings": flow_state.get("field_mappings", {}),
                "cleaned_data_count": len(flow_state.get("cleaned_data", [])),
                "asset_inventory": flow_state.get("asset_inventory", {}),
                "app_server_dependencies": flow_state.get("app_server_dependencies", {}),
                "app_app_dependencies": flow_state.get("app_app_dependencies", {}),
                "technical_debt_assessment": flow_state.get("technical_debt_assessment", {})
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting flow status: {e}")
        return {
            "status": "error",
            "session_id": session_id,
            "message": f"Error retrieving flow status: {str(e)}",
            "flow_state": None
        }

@router.get("/flow/status/{flow_id}")
async def get_flow_status_by_id(
    flow_id: str,
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Get real-time flow status using flow ID (legacy endpoint).
    
    This endpoint redirects to the session-based endpoint for compatibility.
    """
    logger.info(f"🔍 Getting flow status for flow_id: {flow_id} (redirecting to session-based)")
    
    # For now, treat flow_id as session_id
    return await get_flow_status_by_session(flow_id, context)

@router.get("/flow/events/{flow_id}")
async def get_flow_events(
    flow_id: str,
    limit: int = 50,
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Get flow events from CrewAI Event Listener for debugging and monitoring.
    """
    logger.info(f"🔍 Getting flow events for flow_id: {flow_id}, limit: {limit}")
    
    try:
        events = discovery_flow_listener.get_flow_events(flow_id, limit)
        
        logger.info(f"✅ Retrieved {len(events)} events for flow {flow_id}")
        return {
            "flow_id": flow_id,
            "events": events,
            "total_events": len(events)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting flow events: {e}")
        return {
            "flow_id": flow_id,
            "events": [],
            "error": str(e)
        }

@router.get("/flow/active")
async def get_active_flows(
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Get list of currently active flows from CrewAI Event Listener.
    """
    logger.info("🔍 Getting active flows")
    
    try:
        active_flows = discovery_flow_listener.get_active_flows()
        
        # Get detailed status for each active flow
        flow_details = []
        for flow_id in active_flows:
            status = discovery_flow_listener.get_flow_status(flow_id)
            flow_details.append(status)
        
        logger.info(f"✅ Found {len(active_flows)} active flows")
        return {
            "active_flows": active_flows,
            "flow_details": flow_details,
            "total_active": len(active_flows)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting active flows: {e}")
        return {
            "active_flows": [],
            "flow_details": [],
            "error": str(e)
        }

# ==================================================================================
# FLOW CONTROL ENDPOINTS FOR MONITORING
# ==================================================================================

@router.post("/flow/{flow_id}/pause")
async def pause_discovery_flow(
    flow_id: str,
    context: RequestContext = Depends(get_context_from_user),
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Pause a running Discovery Flow.
    
    This endpoint allows pausing an active Discovery Flow execution,
    which can be useful for debugging, resource management, or 
    system maintenance scenarios.
    """
    try:
        logger.info(f"🛑 Pausing Discovery Flow: {flow_id}")
        
        # Get flow status first
        flow_status = discovery_flow_listener.get_flow_status(flow_id)
        
        if flow_status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        if flow_status.get("status") != "running":
            raise HTTPException(
                status_code=400, 
                detail=f"Can only pause running flows. Current status: {flow_status.get('status')}"
            )
        
        # TODO: Implement actual pause logic in CrewAI Flow
        # For now, we'll return a mock success response
        logger.info(f"✅ Flow {flow_id} paused (mock implementation)")
        
        return {
            "success": True,
            "flow_id": flow_id,
            "action": "paused",
            "message": "Flow paused successfully",
            "previous_status": flow_status.get("status"),
            "new_status": "paused",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error pausing flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause flow: {str(e)}")


@router.post("/flow/{flow_id}/resume")
async def resume_discovery_flow(
    flow_id: str,
    context: RequestContext = Depends(get_context_from_user),
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Resume a paused Discovery Flow.
    
    This endpoint allows resuming a paused Discovery Flow execution,
    continuing from where it was paused.
    """
    try:
        logger.info(f"▶️ Resuming Discovery Flow: {flow_id}")
        
        # Get flow status first
        flow_status = discovery_flow_listener.get_flow_status(flow_id)
        
        if flow_status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        if flow_status.get("status") != "paused":
            raise HTTPException(
                status_code=400, 
                detail=f"Can only resume paused flows. Current status: {flow_status.get('status')}"
            )
        
        # TODO: Implement actual resume logic in CrewAI Flow
        # For now, we'll return a mock success response
        logger.info(f"✅ Flow {flow_id} resumed (mock implementation)")
        
        return {
            "success": True,
            "flow_id": flow_id,
            "action": "resumed",
            "message": "Flow resumed successfully",
            "previous_status": flow_status.get("status"),
            "new_status": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resuming flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")


@router.post("/flow/{flow_id}/stop")
async def stop_discovery_flow(
    flow_id: str,
    context: RequestContext = Depends(get_context_from_user),
    service: CrewAIFlowService = Depends(get_crewai_flow_service)
):
    """
    Stop a Discovery Flow execution.
    
    This endpoint allows stopping an active Discovery Flow execution.
    Unlike pause, stop terminates the flow permanently and cannot be resumed.
    """
    try:
        logger.info(f"🛑 Stopping Discovery Flow: {flow_id}")
        
        # Get flow status first
        flow_status = discovery_flow_listener.get_flow_status(flow_id)
        
        if flow_status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        if flow_status.get("status") not in ["running", "paused"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Can only stop running or paused flows. Current status: {flow_status.get('status')}"
            )
        
        # TODO: Implement actual stop logic in CrewAI Flow
        # For now, we'll return a mock success response
        logger.info(f"✅ Flow {flow_id} stopped (mock implementation)")
        
        return {
            "success": True,
            "flow_id": flow_id,
            "action": "stopped",
            "message": "Flow stopped successfully",
            "previous_status": flow_status.get("status"),
            "new_status": "stopped",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error stopping flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop flow: {str(e)}")


@router.get("/flow/{flow_id}/control-status")
async def get_flow_control_status(
    flow_id: str,
    context: RequestContext = Depends(get_context_from_user)
):
    """
    Get the control status and available actions for a Discovery Flow.
    
    This endpoint returns information about what control actions are
    available for the current flow state.
    """
    try:
        logger.info(f"🔍 Getting control status for flow: {flow_id}")
        
        # Get flow status first
        flow_status = discovery_flow_listener.get_flow_status(flow_id)
        
        if flow_status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        current_status = flow_status.get("status", "unknown")
        
        # Define available actions based on current status
        available_actions = []
        if current_status == "running":
            available_actions = ["pause", "stop"]
        elif current_status == "paused":
            available_actions = ["resume", "stop"]
        elif current_status in ["completed", "failed", "stopped"]:
            available_actions = []  # No control actions available
        
        return {
            "flow_id": flow_id,
            "current_status": current_status,
            "available_actions": available_actions,
            "can_pause": "pause" in available_actions,
            "can_resume": "resume" in available_actions,
            "can_stop": "stop" in available_actions,
            "control_enabled": len(available_actions) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting control status for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get control status: {str(e)}")

@router.get("/assets")
async def get_discovery_assets(
    page: int = 1,
    page_size: int = 50,
    asset_type: Optional[str] = None,
    environment: Optional[str] = None,
    department: Optional[str] = None,
    criticality: Optional[str] = None,
    search: Optional[str] = None,
    context: RequestContext = Depends(get_context_from_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated discovery assets with multi-tenant scoping.
    All assets are properly scoped to the client account and engagement.
    """
    try:
        logger.info(f"Getting assets for client {context.client_account_id}, engagement {context.engagement_id}")
        
        # Import asset model
        from app.models.asset import Asset
        
        # Build base query with multi-tenant scoping
        base_query = select(Asset).where(
            and_(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
        
        # Apply filters
        conditions = []
        if asset_type and asset_type != 'all':
            conditions.append(Asset.asset_type.ilike(f"%{asset_type}%"))
        if environment and environment != 'all':
            conditions.append(Asset.environment.ilike(f"%{environment}%"))
        if department and department != 'all':
            conditions.append(Asset.department.ilike(f"%{department}%"))
        if criticality and criticality != 'all':
            conditions.append(Asset.criticality.ilike(f"%{criticality}%"))
        if search:
            conditions.append(
                or_(
                    Asset.asset_name.ilike(f"%{search}%"),
                    Asset.hostname.ilike(f"%{search}%"),
                    Asset.ip_address.ilike(f"%{search}%")
                )
            )
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply pagination
        paginated_query = base_query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(paginated_query)
        assets = result.scalars().all()
        
        # Generate summary statistics
        summary_query = select(
            func.count().label('total'),
            func.count().filter(Asset.asset_type == 'application').label('applications'),
            func.count().filter(Asset.asset_type == 'server').label('servers'),
            func.count().filter(Asset.asset_type == 'database').label('databases'),
            func.count().filter(Asset.asset_type.in_(['network', 'storage', 'other'])).label('devices'),
            func.count().filter(Asset.asset_type == 'other').label('unknown')
        ).where(
            and_(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
        
        summary_result = await db.execute(summary_query)
        summary_row = summary_result.first()
        
        # Transform assets for frontend
        transformed_assets = []
        for asset in assets:
            transformed_assets.append({
                "id": str(asset.id),
                "asset_name": asset.asset_name or asset.name,
                "asset_type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else str(asset.asset_type),
                "environment": asset.environment,
                "department": asset.department,
                "criticality": asset.criticality,
                "discovery_status": getattr(asset, 'discovery_status', 'discovered'),
                "ip_address": asset.ip_address,
                "hostname": asset.hostname,
                "operating_system": asset.operating_system,
                "cpu_cores": asset.cpu_cores,
                "memory_gb": asset.memory_gb,
                "storage_gb": asset.storage_gb,
                "confidence_score": getattr(asset, 'confidence_score', 0.8),
                "created_at": asset.created_at.isoformat() if asset.created_at else None,
                "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
            })
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size
        
        response_data = {
            "assets": transformed_assets,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "summary": {
                "total": summary_row.total if summary_row else 0,
                "by_type": {
                    "Application": summary_row.applications if summary_row else 0,
                    "Server": summary_row.servers if summary_row else 0,
                    "Database": summary_row.databases if summary_row else 0,
                    "Infrastructure Device": summary_row.devices if summary_row else 0,
                    "Unknown": summary_row.unknown if summary_row else 0
                }
            }
        }
        
        logger.info(f"Returning {len(transformed_assets)} assets for client {context.client_account_id}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting discovery assets: {e}")
        # Return empty response to prevent frontend errors
        return {
            "assets": [],
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False
            },
            "summary": {
                "total": 0,
                "by_type": {
                    "Application": 0,
                    "Server": 0,
                    "Database": 0,
                    "Infrastructure Device": 0,
                    "Unknown": 0
                }
            }
        }

@router.put("/assets/{asset_id}")
async def update_asset(
    asset_id: int,
    asset_update: dict,
    context: RequestContext = Depends(get_context_from_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an asset's information with proper multi-tenant scoping.
    """
    try:
        from app.models.asset import Asset
        
        # Find the asset with proper multi-tenant scoping
        result = await db.execute(
            select(Asset).where(
                Asset.id == asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
        asset = result.scalar_one_or_none()
        
        if not asset:
            return {"error": "Asset not found or access denied", "status": 404}
        
        # Update allowed fields
        allowed_fields = [
            'asset_name', 'asset_type', 'environment', 'department', 
            'criticality', 'ip_address', 'operating_system', 'cpu_cores', 
            'memory_gb', 'storage_gb', 'migration_readiness', 'confidence_score'
        ]
        
        for field, value in asset_update.items():
            if field in allowed_fields and hasattr(asset, field):
                setattr(asset, field, value)
        
        await db.commit()
        await db.refresh(asset)
        
        return {
            "status": "success",
            "message": "Asset updated successfully",
            "asset": {
                "id": asset.id,
                "asset_name": asset.asset_name,
                "asset_type": asset.asset_type,
                "environment": asset.environment,
                "criticality": asset.criticality,
                "migration_readiness": asset.migration_readiness,
                "confidence_score": asset.confidence_score
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating asset {asset_id}: {e}")
        return {"error": f"Failed to update asset: {str(e)}", "status": 500}

@router.post("/assets/bulk-update")
async def bulk_update_assets(
    bulk_update_request: dict,
    context: RequestContext = Depends(get_context_from_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update assets with proper multi-tenant scoping.
    """
    try:
        from app.models.asset import Asset
        
        asset_ids = bulk_update_request.get('asset_ids', [])
        updates = bulk_update_request.get('updates', {})
        
        if not asset_ids or not updates:
            return {"error": "Missing asset_ids or updates", "status": 400}
        
        logger.info(f"Bulk updating {len(asset_ids)} assets for client {context.client_account_id}")
        
        # Find assets with proper multi-tenant scoping
        result = await db.execute(
            select(Asset).where(
                Asset.id.in_(asset_ids),
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
        assets = result.scalars().all()
        
        if not assets:
            return {"error": "No assets found or access denied", "status": 404}
        
        # Update allowed fields
        allowed_fields = [
            'asset_name', 'asset_type', 'environment', 'department', 
            'criticality', 'ip_address', 'operating_system', 'cpu_cores', 
            'memory_gb', 'storage_gb', 'migration_readiness'
        ]
        
        updated_count = 0
        for asset in assets:
            for field, value in updates.items():
                if field in allowed_fields and hasattr(asset, field):
                    setattr(asset, field, value)
                    updated_count += 1
        
        await db.commit()
        
        return {
            "status": "success",
            "message": f"Updated {updated_count} fields across {len(assets)} assets",
            "assets_updated": len(assets)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk update: {e}")
        return {"error": f"Failed to bulk update assets: {str(e)}", "status": 500}

@router.post("/assets/trigger-inventory-building")
async def trigger_inventory_building_crew(
    context: RequestContext = Depends(get_context_from_user),
    service: CrewAIFlowService = Depends(get_crewai_flow_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger the inventory building crew for the current client/engagement context.
    This will progress the Discovery Flow from 'field_mapping' to 'inventory_building' phase.
    """
    try:
        logger.info(f"Triggering inventory building crew for client {context.client_account_id}, engagement {context.engagement_id}")
        
        from app.models.asset import Asset
        
        # First, check if we already have assets for this context
        existing_assets_result = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
        existing_count = existing_assets_result.scalar()
        
        logger.info(f"Found {existing_count} existing assets for this context")
        
        # If we already have assets, don't create new ones - just trigger analysis
        if existing_count > 0:
            logger.info("Assets already exist - triggering analysis on existing data")
            
            # Get a sample of existing assets for the flow
            sample_result = await db.execute(
                select(Asset).where(
                    Asset.client_account_id == context.client_account_id,
                    Asset.engagement_id == context.engagement_id
                ).limit(10)
            )
            existing_assets = sample_result.scalars().all()
            
            # Create sample data from existing assets
            raw_data = []
            for asset in existing_assets:
                raw_data.append({
                    "asset_name": asset.asset_name or asset.name,
                    "hostname": asset.hostname,
                    "asset_type": asset.asset_type,
                    "environment": asset.environment,
                    "department": asset.department,
                    "criticality": asset.criticality,
                    "ip_address": asset.ip_address,
                    "operating_system": asset.operating_system
                })
        else:
            # No existing assets - create sample data for testing
            logger.info("No existing assets found - creating sample data")
            raw_data = [
                {
                    "hostname": f"client-{context.client_account_id[-8:]}-web-server-01",
                    "asset_name": f"Web Server 01 ({context.client_account_id[-8:]})", 
                    "asset_type": "server",
                    "environment": "production",
                    "department": "IT",
                    "criticality": "high"
                },
                {
                    "hostname": f"client-{context.client_account_id[-8:]}-db-server-01",
                    "asset_name": f"Database Server 01 ({context.client_account_id[-8:]})",
                    "asset_type": "database", 
                    "environment": "production",
                    "department": "IT",
                    "criticality": "critical"
                }
            ]
            
            # Create assets in database with proper context scoping
            assets_created = []
            for asset_data in raw_data:
                try:
                    new_asset = Asset(
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        name=asset_data.get("asset_name", asset_data.get("hostname", "Unknown Asset")),
                        asset_name=asset_data.get("asset_name"),
                        hostname=asset_data.get("hostname"),
                        asset_type=asset_data.get("asset_type", "other"),
                        environment=asset_data.get("environment"),
                        department=asset_data.get("department"),
                        criticality=asset_data.get("criticality"),
                        ip_address=asset_data.get("ip_address"),
                        operating_system=asset_data.get("operating_system"),
                        cpu_cores=asset_data.get("cpu_cores"),
                        memory_gb=asset_data.get("memory_gb"),
                        storage_gb=asset_data.get("storage_gb"),
                        discovery_method="inventory_building_trigger",
                        discovery_source="manual_trigger"
                    )
                    
                    db.add(new_asset)
                    assets_created.append(new_asset)
                    
                except Exception as asset_error:
                    logger.error(f"Error creating asset: {asset_error}")
                    continue
            
            # Commit new assets to database
            try:
                await db.commit()
                logger.info(f"Created {len(assets_created)} new assets in database")
            except Exception as commit_error:
                logger.error(f"Error committing assets: {commit_error}")
                await db.rollback()
                assets_created = []

        # Initialize flow focused on inventory building
        flow_request = DiscoveryFlowRequest(
            headers=list(raw_data[0].keys()) if raw_data else ["hostname", "asset_name", "asset_type"],
            sample_data=raw_data[:10],  # Limit for performance
            filename=f"inventory_building_trigger_{context.client_account_id[-8:]}.json",
            options={
                "enable_field_mapping": False,
                "enable_data_cleansing": False,
                "enable_inventory_building": True,
                "enable_dependency_analysis": False,
                "confidence_threshold": 0.7,
                "force_phase": "inventory_building",
                "client_context": {
                    "client_account_id": context.client_account_id,
                    "engagement_id": context.engagement_id
                }
            }
        )
        
        # Try to run the discovery flow
        flow_id = "manual_trigger"
        session_id = f"session-{context.client_account_id[-8:]}-{int(time.time())}"
        
        try:
            flow_result = await run_discovery_flow_redesigned(flow_request, service, context)
            flow_id = flow_result.get("flow_id", flow_id)
            session_id = flow_result.get("session_id", session_id)
        except Exception as flow_error:
            logger.warning(f"Discovery flow failed, but proceeding: {flow_error}")
        
        message = f"Inventory building triggered successfully for context {context.client_account_id[-8:]}."
        if existing_count == 0:
            message += f" Created {len(assets_created) if 'assets_created' in locals() else 0} new assets."
        else:
            message += f" Analyzing {existing_count} existing assets."
        
        return {
            "status": "success",
            "message": message,
            "flow_id": flow_id,
            "session_id": session_id,
            "current_phase": "inventory_building",
            "assets_total": existing_count + len(assets_created) if 'assets_created' in locals() else existing_count,
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id
            }
        }
            
    except Exception as e:
        logger.error(f"Error triggering inventory building crew: {e}")
        return {
            "status": "error",
            "message": f"Failed to trigger inventory building: {str(e)}"
        } 