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

# === Import Handlers (Modular Pattern) ===

# Flow Management Handler
try:
    from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
    FLOW_MANAGEMENT_AVAILABLE = True
except ImportError:
    FLOW_MANAGEMENT_AVAILABLE = False
    logger.warning("⚠️ Flow Management Handler not available")

# CrewAI Execution Handler
try:
    from app.api.v1.discovery_handlers.crewai_execution import CrewAIExecutionHandler
    CREWAI_EXECUTION_AVAILABLE = True
except ImportError:
    CREWAI_EXECUTION_AVAILABLE = False
    logger.warning("⚠️ CrewAI Execution Handler not available")

# Asset Management Handler
try:
    from app.api.v1.discovery_handlers.asset_management import AssetManagementHandler
    ASSET_MANAGEMENT_AVAILABLE = True
except ImportError:
    ASSET_MANAGEMENT_AVAILABLE = False
    logger.warning("⚠️ Asset Management Handler not available")


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
        
        # Generate flow_id
        flow_id = uuid.uuid4()
        
        flow_result = {
            "flow_id": flow_id,
            "name": request.name,
            "description": request.description,
            "client_account_id": request.client_account_id,
            "engagement_id": request.engagement_id,
            "user_id": context.user_id,
            "status": FlowStatus.INITIALIZING,
            "current_phase": FlowPhase.INITIALIZATION,
            "progress_percentage": 0.0,
            "phases_completed": [],
            "phases_status": {},
            "execution_mode": request.execution_mode,
            "crewai_status": "pending",
            "database_status": "pending",
            "metadata": request.metadata,
            "agent_insights": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "records_total": len(request.raw_data),
            "assets": []
        }
        
        # Initialize CrewAI execution if available
        if CREWAI_EXECUTION_AVAILABLE and request.execution_mode in [ExecutionMode.CREWAI, ExecutionMode.HYBRID]:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.initialize_flow(
                    flow_id=str(flow_id),
                    raw_data=request.raw_data,
                    metadata=request.metadata
                )
                flow_result["crewai_status"] = crewai_result.get("status", "initialized")
                flow_result["agent_insights"] = crewai_result.get("agent_insights", [])
                logger.info("✅ CrewAI execution initialized")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI initialization failed: {e}")
                flow_result["crewai_status"] = "failed"
        
        # Initialize PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE and request.execution_mode in [ExecutionMode.DATABASE, ExecutionMode.HYBRID]:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.create_flow(
                    flow_id=str(flow_id),
                    raw_data=request.raw_data,
                    metadata=request.metadata,
                    data_import_id=request.data_import_id
                )
                flow_result["database_status"] = "initialized"
                flow_result.update(db_result)
                logger.info("✅ PostgreSQL management initialized")
            except Exception as e:
                logger.warning(f"⚠️ Database initialization failed: {e}")
                flow_result["database_status"] = "failed"
        
        # Update overall status
        if flow_result["crewai_status"] == "initialized" or flow_result["database_status"] == "initialized":
            flow_result["status"] = FlowStatus.INITIALIZED
            flow_result["current_phase"] = FlowPhase.FIELD_MAPPING
        else:
            flow_result["status"] = FlowStatus.FAILED
        
        logger.info(f"✅ Discovery flow created: {flow_id}")
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
        
        # Initialize response with defaults
        flow_data = {
            "flow_id": flow_id,
            "name": "Unknown Flow",
            "client_account_id": context.client_account_id or uuid.uuid4(),
            "engagement_id": context.engagement_id or uuid.uuid4(),
            "user_id": context.user_id or uuid.uuid4(),
            "status": FlowStatus.FAILED,
            "current_phase": FlowPhase.INITIALIZATION,
            "progress_percentage": 0.0,
            "phases_completed": [],
            "phases_status": {},
            "execution_mode": ExecutionMode.HYBRID,
            "crewai_status": "unknown",
            "database_status": "unknown",
            "metadata": {},
            "agent_insights": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "assets": []
        }
        
        # Try to get flow data from PostgreSQL
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_data = await flow_handler.get_flow_status(str(flow_id))
                if db_data:
                    flow_data.update(db_data)
                    flow_data["database_status"] = "active"
                    logger.info("✅ PostgreSQL flow data retrieved")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL flow retrieval failed: {e}")
                flow_data["database_status"] = "failed"
        
        # Try to get flow data from CrewAI
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_data = await crewai_handler.get_flow_status(str(flow_id))
                if crewai_data:
                    flow_data.update(crewai_data)
                    flow_data["crewai_status"] = crewai_data.get("status", "active")
                    logger.info("✅ CrewAI flow data retrieved")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI flow retrieval failed: {e}")
                flow_data["crewai_status"] = "failed"
        
        # Check if flow was found
        if flow_data["database_status"] == "failed" and flow_data["crewai_status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {flow_id}"
            )
        
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
        
        execution_result = {
            "success": True,
            "flow_id": flow_id,
            "action": f"execute_{phase}",
            "status": FlowStatus.IN_PROGRESS,
            "message": f"Phase {phase} execution started",
            "timestamp": datetime.utcnow(),
            "phase": phase,
            "crewai_execution": "pending",
            "database_execution": "pending",
            "agent_insights": [],
            "errors": []
        }
        
        # Execute with CrewAI if available
        if CREWAI_EXECUTION_AVAILABLE and request.execution_mode in [ExecutionMode.CREWAI, ExecutionMode.HYBRID]:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.execute_phase(
                    phase=str(phase),
                    data=request.data
                )
                execution_result["crewai_execution"] = crewai_result.get("status", "completed")
                execution_result["agent_insights"] = crewai_result.get("agent_insights", [])
                logger.info("✅ CrewAI phase execution completed")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI execution failed: {e}")
                execution_result["crewai_execution"] = "failed"
                execution_result["errors"].append(f"CrewAI execution error: {str(e)}")
        
        # Execute with PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE and request.execution_mode in [ExecutionMode.DATABASE, ExecutionMode.HYBRID]:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.execute_phase(
                    phase=str(phase),
                    data=request.data
                )
                execution_result["database_execution"] = "completed"
                logger.info("✅ PostgreSQL phase execution completed")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL execution failed: {e}")
                execution_result["database_execution"] = "failed"
                execution_result["errors"].append(f"Database execution error: {str(e)}")
        
        # Update overall status
        if execution_result["crewai_execution"] == "completed" or execution_result["database_execution"] == "completed":
            execution_result["status"] = FlowStatus.COMPLETED
            execution_result["success"] = True
        else:
            execution_result["status"] = FlowStatus.FAILED
            execution_result["success"] = False
        
        logger.info(f"✅ Phase execution completed: {phase}")
        return FlowExecutionResponse(**execution_result)
        
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
        
        flows = []
        total_flows = 0
        
        # Get flows from PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_flows = await flow_handler.get_active_flows()
                
                # Apply filters
                if status_filter:
                    db_flows = [f for f in db_flows if f.get("status") == status_filter]
                if current_phase:
                    db_flows = [f for f in db_flows if f.get("current_phase") == current_phase]
                if execution_mode:
                    db_flows = [f for f in db_flows if f.get("execution_mode") == execution_mode]
                
                # Convert to FlowResponse format
                for flow_data in db_flows:
                    try:
                        flow_response = FlowResponse(
                            flow_id=flow_data.get("flow_id", uuid.uuid4()),
                            name=flow_data.get("name", "Unknown Flow"),
                            status=flow_data.get("status", FlowStatus.FAILED),
                            current_phase=flow_data.get("current_phase", FlowPhase.INITIALIZATION),
                            progress_percentage=flow_data.get("progress_percentage", 0.0),
                            created_at=datetime.fromisoformat(flow_data.get("created_at", datetime.utcnow().isoformat())),
                            updated_at=datetime.fromisoformat(flow_data.get("updated_at", datetime.utcnow().isoformat())),
                            client_account_id=context.client_account_id or uuid.uuid4(),
                            engagement_id=context.engagement_id or uuid.uuid4(),
                            execution_mode=flow_data.get("execution_mode", ExecutionMode.HYBRID),
                            phases_completed=flow_data.get("phases_completed", []),
                            metadata=flow_data.get("metadata", {}),
                            agent_insights=flow_data.get("agent_insights", []),
                            assets=[]
                        )
                        flows.append(flow_response)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to convert flow data: {e}")
                        continue
                
                total_flows = len(flows)
                logger.info(f"✅ Retrieved {len(flows)} flows from database")
            except Exception as e:
                logger.warning(f"⚠️ Database flow retrieval failed: {e}")
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_flows = flows[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total_flows + page_size - 1) // page_size
        has_next = page < total_pages
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
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "force_delete": force_delete,
            "message": f"Flow {flow_id} deleted successfully",
            "timestamp": datetime.utcnow(),
            "cleanup_summary": {},
            "crewai_cleanup": None,
            "database_cleanup": None
        }
        
        # Delete from CrewAI execution if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.delete_flow(str(flow_id), force_delete)
                result["crewai_cleanup"] = crewai_result.get("cleanup_summary", {})
                logger.info("✅ CrewAI flow deleted")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI deletion failed: {e}")
                result["crewai_cleanup"] = {"error": str(e)}
        
        # Delete from PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.delete_flow(str(flow_id), force_delete)
                result["database_cleanup"] = db_result.get("cleanup_summary", {})
                result["cleanup_summary"] = db_result.get("cleanup_summary", {})
                logger.info("✅ PostgreSQL flow deleted")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL deletion failed: {e}")
                result["database_cleanup"] = {"error": str(e)}
        
        logger.info(f"✅ Flow deleted: {flow_id}")
        return FlowDeletionResponse(**result)
        
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
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "action": "paused",
            "status": FlowStatus.PAUSED,
            "message": f"Flow {flow_id} paused: {request.reason}",
            "timestamp": datetime.utcnow(),
            "crewai_execution": "pending",
            "database_execution": "pending",
            "agent_insights": [],
            "errors": []
        }
        
        # Pause CrewAI flow if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                from app.services.crewai_flow_service import CrewAIFlowService
                crewai_flow_service = CrewAIFlowService(db)
                pause_result = await crewai_flow_service.pause_flow(str(flow_id), request.reason)
                result["crewai_execution"] = "paused"
                logger.info("✅ CrewAI flow paused")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI pause failed: {e}")
                result["crewai_execution"] = "failed"
                result["errors"].append(f"CrewAI pause error: {str(e)}")
        
        # Update PostgreSQL status
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                await flow_handler.update_flow_status(str(flow_id), "paused", request.reason)
                result["database_execution"] = "paused"
                logger.info("✅ PostgreSQL flow status updated to paused")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL pause update failed: {e}")
                result["database_execution"] = "failed"
                result["errors"].append(f"Database pause error: {str(e)}")
        
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
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "action": "resumed",
            "status": FlowStatus.IN_PROGRESS,
            "message": f"Flow {flow_id} resumed successfully",
            "timestamp": datetime.utcnow(),
            "crewai_execution": "pending",
            "database_execution": "pending",
            "agent_insights": [],
            "errors": []
        }
        
        # Resume CrewAI flow if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                from app.services.crewai_flow_service import CrewAIFlowService
                crewai_flow_service = CrewAIFlowService(db)
                
                resume_context = request.resume_context or {"trigger": "user_requested"}
                if request.target_phase:
                    resume_context["target_phase"] = str(request.target_phase)
                if request.human_input:
                    resume_context["human_input"] = request.human_input
                
                resume_result = await crewai_flow_service.resume_flow(str(flow_id), resume_context)
                result["crewai_execution"] = "resumed"
                result["next_phase"] = resume_result.get("next_phase", "unknown")
                logger.info("✅ CrewAI flow resumed")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI resume failed: {e}")
                result["crewai_execution"] = "failed"
                result["errors"].append(f"CrewAI resume error: {str(e)}")
        
        # Update PostgreSQL status
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                await flow_handler.update_flow_status(str(flow_id), "running", "resumed")
                result["database_execution"] = "running"
                logger.info("✅ PostgreSQL flow status updated to running")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL resume update failed: {e}")
                result["database_execution"] = "failed"
                result["errors"].append(f"Database resume error: {str(e)}")
        
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


