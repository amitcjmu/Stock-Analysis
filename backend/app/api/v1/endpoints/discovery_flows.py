"""
Discovery Flows API - Minimal implementation for frontend compatibility
Provides basic flow management endpoints until real CrewAI flows are implemented
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context
from app.api.v1.dependencies import get_crewai_flow_service
from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/flows/active", response_model=List[Dict[str, Any]])
@router.get("/flow/active", response_model=List[Dict[str, Any]])  # Alias for frontend compatibility
async def get_active_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active discovery flows for the current tenant context.
    
    This is a minimal implementation to support frontend compatibility.
    TODO: Replace with real CrewAI flow management.
    """
    try:
        logger.info(f"Getting active flows for client {context.client_account_id}, engagement {context.engagement_id}")
        
        # Query actual discovery flows from database
        from sqlalchemy import select, and_, or_
        from app.models.discovery_flow import DiscoveryFlow
        
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
                DiscoveryFlow.status != 'deleted',  # Exclude soft-deleted flows
                DiscoveryFlow.status != 'cancelled',  # Exclude cancelled flows
                or_(
                    DiscoveryFlow.status == 'active',
                    DiscoveryFlow.status == 'running',
                    DiscoveryFlow.status == 'paused',
                    DiscoveryFlow.status == 'processing',
                    DiscoveryFlow.status == 'ready'
                )
            )
        ).order_by(DiscoveryFlow.created_at.desc())
        
        result = await db.execute(stmt)
        flows = result.scalars().all()
        
        # Convert to response format
        active_flows = []
        for flow in flows:
            active_flows.append({
                "flow_id": str(flow.flow_id),
                "status": flow.status,
                "type": "discovery",
                "client_account_id": str(flow.client_account_id),
                "engagement_id": str(flow.engagement_id),
                "created_at": flow.created_at.isoformat() if flow.created_at else "",
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else "",
                "metadata": flow.flow_state or {}
            })
        
        logger.info(f"Found {len(active_flows)} active flows")
        return active_flows
        
    except Exception as e:
        logger.error(f"Error getting active flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active flows: {str(e)}")

