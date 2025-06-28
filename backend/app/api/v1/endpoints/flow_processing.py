"""
Flow Processing API endpoints for intelligent flow continuation and routing.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.context import get_current_context, RequestContext
from app.services.agents.flow_processing_agent import FlowProcessingAgent, FlowContinuationResult
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flow-processing", tags=["flow-processing"])

class FlowContinuationRequest(BaseModel):
    """Request model for flow continuation"""
    user_context: Dict[str, Any] = Field(default_factory=dict)
    user_action: str = Field(default="continue_flow")

class FlowContinuationResponse(BaseModel):
    """Response model for flow continuation"""
    success: bool
    flow_id: str
    current_phase: str
    next_action: str
    routing_context: Dict[str, Any]
    checklist_status: List[Dict[str, Any]]
    user_guidance: Dict[str, Any]
    error_message: str = None

class FlowChecklistResponse(BaseModel):
    """Response model for flow checklist status"""
    flow_id: str
    phases: List[Dict[str, Any]]
    overall_completion: float
    next_required_tasks: List[str]
    blocking_issues: List[str]

@router.post("/continue/{flow_id}")
async def continue_flow_with_agent(
    flow_id: str,
    request: FlowContinuationRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> FlowContinuationResponse:
    """
    Process flow continuation using the Flow Processing Agent.
    
    This endpoint serves as the central entry point for all "Continue Flow" requests.
    The Flow Processing Agent analyzes the flow state, evaluates completion checklists,
    and determines the optimal next step for the user.
    """
    
    try:
        logger.info(f"🤖 FLOW PROCESSING API: Received continuation request for flow {flow_id}")
        
        # Initialize Flow Processing Agent with context
        flow_agent = FlowProcessingAgent(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Process the continuation request
        result = await flow_agent.process_flow_continuation(
            flow_id=flow_id,
            user_context={
                **request.user_context,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_action": request.user_action
            }
        )
        
        if result.success:
            logger.info(f"✅ FLOW PROCESSING SUCCESS: {flow_id} -> {result.routing_decision.target_page}")
            
            return FlowContinuationResponse(
                success=True,
                flow_id=flow_id,
                current_phase=result.current_phase,
                next_action=result.next_action,
                routing_context={
                    "target_page": result.routing_decision.target_page,
                    "context_data": result.routing_decision.context_data,
                    "specific_task": result.routing_decision.specific_task
                },
                checklist_status=[
                    {
                        "phase": phase.phase,
                        "status": phase.status.value,
                        "completion_percentage": phase.completion_percentage,
                        "tasks": [
                            {
                                "task_id": task.task_id,
                                "task_name": task.task_name,
                                "status": task.status.value,
                                "confidence": task.confidence,
                                "next_steps": task.next_steps
                            }
                            for task in phase.tasks
                        ],
                        "next_required_actions": phase.next_required_actions
                    }
                    for phase in result.checklist_status
                ],
                user_guidance=result.user_guidance
            )
        else:
            logger.error(f"❌ FLOW PROCESSING FAILED: {flow_id} - {result.error_message}")
            
            return FlowContinuationResponse(
                success=False,
                flow_id=flow_id,
                current_phase="error",
                next_action="error_recovery",
                routing_context={
                    "target_page": "/discovery/enhanced-dashboard",
                    "context_data": {"error": result.error_message}
                },
                checklist_status=[],
                user_guidance={"error": result.error_message},
                error_message=result.error_message
            )
        
    except Exception as e:
        logger.error(f"❌ FLOW PROCESSING API ERROR: {flow_id} - {str(e)}")
        
        return FlowContinuationResponse(
            success=False,
            flow_id=flow_id,
            current_phase="error",
            next_action="error_recovery",
            routing_context={
                "target_page": "/discovery/enhanced-dashboard",
                "context_data": {"error": str(e)}
            },
            checklist_status=[],
            user_guidance={"error": f"Flow processing failed: {str(e)}"},
            error_message=str(e)
        )

@router.get("/checklist/{flow_id}")
async def get_flow_checklist_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> FlowChecklistResponse:
    """
    Get detailed checklist status for a flow.
    
    This endpoint provides comprehensive information about what tasks have been
    completed and what still needs to be done for each phase of the flow.
    """
    
    try:
        logger.info(f"📋 CHECKLIST API: Getting status for flow {flow_id}")
        
        # Initialize Flow Processing Agent
        flow_agent = FlowProcessingAgent(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Get flow analysis and checklist status
        flow_analysis = await flow_agent._analyze_flow_state(flow_id)
        checklist_results = await flow_agent._evaluate_all_phase_checklists(flow_analysis)
        
        # Calculate overall completion
        total_tasks = sum(len(phase.tasks) for phase in checklist_results)
        completed_tasks = sum(
            len([task for task in phase.tasks if task.status.value == "completed"])
            for phase in checklist_results
        )
        overall_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get next required tasks across all phases
        next_required_tasks = []
        blocking_issues = []
        
        for phase in checklist_results:
            if phase.status.value != "completed":
                next_required_tasks.extend(phase.next_required_actions[:2])  # Top 2 per phase
                if phase.blocking_issues:
                    blocking_issues.extend(phase.blocking_issues)
        
        return FlowChecklistResponse(
            flow_id=flow_id,
            phases=[
                {
                    "phase": phase.phase,
                    "status": phase.status.value,
                    "completion_percentage": phase.completion_percentage,
                    "tasks": [
                        {
                            "task_id": task.task_id,
                            "task_name": task.task_name,
                            "status": task.status.value,
                            "confidence": task.confidence,
                            "evidence": task.evidence,
                            "next_steps": task.next_steps
                        }
                        for task in phase.tasks
                    ],
                    "ready_for_next_phase": phase.ready_for_next_phase,
                    "next_required_actions": phase.next_required_actions
                }
                for phase in checklist_results
            ],
            overall_completion=overall_completion,
            next_required_tasks=next_required_tasks[:5],  # Top 5 overall
            blocking_issues=blocking_issues
        )
        
    except Exception as e:
        logger.error(f"❌ CHECKLIST API ERROR: {flow_id} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get checklist status: {str(e)}"
        )

@router.post("/analyze/{flow_id}")
async def analyze_flow_state(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed analysis of flow state for debugging and monitoring.
    
    This endpoint provides comprehensive information about the flow's current state,
    including all data sources that the Flow Processing Agent uses for decision making.
    """
    
    try:
        logger.info(f"🔍 ANALYSIS API: Analyzing flow state for {flow_id}")
        
        # Initialize Flow Processing Agent
        flow_agent = FlowProcessingAgent(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Get comprehensive flow analysis
        flow_analysis = await flow_agent._analyze_flow_state(flow_id)
        checklist_results = await flow_agent._evaluate_all_phase_checklists(flow_analysis)
        routing_decision = await flow_agent._determine_optimal_route(flow_analysis, checklist_results)
        user_guidance = await flow_agent._generate_user_guidance(routing_decision, checklist_results)
        
        return {
            "flow_id": flow_id,
            "timestamp": "2025-01-27T12:00:00Z",
            "analysis": {
                "flow_state": flow_analysis,
                "checklist_results": [
                    {
                        "phase": phase.phase,
                        "status": phase.status.value,
                        "completion_percentage": phase.completion_percentage,
                        "tasks": [
                            {
                                "task_id": task.task_id,
                                "status": task.status.value,
                                "confidence": task.confidence,
                                "evidence_count": len(task.evidence)
                            }
                            for task in phase.tasks
                        ]
                    }
                    for phase in checklist_results
                ],
                "routing_decision": {
                    "target_page": routing_decision.target_page,
                    "phase": routing_decision.phase,
                    "specific_task": routing_decision.specific_task
                },
                "user_guidance": user_guidance
            }
        }
        
    except Exception as e:
        logger.error(f"❌ ANALYSIS API ERROR: {flow_id} - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze flow state: {str(e)}"
        ) 