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

# Import the REAL single intelligent CrewAI agent
try:
    from app.services.agents.intelligent_flow_agent import IntelligentFlowAgent, FlowIntelligenceResult
    INTELLIGENT_AGENT_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ REAL Single Intelligent CrewAI Agent imported successfully")
except ImportError as e:
    INTELLIGENT_AGENT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to import intelligent agent: {e}")
    
    # Fallback classes
    class FlowIntelligenceResult:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class IntelligentFlowAgent:
        async def analyze_flow_continuation(self, flow_id: str, **kwargs):
            return FlowIntelligenceResult(
                success=False,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="data_import",
                routing_decision="/discovery/overview",
                user_guidance="Intelligent agent not available",
                reasoning="Agent import failed",
                confidence=0.0
            )

logger = logging.getLogger(__name__)

router = APIRouter()

class FlowContinuationRequest(BaseModel):
    user_context: Optional[Dict[str, Any]] = None

class TaskResult(BaseModel):
    task_id: str
    task_name: str
    status: str  # 'completed', 'in_progress', 'not_started', 'failed'
    confidence: float
    next_steps: List[str] = []

class PhaseStatus(BaseModel):
    phase_id: str
    phase_name: str
    status: str  # 'completed', 'in_progress', 'not_started', 'blocked'
    completion_percentage: float
    tasks: List[TaskResult]
    estimated_time_remaining: Optional[int] = None

class RoutingContext(BaseModel):
    target_page: str
    recommended_page: str
    flow_id: str
    phase: str
    flow_type: str

class UserGuidance(BaseModel):
    primary_message: str
    action_items: List[str]
    user_actions: List[str]
    system_actions: List[str]
    estimated_completion_time: Optional[int] = None

class FlowContinuationResponse(BaseModel):
    success: bool
    flow_id: str
    flow_type: str
    current_phase: str
    routing_context: RoutingContext
    user_guidance: UserGuidance
    checklist_status: List[PhaseStatus]
    agent_insights: List[Dict[str, Any]] = []
    confidence: float
    reasoning: str
    execution_time: float

@router.post("/continue/{flow_id}", response_model=FlowContinuationResponse)
async def continue_flow_processing(
    flow_id: str,
    request: FlowContinuationRequest,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Continue flow processing using single intelligent CrewAI agent
    
    This endpoint uses a single, intelligent agent that:
    - Analyzes flow status using multiple tools
    - Validates phase completion against success criteria
    - Makes intelligent routing decisions
    - Provides specific, actionable user guidance
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"🧠 SINGLE INTELLIGENT AGENT: Starting flow continuation for {flow_id}")
        
        if not INTELLIGENT_AGENT_AVAILABLE:
            logger.error("❌ Intelligent agent not available - using fallback")
            return _create_fallback_response(flow_id, "Intelligent agent not available")
        
        # Create single intelligent agent
        intelligent_agent = IntelligentFlowAgent()
        
        # Analyze flow using single agent with multiple tools
        result = await intelligent_agent.analyze_flow_continuation(
            flow_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id
        )
        
        execution_time = time.time() - start_time
        logger.info(f"✅ SINGLE AGENT COMPLETE: {flow_id} analyzed in {execution_time:.3f}s")
        
        # Convert result to API response format
        return _convert_to_api_response(result, execution_time)
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ SINGLE AGENT ERROR: {flow_id} failed after {execution_time:.3f}s - {str(e)}")
        
        return _create_fallback_response(flow_id, f"Agent analysis failed: {str(e)}")