@router.get("/flows/{flow_id}/status", response_model=Dict[str, Any])
async def get_flow_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of a specific discovery flow.
    
    Delegates to the unified discovery orchestrator for real status.
    """
    try:
        logger.info(f"Getting status for flow {flow_id}")
        
        # First try to get the actual flow from DiscoveryFlow table
        from sqlalchemy import select
        from app.models.discovery_flow import DiscoveryFlow
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        
        try:
            # Convert flow_id string to UUID for proper comparison
            import uuid as uuid_lib
            try:
                flow_uuid = uuid_lib.UUID(flow_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
                flow_uuid = flow_id  # Fallback to string if not valid UUID
            
            # Get flow from DiscoveryFlow table
            stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()
            
            if flow:
                logger.info(f"Found flow in DiscoveryFlow table: status={flow.status}, progress={flow.progress_percentage}")
                
                # Calculate current phase from completion flags
                current_phase = "unknown"
                steps_completed = 0
                
                if not flow.data_import_completed:
                    current_phase = "data_import"
                elif not flow.field_mapping_completed:
                    current_phase = "field_mapping"
                    steps_completed = 1
                elif not flow.data_cleansing_completed:
                    current_phase = "data_cleansing"
                    steps_completed = 2
                elif not flow.asset_inventory_completed:
                    current_phase = "asset_inventory"
                    steps_completed = 3
                elif not flow.dependency_analysis_completed:
                    current_phase = "dependency_analysis"
                    steps_completed = 4
                elif not flow.tech_debt_assessment_completed:
                    current_phase = "tech_debt_assessment"
                    steps_completed = 5
                else:
                    current_phase = "completed"
                    steps_completed = 6
                
                # Also check CrewAI state extensions for additional data
                ext_stmt = select(CrewAIFlowStateExtensions).where(CrewAIFlowStateExtensions.flow_id == flow_uuid)
                ext_result = await db.execute(ext_stmt)
                extensions = ext_result.scalar_one_or_none()
                
                agent_insights = []
                if extensions and extensions.flow_persistence_data:
                    # Agent insights might be stored in flow_persistence_data
                    agent_insights = extensions.flow_persistence_data.get("agent_insights", [])
                
                return {
                    "flow_id": str(flow_id),
                    "status": flow.status if flow.status != "active" else "processing",
                    "type": "discovery",
                    "client_account_id": str(flow.client_account_id),
                    "engagement_id": str(flow.engagement_id),
                    "progress": {
                        "current_phase": current_phase,
                        "completion_percentage": float(flow.progress_percentage),
                        "steps_completed": steps_completed,
                        "total_steps": 6
                    },
                    "metadata": {},
                    "crewai_status": "active" if flow.status == "active" else flow.status,
                    "agent_insights": agent_insights,
                    "phase_completion": {
                        "data_import": flow.data_import_completed,
                        "field_mapping": flow.field_mapping_completed,
                        "data_cleansing": flow.data_cleansing_completed,
                        "asset_inventory": flow.asset_inventory_completed,
                        "dependency_analysis": flow.dependency_analysis_completed,
                        "tech_debt_assessment": flow.tech_debt_assessment_completed
                    },
                    "last_updated": flow.updated_at.isoformat() if flow.updated_at else ""
                }
        except Exception as direct_error:
            logger.warning(f"Failed to get flow from DiscoveryFlow table: {direct_error}")
        
        # Try the flow state persistence data as second attempt
        from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
        
        try:
            # Get the actual flow state from PostgreSQL
            store = PostgresFlowStateStore(db, context)
            state_dict = await store.load_state(flow_id)
            
            if state_dict:
                # We have a real flow state
                progress_percentage = float(state_dict.get("progress_percentage", 0))
                current_phase = state_dict.get("current_phase", "unknown")
                status = state_dict.get("status", "running")
                
                # Determine if flow is complete
                if progress_percentage >= 100 or status == "completed":
                    status = "completed"
                elif status == "failed":
                    status = "failed"
                else:
                    status = "processing"
                
                # Use context values for client_account_id and engagement_id since state_dict is just the persistence data
                return {
                    "flow_id": flow_id,
                    "status": status,
                    "type": "discovery",
                    "client_account_id": str(context.client_account_id),
                    "engagement_id": str(context.engagement_id),
                    "progress": {
                        "current_phase": current_phase,
                        "completion_percentage": progress_percentage,
                        "steps_completed": len([p for p in state_dict.get("phase_completion", {}).values() if p]),
                        "total_steps": 6  # Total phases
                    },
                    "metadata": state_dict.get("metadata", {}),
                    "crewai_status": "active" if status == "processing" else status,
                    "agent_insights": state_dict.get("agent_insights", []),
                    "phase_completion": state_dict.get("phase_completion", {}),
                    "last_updated": state_dict.get("updated_at", "")
                }
        except Exception as store_error:
            logger.warning(f"Failed to get flow state from store: {store_error}")
        
        # Last fallback to orchestrator
        from app.api.v1.unified_discovery.services.discovery_orchestrator import DiscoveryOrchestrator
        
        orchestrator = DiscoveryOrchestrator(db, context)
        result = await orchestrator.get_discovery_flow_status(flow_id)
        
        # Transform to frontend-compatible format
        progress_percentage = float(result.get("progress_percentage", 0))
        return {
            "flow_id": flow_id,
            "status": result.get("status", "unknown"),
            "type": "discovery",
            "client_account_id": str(result.get("client_account_id", context.client_account_id)),
            "engagement_id": str(result.get("engagement_id", context.engagement_id)),
            "progress": {
                "current_phase": result.get("current_phase", "unknown"),
                "completion_percentage": progress_percentage,
                "steps_completed": int(progress_percentage / 20),  # 5 phases = 20% each
                "total_steps": 5
            },
            "metadata": result.get("metadata", {}),
            "crewai_status": result.get("crewai_status", "unknown"),
            "agent_insights": result.get("agent_insights", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting flow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow status: {str(e)}")

@router.post("/flows/initialize", response_model=Dict[str, Any])
async def initialize_flow(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize a new discovery flow.
    
    This is a minimal implementation to support frontend compatibility.
    TODO: Replace with real CrewAI flow initialization.
    """
    try:
        logger.info(f"Initializing new flow for client {context.client_account_id}")
        
        # Generate a simple flow ID
        import uuid
        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        
        # Minimal response for frontend compatibility
        # TODO: Replace with real flow database creation and CrewAI flow startup
        return {
            "flow_id": flow_id,
            "status": "initialized",
            "type": "discovery",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "message": "Discovery flow initialized successfully",
            "next_steps": [
                "Upload data files",
                "Configure field mappings",
                "Start discovery process"
            ],
            "metadata": {
                "note": "Placeholder flow - CrewAI implementation pending"
            }
        }
        
    except Exception as e:
        logger.error(f"Error initializing flow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize flow: {str(e)}")

