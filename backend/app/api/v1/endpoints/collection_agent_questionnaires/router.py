"""
Collection Agent Questionnaire Router
Questionnaire status polling endpoint for frontend.

DEPRECATION NOTICE (Nov 2025):
- POST /questionnaires/generate endpoint REMOVED (dead code)
- Per ADR-035: Use MFO auto-progression or _start_agent_generation instead
- Only GET /questionnaires/status remains (actively used by QuestionnaireGenerationModal.tsx)
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.models import User
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
# Bug #893 Fix: Increased timeout from 30s to 90s to accommodate LLM API latency and agent orchestration
AGENT_GENERATION_TIMEOUT = (
    90  # seconds (allows sufficient time for agent + LLM execution)
)


@router.get("/flows/{flow_id}/questionnaires/status")
async def check_questionnaire_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user: User = Depends(lambda: User()),  # Simplified for now
) -> Dict[str, Any]:
    """
    Check the status of questionnaire generation for a flow.
    Returns immediately with current status.

    Used by: QuestionnaireGenerationModal.tsx (frontend polling)
    """
    try:
        # Verify flow exists and user has access
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.client_account_id == context.client_account_id,
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Check if agent questionnaire is ready
        if flow.flow_metadata and flow.flow_metadata.get("questionnaire_ready"):
            # Get the questionnaire
            questionnaire_id = flow.flow_metadata.get("agent_questionnaire_id")
            if questionnaire_id:
                questionnaire_result = await db.execute(
                    select(AdaptiveQuestionnaire).where(
                        AdaptiveQuestionnaire.id == UUID(questionnaire_id)
                    )
                )
                questionnaire = questionnaire_result.scalar_one_or_none()
                if questionnaire:
                    return {
                        "status": "ready",
                        "questionnaire": {
                            "id": str(questionnaire.id),
                            "title": questionnaire.title,
                            "description": questionnaire.description,
                            "questions": questionnaire.questions,
                            "target_gaps": questionnaire.target_gaps,
                            "validation_rules": questionnaire.validation_rules,
                        },
                    }

        # Check if still generating
        if flow.flow_metadata and flow.flow_metadata.get("questionnaire_generating"):
            generation_start = flow.flow_metadata.get("generation_started_at")
            if generation_start:
                started = datetime.fromisoformat(generation_start)
                elapsed = (datetime.utcnow() - started).total_seconds()
                if elapsed < AGENT_GENERATION_TIMEOUT:
                    return {
                        "status": "generating",
                        "elapsed_seconds": int(elapsed),
                        "message": f"Generating questionnaire ({int(elapsed)}s elapsed)",
                    }
                else:
                    # Timed out
                    return {"status": "error", "error": "Generation timed out"}

        # Check if generation failed
        if flow.flow_metadata and flow.flow_metadata.get("generation_failed"):
            return {"status": "error", "error": "Generation failed"}

        # Not started or unknown state
        return {
            "status": "not_started",
            "message": "Questionnaire generation not started",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking questionnaire status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check status")