def _convert_to_api_response(result: FlowIntelligenceResult, execution_time: float) -> FlowContinuationResponse:
    """Convert agent result to API response format"""
    try:
        # Parse routing decision
        routing_path = result.routing_decision
        
        # Create routing context
        routing_context = RoutingContext(
            target_page=routing_path,
            recommended_page=routing_path,
            flow_id=result.flow_id,
            phase=result.current_phase,
            flow_type=result.flow_type
        )
        
        # Create user guidance
        user_guidance = UserGuidance(
            primary_message=result.user_guidance,
            action_items=[result.user_guidance],
            user_actions=result.next_actions if result.next_actions else [result.user_guidance],
            system_actions=["Continue background processing"],
            estimated_completion_time=30  # Fast single agent
        )
        
        # Create checklist status based on current phase
        checklist_status = _create_checklist_status(result)
        
        return FlowContinuationResponse(
            success=result.success,
            flow_id=result.flow_id,
            flow_type=result.flow_type,
            current_phase=result.current_phase,
            routing_context=routing_context,
            user_guidance=user_guidance,
            checklist_status=checklist_status,
            agent_insights=[{
                "agent": "Single Intelligent Flow Agent",
                "analysis": result.reasoning,
                "confidence": result.confidence,
                "issues_found": result.issues_found
            }],
            confidence=result.confidence,
            reasoning=result.reasoning,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Failed to convert agent result: {e}")
        return _create_fallback_response(result.flow_id, f"Response conversion failed: {str(e)}")

def _create_checklist_status(result: FlowIntelligenceResult) -> List[PhaseStatus]:
    """Create checklist status based on agent analysis"""
    try:
        phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
        checklist_status = []
        
        current_phase_index = 0
        try:
            current_phase_index = phases.index(result.current_phase)
        except ValueError:
            current_phase_index = 0
        
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
                # Current phase - determine status from agent result
                if result.success and "completed successfully" in result.user_guidance:
                    status = "completed"
                    completion = 100.0
                    task_status = "completed"
                elif "ISSUE:" in result.user_guidance or not result.success:
                    status = "not_started" if "No data" in result.user_guidance else "in_progress"
                    completion = 0.0 if "No data" in result.user_guidance else 25.0
                    task_status = "not_started" if "No data" in result.user_guidance else "in_progress"
                else:
                    status = "in_progress"
                    completion = 50.0
                    task_status = "in_progress"
                
                # Create task based on agent guidance
                task_name = result.user_guidance.split(":")[1].strip() if ":" in result.user_guidance else phase.replace('_', ' ').title()
                if "ACTION NEEDED:" in result.user_guidance:
                    task_name = result.user_guidance.split("ACTION NEEDED:")[1].strip()
                
                tasks = [TaskResult(
                    task_id=f"{phase}_main",
                    task_name=task_name,
                    status=task_status,
                    confidence=result.confidence,
                    next_steps=result.next_actions
                )]
            else:
                status = "not_started"
                completion = 0.0
                tasks = [TaskResult(
                    task_id=f"{phase}_main",
                    task_name=f"{phase.replace('_', ' ').title()}",
                    status="not_started",
                    confidence=0.0,
                    next_steps=[]
                )]
            
            checklist_status.append(PhaseStatus(
                phase_id=phase,
                phase_name=phase.replace('_', ' ').title(),
                status=status,
                completion_percentage=completion,
                tasks=tasks,
                estimated_time_remaining=5 if status != "completed" else None
            ))
        
        return checklist_status
        
    except Exception as e:
        logger.error(f"Failed to create checklist status: {e}")
        return []

def _create_fallback_response(flow_id: str, error_message: str) -> FlowContinuationResponse:
    """Create fallback response when agent fails"""
    return FlowContinuationResponse(
        success=False,
        flow_id=flow_id,
        flow_type="discovery",
        current_phase="data_import",
        routing_context=RoutingContext(
            target_page="/discovery/data-import",
            recommended_page="/discovery/data-import",
            flow_id=flow_id,
            phase="data_import",
            flow_type="discovery"
        ),
        user_guidance=UserGuidance(
            primary_message=f"System error: {error_message}",
            action_items=["Check system logs", "Retry flow processing"],
            user_actions=["Upload data file if needed"],
            system_actions=["Fix agent system"],
            estimated_completion_time=None
        ),
        checklist_status=[],
        agent_insights=[{
            "agent": "Fallback System",
            "analysis": error_message,
            "confidence": 0.0,
            "issues_found": [error_message]
        }],
        confidence=0.0,
        reasoning=f"Fallback response due to: {error_message}",
        execution_time=0.0
    )

# Legacy validation endpoints - kept for compatibility but simplified

async def validate_flow_phases(flow_id: str, db: AsyncSession, context: RequestContext) -> Dict[str, Any]:
    """Legacy validation function - simplified for compatibility"""
    try:
        # Use the intelligent agent for validation too
        intelligent_agent = IntelligentFlowAgent()
        result = await intelligent_agent.analyze_flow_continuation(flow_id)
        
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
        result = await intelligent_agent.analyze_flow_continuation(flow_id)
        
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