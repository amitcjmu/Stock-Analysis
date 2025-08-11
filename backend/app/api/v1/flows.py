"""
Unified Flow API Layer
Task MFO-059 through MFO-073: Unified API endpoints for all flow types
Provides a single, consistent API for creating, managing, and monitoring all CrewAI flows
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models import User
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Flow Management"])


# ===========================
# Request/Response Models (MFO-069)
# ===========================


class CreateFlowRequest(BaseModel):
    """Request model for creating a flow"""

    flow_type: str = Field(
        ..., description="Type of flow (discovery, assessment, planning, etc.)"
    )
    flow_name: Optional[str] = Field(
        None, description="Optional human-readable name for the flow"
    )
    configuration: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Flow-specific configuration"
    )
    initial_state: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Initial state data"
    )

    @validator("flow_type")
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

    phase_input: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Input data for the phase"
    )
    force_execution: bool = Field(
        False, description="Force execution even if preconditions fail"
    )


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
    agent_insights: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Real-time agent insights for this flow"
    )
    field_mappings: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Field mappings for discovery flows"
    )
    raw_data: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Raw import data for discovery flows"
    )
    import_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Import metadata for discovery flows"
    )
    awaitingUserApproval: Optional[bool] = Field(
        None, description="Whether the flow is waiting for user approval"
    )
    currentPhase: Optional[str] = Field(None, description="Current phase of the flow")
    progress: Optional[float] = Field(
        None, description="Progress percentage (alias for progress_percentage)"
    )


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
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
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
            detail="User not associated with a client account",
        )

    return RequestContext(
        user_id=str(current_user.id),
        client_account_id=user_context.client.id,
        engagement_id=user_context.engagement.id if user_context.engagement else None,
    )


async def get_orchestrator(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> MasterFlowOrchestrator:
    """Dependency injection for MasterFlowOrchestrator"""
    return MasterFlowOrchestrator(db, context)


# ===========================
# API Endpoints (MFO-060 through MFO-068)
# ===========================


@router.post("/", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    request: CreateFlowRequest,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
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
            initial_state=request.initial_state,
        )

        # Convert to response model
        return FlowResponse(
            flow_id=flow_id,
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data.get("flow_status", "unknown"),
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data.get("created_by") or "system",
            configuration=flow_data.get("flow_configuration", {}),
            metadata=flow_data.get("metadata", {}),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating flow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create flow: {str(e)}",
        )


@router.get("/", response_model=FlowListResponse)
async def list_flows(
    flow_type: Optional[str] = Query(None, description="Filter by flow type"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
) -> FlowListResponse:
    """
    List all flows with optional filtering (MFO-061)

    Returns a paginated list of flows for the current tenant context.
    """
    try:
        # Get flows filtered by type
        flows = await orchestrator.get_active_flows(
            flow_type=flow_type, limit=100
        )  # Get more flows for filtering

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
            flow_responses.append(
                FlowResponse(
                    flow_id=flow["flow_id"],
                    flow_type=flow["flow_type"],
                    flow_name=flow.get("flow_name"),
                    status=flow.get("flow_status", "unknown"),
                    phase=flow.get("current_phase"),
                    progress_percentage=flow.get("progress_percentage", 0.0),
                    created_at=flow["created_at"],
                    updated_at=flow["updated_at"],
                    created_by=flow.get("created_by", "system"),
                    configuration=flow.get("flow_configuration", {}),
                    metadata=flow.get("metadata", {}),
                )
            )

        return FlowListResponse(
            flows=flow_responses, total=len(flows), page=page, page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing flows: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list flows: {str(e)}",
        )


@router.get("/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: str, orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
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
                detail=f"Flow {flow_id} not found",
            )

        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data.get("flow_status", "unknown"),
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data.get("created_by") or "system",
            configuration=flow_data.get("flow_configuration", {}),
            metadata=flow_data.get("metadata", {}),
        )

    except HTTPException:
        raise
    except ValueError:
        # Flow not found - proper 404 handling
        logger.warning(f"Flow not found: {flow_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Flow {flow_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow: {str(e)}",
        )


@router.post("/{flow_id}/execute", response_model=FlowResponse)
async def execute_phase(
    flow_id: str,
    request: ExecutePhaseRequest,
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
) -> FlowResponse:
    """
    Execute the next phase of a flow (MFO-063)

    Executes the next phase in the flow's lifecycle.
    The flow must be in a valid state to execute the next phase.
    """
    try:
        # For the unified flow API, we need to determine the next phase based on flow state
        # First, get the current flow status to determine the next phase
        try:
            flow_status = await orchestrator.get_flow_status(flow_id)
        except ValueError:
            # Flow not found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        # Check for corrupted flow state and attempt recovery
        if flow_status.get("status") == "failed" and (
            flow_status.get("flow_type") is None
            or flow_status.get("current_phase") is None
        ):
            logger.warning(
                f"Detected corrupted flow state for {flow_id}, attempting recovery..."
            )

            # Try to recover the flow based on its data
            recovery_result = await _recover_corrupted_flow(
                orchestrator, flow_id, flow_status
            )
            if recovery_result["success"]:
                logger.info(f"✅ Flow {flow_id} recovered successfully")
                # Get the updated flow status after recovery
                flow_status = await orchestrator.get_flow_status(flow_id)
            else:
                logger.error(
                    f"❌ Failed to recover flow {flow_id}: {recovery_result['error']}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Flow is in corrupted state and recovery failed: {recovery_result['error']}",
                )

        # Check if this is a paused flow that should be resumed
        if flow_status.get("status") in ["paused", "waiting_for_approval"]:
            # Resume the flow instead of executing a specific phase
            resume_context = request.phase_input if request.phase_input else {}
            if request.force_execution:
                resume_context["force_execution"] = True
            result = await orchestrator.resume_flow(flow_id, resume_context)
        else:
            # For active flows, use the MFO's flow registry to determine next phase
            # This is the proper way to handle phase progression
            flow_type = flow_status.get("flow_type", "unknown")
            current_phase = flow_status.get("current_phase", "unknown")

            try:
                # Get the flow configuration from the registry
                flow_config = orchestrator.flow_registry.get_flow_config(flow_type)
                next_phase = flow_config.get_next_phase(current_phase)

                if not next_phase:
                    # This means we're at the end of the flow
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Flow '{flow_id}' has completed all phases. Current phase: '{current_phase}'",
                    )

                logger.info(
                    f"Flow {flow_id}: Executing next phase '{next_phase}' after '{current_phase}'"
                )

                result = await orchestrator.execute_phase(
                    flow_id=flow_id,
                    phase_name=next_phase,
                    phase_input=request.phase_input,
                    validation_overrides=(
                        {"force_execution": request.force_execution}
                        if request.force_execution
                        else None
                    ),
                )

            except ValueError as e:
                # Flow type not registered
                logger.error(f"Flow type '{flow_type}' not found in registry: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Flow type '{flow_type}' is not registered in the flow registry",
                )

        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to execute phase"),
            )

        # Get updated flow data
        flow_data = await orchestrator.get_flow_status(flow_id)

        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data.get("status", "unknown"),
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data.get("created_by") or "system",
            configuration=flow_data.get("flow_configuration", {}),
            metadata=flow_data.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing phase for flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute phase: {str(e)}",
        )


@router.post("/{flow_id}/pause", response_model=FlowResponse)
async def pause_flow(
    flow_id: str, orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Pause a running flow (MFO-064)

    Pauses a currently running flow, preserving its state for later resumption.
    """
    try:
        result = await orchestrator.pause_flow(flow_id)

        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to pause flow"),
            )

        # Get updated flow data
        flow_data = await orchestrator.get_flow_status(flow_id)

        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data.get("status", "unknown"),
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data.get("created_by") or "system",
            configuration=flow_data.get("flow_configuration", {}),
            metadata=flow_data.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause flow: {str(e)}",
        )


