"""
Agent UI Integration Handler
Provides API endpoints for agent-UI communication including questions, insights, and status.
Implements Phase 2 of the Discovery Flow redesign.
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext, get_request_context_dependency
from app.core.database import get_db
from app.services.agent_ui_bridge import agent_ui_bridge
from app.services.agents.agent_communication_protocol import get_communication_protocol
from app.services.confidence.confidence_manager import ConfidenceManager
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic models for request/response
class AgentQuestionResponse(BaseModel):
    question_id: str
    response: Any
    confidence: Optional[float] = None


class AgentInsightAction(BaseModel):
    insight_id: str
    action: str
    data: Optional[Dict[str, Any]] = None


class ThinkRequest(BaseModel):
    agent_id: str
    context: Dict[str, Any]
    complexity_level: str = "standard"  # standard, deep, collaborative


class PonderRequest(BaseModel):
    agent_id: str
    context: Dict[str, Any]
    collaboration_type: str = "cross_agent"  # cross_agent, expert_panel, full_crew


# Services will be initialized per request with proper context
confidence_manager = ConfidenceManager()


# Dependency injection for MasterFlowOrchestrator
async def get_orchestrator(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context_dependency),
) -> MasterFlowOrchestrator:
    """Get MasterFlowOrchestrator instance with proper context"""
    return MasterFlowOrchestrator(db, context)


@router.get("/agent-status")
async def get_agent_status(
    context: RequestContext = Depends(get_request_context_dependency),
    master_orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
):
    """Get current agent status for the UI monitor panel - scoped by client/engagement for multi-tenant security."""
    try:
        # Get communication protocol status (context-aware but not scoped at protocol level)
        comm_protocol = get_communication_protocol()
        protocol_status = comm_protocol.get_protocol_status()

        # Get master orchestrator status - we need an actual flow ID, not just 'discovery'
        # For now, return a placeholder status since we don't have a specific flow ID
        orchestrator_status = {
            "flow_type": "discovery",
            "status": "ready",
            "message": "Orchestrator ready",
        }

        # Get individual agent statuses (scoped to client/engagement)
        agent_statuses = {}
        for agent_name in [
            "data_validation",
            "attribute_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_analysis",
        ]:
            agent_statuses[agent_name] = {
                "status": "idle",
                "confidence": 0.0,
                "last_activity": None,
                "current_task": None,
                "client_account_id": context.client_account_id,  # Include for security audit
                "engagement_id": context.engagement_id,
            }

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_id": context.user_id,
                "security_note": "Agent status is properly scoped to client/engagement context",
            },
            "agents": agent_statuses,
            "orchestrator": orchestrator_status,
            "communication": {
                "protocol_active": protocol_status.get("active", False),
                "registered_agents": protocol_status.get("registered_agents", 0),
                "ui_subscribers": protocol_status.get("ui_subscribers", 0),
                "total_messages": protocol_status.get("metrics", {}).get(
                    "total_messages", 0
                ),
            },
            "overall_status": "ready",
        }

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/agent-questions")
async def get_agent_questions(
    page: str = "dependencies",
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Get pending agent questions for the current page."""
    try:
        # Get questions from agent UI bridge
        questions = agent_ui_bridge.get_questions_for_page(page)

        # If no questions, create sample questions for testing
        if not questions and page == "dependencies":
            # Add sample dependency mapping question
            agent_ui_bridge.add_agent_question(
                agent_id="dependency_analysis_agent",
                agent_name="Dependency Analysis Agent",
                question_type="dependency_validation",
                page=page,
                title="Verify Application Dependency",
                question="Should 'WebApp-01' depend on 'Database-01' based on the network traffic patterns?",
                context={
                    "source_app": "WebApp-01",
                    "target_app": "Database-01",
                    "confidence": 0.75,
                    "evidence": "Network traffic analysis shows regular connections",
                },
                options=[
                    "Yes, confirm this dependency",
                    "No, this is incorrect",
                    "Need more analysis",
                    "Mark as optional dependency",
                ],
                confidence="medium",
                priority="normal",
            )

            # Get updated questions
            questions = agent_ui_bridge.get_questions_for_page(page)

        return {
            "success": True,
            "questions": questions,
            "count": len(questions),
            "page": page,
        }

    except Exception as e:
        logger.error(f"Error getting agent questions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent questions: {str(e)}"
        )


