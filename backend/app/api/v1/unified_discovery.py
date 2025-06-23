"""
Unified Discovery Flow API Endpoints
Consolidates all discovery flow API endpoints into a single, consistent interface.

Replaces:
- backend/app/api/v1/discovery/discovery_flow.py
- Multiple competing API implementations
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context
from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.crewai_flow_service import CrewAIFlowService
from app.models.workflow_state import WorkflowState
from app.services.crewai_flows.discovery_flow_state_manager import DiscoveryFlowStateManager
from app.models.data_import.core import RawImportRecord
from app.models.data_import_session import DataImportSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-discovery", tags=["Unified Discovery Flow"])

# Request/Response Models
class InitializeFlowRequest(BaseModel):
    client_account_id: str
    engagement_id: str
    user_id: str
    raw_data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)

class FlowStatusResponse(BaseModel):
    flow_id: str
    session_id: str
    status: str
    current_phase: str
    progress_percentage: float
    phase_completion: Dict[str, bool]
    crew_status: Dict[str, Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[str]
    started_at: Optional[str]
    updated_at: str

@router.post("/flow/initialize")
async def initialize_discovery_flow(
    request: InitializeFlowRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Initialize a new unified discovery flow"""
    try:
        logger.info(f"🚀 Initializing unified discovery flow for client {request.client_account_id}")
        
        if not request.raw_data:
            raise HTTPException(status_code=400, detail="Raw data is required")
        
        # Create CrewAI service
        crewai_service = CrewAIFlowService()
        
        # Generate session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create unified discovery flow
        flow = create_unified_discovery_flow(
            session_id=session_id,
            client_account_id=request.client_account_id,
            engagement_id=request.engagement_id,
            user_id=request.user_id,
            raw_data=request.raw_data,
            metadata=request.metadata,
            crewai_service=crewai_service,
            context=context
        )
        
        # Execute flow in background
        background_tasks.add_task(_execute_flow_background, flow, context, db)
        
        return {
            "status": "success",
            "message": "Unified discovery flow initialized successfully",
            "flow_id": flow.state.flow_id,
            "session_id": session_id,
            "current_phase": "initialization",
            "progress_percentage": 0.0
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize discovery flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize discovery flow: {str(e)}")

@router.get("/flow/status/{session_id}")
async def get_flow_status(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a discovery flow"""
    try:
        logger.info(f"🔍 Getting flow status for session: {session_id}")
        
        # Query the database for the actual workflow state
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        # Query workflow state with multi-tenant filtering
        stmt = select(WorkflowState).where(
            and_(
                WorkflowState.session_id == session_uuid,
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id,
                WorkflowState.workflow_type == "unified_discovery"
            )
        ).order_by(desc(WorkflowState.updated_at))
        
        result = await db.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            logger.warning(f"⚠️ No workflow found for session: {session_id}")
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Convert workflow state to response format
        response = {
            "flow_id": str(workflow.flow_id) if workflow.flow_id else session_id,
            "session_id": str(workflow.session_id),
            "client_account_id": str(workflow.client_account_id),
            "engagement_id": str(workflow.engagement_id),
            "user_id": workflow.user_id or "",
            "status": workflow.status or "running",
            "current_phase": workflow.current_phase or "initialization",
            "progress_percentage": workflow.progress_percentage or 0.0,
            "phase_completion": workflow.phase_completion or {},
            "crew_status": workflow.crew_status or {},
            "errors": workflow.errors or [],
            "warnings": workflow.warnings or [],
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else datetime.utcnow().isoformat(),
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            
            # Phase-specific data
            "raw_data": workflow.raw_data or [],
            "field_mappings": workflow.field_mappings or {},
            "cleaned_data": workflow.cleaned_data or [],
            "asset_inventory": workflow.asset_inventory or {},
            "dependencies": workflow.dependencies or {},
            "technical_debt": workflow.technical_debt or {},
            "data_quality_metrics": workflow.data_quality_metrics or {},
            "agent_insights": workflow.agent_insights or [],
            "discovery_summary": workflow.discovery_summary or {}
        }
        
        logger.info(f"✅ Flow status retrieved: {session_id}, phase: {response['current_phase']}, progress: {response['progress_percentage']}%")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow status: {str(e)}")

@router.post("/flow/execute/{phase}")
async def execute_flow_phase(
    phase: str,
    request: Dict[str, Any],
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Execute a specific phase of the discovery flow"""
    try:
        session_id = request.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        logger.info(f"🔄 Executing phase {phase} for session {session_id}")
        
        # Get current flow state from database
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        stmt = select(WorkflowState).where(
            and_(
                WorkflowState.session_id == session_uuid,
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id
            )
        )
        
        result = await db.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Use DiscoveryFlowStateManager to execute the phase
        flow_manager = DiscoveryFlowStateManager()
        
        # Execute the specific phase
        execution_result = await flow_manager.execute_flow_phase(
            session_id=session_id,
            phase=phase,
            phase_data=request.get("data", {}),
            configuration=request.get("configuration", {})
        )
        
        if not execution_result:
            raise HTTPException(status_code=500, detail=f"Phase {phase} execution failed")
        
        return {
            "status": "success",
            "message": f"Phase {phase} execution completed",
            "session_id": session_id,
            "phase": phase,
            "result": execution_result,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to execute phase {phase}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute phase {phase}: {str(e)}")

@router.get("/flow/current")
async def get_current_flow(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current active discovery flow for the client/engagement.
    Uses existing raw_import_records data instead of duplicating it.
    """
    try:
        logger.info(f"🔍 Checking for current flow - Client: {context.client_account_id}, Engagement: {context.engagement_id}")
        
        # Query for active workflow states with proper relationships
        from sqlalchemy import select, and_, desc
        
        # Get the most recent active workflow state
        workflow_query = select(WorkflowState).where(
            and_(
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id,
                WorkflowState.workflow_type == "unified_discovery",
                WorkflowState.status.in_(["running", "paused"])
            )
        ).order_by(desc(WorkflowState.updated_at))
        
        result = await db.execute(workflow_query)
        workflow_state = result.scalar_one_or_none()
        
        if not workflow_state:
            logger.info("❌ No active discovery flow found")
            return {
                "has_current_flow": False,
                "message": "No active discovery flow found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Get associated raw import records count (don't duplicate data)
        raw_records_query = select(RawImportRecord).where(
            and_(
                RawImportRecord.client_account_id == context.client_account_id,
                RawImportRecord.engagement_id == context.engagement_id,
                RawImportRecord.session_id == workflow_state.session_id
            )
        )
        
        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()
        
        logger.info(f"✅ Found active flow: {workflow_state.flow_id} with {len(raw_records)} raw records")
        
        return {
            "has_current_flow": True,
            "flow_id": str(workflow_state.flow_id),
            "session_id": str(workflow_state.session_id),
            "current_phase": workflow_state.current_phase,
            "status": workflow_state.status,
            "progress_percentage": workflow_state.progress_percentage,
            "raw_records_count": len(raw_records),  # Reference count, not duplicate data
            "phase_completion": workflow_state.phase_completion,
            "started_at": workflow_state.started_at.isoformat() if workflow_state.started_at else None,
            "updated_at": workflow_state.updated_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting current flow: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting current flow: {str(e)}")

@router.get("/flow/health")
async def get_flow_health():
    """Get health status of the unified discovery flow system"""
    try:
        from app.services.crewai_flows.unified_discovery_flow import CREWAI_FLOW_AVAILABLE
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "crewai_available": CREWAI_FLOW_AVAILABLE,
            "system_info": {
                "unified_flow_active": True,
                "api_version": "1.0"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/flow/active")
async def get_active_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get all active discovery flows for the current context"""
    try:
        logger.info(f"🔍 Getting active flows for client: {context.client_account_id}")
        
        # Query for all active flows in the current context
        stmt = select(WorkflowState).where(
            and_(
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id,
                WorkflowState.workflow_type == "unified_discovery",
                or_(
                    WorkflowState.status == "running",
                    WorkflowState.status == "paused",
                    WorkflowState.status == "waiting",
                    WorkflowState.status == "completed"
                )
            )
        ).order_by(desc(WorkflowState.updated_at))
        
        result = await db.execute(stmt)
        workflows = result.scalars().all()
        
        # Convert to response format
        flow_details = []
        active_count = 0
        completed_count = 0
        failed_count = 0
        
        for workflow in workflows:
            flow_info = {
                "flow_id": str(workflow.flow_id) if workflow.flow_id else None,
                "session_id": str(workflow.session_id),
                "status": workflow.status,
                "current_phase": workflow.current_phase,
                "progress_percentage": workflow.progress_percentage,
                "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                "updated_at": workflow.updated_at.isoformat(),
                "phase_completion": workflow.phase_completion or {}
            }
            flow_details.append(flow_info)
            
            # Count by status
            if workflow.status in ["running", "paused", "waiting"]:
                active_count += 1
            elif workflow.status == "completed":
                completed_count += 1
            elif workflow.status in ["failed", "error"]:
                failed_count += 1
        
        return {
            "success": True,
            "message": "Active flows retrieved successfully",
            "flow_details": flow_details,
            "total_flows": len(flow_details),
            "active_flows": active_count,
            "completed_flows": completed_count,
            "failed_flows": failed_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get active flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active flows: {str(e)}")

@router.get("/flow/{session_id}/data")
async def get_flow_data(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get flow data by connecting to existing raw_import_records instead of duplicating data.
    This eliminates the architectural fragmentation issue.
    """
    try:
        logger.info(f"🔍 Getting flow data for session: {session_id}")
        
        from sqlalchemy import select, and_
        
        # Get workflow state
        workflow_query = select(WorkflowState).where(
            and_(
                WorkflowState.session_id == session_id,
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id
            )
        )
        
        workflow_result = await db.execute(workflow_query)
        workflow_state = workflow_result.scalar_one_or_none()
        
        if not workflow_state:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Get actual raw import records (single source of truth)
        raw_records_query = select(RawImportRecord).where(
            and_(
                RawImportRecord.session_id == session_id,
                RawImportRecord.client_account_id == context.client_account_id,
                RawImportRecord.engagement_id == context.engagement_id
            )
        ).limit(100)  # Limit for performance
        
        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()
        
        # Get data import session for metadata
        session_query = select(DataImportSession).where(
            DataImportSession.id == session_id
        )
        
        session_result = await db.execute(session_query)
        import_session = session_result.scalar_one_or_none()
        
        # Build unified response using existing data
        flow_data = {
            "flow_id": str(workflow_state.flow_id),
            "session_id": str(workflow_state.session_id),
            "current_phase": workflow_state.current_phase,
            "status": workflow_state.status,
            "progress_percentage": workflow_state.progress_percentage,
            "phase_completion": workflow_state.phase_completion,
            
            # Metadata from import session
            "metadata": {
                "session_name": import_session.session_name if import_session else "Unknown",
                "filename": import_session.source_filename if import_session else None,
                "total_records": len(raw_records),
                "import_status": import_session.status if import_session else "unknown"
            },
            
            # Sample of actual raw data (not duplicated)
            "sample_data": [
                {
                    "Asset_ID": record.raw_data.get("Asset_ID"),
                    "Asset_Name": record.raw_data.get("Asset_Name"),
                    "Operating_System": record.raw_data.get("Operating_System"),
                    "CPU_Cores": record.raw_data.get("CPU_Cores"),
                    "RAM_GB": record.raw_data.get("RAM_GB")
                }
                for record in raw_records[:5]  # Just a sample
            ],
            
            # Available fields from actual data
            "available_fields": list(set([
                field for record in raw_records[:10] 
                for field in record.raw_data.keys()
            ])) if raw_records else [],
            
            "updated_at": workflow_state.updated_at.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Retrieved flow data: {len(raw_records)} records, {len(flow_data['available_fields'])} fields")
        
        return flow_data
        
    except Exception as e:
        logger.error(f"❌ Error getting flow data: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting flow data: {str(e)}")

async def _execute_flow_background(flow, context: RequestContext, db: AsyncSession):
    """Execute the complete discovery flow in background"""
    try:
        logger.info(f"🔄 Starting background execution of flow: {flow.state.session_id}")
        
        # Execute the flow using CrewAI Flow patterns
        result = flow.kickoff()
        
        logger.info(f"✅ Flow execution completed: {flow.state.session_id}")
        
    except Exception as e:
        logger.error(f"❌ Background flow execution failed: {e}")
        flow.state.add_error("background_execution", str(e))
        flow.state.status = "failed"

@router.post("/flow/{session_id}/resume")
async def resume_discovery_flow(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Resume a paused or incomplete discovery flow"""
    try:
        logger.info(f"🔄 Resuming discovery flow for session: {session_id}")
        
        # Get current flow state from database
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        # Query workflow state with multi-tenant filtering
        stmt = select(WorkflowState).where(
            and_(
                WorkflowState.session_id == session_uuid,
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id
            )
        )
        
        result = await db.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Check if flow can be resumed
        if workflow.status == "completed":
            raise HTTPException(status_code=400, detail="Flow is already completed")
        
        if workflow.status == "failed":
            raise HTTPException(status_code=400, detail="Failed flows cannot be resumed")
        
        # Determine next phase based on current phase and completion status
        phase_order = [
            "data_import", "field_mapping", "data_cleansing", 
            "asset_inventory", "dependency_analysis", "tech_debt_analysis"
        ]
        
        current_phase = workflow.current_phase
        phase_completion = workflow.phase_completion or {}
        
        # Find the next incomplete phase
        next_phase = None
        for phase in phase_order:
            if not phase_completion.get(phase, False):
                next_phase = phase
                break
        
        if not next_phase:
            # All phases complete, mark as completed
            from sqlalchemy import update
            await db.execute(
                update(WorkflowState).where(
                    WorkflowState.id == workflow.id
                ).values(
                    status="completed",
                    progress_percentage=100.0,
                    updated_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            return {
                "success": True,
                "message": "Flow is already complete",
                "session_id": session_id,
                "flow_id": str(workflow.flow_id),
                "status": "completed",
                "progress_percentage": 100.0
            }
        
        # Resume the flow by updating status and navigating to next phase
        from sqlalchemy import update
        await db.execute(
            update(WorkflowState).where(
                WorkflowState.id == workflow.id
            ).values(
                status="running",
                current_phase=next_phase,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        logger.info(f"✅ Flow resumed: session={session_id}, next_phase={next_phase}")
        
        return {
            "success": True,
            "message": f"Flow resumed successfully",
            "session_id": session_id,
            "flow_id": str(workflow.flow_id),
            "current_phase": next_phase,
            "status": "running",
            "progress_percentage": workflow.progress_percentage,
            "phase_completion": phase_completion,
            "resumed_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resume flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")

@router.get("/flow/{session_id}/details")
async def get_flow_details(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific discovery flow"""
    try:
        logger.info(f"🔍 Getting flow details for session: {session_id}")
        
        # Get workflow state
        try:
            session_uuid = UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        stmt = select(WorkflowState).where(
            and_(
                WorkflowState.session_id == session_uuid,
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id
            )
        )
        
        result = await db.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Flow not found")
        
        # Get associated raw import records count
        raw_records_query = select(RawImportRecord).where(
            and_(
                RawImportRecord.session_id == session_uuid,
                RawImportRecord.client_account_id == context.client_account_id,
                RawImportRecord.engagement_id == context.engagement_id
            )
        )
        
        raw_records_result = await db.execute(raw_records_query)
        raw_records = raw_records_result.scalars().all()
        
        # Get data import session for metadata
        session_query = select(DataImportSession).where(
            DataImportSession.id == session_uuid
        )
        
        session_result = await db.execute(session_query)
        import_session = session_result.scalar_one_or_none()
        
        return {
            "session_id": str(workflow.session_id),
            "flow_id": str(workflow.flow_id),
            "current_phase": workflow.current_phase,
            "status": workflow.status,
            "progress_percentage": workflow.progress_percentage,
            "phase_completion": workflow.phase_completion,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "can_resume": workflow.status in ["running", "paused"],
            "metadata": {
                "session_name": import_session.session_name if import_session else "Unknown",
                "filename": import_session.source_filename if import_session else None,
                "total_records": len(raw_records),
                "import_status": import_session.status if import_session else "unknown"
            },
            "agent_insights": workflow.agent_insights or [],
            "errors": workflow.errors or [],
            "warnings": workflow.warnings or [],
            "workflow_log": workflow.workflow_log or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flow details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow details: {str(e)}")

@router.get("/flow/by-id/{flow_id}")
async def get_flow_status_by_id(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a discovery flow by flow_id (cleaner than session_id lookup)"""
    try:
        logger.info(f"🔍 Getting flow status by flow_id: {flow_id}")
        
        # Query the database for the actual workflow state by flow_id
        try:
            flow_uuid = UUID(flow_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid flow ID format")
        
        # First try: Query workflow state with multi-tenant filtering by flow_id
        stmt = select(WorkflowState).where(
            and_(
                WorkflowState.flow_id == flow_uuid,
                WorkflowState.client_account_id == context.client_account_id,
                WorkflowState.engagement_id == context.engagement_id,
                WorkflowState.workflow_type == "unified_discovery"
            )
        ).order_by(desc(WorkflowState.updated_at))
        
        result = await db.execute(stmt)
        workflow = result.scalar_one_or_none()
        
        # Second try: If not found by flow_id, try by session_id (for backward compatibility)
        if not workflow:
            logger.info(f"🔍 Flow not found by flow_id, trying session_id: {flow_id}")
            stmt = select(WorkflowState).where(
                and_(
                    WorkflowState.session_id == flow_uuid,
                    WorkflowState.client_account_id == context.client_account_id,
                    WorkflowState.engagement_id == context.engagement_id,
                    WorkflowState.workflow_type == "unified_discovery"
                )
            ).order_by(desc(WorkflowState.updated_at))
            
            result = await db.execute(stmt)
            workflow = result.scalar_one_or_none()
        
        if not workflow:
            logger.warning(f"⚠️ No workflow found for flow_id or session_id: {flow_id}")
            raise HTTPException(status_code=404, detail="Discovery flow not found")
        
        # Convert workflow state to response format
        response = {
            "flow_id": str(workflow.flow_id),
            "session_id": str(workflow.session_id),
            "client_account_id": str(workflow.client_account_id),
            "engagement_id": str(workflow.engagement_id),
            "user_id": workflow.user_id or "",
            "status": workflow.status or "running",
            "current_phase": workflow.current_phase or "initialization",
            "progress_percentage": workflow.progress_percentage or 0.0,
            "phase_completion": workflow.phase_completion or {},
            "crew_status": workflow.crew_status or {},
            "errors": workflow.errors or [],
            "warnings": workflow.warnings or [],
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else datetime.utcnow().isoformat(),
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            
            # Phase-specific data (only fields that exist on WorkflowState)
            "field_mappings": workflow.field_mappings or {},
            "cleaned_data": workflow.cleaned_data or [],
            "asset_inventory": workflow.asset_inventory or {},
            "dependencies": workflow.dependencies or {},
            "technical_debt": workflow.technical_debt or {},
            "data_quality_metrics": workflow.data_quality_metrics or {},
            "agent_insights": workflow.agent_insights or [],
            "discovery_summary": workflow.discovery_summary or {}
        }
        
        logger.info(f"✅ Flow status retrieved by flow_id: {flow_id}, phase: {response['current_phase']}, progress: {response['progress_percentage']}%")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flow status by flow_id: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow status: {str(e)}") 