"""
Agent Insights API Endpoints

This module contains all agent insights and questions related endpoints,
extracted from unified_discovery.py for better modularity.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/flow/{flow_id}/agent-insights")
async def get_agent_insights(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get agent insights for a discovery flow."""
    try:
        logger.info(
            safe_log_format(
                "Getting agent insights for flow: {flow_id}", flow_id=flow_id
            )
        )

        # Get the discovery flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Extract agent insights from flow state
        insights = (
            flow.crewai_state_data.get("agent_insights", {})
            if flow.crewai_state_data
            else {}
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "insights": insights,
            "has_insights": bool(insights),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get agent insights: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


def _extract_questions_from_discovery_flow(discovery_flow):
    """Extract questions from discovery flow state data."""
    questions = []
    has_pending = False

    if discovery_flow and discovery_flow.crewai_state_data:
        agent_messages = discovery_flow.crewai_state_data.get("agent_messages", [])
        for msg in agent_messages:
            if msg.get("type") == "question" and msg.get("status") == "pending":
                questions.append(
                    {
                        "id": msg.get("id"),
                        "agent": msg.get("agent"),
                        "question": msg.get("content"),
                        "context": msg.get("context"),
                        "timestamp": msg.get("timestamp"),
                        "status": "pending",
                    }
                )
                has_pending = True

    return questions, has_pending


def _extract_questions_from_crewai_flow(crewai_flow, existing_questions):
    """Extract questions from master flow phase state."""
    questions = []
    has_pending = False

    if crewai_flow and crewai_flow.flow_persistence_data:
        current_phase_state = crewai_flow.flow_persistence_data.get(
            "current_phase_state", {}
        )
        phase_questions = current_phase_state.get("pending_questions", [])
        for q in phase_questions:
            if q not in existing_questions:
                questions.append(q)
                if q.get("status") == "pending":
                    has_pending = True

    return questions, has_pending


def _get_generic_questions():
    """Return default generic questions."""
    return [
        {
            "id": "generic_1",
            "agent": "Discovery Agent",
            "question": "What is the primary business objective for this migration?",
            "context": "business_context",
            "status": "pending",
        },
        {
            "id": "generic_2",
            "agent": "Technical Agent",
            "question": "Are there any specific technical constraints we should be aware of?",
            "context": "technical_context",
            "status": "pending",
        },
    ]


@router.get("/agents/discovery/agent-questions")
async def get_agent_questions(
    flow_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get agent questions, either specific to a flow or generic questions.
    This endpoint retrieves the questions that agents may ask during discovery.
    """
    try:
        logger.info(
            safe_log_format(
                "Getting agent questions for flow: {flow_id}", flow_id=flow_id
            )
        )

        questions = []
        has_pending_questions = False

        if flow_id:
            # Get from DiscoveryFlow
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
            result = await db.execute(stmt)
            discovery_flow = result.scalar_one_or_none()

            # Extract questions from discovery flow
            flow_questions, flow_has_pending = _extract_questions_from_discovery_flow(
                discovery_flow
            )
            questions.extend(flow_questions)
            has_pending_questions = has_pending_questions or flow_has_pending

            # Check CrewAI Flow State for additional context
            master_stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                )
            )
            master_result = await db.execute(master_stmt)
            master_flow = master_result.scalar_one_or_none()

            # Extract questions from master flow
            master_questions, master_has_pending = _extract_questions_from_crewai_flow(
                master_flow, questions
            )
            questions.extend(master_questions)
            has_pending_questions = has_pending_questions or master_has_pending

        # If no questions found, return generic structure
        if not questions:
            questions = _get_generic_questions()

        return {
            "success": True,
            "flow_id": flow_id,
            "questions": questions,
            "has_pending_questions": has_pending_questions,
            "total_questions": len(questions),
        }

    except Exception as e:
        logger.error(safe_log_format("Failed to get agent questions: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
