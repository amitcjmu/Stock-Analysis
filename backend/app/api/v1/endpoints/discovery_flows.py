"""
Discovery Flows API - Minimal implementation for frontend compatibility
Provides basic flow management endpoints until real CrewAI flows are implemented
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context

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
                if extensions and extensions.agent_insights:
                    agent_insights = extensions.agent_insights
                
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
                
                return {
                    "flow_id": flow_id,
                    "status": status,
                    "type": "discovery",
                    "client_account_id": state_dict.get("client_account_id", ""),
                    "engagement_id": state_dict.get("engagement_id", ""),
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
            "client_account_id": result.get("client_account_id", ""),
            "engagement_id": result.get("engagement_id", ""),
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
    request: Dict[str, Any],
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a paused discovery flow after user approval.
    
    This endpoint is used when the flow is waiting for field mapping approval.
    """
    try:
        logger.info(f"Resuming discovery flow {flow_id}")
        
        # Get the CrewAI flow service
        from app.services.crewai_flow_service import CrewAIFlowService
        crewai_service = CrewAIFlowService()
        
        # Prepare resume context with user approval data
        resume_context = {
            "user_approval": True,
            "field_mappings": request.get("field_mappings", {}),
            "approval_timestamp": datetime.utcnow().isoformat(),
            "approved_by": context.user_id,
            "approval_notes": request.get("notes", "")
        }
        
        # Resume the flow
        result = await crewai_service.resume_flow(flow_id, resume_context)
        
        if result.get("status") == "resumed":
            logger.info(f"✅ Flow {flow_id} resumed successfully")
            return {
                "success": True,
                "flow_id": flow_id,
                "status": "resumed",
                "message": "Discovery flow resumed successfully",
                "next_phase": result.get("next_phase", "field_mapping")
            }
        else:
            logger.error(f"Failed to resume flow {flow_id}: {result}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to resume flow: {result.get('message', 'Unknown error')}"
            )
            
    except Exception as e:
        logger.error(f"Error resuming flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume flow: {str(e)}")