# === Phase 2 Flow Manager Endpoints ===

@router.post("/flows/crewai", response_model=FlowResponse)
async def create_crewai_flow(
    request: FlowCreate,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> FlowResponse:
    """
    Create a new CrewAI flow using Phase 2 flow manager
    """
    try:
        from app.services.flows.manager import flow_manager
        
        # Prepare import data for flow creation
        import_data = {
            "flow_id": str(uuid.uuid4()),
            "import_id": request.name,  # Use name as import identifier
            "filename": f"{request.name}.data",
            "record_count": 0,  # Will be updated with actual data
            "raw_data": [],  # Initial empty data
            "session_id": str(uuid.uuid4())
        }
        
        # Create and start flow
        flow_id = await flow_manager.create_discovery_flow(db, context, import_data)
        
        # Return response
        return FlowResponse(
            flow_id=uuid.UUID(flow_id),
            name=request.name,
            description=request.description,
            status=FlowStatus.IN_PROGRESS,
            current_phase=FlowPhase.INITIALIZATION,
            execution_mode=request.execution_mode,
            progress_percentage=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            client_account_id=uuid.UUID(context.client_account_id),
            engagement_id=uuid.UUID(context.engagement_id),
            user_id=uuid.UUID(context.user_id) if context.user_id != "anonymous" else None,
            phases_completed=[],
            next_phase=FlowPhase.DATA_VALIDATION,
            estimated_completion=None
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to create CrewAI flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create CrewAI flow: {str(e)}"
        )


@router.get("/flows/{flow_id}/crewai-status")
async def get_crewai_flow_status(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get CrewAI flow status from Phase 2 flow manager
    """
    try:
        from app.services.flows.manager import flow_manager
        
        # Get flow status
        status_info = await flow_manager.get_flow_status(str(flow_id))
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CrewAI flow not found: {flow_id}"
            )
        
        return {
            "success": True,
            "data": status_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get CrewAI flow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/flows/{flow_id}/pause")
async def pause_crewai_flow(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Pause a CrewAI flow using Phase 2 flow manager
    """
    try:
        from app.services.flows.manager import flow_manager
        
        # Pause flow
        success = await flow_manager.pause_flow(str(flow_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found or not pausable: {flow_id}"
            )
        
        return {
            "success": True,
            "message": f"Flow {flow_id} paused successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to pause CrewAI flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause flow: {str(e)}"
        )


@router.post("/flows/{flow_id}/resume")
async def resume_crewai_flow(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Resume a CrewAI flow using Phase 2 flow manager
    """
    try:
        from app.services.flows.manager import flow_manager
        
        # Resume flow
        success = await flow_manager.resume_flow(str(flow_id), db, context)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found or not resumable: {flow_id}"
            )
        
        return {
            "success": True,
            "message": f"Flow {flow_id} resumed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resume CrewAI flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flow: {str(e)}"
        )


@router.get("/flows/events/{flow_id}")
async def get_flow_events(
    flow_id: uuid.UUID = Path(..., description="Flow identifier"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get flow events from Phase 2 event bus
    """
    try:
        from app.services.flows.events import flow_event_bus
        
        # Get flow events
        events = flow_event_bus.get_flow_events(str(flow_id))
        recent_events = events[-limit:] if len(events) > limit else events
        
        # Convert events to JSON-serializable format
        event_data = []
        for event in recent_events:
            event_data.append({
                "flow_id": event.flow_id,
                "event_type": event.event_type,
                "phase": event.phase,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "context": event.context
            })
        
        return {
            "success": True,
            "data": {
                "flow_id": str(flow_id),
                "events": event_data,
                "total_events": len(events),
                "returned_events": len(event_data)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow events: {str(e)}"
        )


@router.get("/flows/manager/status")
async def get_flow_manager_status(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> Dict[str, Any]:
    """
    Get overall flow manager status
    """
    try:
        from app.services.flows.manager import flow_manager
        from app.services.flows.events import flow_event_bus
        
        # Get all flow statuses
        flow_statuses = await flow_manager.get_all_flow_statuses()
        
        # Cleanup completed flows
        cleaned_count = await flow_manager.cleanup_completed_flows()
        
        # Get recent events
        recent_events = flow_event_bus.get_recent_events(50)
        
        return {
            "success": True,
            "data": {
                "active_flows": len(flow_manager.active_flows),
                "running_tasks": len(flow_manager.flow_tasks),
                "flows": flow_statuses,
                "cleaned_flows": cleaned_count,
                "recent_events": len(recent_events),
                "event_history_size": len(flow_event_bus.event_history),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow manager status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get manager status: {str(e)}"
        )


# === Health Check ===

@router.get("/health", response_model=FlowHealthResponse)
async def health_check():
    """
    Discovery flow health check including Phase 2 components
    """
    try:
        from app.services.flows.manager import flow_manager
        from app.services.flows.events import flow_event_bus
        phase2_available = True
    except ImportError:
        phase2_available = False
    
    return FlowHealthResponse(
        timestamp=datetime.utcnow(),
        components={
            "flow_management": FLOW_MANAGEMENT_AVAILABLE,
            "crewai_execution": CREWAI_EXECUTION_AVAILABLE,
            "asset_management": ASSET_MANAGEMENT_AVAILABLE,
            "phase2_flow_manager": phase2_available,
            "phase2_event_bus": phase2_available
        }
    )