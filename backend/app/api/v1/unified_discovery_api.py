"""
Consolidated Discovery API - Single Source of Truth
Integrates UnifiedDiscoveryFlow (CrewAI execution) with V2 management layer (PostgreSQL persistence).
Follows modular handler pattern for maintainability.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Discovery - Unified API"])

# === Import Handlers (Modular Pattern) ===

# Discovery Flow Management Handler
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

# === Request/Response Models ===

class InitializeDiscoveryRequest(BaseModel):
    """Unified request for initializing discovery flow"""
    raw_data: List[Dict[str, Any]] = Field(..., description="Raw CMDB data")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")
    import_session_id: Optional[str] = Field(default=None, description="Import session ID for backward compatibility")
    execution_mode: str = Field(default="hybrid", description="Execution mode: 'crewai', 'database', or 'hybrid'")

class DiscoveryFlowResponse(BaseModel):
    """Unified response for discovery flow operations"""
    flow_id: str
    session_id: Optional[str]
    client_account_id: str
    engagement_id: str
    user_id: str
    status: str
    current_phase: str
    progress_percentage: float
    phases: Dict[str, bool]
    crewai_status: Optional[str]
    database_status: Optional[str]
    agent_insights: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class FlowExecutionRequest(BaseModel):
    """Request for executing flow phases"""
    phase: Optional[str] = Field(default=None, description="Specific phase to execute")
    data: Optional[Dict[str, Any]] = Field(default={}, description="Phase-specific data")
    execution_mode: str = Field(default="hybrid", description="Execution mode")

# === Core Discovery Flow Endpoints ===

@router.post("/flow/initialize", response_model=DiscoveryFlowResponse)
async def initialize_discovery_flow(
    request: InitializeDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Initialize discovery flow with hybrid CrewAI + PostgreSQL architecture.
    Single entry point that coordinates both execution engine and management layer.
    """
    try:
        logger.info(f"🚀 Initializing unified discovery flow, mode: {request.execution_mode}")
        
        flow_result = {
            "flow_id": f"flow-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "session_id": request.import_session_id,
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "user_id": context.user_id,
            "status": "initializing",
            "current_phase": "initialization",
            "progress_percentage": 0.0,
            "phases": {
                "data_import": False,
                "field_mapping": False,
                "data_cleansing": False,
                "asset_inventory": False,
                "dependency_analysis": False,
                "tech_debt_analysis": False
            },
            "crewai_status": "pending",
            "database_status": "pending",
            "agent_insights": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Initialize CrewAI execution if available
        if CREWAI_EXECUTION_AVAILABLE and request.execution_mode in ["crewai", "hybrid"]:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.initialize_flow(
                    flow_id=flow_result["flow_id"],
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
        if FLOW_MANAGEMENT_AVAILABLE and request.execution_mode in ["database", "hybrid"]:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.create_flow(
                    flow_id=flow_result["flow_id"],
                    raw_data=request.raw_data,
                    metadata=request.metadata,
                    import_session_id=request.import_session_id
                )
                flow_result["database_status"] = "initialized"
                flow_result.update(db_result)
                logger.info("✅ PostgreSQL management initialized")
            except Exception as e:
                logger.warning(f"⚠️ Database initialization failed: {e}")
                flow_result["database_status"] = "failed"
        
        # Update overall status
        if flow_result["crewai_status"] == "initialized" or flow_result["database_status"] == "initialized":
            flow_result["status"] = "initialized"
            flow_result["current_phase"] = "data_import"
        else:
            flow_result["status"] = "failed"
        
        logger.info(f"✅ Discovery flow initialized: {flow_result['flow_id']}")
        return DiscoveryFlowResponse(**flow_result)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize discovery flow: {str(e)}"
        )

@router.get("/flow/status/{flow_id}", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get unified discovery flow status from both CrewAI and PostgreSQL layers.
    """
    try:
        logger.info(f"🔍 Getting discovery flow status: {flow_id}")
        
        # Ensure context values are not None to avoid Pydantic validation errors
        client_account_id = context.client_account_id or "11111111-1111-1111-1111-111111111111"
        engagement_id = context.engagement_id or "22222222-2222-2222-2222-222222222222"
        user_id = context.user_id or "347d1ecd-04f6-4e3a-86ca-d35703512301"
        
        flow_status = {
            "flow_id": flow_id,
            "session_id": None,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "user_id": user_id,
            "status": "unknown",
            "current_phase": "unknown",
            "progress_percentage": 0.0,
            "phases": {},
            "crewai_status": "unknown",
            "database_status": "unknown",
            "agent_insights": [],
            "created_at": "",
            "updated_at": datetime.now().isoformat()
        }
        
        # Get CrewAI status if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_status = await crewai_handler.get_flow_status(flow_id)
                # Preserve context fields when updating
                for key, value in crewai_status.items():
                    if key not in ["client_account_id", "engagement_id", "user_id"] or value is not None:
                        flow_status[key] = value
                flow_status["crewai_status"] = "active"
                logger.info("✅ CrewAI status retrieved")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI status retrieval failed: {e}")
                flow_status["crewai_status"] = "unavailable"
        
        # Get PostgreSQL status if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_status = await flow_handler.get_flow_status(flow_id)
                # Preserve context fields when updating
                for key, value in db_status.items():
                    if key not in ["client_account_id", "engagement_id", "user_id"] or value is not None:
                        flow_status[key] = value
                flow_status["database_status"] = "active"
                logger.info("✅ Database status retrieved")
            except Exception as e:
                logger.warning(f"⚠️ Database status retrieval failed: {e}")
                flow_status["database_status"] = "unavailable"
        
        # Determine overall status
        if flow_status["crewai_status"] == "active" or flow_status["database_status"] == "active":
            if flow_status["status"] == "unknown":
                flow_status["status"] = "active"
        else:
            flow_status["status"] = "not_found"
        
        logger.info(f"✅ Flow status retrieved: {flow_id}")
        return DiscoveryFlowResponse(**flow_status)
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )

@router.post("/flow/execute", response_model=Dict[str, Any])
async def execute_discovery_flow(
    request: FlowExecutionRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Execute discovery flow phase with coordinated CrewAI + PostgreSQL execution.
    """
    try:
        logger.info(f"🔄 Executing discovery flow phase: {request.phase}")
        
        execution_result = {
            "status": "started",
            "phase": request.phase,
            "crewai_execution": "pending",
            "database_execution": "pending",
            "agent_insights": []
        }
        
        # Execute with CrewAI if available
        if CREWAI_EXECUTION_AVAILABLE and request.execution_mode in ["crewai", "hybrid"]:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.execute_phase(
                    phase=request.phase,
                    data=request.data
                )
                execution_result["crewai_execution"] = crewai_result.get("status", "completed")
                execution_result["agent_insights"] = crewai_result.get("agent_insights", [])
                logger.info("✅ CrewAI phase execution completed")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI execution failed: {e}")
                execution_result["crewai_execution"] = "failed"
        
        # Execute with PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE and request.execution_mode in ["database", "hybrid"]:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.execute_phase(
                    phase=request.phase,
                    data=request.data
                )
                execution_result["database_execution"] = "completed"
                logger.info("✅ Database phase execution completed")
            except Exception as e:
                logger.warning(f"⚠️ Database execution failed: {e}")
                execution_result["database_execution"] = "failed"
        
        # Update overall status
        if execution_result["crewai_execution"] == "completed" or execution_result["database_execution"] == "completed":
            execution_result["status"] = "completed"
        else:
            execution_result["status"] = "failed"
        
        logger.info(f"✅ Discovery flow execution completed: {request.phase}")
        return execution_result
        
    except Exception as e:
        logger.error(f"❌ Failed to execute discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute discovery flow: {str(e)}"
        )

# === Active Flows Management ===

@router.get("/flows/active", response_model=Dict[str, Any])
async def get_active_discovery_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get active discovery flows from unified management layer.
    Consolidates data from both CrewAI and PostgreSQL sources.
    """
    try:
        logger.info("🔍 Getting active discovery flows")
        
        active_flows = {
            "success": True,
            "total_flows": 0,
            "active_flows": 0,
            "flow_details": [],
            "crewai_flows": 0,
            "database_flows": 0,
            "api_version": "unified",
            "timestamp": datetime.now().isoformat()
        }
        
        # Get flows from PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_flows = await flow_handler.get_active_flows()
                active_flows["database_flows"] = len(db_flows)
                active_flows["flow_details"].extend(db_flows)
                logger.info(f"✅ Retrieved {len(db_flows)} flows from database")
            except Exception as e:
                logger.warning(f"⚠️ Database flow retrieval failed: {e}")
        
        # Get flows from CrewAI if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_flows = await crewai_handler.get_active_flows()
                active_flows["crewai_flows"] = len(crewai_flows)
                # Merge with database flows (avoid duplicates)
                for crewai_flow in crewai_flows:
                    if not any(f["flow_id"] == crewai_flow["flow_id"] for f in active_flows["flow_details"]):
                        active_flows["flow_details"].append(crewai_flow)
                logger.info(f"✅ Retrieved {len(crewai_flows)} flows from CrewAI")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI flow retrieval failed: {e}")
        
        # Update totals
        active_flows["total_flows"] = len(active_flows["flow_details"])
        active_flows["active_flows"] = len([f for f in active_flows["flow_details"] if f.get("status") in ["running", "active"]])
        
        logger.info(f"✅ Retrieved {active_flows['total_flows']} total active flows")
        return active_flows
        
    except Exception as e:
        logger.error(f"❌ Failed to get active flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active flows: {str(e)}"
        )

# === Asset Management ===

@router.get("/assets/{flow_id}", response_model=List[Dict[str, Any]])
async def get_flow_assets(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get assets for a discovery flow from unified asset management.
    """
    try:
        logger.info(f"📦 Getting assets for flow: {flow_id}")
        
        assets = []
        
        if ASSET_MANAGEMENT_AVAILABLE:
            try:
                asset_handler = AssetManagementHandler(db, context)
                assets = await asset_handler.get_flow_assets(flow_id)
                logger.info(f"✅ Retrieved {len(assets)} assets for flow: {flow_id}")
            except Exception as e:
                logger.warning(f"⚠️ Asset retrieval failed: {e}")
                assets = []
        
        return assets
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow assets: {str(e)}"
        )

