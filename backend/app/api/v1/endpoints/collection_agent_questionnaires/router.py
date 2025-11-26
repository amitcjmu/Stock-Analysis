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
async def check_questionnaire_status(  # noqa: C901
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user: User = Depends(lambda: User()),  # Simplified for now
) -> Dict[str, Any]:
    """
    Check the status of questionnaire generation for a flow.
    Returns immediately with current status.

    Used by: QuestionnaireGenerationModal.tsx (frontend polling)

    Bug #31 Fix: Query database directly for questionnaire status instead of relying
    solely on flow_metadata flags. This ensures we detect ready questionnaires even
    if the metadata flags weren't set correctly.
    """
    try:
        # Verify flow exists and user has access
        # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
        flow_uuid = UUID(flow_id)
        flow_result = await db.execute(
            select(CollectionFlow).where(
                (CollectionFlow.flow_id == flow_uuid)
                | (CollectionFlow.id == flow_uuid),
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.client_account_id == context.client_account_id,
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # ✅ Bug #31 Fix: ALWAYS check database for questionnaire status
        # Don't rely only on flow_metadata flags - query the actual questionnaire table
        # This handles cases where background_task completed but metadata wasn't updated

        # Get selected asset IDs from flow_metadata for filtering
        selected_asset_ids = None
        if flow.flow_metadata:
            selected_asset_ids = flow.flow_metadata.get("selected_asset_ids", [])

        # Query for questionnaires linked to this flow
        query_conditions = [
            AdaptiveQuestionnaire.collection_flow_id == flow.id,
            AdaptiveQuestionnaire.client_account_id == context.client_account_id,
            AdaptiveQuestionnaire.engagement_id == context.engagement_id,
        ]

        # Bug #30 Fix: Filter by selected asset IDs if available
        if selected_asset_ids:
            selected_uuids = [
                UUID(aid) if isinstance(aid, str) else aid for aid in selected_asset_ids
            ]
            query_conditions.append(AdaptiveQuestionnaire.asset_id.in_(selected_uuids))

        questionnaire_result = await db.execute(
            select(AdaptiveQuestionnaire).where(*query_conditions)
        )
        questionnaires = questionnaire_result.scalars().all()

        # Check if any questionnaire is ready with questions
        for questionnaire in questionnaires:
            if (
                questionnaire.completion_status == "ready"
                and questionnaire.questions
                and len(questionnaire.questions) > 0
            ):
                logger.info(
                    f"✅ Bug #31 Fix: Found ready questionnaire {questionnaire.id} "
                    f"with {len(questionnaire.questions)} questions"
                )
                return {
                    "status": "ready",
                    "questionnaire": {
                        "id": str(questionnaire.id),
                        "title": questionnaire.title,
                        "description": questionnaire.description,
                        "questions": questionnaire.questions,
                        "target_gaps": getattr(questionnaire, "target_gaps", None),
                        "validation_rules": questionnaire.validation_rules,
                        "asset_id": (
                            str(questionnaire.asset_id)
                            if questionnaire.asset_id
                            else None
                        ),
                    },
                }

        # Check if any questionnaire is pending (still generating)
        for questionnaire in questionnaires:
            if questionnaire.completion_status == "pending":
                # Still generating - check elapsed time
                generation_start = None
                if flow.flow_metadata:
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
                else:
                    # No start time, just report as generating
                    return {
                        "status": "generating",
                        "message": "Generating questionnaire...",
                    }

        # Check for failed questionnaires
        for questionnaire in questionnaires:
            if questionnaire.completion_status == "failed":
                return {"status": "error", "error": "Questionnaire generation failed"}

        # Fallback: Check flow_metadata flags (legacy support)
        if flow.flow_metadata and flow.flow_metadata.get("questionnaire_ready"):
            # Metadata says ready but we didn't find a questionnaire above
            questionnaire_id = flow.flow_metadata.get("agent_questionnaire_id")
            if questionnaire_id:
                questionnaire_result = await db.execute(
                    select(AdaptiveQuestionnaire).where(
                        AdaptiveQuestionnaire.id == UUID(questionnaire_id)
                    )
                )
                questionnaire = questionnaire_result.scalar_one_or_none()
                if questionnaire and questionnaire.questions:
                    return {
                        "status": "ready",
                        "questionnaire": {
                            "id": str(questionnaire.id),
                            "title": questionnaire.title,
                            "description": questionnaire.description,
                            "questions": questionnaire.questions,
                            "target_gaps": getattr(questionnaire, "target_gaps", None),
                            "validation_rules": questionnaire.validation_rules,
                            "asset_id": (
                                str(questionnaire.asset_id)
                                if questionnaire.asset_id
                                else None
                            ),
                        },
                    }

        # Check if still generating via metadata
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

        # Check if generation failed via metadata
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
