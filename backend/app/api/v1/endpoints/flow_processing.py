"""
Flow Processing API Endpoints
Handles flow continuation and routing decisions using intelligent agents
"""

import logging
from typing import Dict, Any, Optional
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

class FlowContinuationResponse(BaseModel):
    success: bool
    flow_id: str
    routing_decision: str
    user_guidance: str
    system_actions: list[str]
    confidence: float
    reasoning: str
    estimated_completion_time: int
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
        
        # Convert to API response format
        if result.success:
            # Format user guidance from user actions
            user_guidance = result.user_actions[0] if result.user_actions else "Follow system guidance"
            
            # Add specific guidance based on routing decision
            if "/discovery/data-import" in result.routing_decision:
                user_guidance = "Go to the Data Import page and upload a data file containing asset information."
            elif "enhanced-dashboard" in result.routing_decision:
                if "action=processing" in result.routing_decision:
                    user_guidance = "Stay on the dashboard while the system processes your data in the background."
                else:
                    user_guidance = "Review your flow status on the enhanced dashboard."
            
            logger.info(f"✅ FLOW PROCESSING SUCCESS: {flow_id} -> {result.routing_decision}")
            
            return FlowContinuationResponse(
                success=True,
                flow_id=flow_id,
                routing_decision=result.routing_decision,
                user_guidance=user_guidance,
                system_actions=result.system_actions,
                confidence=result.confidence,
                reasoning=result.reasoning,
                estimated_completion_time=result.estimated_completion_time
            )
        else:
            logger.error(f"❌ FLOW PROCESSING FAILED: {flow_id} - {result.error_message}")
            
            return FlowContinuationResponse(
                success=False,
                flow_id=flow_id,
                routing_decision=result.routing_decision,
                user_guidance="There was an issue analyzing your flow. Please try again.",
                system_actions=result.system_actions,
                confidence=result.confidence,
                reasoning=result.reasoning,
                estimated_completion_time=0,
                error_message=result.error_message
            )
            
    except Exception as e:
        logger.error(f"❌ FLOW PROCESSING ERROR: {flow_id} - {str(e)}")
        
        return FlowContinuationResponse(
            success=False,
            flow_id=flow_id,
            routing_decision="/discovery/enhanced-dashboard",
            user_guidance="An error occurred while processing your request. Please try again.",
            system_actions=["Log error and investigate"],
            confidence=0.1,
            reasoning=f"API error: {str(e)}",
            estimated_completion_time=0,
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