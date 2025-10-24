"""
Collection Bulk Answer Endpoints

Provides endpoints for multi-asset answer population and bulk operations.
Part of Collection Flow Adaptive Questionnaire Enhancements.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context_dependency
from app.schemas.collection import (
    BulkAnswerPreviewRequest,
    BulkAnswerPreviewResponse,
    BulkAnswerSubmitRequest,
    BulkAnswerSubmitResponse,
)
from app.services.collection.bulk_answer import CollectionBulkAnswerService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/bulk-answer-preview", response_model=BulkAnswerPreviewResponse)
async def preview_bulk_answers(
    request: BulkAnswerPreviewRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Preview bulk answer operation to identify conflicts.

    Analyzes existing answers across selected assets and identifies
    potential conflicts before submission.
    """
    try:
        service = CollectionBulkAnswerService(db=db, context=context)

        # Service now returns Pydantic model directly
        preview = await service.preview_bulk_answers(
            child_flow_id=request.child_flow_id,
            asset_ids=request.asset_ids,
            question_ids=request.question_ids,
        )

        return preview

    except Exception as e:
        logger.error(f"❌ Bulk answer preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-answer", response_model=BulkAnswerSubmitResponse)
async def submit_bulk_answers(
    request: BulkAnswerSubmitRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit bulk answers to multiple assets.

    Processes answers in chunks of 100 assets per transaction for data integrity.
    Returns partial success if some chunks fail.
    """
    try:
        service = CollectionBulkAnswerService(db=db, context=context)

        # Convert Pydantic models to dicts for service
        answers = [answer.model_dump() for answer in request.answers]

        # Service now returns Pydantic model directly
        result = await service.submit_bulk_answers(
            child_flow_id=request.child_flow_id,
            asset_ids=request.asset_ids,
            answers=answers,
            conflict_resolution_strategy=request.conflict_resolution_strategy,
        )

        return result

    except Exception as e:
        logger.error(f"❌ Bulk answer submission failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
