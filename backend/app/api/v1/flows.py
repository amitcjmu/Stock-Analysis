"""
Unified Flow API Layer
Task MFO-059 through MFO-073: Unified API endpoints for all flow types
Provides a single, consistent API for creating, managing, and monitoring all CrewAI flows
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
import logging

from app.core.database import get_db
from app.api.v1.auth.auth_utils import get_current_user
from app.models import User
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.context import RequestContext
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Flow Management"])


# ===========================
# Request/Response Models (MFO-069)
# ===========================

class CreateFlowRequest(BaseModel):
    """Request model for creating a flow"""
    flow_type: str = Field(..., description="Type of flow (discovery, assessment, planning, etc.)")
    flow_name: Optional[str] = Field(None, description="Optional human-readable name for the flow")
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Flow-specific configuration")
    initial_state: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial state data")
    
    @validator('flow_type')
    def validate_flow_type(cls, v):
        """Validate flow type is not empty"""
        if not v or not v.strip():
            raise ValueError("Flow type cannot be empty")
        return v.strip().lower()


class FlowResponse(BaseModel):
    """Response model for flow operations"""
    flow_id: str
    flow_type: str
    flow_name: Optional[str]
    status: str
    phase: Optional[str]
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    created_by: str
    configuration: Dict[str, Any]
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ExecutePhaseRequest(BaseModel):
    """Request model for executing a flow phase"""
    phase_input: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input data for the phase")
    force_execution: bool = Field(False, description="Force execution even if preconditions fail")


class FlowStatusResponse(BaseModel):
    """Detailed flow status response"""
    flow_id: str
    flow_type: str
    flow_name: Optional[str]
    status: str
    phase: Optional[str]
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    execution_history: List[Dict[str, Any]]
    current_state: Dict[str, Any]
    error_details: Optional[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class FlowListResponse(BaseModel):
    """Response model for listing flows"""
    flows: List[FlowResponse]
    total: int
    page: int
    page_size: int


class FlowAnalyticsResponse(BaseModel):
    """Response model for flow analytics"""
    total_flows: int
    flows_by_type: Dict[str, int]
    flows_by_status: Dict[str, int]
    average_duration_seconds: Dict[str, float]
    success_rate_by_type: Dict[str, float]
    error_rate_by_type: Dict[str, float]
    recent_activity: List[Dict[str, Any]]


# ===========================
# Helper Functions
# ===========================

async def get_current_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RequestContext:
    """
    Get user context with client_account_id and engagement_id from authenticated user.
    Returns a proper RequestContext object for the orchestrator.
    """
    service = UserService(db)
    user_context = await service.get_user_context(current_user)
    
    if not user_context.client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not associated with a client account"
        )
    
    return RequestContext(
        user_id=str(current_user.id),
        client_account_id=user_context.client.id,
        engagement_id=user_context.engagement.id if user_context.engagement else None
    )


async def get_orchestrator(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_user_context)
) -> MasterFlowOrchestrator:
    """Dependency injection for MasterFlowOrchestrator"""
    return MasterFlowOrchestrator(db, context)


# ===========================
# API Endpoints (MFO-060 through MFO-068)
# ===========================

@router.post("/", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    request: CreateFlowRequest,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Create a new flow of any type (MFO-060)
    
    This endpoint creates a new flow instance for any supported flow type.
    The flow type must be registered in the FlowTypeRegistry.
    """
    try:
        flow_id, flow_data = await orchestrator.create_flow(
            flow_type=request.flow_type,
            flow_name=request.flow_name,
            configuration=request.configuration,
            initial_state=request.initial_state
        )
        
        # Convert to response model
        return FlowResponse(
            flow_id=flow_id,
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data["status"],
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data["created_by"],
            configuration=flow_data.get("configuration", {}),
            metadata=flow_data.get("metadata", {})
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create flow: {str(e)}"
        )