# === Health Check ===

@router.get("/health", response_model=Dict[str, Any])
async def discovery_health_check():
    """
    Unified discovery health check showing status of all components.
    """
    return {
        "status": "healthy",
        "service": "discovery-unified",
        "version": "1.0.0",
        "components": {
            "flow_management": FLOW_MANAGEMENT_AVAILABLE,
            "crewai_execution": CREWAI_EXECUTION_AVAILABLE,
            "asset_management": ASSET_MANAGEMENT_AVAILABLE
        },
        "architecture": "hybrid_crewai_postgresql",
        "timestamp": datetime.now().isoformat()
    }

# === Legacy Compatibility Endpoints ===

@router.post("/flow/continue/{flow_id}", response_model=Dict[str, Any])
async def continue_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Continue a paused or incomplete discovery flow.
    """
    try:
        logger.info(f"▶️ Continuing discovery flow: {flow_id}")
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "action": "continued",
            "status": "running",
            "message": f"Flow {flow_id} continued successfully",
            "timestamp": datetime.now().isoformat()
        }
        
        # Continue with CrewAI execution if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.continue_flow(flow_id)
                result["crewai_status"] = "continued"
                result["next_phase"] = crewai_result.get("next_phase", "analysis")
                logger.info("✅ CrewAI flow continued")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI continuation failed: {e}")
                result["crewai_status"] = "failed"
        
        # Continue with PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.continue_flow(flow_id)
                result["database_status"] = "continued"
                result.update(db_result)
                logger.info("✅ Database flow continued")
            except Exception as e:
                logger.warning(f"⚠️ Database continuation failed: {e}")
                result["database_status"] = "failed"
        
        logger.info(f"✅ Discovery flow continued: {flow_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to continue discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to continue discovery flow: {str(e)}"
        )

@router.post("/flow/complete/{flow_id}", response_model=Dict[str, Any])
async def complete_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Mark a discovery flow as complete.
    """
    try:
        logger.info(f"✅ Completing discovery flow: {flow_id}")
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "action": "completed",
            "status": "completed",
            "message": f"Flow {flow_id} completed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
        # Complete with CrewAI execution if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.complete_flow(flow_id)
                result["crewai_status"] = "completed"
                result["final_insights"] = crewai_result.get("insights", [])
                logger.info("✅ CrewAI flow completed")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI completion failed: {e}")
                result["crewai_status"] = "failed"
        
        # Complete with PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.complete_flow(flow_id)
                result["database_status"] = "completed"
                result.update(db_result)
                logger.info("✅ Database flow completed")
            except Exception as e:
                logger.warning(f"⚠️ Database completion failed: {e}")
                result["database_status"] = "failed"
        
        logger.info(f"✅ Discovery flow completed: {flow_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to complete discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete discovery flow: {str(e)}"
        )

