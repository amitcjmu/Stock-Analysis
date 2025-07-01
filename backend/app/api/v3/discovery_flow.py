"""
Unified Discovery Flow API v3
Consolidates all discovery flow operations into a single, coherent API
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.api.v3.schemas.discovery import (
    FlowCreate, FlowUpdate, FlowResponse, FlowListResponse, FlowStatusResponse,
    FlowExecutionResponse, FlowDeletionResponse, FlowHealthResponse,
    PhaseExecution, FlowResumeRequest, FlowPauseRequest, AssetPromotionResponse,
    FlowFilterParams, PaginationParams, FlowStatus, FlowPhase, ExecutionMode
)
from app.api.v3.schemas.responses import (
    ErrorResponse, ValidationErrorResponse, NotFoundErrorResponse,
    create_error_response, create_validation_error, generate_request_id
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discovery-flow", tags=["discovery-flow-v3"])

# === Import V3 Services ===

from app.services.v3.discovery_flow_service import V3DiscoveryFlowService
from app.services.v3.data_import_service import V3DataImportService
from app.services.v3.field_mapping_service import V3FieldMappingService
from app.services.v3.asset_service import V3AssetService

logger.info("✅ V3 Discovery flow services loaded")


# === Core Discovery Flow Endpoints ===

@router.post("/flows", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    request: FlowCreate,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowResponse:
    """
    Create a new discovery flow
    Uses flow_id from the start (no session_id)
    """
    try:
        logger.info(f"🚀 Creating discovery flow: {request.name}")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Create the discovery flow using V3 service
        flow = await flow_service.create_flow(
            name=request.name,
            description=request.description,
            metadata=request.metadata or {},
            execution_mode=request.execution_mode.value if request.execution_mode else "hybrid",
            user_id=str(context.user_id) if context.user_id and context.user_id != "anonymous" else None
        )
        
        # If raw data provided, create data import and associate with flow
        data_import_id = None
        if request.raw_data:
            import_service = V3DataImportService(
                db,
                str(context.client_account_id),
                str(context.engagement_id)
            )
            
            # Create data import from raw data
            import json
            data_json = json.dumps(request.raw_data)
            file_data = data_json.encode('utf-8')
            
            data_import = await import_service.create_import(
                filename=f"{request.name}_raw_data.json",
                file_data=file_data,
                source_system="api",
                import_name=f"Data for {request.name}",
                import_type="json",
                user_id=str(context.user_id) if context.user_id and context.user_id != "anonymous" else None,
                flow_id=str(flow.id)
            )
            
            # Process the data
            await import_service.process_import_data(
                str(data_import.id),
                request.raw_data
            )
            
            data_import_id = data_import.id
        
        # Get flow status with all data
        flow_status = await flow_service.get_flow_status(str(flow.id))
        
        # Build response
        flow_result = {
            "flow_id": flow.id,
            "name": flow.name,
            "description": flow.description,
            "client_account_id": flow.client_account_id,
            "engagement_id": flow.engagement_id,
            "user_id": flow.created_by_user_id or context.user_id,
            "status": FlowStatus.INITIALIZING,
            "current_phase": FlowPhase.INITIALIZATION,
            "progress_percentage": flow_status.get("progress_percentage", 0.0),
            "phases_completed": flow_status.get("phases_completed", []),
            "phases_status": flow_status.get("phases_status", {}),
            "execution_mode": ExecutionMode(flow.execution_mode) if flow.execution_mode else ExecutionMode.HYBRID,
            "crewai_status": "initialized" if flow.crewai_flow_id else "pending",
            "database_status": "initialized",
            "metadata": flow.metadata or {},
            "agent_insights": flow_status.get("agent_insights", []),
            "created_at": flow.created_at,
            "updated_at": flow.updated_at,
            "records_total": len(request.raw_data) if request.raw_data else 0,
            "assets": []
        }
        
        # Update status based on data import
        if data_import_id:
            flow_result["status"] = FlowStatus.INITIALIZED
            flow_result["current_phase"] = FlowPhase.FIELD_MAPPING
        
        logger.info(f"✅ Discovery flow created: {flow.id}")
        return FlowResponse(**flow_result)
        
    except Exception as e:
        logger.error(f"❌ Failed to create discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create discovery flow: {str(e)}"
        )


@router.get("/flows/{flow_id}", response_model=FlowResponse)
async def get_flow(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowResponse:
    """
    Get flow details with all sub-resources
    """
    try:
        logger.info(f"🔍 Getting flow details: {flow_id}")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get flow data from V3 service
        flow = await flow_service.get_flow(str(flow_id))
        
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        # Get detailed flow status
        flow_status = await flow_service.get_flow_status(str(flow_id))
        
        # Get associated assets if available
        assets = []
        try:
            asset_service = V3AssetService(
                db,
                str(context.client_account_id),
                str(context.engagement_id)
            )
            assets = await asset_service.get_assets_for_flow(str(flow_id))
        except Exception as e:
            logger.warning(f"⚠️ Failed to get assets for flow: {e}")
        
        # Build response data
        flow_data = {
            "flow_id": flow.id,
            "name": flow.name,
            "description": flow.description,
            "client_account_id": flow.client_account_id,
            "engagement_id": flow.engagement_id,
            "user_id": flow.created_by_user_id or context.user_id,
            "status": FlowStatus(flow.status) if flow.status else FlowStatus.INITIALIZED,
            "current_phase": FlowPhase(flow.current_phase) if flow.current_phase else FlowPhase.INITIALIZATION,
            "progress_percentage": flow_status.get("progress_percentage", 0.0),
            "phases_completed": flow_status.get("phases_completed", []),
            "phases_status": flow_status.get("phases_status", {}),
            "execution_mode": ExecutionMode(flow.execution_mode) if flow.execution_mode else ExecutionMode.HYBRID,
            "crewai_status": "active" if flow.crewai_flow_id else "pending",
            "database_status": "active",
            "metadata": flow.metadata or {},
            "agent_insights": flow_status.get("agent_insights", []),
            "created_at": flow.created_at,
            "updated_at": flow.updated_at,
            "records_total": flow_status.get("records_total", 0),
            "assets": assets or []
        }
        
        logger.info(f"✅ Flow details retrieved: {flow_id}")
        return FlowResponse(**flow_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow: {str(e)}"
        )


@router.get("/flows/{flow_id}/status", response_model=FlowStatusResponse)
async def get_flow_status(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowStatusResponse:
    """
    Get real-time flow execution status
    """
    try:
        logger.info(f"📊 Getting flow status: {flow_id}")
        
        # Get flow details first
        flow_data = await get_flow(flow_id, db, context)
        
        # Build status response with real-time information
        status_data = {
            "flow_id": flow_id,
            "status": flow_data.status,
            "current_phase": flow_data.current_phase,
            "progress_percentage": flow_data.progress_percentage,
            "updated_at": flow_data.updated_at,
            "execution_mode": flow_data.execution_mode,
            "crewai_status": flow_data.crewai_status,
            "database_status": flow_data.database_status,
            "latest_insights": flow_data.agent_insights[-5:] if flow_data.agent_insights else []
        }
        
        # Determine real-time capabilities
        status_data["is_running"] = flow_data.status == FlowStatus.IN_PROGRESS
        status_data["is_paused"] = flow_data.status == FlowStatus.PAUSED
        status_data["can_resume"] = flow_data.status in [FlowStatus.PAUSED, FlowStatus.FAILED]
        status_data["can_cancel"] = flow_data.status in [FlowStatus.IN_PROGRESS, FlowStatus.PAUSED]
        
        # Determine next phase
        phase_order = [
            FlowPhase.INITIALIZATION,
            FlowPhase.FIELD_MAPPING,
            FlowPhase.DATA_CLEANSING,
            FlowPhase.INVENTORY_BUILDING,
            FlowPhase.APP_SERVER_DEPENDENCIES,
            FlowPhase.APP_APP_DEPENDENCIES,
            FlowPhase.TECHNICAL_DEBT,
            FlowPhase.COMPLETED
        ]
        
        current_index = phase_order.index(flow_data.current_phase)
        if current_index < len(phase_order) - 1:
            status_data["next_phase"] = phase_order[current_index + 1]
        
        logger.info(f"✅ Flow status retrieved: {flow_id}")
        return FlowStatusResponse(**status_data)
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/flows/{flow_id}/execute/{phase}", response_model=FlowExecutionResponse)
async def execute_phase(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    phase: FlowPhase = Path(..., description="Phase to execute"),
    request: PhaseExecution = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowExecutionResponse:
    """
    Execute a specific flow phase
    """
    try:
        logger.info(f"🔄 Executing phase {phase} for flow: {flow_id}")
        
        if request is None:
            request = PhaseExecution(phase=phase)
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Execute the phase using V3 service
        execution_result = await flow_service.execute_phase(
            flow_id=str(flow_id),
            phase=phase.value,
            data=request.data if request else {}
        )
        
        # Build response
        result = {
            "success": execution_result.get("success", True),
            "flow_id": flow_id,
            "action": f"execute_{phase}",
            "status": FlowStatus.IN_PROGRESS if execution_result.get("success") else FlowStatus.FAILED,
            "message": execution_result.get("message", f"Phase {phase} execution completed"),
            "timestamp": datetime.utcnow(),
            "phase": phase,
            "crewai_execution": execution_result.get("crewai_status", "completed"),
            "database_execution": "completed",
            "agent_insights": execution_result.get("agent_insights", []),
            "errors": execution_result.get("errors", [])
        }
        
        logger.info(f"✅ Phase execution completed: {phase}")
        return FlowExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Failed to execute phase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute phase: {str(e)}"
        )


@router.get("/flows", response_model=FlowListResponse)
async def list_flows(
    status_filter: Optional[FlowStatus] = Query(None, description="Filter by status"),
    current_phase: Optional[FlowPhase] = Query(None, description="Filter by current phase"),
    execution_mode: Optional[ExecutionMode] = Query(None, description="Filter by execution mode"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowListResponse:
    """
    List all flows with filtering and pagination
    """
    try:
        logger.info(f"📋 Listing flows with filters")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get flows from V3 service
        flows_data = await flow_service.list_flows(
            limit=page_size * 10,  # Get extra for filtering
            offset=(page - 1) * page_size,
            status_filter=status_filter.value if status_filter else None,
            execution_mode=execution_mode.value if execution_mode else None
        )
        
        flows = []
        for flow_data in flows_data:
            try:
                # Get detailed status for each flow
                flow_status = await flow_service.get_flow_status(str(flow_data.id))
                
                flow_response = FlowResponse(
                    flow_id=flow_data.id,
                    name=flow_data.name,
                    description=flow_data.description,
                    status=FlowStatus(flow_data.status) if flow_data.status else FlowStatus.INITIALIZED,
                    current_phase=FlowPhase(flow_data.current_phase) if flow_data.current_phase else FlowPhase.INITIALIZATION,
                    progress_percentage=flow_status.get("progress_percentage", 0.0),
                    created_at=flow_data.created_at,
                    updated_at=flow_data.updated_at,
                    client_account_id=flow_data.client_account_id,
                    engagement_id=flow_data.engagement_id,
                    user_id=flow_data.created_by_user_id,
                    execution_mode=ExecutionMode(flow_data.execution_mode) if flow_data.execution_mode else ExecutionMode.HYBRID,
                    phases_completed=flow_status.get("phases_completed", []),
                    phases_status=flow_status.get("phases_status", {}),
                    metadata=flow_data.metadata or {},
                    agent_insights=flow_status.get("agent_insights", []),
                    crewai_status="active" if flow_data.crewai_flow_id else "pending",
                    database_status="active",
                    assets=[],
                    records_total=flow_status.get("records_total", 0)
                )
                
                # Apply additional filters (phase filter)
                if current_phase and flow_response.current_phase != current_phase:
                    continue
                    
                flows.append(flow_response)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert flow data: {e}")
                continue
        
        total_flows = len(flows)
        
        # Apply pagination
        start_idx = 0  # Already handled by service offset
        end_idx = min(page_size, len(flows))
        paginated_flows = flows[start_idx:end_idx]
        
        # Calculate pagination info
        has_next = len(flows) >= page_size
        has_previous = page > 1
        
        result = FlowListResponse(
            flows=paginated_flows,
            total=total_flows,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
        
        logger.info(f"✅ Flow list retrieved: {len(paginated_flows)} items")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to list flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list flows: {str(e)}"
        )


@router.delete("/flows/{flow_id}", response_model=FlowDeletionResponse)
async def delete_flow(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    force_delete: bool = Query(False, description="Force delete even if flow is active"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowDeletionResponse:
    """
    Soft delete a flow and its resources
    """
    try:
        logger.info(f"🗑️ Deleting flow: {flow_id}, force: {force_delete}")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Delete the flow using V3 service
        deletion_result = await flow_service.delete_flow(
            str(flow_id), 
            cascade=force_delete
        )
        
        if not deletion_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "force_delete": force_delete,
            "message": f"Flow {flow_id} deleted successfully",
            "timestamp": datetime.utcnow(),
            "cleanup_summary": {
                "flows_deleted": 1,
                "assets_deleted": deletion_result.get("assets_deleted", 0),
                "imports_deleted": deletion_result.get("imports_deleted", 0)
            },
            "crewai_cleanup": {"status": "completed"},
            "database_cleanup": {"status": "completed"}
        }
        
        logger.info(f"✅ Flow deleted: {flow_id}")
        return FlowDeletionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flow: {str(e)}"
        )


# === Flow Control Endpoints ===

@router.post("/flows/{flow_id}/pause", response_model=FlowExecutionResponse)
async def pause_flow(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    request: FlowPauseRequest = FlowPauseRequest(),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowExecutionResponse:
    """
    Pause a running discovery flow
    """
    try:
        logger.info(f"⏸️ Pausing flow: {flow_id}, reason: {request.reason}")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Pause the flow using V3 service
        pause_result = await flow_service.pause_flow(
            str(flow_id),
            reason=request.reason
        )
        
        result = {
            "success": pause_result.get("success", True),
            "flow_id": flow_id,
            "action": "paused",
            "status": FlowStatus.PAUSED,
            "message": pause_result.get("message", f"Flow {flow_id} paused: {request.reason}"),
            "timestamp": datetime.utcnow(),
            "crewai_execution": "paused",
            "database_execution": "paused",
            "agent_insights": pause_result.get("agent_insights", []),
            "errors": pause_result.get("errors", [])
        }
        
        logger.info(f"✅ Flow paused: {flow_id}")
        return FlowExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Failed to pause flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause flow: {str(e)}"
        )


@router.post("/flows/{flow_id}/resume", response_model=FlowExecutionResponse)
async def resume_flow(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    request: FlowResumeRequest = FlowResumeRequest(),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowExecutionResponse:
    """
    Resume a paused discovery flow
    """
    try:
        logger.info(f"▶️ Resuming flow: {flow_id}")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Prepare resume context
        resume_context = request.resume_context or {"trigger": "user_requested"}
        if request.target_phase:
            resume_context["target_phase"] = str(request.target_phase)
        if request.human_input:
            resume_context["human_input"] = request.human_input
        
        # Resume the flow using V3 service
        resume_result = await flow_service.resume_flow(
            str(flow_id),
            context=resume_context
        )
        
        result = {
            "success": resume_result.get("success", True),
            "flow_id": flow_id,
            "action": "resumed",
            "status": FlowStatus.IN_PROGRESS,
            "message": resume_result.get("message", f"Flow {flow_id} resumed successfully"),
            "timestamp": datetime.utcnow(),
            "crewai_execution": "resumed",
            "database_execution": "running",
            "agent_insights": resume_result.get("agent_insights", []),
            "errors": resume_result.get("errors", []),
            "next_phase": resume_result.get("next_phase")
        }
        
        logger.info(f"✅ Flow resumed: {flow_id}")
        return FlowExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Failed to resume flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flow: {str(e)}"
        )


# === Asset Management Endpoints ===

@router.post("/flows/{flow_id}/promote-assets", response_model=AssetPromotionResponse)
async def promote_assets(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> AssetPromotionResponse:
    """
    Promote discovery assets to main assets table
    """
    try:
        logger.info(f"🚀 Promoting assets for flow: {flow_id}")
        
        from app.services.asset_creation_bridge_service import AssetCreationBridgeService
        
        bridge_service = AssetCreationBridgeService(db, context)
        creation_result = await bridge_service.create_assets_from_discovery(
            discovery_flow_id=flow_id,
            user_id=uuid.UUID(context.user_id) if context.user_id and context.user_id != "anonymous" else None
        )
        
        result = AssetPromotionResponse(
            success=creation_result.get("success", False),
            flow_id=flow_id,
            message=f"Successfully promoted {creation_result.get('statistics', {}).get('assets_created', 0)} assets",
            timestamp=datetime.utcnow(),
            assets_promoted=creation_result.get("statistics", {}).get("assets_created", 0),
            assets_skipped=creation_result.get("statistics", {}).get("assets_skipped", 0),
            errors=creation_result.get("statistics", {}).get("errors", 0),
            statistics=creation_result.get("statistics", {})
        )
        
        logger.info(f"✅ Asset promotion completed: {result.assets_promoted} assets")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to promote assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to promote assets: {str(e)}"
        )


# === Health Check ===

@router.get("/health", response_model=FlowHealthResponse)
async def health_check():
    """
    Discovery flow health check for V3 services
    """
    # Check V3 service availability
    v3_services_available = True
    try:
        from app.services.v3.discovery_flow_service import V3DiscoveryFlowService
        from app.services.v3.data_import_service import V3DataImportService
        from app.services.v3.field_mapping_service import V3FieldMappingService
        from app.services.v3.asset_service import V3AssetService
        v3_services_available = True
    except ImportError:
        v3_services_available = False
    
    return FlowHealthResponse(
        timestamp=datetime.utcnow(),
        components={
            "v3_discovery_flow_service": v3_services_available,
            "v3_data_import_service": v3_services_available,
            "v3_field_mapping_service": v3_services_available,
            "v3_asset_service": v3_services_available,
            "database_connectivity": True  # Assumes DB is working if endpoint is reached
        }
    )