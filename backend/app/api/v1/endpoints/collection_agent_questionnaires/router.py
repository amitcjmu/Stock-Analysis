"""
Collection Agent Questionnaire Router
Main API endpoints for agent-driven questionnaire generation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.feature_flags import is_feature_enabled
from app.models import User
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import (
    QuestionnaireGenerationRequest,
    QuestionnaireGenerationResponse,
)

from .generation import generate_questionnaire_with_agent

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
AGENT_GENERATION_TIMEOUT = 30  # seconds (increased to allow agent generation)
QUESTIONNAIRE_POLL_INTERVAL = 5  # seconds


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


@router.post("/flows/{flow_id}/questionnaires/generate")
async def generate_questionnaire(
    flow_id: str,
    request: Optional[QuestionnaireGenerationRequest] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user: User = Depends(lambda: User()),  # Simplified for now
) -> QuestionnaireGenerationResponse:
    """
    Trigger agent-driven questionnaire generation.
    Returns immediately with pending status if agent is working.
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

        # Check if agent-first generation is enabled
        use_agent = is_feature_enabled("collection.gaps.v2_agent_questionnaires", True)
        use_fallback = is_feature_enabled("collection.gaps.bootstrap_fallback", True)

        if not use_agent:
            # Return immediately that bootstrap should be used
            logger.info(
                f"Agent questionnaires disabled, using bootstrap for flow {flow_id}"
            )
            return QuestionnaireGenerationResponse(
                status="ready",
                questionnaire_id="bootstrap",
                message="Using bootstrap questionnaire (agent generation disabled)",
            )

        # Check if questionnaire generation is already in progress
        if flow.flow_metadata and flow.flow_metadata.get("questionnaire_generating"):
            generation_start = flow.flow_metadata.get("generation_started_at")
            if generation_start:
                started = datetime.fromisoformat(generation_start)
                elapsed = (datetime.utcnow() - started).total_seconds()

                if elapsed < AGENT_GENERATION_TIMEOUT:
                    # Still generating
                    return QuestionnaireGenerationResponse(
                        status="pending",
                        error_code="QUESTIONNAIRE_GENERATING",
                        retry_after=QUESTIONNAIRE_POLL_INTERVAL,
                        message=f"Questionnaire generation in progress ({int(elapsed)}s elapsed)",
                    )
                else:
                    # Timeout - use fallback if enabled
                    if use_fallback:
                        logger.warning(
                            f"Agent generation timed out for flow {flow_id}, using fallback"
                        )
                        return QuestionnaireGenerationResponse(
                            status="fallback",
                            questionnaire_id="bootstrap",
                            message="Agent generation timed out, using bootstrap questionnaire",
                        )
                    else:
                        return QuestionnaireGenerationResponse(
                            status="error",
                            error_code="GENERATION_TIMEOUT",
                            message="Questionnaire generation timed out",
                        )

        # Start agent generation
        logger.info(
            f"Starting agent-driven questionnaire generation for flow {flow_id}"
        )

        # Mark flow as generating
        if not flow.flow_metadata:
            flow.flow_metadata = {}
        flow.flow_metadata["questionnaire_generating"] = True
        flow.flow_metadata["generation_started_at"] = datetime.utcnow().isoformat()
        await db.commit()

        # Trigger async agent generation
        asyncio.create_task(
            generate_questionnaire_with_agent(
                flow_id=flow.id,
                flow_uuid=flow.flow_id,
                context=context,
                selected_asset_ids=request.selected_asset_ids if request else None,
            )
        )

        # Return pending status immediately
        return QuestionnaireGenerationResponse(
            status="pending",
            error_code="QUESTIONNAIRE_GENERATING",
            retry_after=QUESTIONNAIRE_POLL_INTERVAL,
            message="Agent is generating questionnaire",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating questionnaire generation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate questionnaire generation",
        )