@router.delete("/flow/{flow_id}", response_model=Dict[str, Any])
async def delete_discovery_flow(
    flow_id: str,
    force_delete: bool = Query(default=False, description="Force delete even if flow is active"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Delete a discovery flow and all associated data.
    """
    try:
        logger.info(f"🗑️ Deleting discovery flow: {flow_id}, force: {force_delete}")
        
        result = {
            "success": True,
            "flow_id": flow_id,
            "action": "deleted",
            "force_delete": force_delete,
            "message": f"Flow {flow_id} deleted successfully",
            "cleanup_summary": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Delete from CrewAI execution if available
        if CREWAI_EXECUTION_AVAILABLE:
            try:
                crewai_handler = CrewAIExecutionHandler(db, context)
                crewai_result = await crewai_handler.delete_flow(flow_id, force_delete)
                result["crewai_cleanup"] = crewai_result.get("cleanup_summary", {})
                logger.info("✅ CrewAI flow deleted")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI deletion failed: {e}")
                result["crewai_cleanup"] = {"error": str(e)}
        
        # Delete from PostgreSQL management if available
        if FLOW_MANAGEMENT_AVAILABLE:
            try:
                flow_handler = FlowManagementHandler(db, context)
                db_result = await flow_handler.delete_flow(flow_id, force_delete)
                result["database_cleanup"] = db_result.get("cleanup_summary", {})
                result["cleanup_summary"] = db_result.get("cleanup_summary", {})
                logger.info("✅ Database flow deleted")
            except Exception as e:
                logger.warning(f"⚠️ Database deletion failed: {e}")
                result["database_cleanup"] = {"error": str(e)}
        
        logger.info(f"✅ Discovery flow deleted: {flow_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to delete discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete discovery flow: {str(e)}"
        )

@router.post("/flow/run", response_model=Dict[str, Any])
async def run_discovery_flow_legacy(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Legacy endpoint for backward compatibility.
    Redirects to unified flow execution.
    """
    logger.info("🔄 Legacy flow run endpoint called, redirecting to unified execution")
    
    # Convert legacy request to new format
    unified_request = FlowExecutionRequest(
        phase=request.get("phase", "data_import"),
        data=request.get("data", {}),
        execution_mode="hybrid"
    )
    
    return await execute_discovery_flow(unified_request, db, context)

@router.get("/flow/status", response_model=DiscoveryFlowResponse)
async def get_flow_status_legacy(
    session_id: str = Query(..., description="Session ID for backward compatibility"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Legacy endpoint for backward compatibility.
    Converts session_id to flow_id lookup.
    """
    logger.info(f"🔄 Legacy status endpoint called with session_id: {session_id}")
    
    # Try to find flow by session_id
    flow_id = f"flow-{session_id}"  # Simple conversion for now
    
    return await get_discovery_flow_status(flow_id, db, context) 