"""
Collection Bulk Import Endpoints

Provides endpoints for CSV/JSON bulk import with intelligent field mapping.
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
async def test_bulk_import_router(
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db),
):
    """
    Test endpoint to verify router registration.
    TODO: Remove after implementing actual endpoints.
    """
    return {
        "status": "success",
        "message": "Bulk import router is registered and working",
        "context": {
            "client_account_id": context.client_account_id,
            "engagement_id": context.engagement_id,
        },
    }


# TODO: Implement actual endpoints
# POST /bulk-import/analyze - Analyze CSV/JSON and suggest mappings
# POST /bulk-import/execute - Execute import with confirmed mappings
# GET /bulk-import/status/{task_id} - Poll import task status
