"""
Collection Dynamic Questions Endpoints

Provides endpoints for asset-type-specific question filtering and dynamic generation.
Part of Collection Flow Adaptive Questionnaire Enhancements.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context_dependency
from app.schemas.collection import (
    DependencyChangeRequest,
    DependencyChangeResponse,
    DynamicQuestionsRequest,
    DynamicQuestionsResponse,
)
from app.services.collection.dynamic_question_engine import DynamicQuestionEngine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/questions/filtered", response_model=DynamicQuestionsResponse)
async def get_filtered_questions(
    request: DynamicQuestionsRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Get questions filtered by asset type.

    Returns questions applicable to the specified asset type with optional
    agent-based pruning for intelligent question reduction.
    """
    try:
        service = DynamicQuestionEngine(db=db, context=context)

        # Service now returns Pydantic model directly
        result = await service.get_filtered_questions(
            child_flow_id=request.child_flow_id,
            asset_id=request.asset_id,
            asset_type=request.asset_type,
            include_answered=request.include_answered,
            refresh_agent_analysis=request.refresh_agent_analysis,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Failed to get filtered questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependency-change", response_model=DependencyChangeResponse)
async def handle_dependency_change(
    request: DependencyChangeRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle a dependency change and reopen affected questions.

    When a critical field changes, this endpoint determines which questions
    should be reopened based on dependency analysis.
    """
    try:
        service = DynamicQuestionEngine(db=db, context=context)

        # Service now returns Pydantic model directly
        result = await service.handle_dependency_change(
            changed_asset_id=request.changed_asset_id,
            changed_field=request.changed_field,
            old_value=request.old_value,
            new_value=request.new_value,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Failed to handle dependency change: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