@router.get("/", response_model=FlowListResponse)
async def list_flows(
    flow_type: Optional[str] = Query(None, description="Filter by flow type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowListResponse:
    """
    List all flows with optional filtering (MFO-061)
    
    Returns a paginated list of flows for the current tenant context.
    """
    try:
        # Get flows filtered by type
        flows = await orchestrator.get_active_flows(
            flow_type=flow_type,
            limit=100  # Get more flows for filtering
        )
        
        # Filter by status if provided
        if status_filter:
            flows = [f for f in flows if f.get("status") == status_filter]
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_flows = flows[start_idx:end_idx]
        
        # Convert to response models
        flow_responses = []
        for flow in paginated_flows:
            flow_responses.append(FlowResponse(
                flow_id=flow["flow_id"],
                flow_type=flow["flow_type"],
                flow_name=flow.get("flow_name"),
                status=flow["status"],
                phase=flow.get("current_phase"),
                progress_percentage=flow.get("progress_percentage", 0.0),
                created_at=flow["created_at"],
                updated_at=flow["updated_at"],
                created_by=flow["created_by"],
                configuration=flow.get("configuration", {}),
                metadata=flow.get("metadata", {})
            ))
        
        return FlowListResponse(
            flows=flow_responses,
            total=len(flows),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing flows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list flows: {str(e)}"
        )


@router.get("/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: str,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Get flow details by ID (MFO-062)
    
    Returns detailed information about a specific flow.
    """
    try:
        flow_data = await orchestrator.get_flow_status(flow_id)
        
        if not flow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data["status"],
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data["created_by"],
            configuration=flow_data.get("configuration", {}),
            metadata=flow_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow: {str(e)}"
        )


@router.post("/{flow_id}/execute", response_model=FlowResponse)
async def execute_phase(
    flow_id: str,
    request: ExecutePhaseRequest,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Execute the next phase of a flow (MFO-063)
    
    Executes the next phase in the flow's lifecycle.
    The flow must be in a valid state to execute the next phase.
    """
    try:
        success, result = await orchestrator.execute_phase(
            flow_id=flow_id,
            phase_input=request.phase_input,
            force_execution=request.force_execution
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to execute phase")
            )
        
        # Get updated flow data
        flow_data = await orchestrator.get_flow_status(flow_id)
        
        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data["status"],
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data["created_by"],
            configuration=flow_data.get("configuration", {}),
            metadata=flow_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing phase for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute phase: {str(e)}"
        )


@router.post("/{flow_id}/pause", response_model=FlowResponse)
async def pause_flow(
    flow_id: str,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Pause a running flow (MFO-064)
    
    Pauses a currently running flow, preserving its state for later resumption.
    """
    try:
        success, result = await orchestrator.pause_flow(flow_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to pause flow")
            )
        
        # Get updated flow data
        flow_data = await orchestrator.get_flow_status(flow_id)
        
        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data["status"],
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data["created_by"],
            configuration=flow_data.get("configuration", {}),
            metadata=flow_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause flow: {str(e)}"
        )


@router.post("/{flow_id}/resume", response_model=FlowResponse)
async def resume_flow(
    flow_id: str,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Resume a paused flow (MFO-065)
    
    Resumes a paused flow from its last saved state.
    """
    try:
        success, result = await orchestrator.resume_flow(flow_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to resume flow")
            )
        
        # Get updated flow data
        flow_data = await orchestrator.get_flow_status(flow_id)
        
        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data["status"],
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data["created_by"],
            configuration=flow_data.get("configuration", {}),
            metadata=flow_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flow: {str(e)}"
        )


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(
    flow_id: str,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> None:
    """
    Soft delete a flow (MFO-066)
    
    Marks a flow as deleted without removing it from the database.
    The flow can be restored if needed.
    """
    try:
        success, result = await orchestrator.delete_flow(flow_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to delete flow")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flow: {str(e)}"
        )


@router.get("/{flow_id}/status", response_model=FlowStatusResponse)
async def get_flow_status(
    flow_id: str,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowStatusResponse:
    """
    Get detailed flow status (MFO-067)
    
    Returns comprehensive status information including execution history,
    current state, and performance metrics.
    """
    try:
        flow_data = await orchestrator.get_flow_status(flow_id)
        
        if not flow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        return FlowStatusResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data["status"],
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            execution_history=flow_data.get("execution_history", []),
            current_state=flow_data.get("current_state", {}),
            error_details=flow_data.get("error_details"),
            performance_metrics=flow_data.get("performance_metrics", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow status {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.get("/analytics/summary", response_model=FlowAnalyticsResponse)
async def get_flow_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowAnalyticsResponse:
    """
    Get flow analytics data (MFO-068)
    
    Returns aggregated analytics data across all flow types for the current tenant.
    """
    try:
        # Get all flows for analytics
        all_flows = await orchestrator.get_active_flows()
        
        # Calculate analytics
        flows_by_type = {}
        flows_by_status = {}
        durations_by_type = {}
        success_counts = {}
        error_counts = {}
        recent_activity = []
        
        for flow in all_flows:
            # Apply date filtering if provided
            created_at = flow.get("created_at")
            if start_date and created_at < start_date:
                continue
            if end_date and created_at > end_date:
                continue
            
            flow_type = flow["flow_type"]
            status = flow["status"]
            
            # Count by type
            flows_by_type[flow_type] = flows_by_type.get(flow_type, 0) + 1
            
            # Count by status
            flows_by_status[status] = flows_by_status.get(status, 0) + 1
            
            # Track success/error rates
            if status == "completed":
                success_counts[flow_type] = success_counts.get(flow_type, 0) + 1
            elif status in ["failed", "error"]:
                error_counts[flow_type] = error_counts.get(flow_type, 0) + 1
            
            # Track durations for completed flows
            if status == "completed" and "performance_metrics" in flow:
                duration = flow["performance_metrics"].get("total_duration_seconds", 0)
                if flow_type not in durations_by_type:
                    durations_by_type[flow_type] = []
                durations_by_type[flow_type].append(duration)
            
            # Add to recent activity (last 10)
            if len(recent_activity) < 10:
                recent_activity.append({
                    "flow_id": flow["flow_id"],
                    "flow_type": flow_type,
                    "status": status,
                    "created_at": created_at,
                    "updated_at": flow.get("updated_at")
                })
        
        # Calculate average durations
        average_durations = {}
        for flow_type, durations in durations_by_type.items():
            if durations:
                average_durations[flow_type] = sum(durations) / len(durations)
        
        # Calculate success/error rates
        success_rates = {}
        error_rates = {}
        for flow_type in flows_by_type:
            total = flows_by_type[flow_type]
            success_rates[flow_type] = success_counts.get(flow_type, 0) / total if total > 0 else 0.0
            error_rates[flow_type] = error_counts.get(flow_type, 0) / total if total > 0 else 0.0
        
        return FlowAnalyticsResponse(
            total_flows=len(all_flows),
            flows_by_type=flows_by_type,
            flows_by_status=flows_by_status,
            average_duration_seconds=average_durations,
            success_rate_by_type=success_rates,
            error_rate_by_type=error_rates,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Error getting flow analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow analytics: {str(e)}"
        )


# ===========================
# Backward Compatibility Layer (MFO-071)
# ===========================

@router.post("/legacy/discovery/create", response_model=FlowResponse, deprecated=True)
async def create_discovery_flow_legacy(
    configuration: Dict[str, Any] = {},
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Legacy endpoint for creating discovery flows
    DEPRECATED: Use POST /flows instead
    """
    return await create_flow(
        CreateFlowRequest(
            flow_type="discovery",
            configuration=configuration
        ),
        orchestrator
    )


@router.post("/legacy/assessment/create", response_model=FlowResponse, deprecated=True)
async def create_assessment_flow_legacy(
    configuration: Dict[str, Any] = {},
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Legacy endpoint for creating assessment flows
    DEPRECATED: Use POST /flows instead
    """
    return await create_flow(
        CreateFlowRequest(
            flow_type="assessment",
            configuration=configuration
        ),
        orchestrator
    )


# ===========================
# OpenAPI Documentation (MFO-070)
# ===========================

# The OpenAPI documentation is automatically generated by FastAPI
# Additional documentation can be added through the docstrings and
# response_description parameters in the route decorators