"""
Flow Processing API Endpoints
Handles flow continuation and routing decisions using intelligent agents
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.services.agents.intelligent_flow_agent import IntelligentFlowAgent, FlowIntelligenceResult

logger = logging.getLogger(__name__)

router = APIRouter()

class FlowContinuationRequest(BaseModel):
    user_context: Optional[Dict[str, Any]] = None

class TaskResult(BaseModel):
    task_id: str
    task_name: str
    status: str  # 'completed' | 'pending' | 'blocked' | 'not_started'
    confidence: float
    next_steps: List[str]

class PhaseChecklistResult(BaseModel):
    phase: str
    status: str  # 'completed' | 'in_progress' | 'pending' | 'blocked'
    completion_percentage: float
    tasks: List[TaskResult]
    next_required_actions: List[str]

class FlowContinuationResponse(BaseModel):
    success: bool
    flow_id: str
    current_phase: str
    next_action: str
    routing_context: Dict[str, Any]
    checklist_status: List[PhaseChecklistResult]
    user_guidance: Dict[str, Any]
    error_message: Optional[str] = None

@router.post("/continue/{flow_id}", response_model=FlowContinuationResponse)
async def continue_flow_processing(
    flow_id: str,
    request: FlowContinuationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
) -> FlowContinuationResponse:
    """
    Continue flow processing with intelligent analysis and routing
    Single agent replaces complex multi-agent system for efficiency
    """
    try:
        logger.info(f"🤖 FLOW PROCESSING API: Received continuation request for flow {flow_id}")
        
        # Initialize the intelligent flow agent
        intelligent_agent = IntelligentFlowAgent()
        
        # Process with intelligent analysis
        result: FlowIntelligenceResult = await intelligent_agent.process_flow_intelligence(
            flow_id=flow_id,
            user_context=request.user_context
        )
        
        # Convert to API response format that frontend expects
        if result.success:
            # Format user guidance from user actions
            user_guidance_text = result.user_actions[0] if result.user_actions else "Follow system guidance"
            
            # Add specific guidance based on routing decision
            if "/discovery/data-import" in result.routing_decision:
                user_guidance_text = "Go to the Data Import page and upload a data file containing asset information."
            elif "enhanced-dashboard" in result.routing_decision:
                if "action=processing" in result.routing_decision:
                    user_guidance_text = "Stay on the dashboard while the system processes your data in the background."
                else:
                    user_guidance_text = "Review your flow status on the enhanced dashboard."
            
            # Create checklist status based on current phase
            checklist_status = []
            phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
            current_phase_index = phases.index(result.current_phase) if result.current_phase in phases else 0
            
            for i, phase in enumerate(phases):
                if i < current_phase_index:
                    status = "completed"
                    completion = 100.0
                    tasks = [TaskResult(
                        task_id=f"{phase}_main",
                        task_name=f"{phase.replace('_', ' ').title()} Complete",
                        status="completed",
                        confidence=0.9,
                        next_steps=[]
                    )]
                elif i == current_phase_index:
                    # Check if this is data_import phase with no data
                    if phase == "data_import" and ("0 records" in result.reasoning or "No data records found" in result.reasoning):
                        status = "pending"
                        completion = 0.0
                        tasks = [TaskResult(
                            task_id=f"{phase}_upload",
                            task_name="Upload Data File",
                            status="not_started",
                            confidence=0.0,
                            next_steps=["Navigate to Data Import page", "Upload CSV/Excel file with asset data"]
                        )]
                    else:
                        status = "in_progress"
                        completion = 50.0
                        tasks = [TaskResult(
                            task_id=f"{phase}_process",
                            task_name=f"Process {phase.replace('_', ' ').title()}",
                            status="pending",
                            confidence=0.7,
                            next_steps=["Continue processing", "Review results"]
                        )]
                else:
                    status = "pending"
                    completion = 0.0
                    tasks = [TaskResult(
                        task_id=f"{phase}_future",
                        task_name=f"{phase.replace('_', ' ').title()} Pending",
                        status="not_started",
                        confidence=0.0,
                        next_steps=["Complete previous phases first"]
                    )]
                
                checklist_status.append(PhaseChecklistResult(
                    phase=phase,
                    status=status,
                    completion_percentage=completion,
                    tasks=tasks,
                    next_required_actions=[task.task_name for task in tasks if task.status != "completed"]
                ))
            
            logger.info(f"✅ FLOW PROCESSING SUCCESS: {flow_id} -> {result.routing_decision}")
            
            return FlowContinuationResponse(
                success=True,
                flow_id=flow_id,
                current_phase=result.current_phase,
                next_action=user_guidance_text,
                routing_context={
                    "target_page": result.routing_decision,
                    "context_data": {
                        "flow_id": flow_id,
                        "phase": result.current_phase,
                        "reasoning": result.reasoning
                    },
                    "specific_task": "upload_data" if "data-import" in result.routing_decision else "continue_flow"
                },
                checklist_status=checklist_status,
                user_guidance={
                    "summary": user_guidance_text,
                    "phase": result.current_phase,
                    "completion_percentage": (current_phase_index / len(phases)) * 100,
                    "next_steps": result.user_actions if result.user_actions else [user_guidance_text],
                    "detailed_status": {
                        "completed_tasks": [
                            {"name": task.task_name, "confidence": task.confidence} 
                            for checklist in checklist_status 
                            for task in checklist.tasks 
                            if task.status == "completed"
                        ],
                        "pending_tasks": [
                            {"name": task.task_name, "next_steps": task.next_steps}
                            for checklist in checklist_status 
                            for task in checklist.tasks 
                            if task.status != "completed"
                        ]
                    }
                }
            )
        else:
            logger.error(f"❌ FLOW PROCESSING FAILED: {flow_id} - {result.error_message}")
            
            return FlowContinuationResponse(
                success=False,
                flow_id=flow_id,
                current_phase="error",
                next_action="There was an issue analyzing your flow. Please try again.",
                routing_context={
                    "target_page": "/discovery/enhanced-dashboard",
                    "context_data": {"error": result.error_message},
                    "specific_task": "retry"
                },
                checklist_status=[],
                user_guidance={
                    "summary": "There was an issue analyzing your flow. Please try again.",
                    "phase": "error",
                    "completion_percentage": 0,
                    "next_steps": ["Retry flow processing", "Check system logs"],
                    "detailed_status": {
                        "completed_tasks": [],
                        "pending_tasks": [{"name": "Resolve Error", "next_steps": ["Retry processing"]}]
                    }
                },
                error_message=result.error_message
            )
            
    except Exception as e:
        logger.error(f"❌ FLOW PROCESSING ERROR: {flow_id} - {str(e)}")
        
        return FlowContinuationResponse(
            success=False,
            flow_id=flow_id,
            current_phase="error",
            next_action="An error occurred while processing your request. Please try again.",
            routing_context={
                "target_page": "/discovery/enhanced-dashboard",
                "context_data": {"error": str(e)},
                "specific_task": "retry"
            },
            checklist_status=[],
            user_guidance={
                "summary": "An error occurred while processing your request. Please try again.",
                "phase": "error", 
                "completion_percentage": 0,
                "next_steps": ["Retry flow processing", "Contact support if issue persists"],
                "detailed_status": {
                    "completed_tasks": [],
                    "pending_tasks": [{"name": "Resolve Error", "next_steps": ["Retry processing"]}]
                }
            },
            error_message=str(e)
        )

# Legacy validation endpoints - kept for compatibility but simplified

async def validate_flow_phases(flow_id: str, db: AsyncSession, context: RequestContext) -> Dict[str, Any]:
    """Legacy validation function - simplified for compatibility"""
    try:
        # Use the intelligent agent for validation too
        intelligent_agent = IntelligentFlowAgent()
        result = await intelligent_agent.process_flow_intelligence(flow_id)
        
        return {
            "current_phase": result.current_phase,
            "status": result.phase_status,
            "validation_details": {
                "data": {
                    "import_sessions": 1,  # Simplified for compatibility
                    "raw_records": 0,  # Will be updated by agent analysis
                    "threshold_met": False
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Legacy validation failed: {e}")
        return {
            "current_phase": "data_import",
            "status": "INCOMPLETE",
            "validation_details": {"error": str(e)}
        }

async def validate_phase_data(flow_id: str, phase: str, db: AsyncSession, context: RequestContext) -> Dict[str, Any]:
    """Legacy phase validation function - simplified for compatibility"""
    try:
        # Use the intelligent agent for phase validation
        intelligent_agent = IntelligentFlowAgent()
        result = await intelligent_agent.process_flow_intelligence(flow_id)
        
        return {
            "phase": phase,
            "status": result.phase_status,
            "complete": result.phase_status == "COMPLETE",
            "data": {
                "import_sessions": 1,
                "raw_records": 0,
                "threshold_met": False
            },
            "actionable_guidance": result.specific_issues[0] if result.specific_issues else "No specific issues"
        }
        
    except Exception as e:
        logger.error(f"Legacy phase validation failed: {e}")
        return {
            "phase": phase,
            "status": "ERROR",
            "complete": False,
            "data": {},
            "actionable_guidance": f"Validation error: {str(e)}"
        } 