@router.post("/{flow_id}/resume", response_model=FlowResponse)
async def resume_flow(
    flow_id: str, orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowResponse:
    """
    Resume a paused flow (MFO-065)

    Resumes a paused flow from its last saved state.
    """
    try:
        # Validate flow_id parameter
        if flow_id in ("None", "null", "") or not flow_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid flow ID: Flow ID cannot be 'None', 'null', or empty",
            )
        result = await orchestrator.resume_flow(flow_id)

        if result.get("status") == "resume_failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to resume flow"),
            )

        # Get updated flow data
        flow_data = await orchestrator.get_flow_status(flow_id)

        return FlowResponse(
            flow_id=flow_data["flow_id"],
            flow_type=flow_data["flow_type"],
            flow_name=flow_data.get("flow_name"),
            status=flow_data.get("status", "unknown"),
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            created_by=flow_data.get("created_by") or "system",
            configuration=flow_data.get("flow_configuration", {}),
            metadata=flow_data.get("metadata", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flow: {str(e)}",
        )


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(
    flow_id: str, orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> None:
    """
    Soft delete a flow (MFO-066)

    Marks a flow as deleted without removing it from the database.
    The flow can be restored if needed.
    """
    try:
        result = await orchestrator.delete_flow(flow_id)

        if result.get("deleted") is not True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to delete flow"),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting flow {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flow: {str(e)}",
        )


@router.get("/{flow_id}/status", response_model=FlowStatusResponse)
async def get_flow_status(
    flow_id: str, orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator)
) -> FlowStatusResponse:
    """
    Get detailed flow status (MFO-067)

    Returns comprehensive status information including execution history,
    current state, and performance metrics.
    """
    try:
        # Validate flow_id parameter
        if flow_id in ("None", "null", "") or not flow_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid flow ID: Flow ID cannot be 'None', 'null', or empty",
            )
        flow_data = await orchestrator.get_flow_status(flow_id)

        if not flow_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found",
            )

        # Check if flow is waiting for approval
        awaiting_approval = (
            flow_data.get("status") == "waiting_for_approval"
            or flow_data.get("current_state", {}).get("awaiting_user_approval", False)
            or flow_data.get("awaiting_user_approval", False)
        )

        return FlowStatusResponse(
            flow_id=flow_data.get("flow_id", flow_id),
            flow_type=flow_data.get("flow_type", "discovery"),
            flow_name=flow_data.get("flow_name"),
            status=flow_data.get("status", "unknown"),
            phase=flow_data.get("current_phase"),
            progress_percentage=flow_data.get("progress_percentage", 0.0),
            created_at=flow_data["created_at"],
            updated_at=flow_data["updated_at"],
            execution_history=flow_data.get("execution_history", []),
            current_state=flow_data.get("current_state", {}),
            error_details=flow_data.get("error_details"),
            performance_metrics=flow_data.get("performance_metrics", {}),
            agent_insights=flow_data.get("agent_insights", []),
            field_mappings=flow_data.get("field_mappings", []),
            raw_data=flow_data.get("raw_data", []),
            import_metadata=flow_data.get("import_metadata", {}),
            awaitingUserApproval=awaiting_approval,
            currentPhase=flow_data.get("current_phase"),
            progress=flow_data.get("progress_percentage", 0.0),
        )

    except HTTPException:
        raise
    except ValueError:
        # Flow not found - proper 404 handling
        logger.warning(f"Flow not found: {flow_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Flow {flow_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting flow status {flow_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}",
        )


