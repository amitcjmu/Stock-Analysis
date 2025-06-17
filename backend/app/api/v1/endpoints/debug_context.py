"""
Debug Context Endpoint - Test context extraction and dependency injection.
"""

from fastapi import APIRouter, Request, Depends
from app.core.context import get_current_context, RequestContext, extract_context_from_request
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/debug/context")
async def debug_context(
    request: Request,
    context: RequestContext = Depends(get_current_context)
):
    """Debug endpoint to test context extraction."""
    
    # Extract context directly from request
    direct_context = extract_context_from_request(request)
    
    # Get context from dependency
    dep_context = context
    
    return {
        "headers": dict(request.headers),
        "direct_context": {
            "client_account_id": direct_context.client_account_id,
            "engagement_id": direct_context.engagement_id,
            "user_id": direct_context.user_id,
            "session_id": direct_context.session_id
        },
        "dependency_context": {
            "client_account_id": dep_context.client_account_id,
            "engagement_id": dep_context.engagement_id,
            "user_id": dep_context.user_id,
            "session_id": dep_context.session_id
        },
        "context_match": (
            direct_context.client_account_id == dep_context.client_account_id and
            direct_context.engagement_id == dep_context.engagement_id
        )
    } 