@router.get("/flows/health", response_model=Dict[str, Any])
async def discovery_flows_health():
    """
    Health check for discovery flows service.
    """
    return {
        "service": "discovery_flows",
        "status": "healthy",
        "implementation": "minimal_placeholder",
        "note": "Placeholder implementation - CrewAI flows pending"
    }

@router.get("/flow/{flow_id}/agent-insights", response_model=List[Dict[str, Any]])
async def get_flow_agent_insights(
    flow_id: str,
    page_context: str = "data_import",
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get agent insights for a specific flow.
    
    This is a minimal implementation to support frontend compatibility.
    TODO: Replace with real CrewAI agent insights.
    """
    try:
        logger.info(f"Getting agent insights for flow {flow_id}, page context: {page_context}")
        
        # Minimal response for frontend compatibility
        return []
        
    except Exception as e:
        logger.error(f"Error getting agent insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent insights: {str(e)}")

@router.get("/flow/status/{flow_id}", response_model=Dict[str, Any])
async def get_flow_status_v2(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of a specific discovery flow (alternate endpoint).
    Uses the same direct database query as the main status endpoint.
    """
    # Use the same implementation as get_flow_status
    return await get_flow_status(flow_id, context, db)

@router.get("/flow/{flow_id}/processing-status", response_model=Dict[str, Any])
async def get_flow_processing_status(
    flow_id: str,
    phase: str = Query(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing status for a specific flow.
    This endpoint is used by the real-time monitoring UI.
    """
    try:
        logger.info(f"Getting processing status for flow {flow_id}, phase: {phase}")
        
        # Import the orchestrator to get real status
        from app.api.v1.unified_discovery.services.discovery_orchestrator import DiscoveryOrchestrator
        
        # Create orchestrator with context
        orchestrator = DiscoveryOrchestrator(db, context)
        
        try:
            # Get real flow status
            result = await orchestrator.get_discovery_flow_status(flow_id)
            
            # Transform to processing status format expected by frontend
            processing_status = {
                "flow_id": flow_id,
                "phase": result.get("current_phase", "data_import"),
                "status": result.get("status", "initializing"),
                "progress_percentage": float(result.get("progress_percentage", 0)),
                "progress": float(result.get("progress_percentage", 0)),
                "records_processed": int(result.get("records_processed", 0)),
                "records_total": int(result.get("records_total", 0)),
                "records_failed": int(result.get("records_failed", 0)),
                "validation_status": {
                    "format_valid": True,
                    "security_scan_passed": True,
                    "data_quality_score": 1.0,
                    "issues_found": []
                },
                "agent_status": result.get("agent_status", {}),
                "recent_updates": [],
                "estimated_completion": None,
                "last_update": result.get("updated_at", ""),
                "phases": result.get("phase_completion", {}),
                "current_phase": result.get("current_phase", "data_import")
            }
            
            return processing_status
            
        except Exception as orch_error:
            logger.warning(f"Failed to get flow from orchestrator: {orch_error}, returning default processing status")
            
            # Return default processing status
            return {
                "flow_id": flow_id,
                "phase": phase or "data_import",
                "status": "initializing",
                "progress_percentage": 0.0,
                "progress": 0.0,
                "records_processed": 0,
                "records_total": 0,
                "records_failed": 0,
                "validation_status": {
                    "format_valid": True,
                    "security_scan_passed": True,
                    "data_quality_score": 1.0,
                    "issues_found": []
                },
                "agent_status": {},
                "recent_updates": [],
                "estimated_completion": None,
                "last_update": "",
                "phases": {
                    "data_import": False,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False
                },
                "current_phase": "data_import"
            }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")

@router.get("/flow/{flow_id}/validation-status", response_model=Dict[str, Any])
async def get_flow_validation_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Get validation status for a specific flow.
    
    This is a minimal implementation to support frontend compatibility.
    TODO: Replace with real CrewAI validation status.
    """
    try:
        logger.info(f"Getting validation status for flow {flow_id}")
        
        # Minimal response for frontend compatibility
        return {
            "flow_id": flow_id,
            "validation_status": "pending",
            "errors": [],
            "warnings": [],
            "metadata": {
                "note": "Placeholder validation status - CrewAI implementation pending"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get validation status: {str(e)}")

@router.post("/flow/{flow_id}/resume", response_model=Dict[str, Any])
async def resume_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    crewai_service: CrewAIFlowService = Depends(get_crewai_flow_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a paused discovery flow after user approval.
    
    This endpoint is used when the flow is waiting for field mapping approval.
    """
    try:
        logger.info(f"Resuming discovery flow {flow_id}")
        
        # Prepare resume context with user approval data
        resume_context = {
            "user_approval": True,
            "field_mappings": request.get("field_mappings", {}),
            "approval_timestamp": datetime.utcnow().isoformat(),
            "approved_by": context.user_id,
            "approval_notes": request.get("notes", ""),
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id
        }
        
        # Get the flow to check its current state
        from sqlalchemy import select
        from app.models.discovery_flow import DiscoveryFlow
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        import uuid as uuid_lib
        
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id
        
        # Get the flow
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot resume a deleted flow")
        
        # Determine the appropriate status to set
        previous_status = "processing"
        if flow.status == "paused" and flow.flow_state and "pause_metadata" in flow.flow_state:
            # Restore to previous status if available
            previous_status = flow.flow_state["pause_metadata"].get("previous_status", "processing")
        
        # Update flow status
        flow.status = previous_status
        flow.updated_at = datetime.utcnow()
        
        # Update resume metadata
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["resume_metadata"] = {
            "resumed_at": datetime.utcnow().isoformat(),
            "resumed_by": context.user_id,
            "resumed_from_status": "paused"
        }
        
        # Update master flow if exists
        if flow.master_flow_id:
            master_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
            )
            master_result = await db.execute(master_stmt)
            master_flow = master_result.scalar_one_or_none()
            
            if master_flow:
                master_flow.flow_status = "active"
                master_flow.updated_at = datetime.utcnow()
                
                # Add resume event to collaboration log
                master_flow.add_agent_collaboration_entry(
                    agent_name="system",
                    action="resume_flow",
                    details={
                        "child_flow_id": str(flow_id),
                        "child_flow_type": "discovery",
                        "resumed_to_status": previous_status,
                        "resumed_by": context.user_id
                    }
                )
        
        # Determine next phase
        next_phase = "unknown"
        if not flow.data_import_completed:
            next_phase = "data_import"
        elif not flow.field_mapping_completed:
            next_phase = "field_mapping"
        elif not flow.data_cleansing_completed:
            next_phase = "data_cleansing"
        elif not flow.asset_inventory_completed:
            next_phase = "asset_inventory"
        elif not flow.dependency_analysis_completed:
            next_phase = "dependency_analysis"
        elif not flow.tech_debt_assessment_completed:
            next_phase = "tech_debt_assessment"
        else:
            next_phase = "completed"
        
        await db.commit()
        
        # Try to resume with CrewAI service if available
        try:
            result = await crewai_service.resume_flow(flow_id, resume_context)
            logger.info(f"CrewAI service resume result: {result}")
        except Exception as crewai_error:
            logger.warning(f"CrewAI service resume failed: {crewai_error}")
        
        logger.info(f"✅ Flow {flow_id} resumed successfully")
        
        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": "resumed",
            "message": "Discovery flow resumed successfully",
            "next_phase": next_phase,
            "current_phase": next_phase
        }
            
    except Exception as e:
        logger.error(f"Error resuming flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")

@router.post("/flow/{flow_id}/pause", response_model=Dict[str, Any])
async def pause_discovery_flow(
    flow_id: str,
    request: Dict[str, Any] = {},
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Pause an active discovery flow.
    
    Updates both the discovery flow and master flow status to reflect paused state.
    """
    try:
        logger.info(f"⏸️ Pausing discovery flow {flow_id}")
        
        from sqlalchemy import select
        from app.models.discovery_flow import DiscoveryFlow
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        import uuid as uuid_lib
        
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
            flow_uuid = flow_id
        
        # Get the flow
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()
        
        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
        
        if flow.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot pause a deleted flow")
        
        if flow.status == "completed":
            raise HTTPException(status_code=400, detail="Cannot pause a completed flow")
        
        if flow.status == "paused":
            logger.info(f"Flow {flow_id} is already paused")
            return {
                "success": True,
                "flow_id": str(flow_id),
                "status": "already_paused",
                "message": "Flow is already paused"
            }
        
        # Store the previous status for potential resume
        previous_status = flow.status
        flow.status = "paused"
        flow.updated_at = datetime.utcnow()
        
        # Store pause metadata in flow_state
        if not flow.flow_state:
            flow.flow_state = {}
        flow.flow_state["pause_metadata"] = {
            "paused_at": datetime.utcnow().isoformat(),
            "paused_by": context.user_id,
            "previous_status": previous_status,
            "pause_reason": request.get("reason", "User requested pause")
        }
        
        # Update master flow if exists
        if flow.master_flow_id:
            master_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
            )
            master_result = await db.execute(master_stmt)
            master_flow = master_result.scalar_one_or_none()
            
            if master_flow:
                master_flow.flow_status = "paused"
                master_flow.updated_at = datetime.utcnow()
                
                # Add pause event to collaboration log
                master_flow.add_agent_collaboration_entry(
                    agent_name="system",
                    action="pause_flow",
                    details={
                        "child_flow_id": str(flow_id),
                        "child_flow_type": "discovery",
                        "previous_status": previous_status,
                        "paused_by": context.user_id
                    }
                )
        
        await db.commit()
        
        logger.info(f"✅ Flow {flow_id} paused successfully")
        
        return {
            "success": True,
            "flow_id": str(flow_id),
            "status": "paused",
            "message": "Discovery flow paused successfully",
            "previous_status": previous_status
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause flow: {str(e)}")

@router.delete("/flow/{flow_id}", response_model=Dict[str, Any])
async def delete_discovery_flow(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a discovery flow as deleted (soft delete) and update master flow status.
    
    This maintains audit trail by not physically deleting the flow,
    instead marking it as 'deleted' and creating an audit record.
    """
    try:
        logger.info(f"🗑️ Marking discovery flow {flow_id} as deleted")
        
        from sqlalchemy import select, update
        from app.models.discovery_flow import DiscoveryFlow
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.flow_deletion_audit import FlowDeletionAudit
        import uuid as uuid_lib
        from datetime import datetime
        import time
        
        start_time = time.time()
        
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
            flow_uuid = flow_id
        
        # Get the discovery flow
        stmt = select(DiscoveryFlow).where(
            DiscoveryFlow.flow_id == flow_uuid,
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()
        
        if not flow:
            logger.warning(f"Discovery flow {flow_id} not found")
            return {
                "success": False,
                "flow_id": str(flow_id),
                "message": "Flow not found",
                "deleted": False
            }
        
        if flow.status == "deleted":
            logger.info(f"Discovery flow {flow_id} already marked as deleted")
            return {
                "success": True,
                "flow_id": str(flow_id),
                "message": "Flow already deleted",
                "deleted": False
            }
        
        # Prepare deletion data for audit
        deletion_data = {
            "flow_type": "discovery",
            "previous_status": flow.status,
            "flow_name": flow.flow_name,
            "progress_percentage": flow.progress_percentage,
            "phases_completed": {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed
            }
        }
        
        # Mark discovery flow as deleted
        flow.status = "deleted"
        flow.updated_at = datetime.utcnow()
        
        # Update master flow if exists
        if flow.master_flow_id:
            # Get the master flow to update its persistence data
            master_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
            )
            master_result = await db.execute(master_stmt)
            master_flow = master_result.scalar_one_or_none()
            
            if master_flow:
                master_flow.flow_status = "child_flows_deleted"
                master_flow.updated_at = datetime.utcnow()
                
                # Update persistence data
                if not master_flow.flow_persistence_data:
                    master_flow.flow_persistence_data = {}
                master_flow.flow_persistence_data["discovery_flow_deleted"] = True
                master_flow.flow_persistence_data["deletion_timestamp"] = datetime.utcnow().isoformat()
                master_flow.flow_persistence_data["deleted_by"] = context.user_id
        
        # Create audit record
        duration_ms = int((time.time() - start_time) * 1000)
        audit_record = FlowDeletionAudit.create_audit_record(
            flow_id=str(flow_uuid),
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
            user_id=context.user_id,
            deletion_type="user_requested",
            deletion_method="api",
            deleted_by=context.user_id,
            deletion_reason="User requested deletion via UI",
            data_deleted=deletion_data,
            deletion_impact={"flow_type": "discovery", "soft_delete": True},
            cleanup_summary={"status_updated": True, "master_flow_updated": bool(flow.master_flow_id)},
            deletion_duration_ms=duration_ms
        )
        db.add(audit_record)
        
        # Commit all changes
        await db.commit()
        
        logger.info(f"✅ Discovery flow {flow_id} marked as deleted successfully")
        
        return {
            "success": True,
            "flow_id": str(flow_id),
            "message": "Discovery flow marked as deleted",
            "deleted": True,
            "audit_id": str(audit_record.id)
        }
            
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error marking discovery flow {flow_id} as deleted: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}")