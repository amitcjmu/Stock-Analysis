"""
Discovery Crew Escalation API Endpoints
Implements Task 2.3: Think/Ponder More Button System crew escalation functionality
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.core.context import RequestContext, get_request_context_dependency
from app.services.escalation.crew_escalation_manager import CrewEscalationManager
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for escalation requests
class ThinkEscalationRequest(BaseModel):
    agent_id: str
    context: Dict[str, Any]
    complexity_level: str = "standard"  # standard, deep, collaborative
    page_data: Optional[Dict[str, Any]] = None

class PonderEscalationRequest(BaseModel):
    agent_id: str
    context: Dict[str, Any]
    collaboration_type: str = "cross_agent"  # cross_agent, expert_panel, full_crew
    page_data: Optional[Dict[str, Any]] = None

# Initialize services
crew_escalation_manager = CrewEscalationManager()

@router.post("/{flow_id}/escalate/{page}/think")
async def escalate_to_think(
    flow_id: str,
    page: str,
    request: ThinkEscalationRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_request_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Escalate to crew-based thinking for deeper analysis.
    Implements 'Think' button functionality from Task 2.3.
    """
    try:
        # Validate flow exists using MasterFlowOrchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_state = await orchestrator.get_flow_status(flow_id)
        
        if not flow_state or flow_state.get('status') == 'not_found':
            raise HTTPException(status_code=404, detail=f"Discovery flow {flow_id} not found")
        
        # Determine appropriate crew based on page and agent
        crew_type = crew_escalation_manager.determine_crew_for_page_agent(page, request.agent_id)
        
        # Prepare escalation context
        escalation_context = {
            "flow_id": flow_id,
            "page": page,
            "agent_id": request.agent_id,
            "complexity_level": request.complexity_level,
            "user_context": request.context,
            "page_data": request.page_data,
            "escalation_type": "think",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "flow_id_context": context.flow_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Start crew escalation in background
        escalation_id = await crew_escalation_manager.start_crew_escalation(
            crew_type=crew_type,
            escalation_context=escalation_context,
            background_tasks=background_tasks
        )
        
        # Update flow state with escalation using orchestrator
        # Note: This would need to be implemented in MasterFlowOrchestrator
        # For now, we'll log the escalation
        logger.info(f"Escalation {escalation_id} recorded for flow {flow_id}")
        
        logger.info(f"Think escalation started: {escalation_id} for flow {flow_id}, page {page}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "crew_type": crew_type,
            "status": "thinking",
            "estimated_duration": "2-5 minutes",
            "message": f"Crew escalation initiated for deeper {page} analysis",
            "progress_endpoint": f"/api/v1/discovery/{flow_id}/escalation/{escalation_id}/status"
        }
        
    except Exception as e:
        logger.error(f"Error in think escalation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to escalate to thinking: {str(e)}")

@router.post("/{flow_id}/escalate/{page}/ponder")
async def escalate_to_ponder_more(
    flow_id: str,
    page: str,
    request: PonderEscalationRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_request_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Escalate to crew collaboration for extended pondering.
    Implements 'Ponder More' button functionality from Task 2.3.
    """
    try:
        # Validate flow exists using MasterFlowOrchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_state = await orchestrator.get_flow_status(flow_id)
        
        if not flow_state or flow_state.get('status') == 'not_found':
            raise HTTPException(status_code=404, detail=f"Discovery flow {flow_id} not found")
        
        # Determine crew collaboration strategy
        crew_strategy = crew_escalation_manager.determine_collaboration_strategy(
            page, request.agent_id, request.collaboration_type
        )
        
        # Prepare extended collaboration context
        collaboration_context = {
            "flow_id": flow_id,
            "page": page,
            "agent_id": request.agent_id,
            "collaboration_type": request.collaboration_type,
            "collaboration_strategy": crew_strategy,
            "user_context": request.context,
            "page_data": request.page_data,
            "escalation_type": "ponder_more",
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
            "flow_id_context": context.flow_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Start extended crew collaboration
        escalation_id = await crew_escalation_manager.start_extended_collaboration(
            collaboration_strategy=crew_strategy,
            collaboration_context=collaboration_context,
            background_tasks=background_tasks
        )
        
        # Update flow state with extended collaboration
        await flow.update_escalation_status(
            flow_id=flow_id,
            escalation_id=escalation_id,
            status="pondering",
            crew_type=crew_strategy["primary_crew"],
            collaboration_crews=crew_strategy.get("additional_crews", [])
        )
        
        logger.info(f"Ponder More escalation started: {escalation_id} for flow {flow_id}, page {page}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "collaboration_strategy": crew_strategy,
            "status": "pondering",
            "estimated_duration": "5-10 minutes",
            "message": f"Extended crew collaboration initiated for {page} analysis",
            "progress_endpoint": f"/api/v1/discovery/{flow_id}/escalation/{escalation_id}/status",
            "collaboration_details": {
                "primary_crew": crew_strategy["primary_crew"],
                "collaboration_pattern": crew_strategy["pattern"],
                "expected_outcomes": crew_strategy.get("expected_outcomes", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Error in ponder more escalation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to escalate to pondering: {str(e)}")

@router.get("/{flow_id}/escalation/{escalation_id}/status")
async def get_escalation_status(
    flow_id: str,
    escalation_id: str,
    context: RequestContext = Depends(get_request_context_dependency)
):
    """
    Get the status of an ongoing crew escalation.
    Provides real-time progress updates for Think/Ponder More operations.
    """
    try:
        # Get escalation status from manager
        status = await crew_escalation_manager.get_escalation_status(escalation_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Escalation {escalation_id} not found")
        
        # Get flow state for additional context
        flow = UnifiedDiscoveryFlow()
        flow_state = await flow.get_flow_state(flow_id)
        
        # Combine escalation status with flow context
        response = {
            "success": True,
            "escalation_id": escalation_id,
            "flow_id": flow_id,
            "status": status["status"],
            "progress": status.get("progress", 0),
            "current_phase": status.get("current_phase", "initializing"),
            "crew_activity": status.get("crew_activity", []),
            "preliminary_insights": status.get("preliminary_insights", []),
            "estimated_completion": status.get("estimated_completion"),
            "error": status.get("error"),
            "started_at": status.get("started_at"),
            "updated_at": status.get("updated_at")
        }
        
        # Add crew collaboration details if available
        if status.get("collaboration_details"):
            response["collaboration_details"] = status["collaboration_details"]
        
        # Add final results if completed
        if status["status"] == "completed":
            response["results"] = status.get("results", {})
            response["insights_generated"] = status.get("insights_generated", [])
            response["recommendations"] = status.get("recommendations", [])
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting escalation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get escalation status: {str(e)}")

@router.get("/{flow_id}/escalation/status")
async def get_flow_escalation_status(
    flow_id: str,
    context: RequestContext = Depends(get_request_context_dependency)
):
    """
    Get overall escalation status for a discovery flow.
    Shows all active and recent escalations.
    """
    try:
        # Get flow state
        flow = UnifiedDiscoveryFlow()
        flow_state = await flow.get_flow_state(flow_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail=f"Discovery flow {flow_id} not found")
        
        # Get all escalations for this flow
        escalations = await crew_escalation_manager.get_flow_escalations(flow_id)
        
        # Organize by status
        active_escalations = [e for e in escalations if e["status"] in ["thinking", "pondering", "collaborating"]]
        completed_escalations = [e for e in escalations if e["status"] == "completed"]
        failed_escalations = [e for e in escalations if e["status"] == "failed"]
        
        return {
            "success": True,
            "flow_id": flow_id,
            "escalation_summary": {
                "total_escalations": len(escalations),
                "active_escalations": len(active_escalations),
                "completed_escalations": len(completed_escalations),
                "failed_escalations": len(failed_escalations)
            },
            "active_escalations": active_escalations,
            "recent_completed": completed_escalations[-5:] if completed_escalations else [],
            "flow_escalation_history": {
                "total_think_operations": len([e for e in escalations if e.get("escalation_type") == "think"]),
                "total_ponder_operations": len([e for e in escalations if e.get("escalation_type") == "ponder_more"]),
                "success_rate": len(completed_escalations) / len(escalations) if escalations else 0.0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting flow escalation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get flow escalation status: {str(e)}")

@router.delete("/{flow_id}/escalation/{escalation_id}")
async def cancel_escalation(
    flow_id: str,
    escalation_id: str,
    context: RequestContext = Depends(get_request_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an ongoing crew escalation.
    Allows users to stop Think/Ponder More operations if needed.
    """
    try:
        # Cancel the escalation
        result = await crew_escalation_manager.cancel_escalation(escalation_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to cancel escalation"))
        
        # Update flow state
        flow = UnifiedDiscoveryFlow()
        await flow.update_escalation_status(
            flow_id=flow_id,
            escalation_id=escalation_id,
            status="cancelled"
        )
        
        logger.info(f"Escalation cancelled: {escalation_id} for flow {flow_id}")
        
        return {
            "success": True,
            "escalation_id": escalation_id,
            "flow_id": flow_id,
            "status": "cancelled",
            "message": "Crew escalation cancelled successfully",
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cancelling escalation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel escalation: {str(e)}") 