"""
Unified Discovery Flow API v3
Consolidates all discovery flow operations into a single, coherent API
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.api.v3.schemas.discovery import (
    FlowCreate, FlowUpdate, FlowResponse, FlowListResponse, FlowStatusResponse,
    FlowExecutionResponse, FlowDeletionResponse, FlowHealthResponse,
    PhaseExecution, FlowResumeRequest, FlowPauseRequest, AssetPromotionResponse,
    FlowFilterParams, PaginationParams, FlowStatus, FlowPhase, ExecutionMode,
    # New schemas for missing functionality
    FlowValidationRequest, FlowValidationResponse,
    FlowRecoveryRequest, FlowRecoveryResponse,
    UserApprovalRequest, UserApprovalResponse,
    ValidationReportRequest, ValidationReportResponse,
    FlowCleanupRequest, FlowCleanupResponse,
    BulkValidationRequest, BulkValidationResponse
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
        flow_state = request.metadata or {}
        if request.description:
            flow_state['description'] = request.description
        
        flow = await flow_service.create_flow(
            flow_name=request.name,
            metadata=flow_state,
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
                user_id=str(context.user_id) if context.user_id and context.user_id != "anonymous" else None
            )
            
            # Update flow with data import ID
            await flow_service.update_flow(
                str(flow.id),
                data_import_id=str(data_import.id)
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
            "name": flow.flow_name,
            "description": (flow.flow_state or {}).get('description', request.description) if hasattr(flow, 'flow_state') else request.description,
            "client_account_id": flow.client_account_id,
            "engagement_id": flow.engagement_id,
            "user_id": flow.user_id or context.user_id,
            "status": FlowStatus.INITIALIZING,
            "current_phase": FlowPhase.INITIALIZATION,
            "progress_percentage": flow_status.get("progress_percentage", 0.0),
            "phases_completed": flow_status.get("phases_completed", []),
            "phases_status": flow_status.get("phases_status", {}),
            "execution_mode": ExecutionMode.HYBRID,
            "crewai_status": "initialized" if flow.flow_id else "pending",
            "database_status": "initialized",
            "metadata": flow.flow_state or {},
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
    flow_id: uuid.UUID,
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
            "name": flow.flow_name,
            "description": (flow.flow_state or {}).get('description') if hasattr(flow, 'flow_state') else None,
            "client_account_id": flow.client_account_id,
            "engagement_id": flow.engagement_id,
            "user_id": flow.user_id or context.user_id,
            "status": FlowStatus(flow.status) if flow.status else FlowStatus.INITIALIZED,
            "current_phase": FlowPhase(flow.current_phase) if flow.current_phase else FlowPhase.INITIALIZATION,
            "progress_percentage": flow_status.get("progress_percentage", 0.0),
            "phases_completed": flow_status.get("phases_completed", []),
            "phases_status": flow_status.get("phases_status", {}),
            "execution_mode": ExecutionMode.HYBRID,
            "crewai_status": "active" if flow.flow_id else "pending",
            "database_status": "active",
            "metadata": flow.flow_state or {},
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
    flow_id: uuid.UUID,
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
            FlowPhase.DATA_VALIDATION,
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
    flow_id: uuid.UUID,
    phase: FlowPhase,
    request: Optional[PhaseExecution] = None,
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
        
        logger.info(f"Service returned {len(flows_data)} flows")
        
        flows = []
        for flow_dict in flows_data:
            try:
                # Map legacy status values
                status_mapping = {
                    'complete': 'completed',
                    'in_progress': 'running'
                }
                flow_status_value = flow_dict.get('status', 'initialized')
                flow_status_value = status_mapping.get(flow_status_value, flow_status_value)
                
                # Map legacy phase values
                phase_mapping = {
                    'initialization_phase': 'initialization',
                    'data_import_phase': 'data_validation',
                    'field_mapping_phase': 'field_mapping',
                    'asset_intelligence_phase': 'inventory_building',
                    'dependencies_phase': 'app_server_dependencies'
                }
                flow_phase_value = flow_dict.get('current_phase', 'initialization')
                flow_phase_value = phase_mapping.get(flow_phase_value, flow_phase_value)
                
                flow_response = FlowResponse(
                    flow_id=uuid.UUID(flow_dict['flow_id']),
                    name=flow_dict['flow_name'],
                    description=None,
                    status=FlowStatus(flow_status_value) if flow_status_value in [s.value for s in FlowStatus] else FlowStatus.INITIALIZED,
                    current_phase=FlowPhase(flow_phase_value) if flow_phase_value in [p.value for p in FlowPhase] else FlowPhase.INITIALIZATION,
                    progress_percentage=flow_dict.get('progress_percentage', 0.0),
                    created_at=datetime.fromisoformat(flow_dict['created_at']) if flow_dict['created_at'] else datetime.now(),
                    updated_at=datetime.fromisoformat(flow_dict['updated_at']) if flow_dict['updated_at'] else datetime.now(),
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id,
                    execution_mode=ExecutionMode.HYBRID,
                    phases_completed=[],
                    phases_status={},
                    metadata={},
                    agent_insights=[],
                    crewai_status="active",
                    database_status="active",
                    assets=[],
                    records_total=0
                )
                
                # Apply additional filters (phase filter)
                if current_phase and flow_response.current_phase != current_phase:
                    continue
                    
                flows.append(flow_response)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert flow {flow_dict.get('flow_id', 'unknown')}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
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
    flow_id: uuid.UUID,
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
    flow_id: uuid.UUID,
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
    flow_id: uuid.UUID,
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
    flow_id: uuid.UUID,
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


# === Validation & Recovery Endpoints ===

@router.post("/flows/{flow_id}/validate", response_model=FlowValidationResponse)
async def validate_flow(
    flow_id: uuid.UUID,
    request: FlowValidationRequest = FlowValidationRequest(),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowValidationResponse:
    """
    Validate flow state and integrity
    """
    try:
        logger.info(f"🔍 Validating flow: {flow_id}")
        
        # Initialize V3 Discovery Flow Service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get flow to validate it exists
        flow = await flow_service.get_flow(str(flow_id))
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        issues = []
        warnings = []
        persistence_status = {}
        crewai_state_status = {}
        
        # Check persistence layer if requested
        if request.check_persistence:
            try:
                from app.services.crewai_flows.flow_state_bridge import FlowStateBridge
                flow_bridge = FlowStateBridge(context)
                state = await flow_bridge.recover_flow_state(str(flow_id))
                
                if state:
                    persistence_status["status"] = "healthy"
                    persistence_status["has_state"] = True
                    persistence_status["current_phase"] = state.current_phase
                else:
                    persistence_status["status"] = "warning"
                    persistence_status["has_state"] = False
                    warnings.append("No persisted state found in PostgreSQL")
            except Exception as e:
                persistence_status["status"] = "error"
                persistence_status["error"] = str(e)
                issues.append(f"Persistence layer error: {str(e)}")
        
        # Check CrewAI state if requested
        if request.check_crewai_state:
            if flow.flow_id:
                crewai_state_status["status"] = "exists"
                crewai_state_status["flow_id"] = str(flow.flow_id)
            else:
                crewai_state_status["status"] = "not_initialized"
                warnings.append("CrewAI flow not yet initialized")
        
        # Comprehensive validation checks
        if request.comprehensive:
            # Check data integrity
            flow_status = await flow_service.get_flow_status(str(flow_id))
            
            if flow_status.get("records_total", 0) == 0 and flow.status != FlowStatus.INITIALIZING:
                warnings.append("No records found in flow")
            
            if flow.status == FlowStatus.FAILED:
                issues.append("Flow is in FAILED state")
            
            # Check phase progression
            phases_completed = flow_status.get("phases_completed", [])
            if flow.current_phase != FlowPhase.INITIALIZATION and len(phases_completed) == 0:
                warnings.append("No phases marked as completed despite non-initial phase")
        
        is_valid = len(issues) == 0
        
        recommendations = []
        if not is_valid:
            recommendations.append("Consider recovering flow from latest checkpoint")
        if len(warnings) > 0:
            recommendations.append("Review warnings and ensure flow is progressing correctly")
        
        return FlowValidationResponse(
            flow_id=flow_id,
            is_valid=is_valid,
            validation_timestamp=datetime.utcnow(),
            issues=issues,
            warnings=warnings,
            persistence_status=persistence_status,
            crewai_state_status=crewai_state_status,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to validate flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate flow: {str(e)}"
        )


@router.post("/flows/{flow_id}/recover", response_model=FlowRecoveryResponse)
async def recover_flow(
    flow_id: uuid.UUID,
    request: FlowRecoveryRequest = FlowRecoveryRequest(),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowRecoveryResponse:
    """
    Recover flow from failed or inconsistent state
    """
    try:
        logger.info(f"🔧 Recovering flow: {flow_id}, strategy: {request.recovery_strategy}")
        
        # Initialize services
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get current flow state
        flow = await flow_service.get_flow(str(flow_id))
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        state_before = {
            "status": flow.status,
            "phase": flow.current_phase,
            "updated_at": flow.updated_at.isoformat()
        }
        
        recovery_successful = False
        recovered_from_checkpoint = None
        state_after = None
        
        # Try recovery based on strategy
        if request.recovery_strategy == "latest_checkpoint":
            # Recover from PostgreSQL persistence
            from app.services.crewai_flows.flow_state_bridge import FlowStateBridge
            flow_bridge = FlowStateBridge(context)
            
            recovered_state = await flow_bridge.recover_flow_state(str(flow_id))
            if recovered_state:
                # Update flow with recovered state
                await flow_service.update_flow(
                    str(flow_id),
                    status=FlowStatus.IN_PROGRESS,
                    current_phase=recovered_state.current_phase,
                    metadata={"recovered_at": datetime.utcnow().isoformat()}
                )
                recovery_successful = True
                recovered_from_checkpoint = datetime.utcnow()
                state_after = {
                    "status": FlowStatus.IN_PROGRESS,
                    "phase": recovered_state.current_phase,
                    "updated_at": datetime.utcnow().isoformat()
                }
        
        elif request.recovery_strategy == "reset_to_phase":
            # Reset to a specific phase (requires force_recovery)
            if request.force_recovery:
                # Reset to field mapping phase as safe starting point
                await flow_service.update_flow(
                    str(flow_id),
                    status=FlowStatus.IN_PROGRESS,
                    current_phase=FlowPhase.FIELD_MAPPING,
                    metadata={"reset_at": datetime.utcnow().isoformat()}
                )
                recovery_successful = True
                state_after = {
                    "status": FlowStatus.IN_PROGRESS,
                    "phase": FlowPhase.FIELD_MAPPING,
                    "updated_at": datetime.utcnow().isoformat()
                }
        
        message = "Recovery successful" if recovery_successful else "Recovery failed - no valid checkpoint found"
        
        return FlowRecoveryResponse(
            flow_id=flow_id,
            recovery_successful=recovery_successful,
            recovery_strategy_used=request.recovery_strategy,
            recovered_from_checkpoint=recovered_from_checkpoint,
            recovery_timestamp=datetime.utcnow(),
            state_before_recovery=state_before,
            state_after_recovery=state_after,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to recover flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to recover flow: {str(e)}"
        )


@router.get("/flows/{flow_id}/validation-report", response_model=ValidationReportResponse)
async def get_validation_report(
    flow_id: uuid.UUID,
    include_details: bool = Query(True, description="Include detailed validation results"),
    phase: Optional[str] = Query(None, description="Specific phase to validate"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> ValidationReportResponse:
    """
    Get comprehensive validation report for a flow
    """
    try:
        logger.info(f"📊 Getting validation report for flow: {flow_id}")
        
        # Get flow details
        flow_data = await get_flow(flow_id, db, context)
        
        # Phase validations
        phase_validations = {}
        
        # Validate each phase
        for phase in FlowPhase:
            phase_validation = {
                "status": "not_started",
                "valid": True,
                "issues": []
            }
            
            if phase in flow_data.phases_completed:
                phase_validation["status"] = "completed"
            elif phase == flow_data.current_phase:
                phase_validation["status"] = "in_progress"
            
            # Add phase-specific validation
            if phase and phase != phase.value:
                continue
                
            phase_validations[phase.value] = phase_validation
        
        # Calculate data quality score
        total_records = flow_data.records_total or 1
        valid_records = flow_data.records_valid or 0
        data_quality_score = (valid_records / total_records) * 100 if total_records > 0 else 0.0
        
        # Security assessment
        security_assessment = {
            "risk_level": "low",
            "issues_found": 0,
            "recommendations": []
        }
        
        # Check if flow needs approval
        awaiting_approval = flow_data.status == FlowStatus.PAUSED and "approval_required" in flow_data.metadata
        
        recommendations = []
        if data_quality_score < 80:
            recommendations.append("Data quality is below 80%, consider data cleansing")
        if awaiting_approval:
            recommendations.append("Flow is awaiting user approval to proceed")
        
        return ValidationReportResponse(
            flow_id=flow_id,
            validation_status="valid" if data_quality_score >= 80 else "needs_attention",
            phase_validations=phase_validations if include_details else {},
            data_quality_score=data_quality_score,
            security_assessment=security_assessment,
            recommendations=recommendations,
            awaiting_approval=awaiting_approval,
            report_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get validation report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation report: {str(e)}"
        )


# === User Approval Endpoints ===

@router.post("/flows/{flow_id}/approve", response_model=UserApprovalResponse)
async def approve_flow_phase(
    flow_id: uuid.UUID,
    request: UserApprovalRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> UserApprovalResponse:
    """
    Record user approval for a flow phase
    """
    try:
        logger.info(f"✅ Processing user approval for flow: {flow_id}, phase: {request.phase_to_approve}")
        
        # Initialize services
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get flow
        flow = await flow_service.get_flow(str(flow_id))
        if not flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        # Update metadata with approval
        flow_state = flow.flow_state or {}
        approvals = flow_state.get("approvals", {})
        approvals[request.phase_to_approve] = {
            "approved": request.approved,
            "user_id": str(context.user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": request.user_feedback
        }
        flow_state["approvals"] = approvals
        
        # Apply any user modifications
        if request.modifications:
            flow_state["user_modifications"] = flow_state.get("user_modifications", {})
            flow_state["user_modifications"][request.phase_to_approve] = request.modifications
        
        # Update flow
        await flow_service.update_flow(
            str(flow_id),
            flow_state=flow_state
        )
        
        flow_resumed = False
        next_phase = None
        
        # If approved and flow was paused for approval, resume it
        if request.approved and flow.status == FlowStatus.PAUSED:
            # Resume flow
            resume_result = await flow_service.resume_flow(str(flow_id))
            flow_resumed = resume_result.get("success", False)
            
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
            
            try:
                current_index = phase_order.index(FlowPhase(request.phase_to_approve))
                if current_index < len(phase_order) - 1:
                    next_phase = phase_order[current_index + 1].value
            except ValueError:
                pass
        
        return UserApprovalResponse(
            flow_id=flow_id,
            approval_recorded=True,
            approved_phase=request.phase_to_approve,
            next_phase=next_phase,
            flow_resumed=flow_resumed,
            approval_timestamp=datetime.utcnow(),
            message=f"Approval recorded for {request.phase_to_approve}" + (" - flow resumed" if flow_resumed else "")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process approval: {str(e)}"
        )


# === Maintenance Endpoints ===

@router.post("/flows/cleanup", response_model=FlowCleanupResponse)
async def cleanup_expired_flows(
    request: FlowCleanupRequest = FlowCleanupRequest(),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowCleanupResponse:
    """
    Clean up expired or abandoned flows
    """
    try:
        logger.info(f"🧹 Cleaning up flows older than {request.older_than_days} days")
        
        # Initialize service
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        # Get all flows
        flows = await flow_service.list_flows(limit=1000)
        
        flows_identified = 0
        flows_cleaned = 0
        cleaned_flow_ids = []
        cutoff_date = datetime.utcnow() - timedelta(days=request.older_than_days)
        
        for flow_dict in flows:
            # Parse updated_at from string
            updated_at_str = flow_dict.get('updated_at')
            if not updated_at_str:
                continue
                
            try:
                from dateutil import parser
                updated_at = parser.parse(updated_at_str).replace(tzinfo=None)
            except:
                continue
            
            # Check if flow should be cleaned
            should_clean = updated_at < cutoff_date
            
            # Apply status filter if provided
            if request.status_filter:
                flow_status = flow_dict.get('status')
                should_clean = should_clean and flow_status in [s.value for s in request.status_filter]
            
            if should_clean:
                flows_identified += 1
                
                if not request.dry_run:
                    # Delete the flow
                    flow_id = flow_dict.get('flow_id')
                    if flow_id:
                        await flow_service.delete_flow(flow_id, cascade=True)
                        flows_cleaned += 1
                        cleaned_flow_ids.append(UUID(flow_id))
        
        message = f"Identified {flows_identified} flows for cleanup"
        if not request.dry_run:
            message = f"Cleaned up {flows_cleaned} flows"
        
        return FlowCleanupResponse(
            flows_cleaned=flows_cleaned,
            flows_identified=flows_identified,
            cleanup_timestamp=datetime.utcnow(),
            dry_run=request.dry_run,
            cleaned_flow_ids=cleaned_flow_ids,
            space_reclaimed_mb=flows_cleaned * 0.5 if not request.dry_run else None,  # Rough estimate
            message=message
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup flows: {str(e)}"
        )


@router.post("/flows/bulk-validate", response_model=BulkValidationResponse)
async def bulk_validate_flows(
    request: BulkValidationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> BulkValidationResponse:
    """
    Validate multiple flows in bulk
    """
    try:
        logger.info(f"🔍 Bulk validating {len(request.flow_ids)} flows")
        
        start_time = datetime.utcnow()
        validation_results = {}
        valid_flows = 0
        invalid_flows = 0
        
        for flow_id in request.flow_ids:
            try:
                # Validate each flow
                validation_request = FlowValidationRequest(
                    comprehensive=request.validation_type == "comprehensive",
                    check_persistence=True,
                    check_crewai_state=True
                )
                
                validation_response = await validate_flow(
                    flow_id=flow_id,
                    request=validation_request,
                    db=db,
                    context=context
                )
                
                validation_results[str(flow_id)] = {
                    "is_valid": validation_response.is_valid,
                    "issues": validation_response.issues,
                    "warnings": validation_response.warnings
                }
                
                if validation_response.is_valid:
                    valid_flows += 1
                else:
                    invalid_flows += 1
                    
            except Exception as e:
                validation_results[str(flow_id)] = {
                    "is_valid": False,
                    "issues": [f"Validation error: {str(e)}"],
                    "warnings": []
                }
                invalid_flows += 1
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return BulkValidationResponse(
            total_flows=len(request.flow_ids),
            valid_flows=valid_flows,
            invalid_flows=invalid_flows,
            validation_results=validation_results,
            validation_timestamp=datetime.utcnow(),
            duration_seconds=duration
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to bulk validate flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk validate flows: {str(e)}"
        )


# === Missing Frontend Endpoints ===

@router.get("/flows/{flow_id}/assets", response_model=List[Dict[str, Any]])
async def get_flow_assets(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> List[Dict[str, Any]]:
    """Get assets for a specific flow"""
    try:
        # Initialize asset service
        asset_service = V3AssetService(
            db,
            str(context.client_account_id),
            str(context.engagement_id)
        )
        
        assets = await asset_service.get_assets_for_flow(str(flow_id))
        return assets
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow assets: {str(e)}"
        )


@router.get("/flows/{flow_id}/processing-status", response_model=Dict[str, Any])
async def get_processing_status(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """Get real-time processing status for a flow"""
    try:
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        flow_status = await flow_service.get_flow_status(str(flow_id))
        if not flow_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        # Return processing-specific status
        return {
            "flow_id": str(flow_id),
            "status": flow_status.get("status", "unknown"),
            "current_phase": flow_status.get("current_phase", "unknown"),
            "progress_percentage": flow_status.get("progress_percentage", 0.0),
            "is_processing": flow_status.get("status") in ["running", "in_progress"],
            "last_activity": flow_status.get("updated_at"),
            "events": [],  # TODO: Integrate with event system
            "agent_status": "active" if flow_status.get("crewai_state_data") else "idle"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing status: {str(e)}"
        )


@router.get("/flows/{flow_id}/insights", response_model=List[Dict[str, Any]])
async def get_agent_insights(
    flow_id: uuid.UUID,
    page_context: Optional[str] = Query(None, description="Context for filtering insights"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> List[Dict[str, Any]]:
    """Get agent insights for a flow"""
    try:
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        flow_status = await flow_service.get_flow_status(str(flow_id))
        if not flow_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
        # Extract insights from flow state
        insights = []
        crewai_state = flow_status.get("crewai_state_data", {})
        
        # Get insights from various sources
        if "agent_insights" in crewai_state:
            insights.extend(crewai_state["agent_insights"])
        
        # Filter by page context if provided
        if page_context:
            insights = [
                insight for insight in insights 
                if insight.get("context") == page_context or insight.get("phase") == page_context
            ]
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get agent insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent insights: {str(e)}"
        )


@router.post("/flows/{flow_id}/complete", response_model=FlowExecutionResponse)
async def complete_flow(
    flow_id: uuid.UUID,
    final_results: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowExecutionResponse:
    """Mark a flow as completed"""
    try:
        flow_service = V3DiscoveryFlowService(
            db, 
            str(context.client_account_id), 
            str(context.engagement_id)
        )
        
        success = await flow_service.complete_flow(str(flow_id), final_results or {})
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found or cannot be completed: {flow_id}"
            )
        
        return FlowExecutionResponse(
            success=True,
            flow_id=flow_id,
            action="completed",
            status=FlowStatus.COMPLETED,
            message="Flow marked as completed",
            timestamp=datetime.utcnow(),
            results=final_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to complete flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete flow: {str(e)}"
        )