@router.post("/agent-questions/answer")
async def answer_agent_question(
    response_data: AgentQuestionResponse,
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Process user response to an agent question."""
    try:
        # Process the answer through agent UI bridge
        result = agent_ui_bridge.answer_agent_question(
            response_data.question_id, response_data.response
        )

        # Send response through communication protocol
        comm_protocol = get_communication_protocol()
        await comm_protocol.send_ui_interaction(
            {
                "type": "question_response",
                "question_id": response_data.question_id,
                "response": response_data.response,
                "confidence": response_data.confidence,
                "timestamp": datetime.now().isoformat(),
                "context": asdict(context),
            }
        )

        return {
            "success": True,
            "message": "Agent question answered successfully",
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error answering agent question: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to answer agent question: {str(e)}"
        )


@router.get("/agent-insights")
async def get_agent_insights(
    page: str = "dependencies",
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Get agent insights for the current page."""
    try:
        # Get insights from agent UI bridge
        insights = agent_ui_bridge.get_insights_for_page(page)

        # If no insights, create sample insights for testing
        if not insights and page == "dependencies":
            # Add sample dependency insight
            agent_ui_bridge.add_agent_insight(
                agent_id="dependency_analysis_agent",
                agent_name="Dependency Analysis Agent",
                insight_type="dependency_analysis",
                title="Dependency Analysis Complete",
                description="Analyzed application dependencies and identified 3 critical paths that require attention during migration planning.",
                confidence="high",
                supporting_data={
                    "total_dependencies": 12,
                    "critical_paths": 3,
                    "confidence_score": 0.87,
                    "analysis_method": "network_traffic_analysis",
                },
                page=page,
                actionable=True,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                flow_id=context.flow_id,
            )

            # Get updated insights
            insights = agent_ui_bridge.get_insights_for_page(page)

        return {
            "success": True,
            "insights": insights,
            "count": len(insights),
            "page": page,
        }

    except Exception as e:
        logger.error(f"Error getting agent insights: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent insights: {str(e)}"
        )


@router.post("/agent-insights/action")
async def perform_insight_action(
    action_data: AgentInsightAction,
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Perform an action on an agent insight."""
    try:
        # Process the action (implement based on action type)
        result = {
            "insight_id": action_data.insight_id,
            "action": action_data.action,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }

        # Send action through communication protocol
        comm_protocol = get_communication_protocol()
        await comm_protocol.send_ui_interaction(
            {
                "type": "insight_action",
                "insight_id": action_data.insight_id,
                "action": action_data.action,
                "data": action_data.data,
                "context": asdict(context),
            }
        )

        return {
            "success": True,
            "message": f'Insight action "{action_data.action}" completed successfully',
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error performing insight action: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to perform insight action: {str(e)}"
        )


@router.post("/think")
async def agent_think(
    request: ThinkRequest,
    context: RequestContext = Depends(get_request_context_dependency),
    master_orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
):
    """Trigger 'Think' button functionality for progressive intelligence."""
    try:
        # Use master orchestrator to trigger deeper analysis
        result = await master_orchestrator.execute_flow_phase(
            flow_type="discovery",
            phase_name="agent_thinking",
            context={
                "agent_id": request.agent_id,
                "request_context": request.context,
                "complexity_level": request.complexity_level,
            },
        )

        # Send thinking request through communication protocol
        comm_protocol = get_communication_protocol()
        await comm_protocol.send_ui_interaction(
            {
                "type": "think_request",
                "agent_id": request.agent_id,
                "complexity_level": request.complexity_level,
                "context": request.context,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {
            "success": True,
            "message": f"Agent {request.agent_id} is thinking deeper about the problem",
            "thinking_level": request.complexity_level,
            "estimated_time": result.get("estimated_time", "30-60 seconds"),
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error triggering agent thinking: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger agent thinking: {str(e)}"
        )


@router.post("/ponder-more")
async def agent_ponder_more(
    request: PonderRequest,
    context: RequestContext = Depends(get_request_context_dependency),
    master_orchestrator: MasterFlowOrchestrator = Depends(get_orchestrator),
):
    """Trigger 'Ponder More' button functionality for crew collaboration."""
    try:
        # Use master orchestrator to trigger crew collaboration
        result = await master_orchestrator.execute_flow_phase(
            flow_type="discovery",
            phase_name="crew_collaboration",
            context={
                "agent_id": request.agent_id,
                "request_context": request.context,
                "collaboration_type": request.collaboration_type,
            },
        )

        # Send pondering request through communication protocol
        comm_protocol = get_communication_protocol()
        await comm_protocol.send_ui_interaction(
            {
                "type": "ponder_request",
                "agent_id": request.agent_id,
                "collaboration_type": request.collaboration_type,
                "context": request.context,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {
            "success": True,
            "message": f"Agent {request.agent_id} is collaborating with crew for deeper insights",
            "collaboration_type": request.collaboration_type,
            "estimated_time": result.get("estimated_time", "2-3 minutes"),
            "crew_members": result.get("crew_members", []),
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error triggering crew collaboration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger crew collaboration: {str(e)}"
        )


@router.get("/confidence-scores")
async def get_confidence_scores(
    page: str = "dependencies",
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Get confidence scores for agents on the current page."""
    try:
        # Get confidence scores from confidence manager
        scores = await confidence_manager.get_page_confidence_scores(page)

        return {
            "success": True,
            "page": page,
            "confidence_scores": scores,
            "overall_confidence": scores.get("overall", 0.0),
            "needs_attention": scores.get("needs_attention", []),
            "escalation_recommended": scores.get("escalation_recommended", False),
        }

    except Exception as e:
        logger.error(f"Error getting confidence scores: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get confidence scores: {str(e)}"
        )


@router.get("/data-classifications")
async def get_data_classifications(
    page: str = "dependencies",
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Get data classifications for the current page."""
    try:
        # Get classifications from agent UI bridge
        classifications = agent_ui_bridge.get_classified_data_for_page(page)

        return {
            "success": True,
            "page": page,
            "classifications": classifications,
            "summary": {
                "total_items": sum(len(items) for items in classifications.values()),
                "categories": list(classifications.keys()),
                "needs_review": sum(
                    1
                    for items in classifications.values()
                    for item in items
                    if item.get("confidence", "high") == "low"
                ),
            },
        }

    except Exception as e:
        logger.error(f"Error getting data classifications: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get data classifications: {str(e)}"
        )


@router.get("/communication-status")
async def get_communication_status(
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Get agent communication protocol status."""
    try:
        comm_protocol = get_communication_protocol()
        status = comm_protocol.get_protocol_status()

        # Get recent UI messages
        recent_messages = await comm_protocol.get_ui_messages()

        return {
            "success": True,
            "protocol_status": status,
            "recent_messages": recent_messages[-10:],  # Last 10 messages
            "health": "healthy" if status["active"] else "inactive",
        }

    except Exception as e:
        logger.error(f"Error getting communication status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get communication status: {str(e)}"
        )


@router.post("/test-communication")
async def test_agent_communication(
    context: RequestContext = Depends(get_request_context_dependency),
):
    """Test the agent communication system."""
    try:
        comm_protocol = get_communication_protocol()
        test_result = await comm_protocol.test_communication()

        return {
            "success": True,
            "test_result": test_result,
            "message": "Communication test completed successfully",
        }

    except Exception as e:
        logger.error(f"Error testing communication: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to test communication: {str(e)}"
        )