@router.get("/analytics/summary", response_model=FlowAnalyticsResponse)
async def get_flow_analytics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for analytics"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
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
                recent_activity.append(
                    {
                        "flow_id": flow["flow_id"],
                        "flow_type": flow_type,
                        "status": status,
                        "created_at": created_at,
                        "updated_at": flow.get("updated_at"),
                    }
                )

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
            success_rates[flow_type] = (
                success_counts.get(flow_type, 0) / total if total > 0 else 0.0
            )
            error_rates[flow_type] = (
                error_counts.get(flow_type, 0) / total if total > 0 else 0.0
            )

        return FlowAnalyticsResponse(
            total_flows=len(all_flows),
            flows_by_type=flows_by_type,
            flows_by_status=flows_by_status,
            average_duration_seconds=average_durations,
            success_rate_by_type=success_rates,
            error_rate_by_type=error_rates,
            recent_activity=recent_activity,
        )

    except Exception as e:
        logger.error(f"Error getting flow analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow analytics: {str(e)}",
        )


# ===========================
# Flow Recovery Helper Functions
# ===========================


async def _recover_corrupted_flow(
    orchestrator, flow_id: str, flow_status: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Attempt to recover a corrupted flow based on its existing data

    This function analyzes the flow's existing data (field mappings, etc.)
    to determine the correct phase and flow type, then repairs the flow state.
    """
    try:
        # Check for existing field mappings to determine the current phase
        from sqlalchemy import select

        from app.models.data_import.mapping import ImportFieldMapping
        from app.models.discovery_flow import DiscoveryFlow

        # Get the discovery flow record
        discovery_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        discovery_result = await orchestrator.db.execute(discovery_query)
        discovery_flow = discovery_result.scalar_one_or_none()

        if not discovery_flow:
            return {"success": False, "error": "No discovery flow record found"}

        # Get field mappings count
        field_mappings_query = select(ImportFieldMapping).where(
            ImportFieldMapping.master_flow_id == flow_id
        )
        field_mappings_result = await orchestrator.db.execute(field_mappings_query)
        field_mappings = field_mappings_result.fetchall()
        field_mappings_count = len(field_mappings)

        # Determine the correct phase and status based on existing data
        if field_mappings_count > 0:
            # Field mappings exist, so we should be in field_mapping phase
            correct_phase = "field_mapping"
            correct_status = "waiting_for_approval"
            progress = 60.0
        else:
            # No field mappings, so we're likely in data_import phase
            correct_phase = "data_import"
            correct_status = "processing"
            progress = 30.0

        # Update the master flow record
        master_flow = await orchestrator.master_repo.get_by_flow_id(flow_id)
        if master_flow:
            # Update the master flow record directly
            master_flow.flow_type = "discovery"
            master_flow.flow_status = correct_status
            master_flow.current_phase = correct_phase
            master_flow.progress_percentage = progress
            master_flow.updated_at = datetime.utcnow()

            # Update phase data
            if not master_flow.flow_persistence_data:
                master_flow.flow_persistence_data = {}
            master_flow.flow_persistence_data.update(
                {
                    "current_phase": correct_phase,
                    "recovered_at": datetime.utcnow().isoformat(),
                    "recovery_reason": "corrupted_state_repair",
                    "field_mappings_count": field_mappings_count,
                }
            )

            await orchestrator.db.commit()

        # Update the discovery flow record
        discovery_flow.current_phase = correct_phase
        discovery_flow.status = correct_status
        discovery_flow.progress_percentage = progress
        discovery_flow.updated_at = datetime.utcnow()
        await orchestrator.db.commit()

        logger.info(
            f"✅ Flow {flow_id} recovered: phase={correct_phase}, status={correct_status}"
        )

        # Return the recovered status
        recovered_status = {
            "flow_id": flow_id,
            "flow_type": "discovery",
            "current_phase": correct_phase,
            "status": correct_status,
            "field_mappings": field_mappings_count,
            "progress": progress,
        }

        return {"success": True, "recovered_status": recovered_status}

    except Exception as e:
        logger.error(f"❌ Flow recovery failed for {flow_id}: {e}")
        return {"success": False, "error": str(e)}


# ===========================
# Backward Compatibility Layer (MFO-071)
# ===========================


@router.post("/legacy/discovery/create", response_model=FlowResponse, deprecated=True)
async def create_discovery_flow_legacy(
    configuration: Dict[str, Any] = {},
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
) -> FlowResponse:
    """
    Legacy endpoint for creating discovery flows
    DEPRECATED: Use POST /flows instead
    """
    return await create_flow(
        CreateFlowRequest(flow_type="discovery", configuration=configuration),
        orchestrator,
    )


@router.post("/legacy/assessment/create", response_model=FlowResponse, deprecated=True)
async def create_assessment_flow_legacy(
    configuration: Dict[str, Any] = {},
    orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
) -> FlowResponse:
    """
    Legacy endpoint for creating assessment flows
    DEPRECATED: Use POST /flows instead
    """
    return await create_flow(
        CreateFlowRequest(flow_type="assessment", configuration=configuration),
        orchestrator,
    )


# ===========================
# OpenAPI Documentation (MFO-070)
# ===========================

# The OpenAPI documentation is automatically generated by FastAPI
# Additional documentation can be added through the docstrings and
# response_description parameters in the route decorators
