"""
Collection Dynamic Questions Endpoints

Provides endpoints for asset-type-specific question filtering and dynamic generation.
Part of Collection Flow Adaptive Questionnaire Enhancements.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context_dependency

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/test")
async def test_dynamic_questions_router(
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Test endpoint to verify router registration.
    TODO: Remove after implementing actual endpoints.
    """
    return {
        "status": "success",
        "message": "Dynamic questions router is registered and working",
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
        },
    }


# TODO: Implement actual endpoints
# GET /questions/filtered - Get questions filtered by asset type
# POST /questions/refresh - Trigger agent-based question refresh
# POST /questions/reopen - Manually reopen closed questions
