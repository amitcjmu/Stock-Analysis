"""
Contextual chat endpoints with page and flow awareness.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import logging

from fastapi import APIRouter, HTTPException

from app.services.chat.contextual_chat_service import (
    ContextualChatRequest,
    contextual_chat_service,
    PageContext,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants for input validation
MAX_MESSAGE_LENGTH = 10000


def _sanitize_log_message(message: str, max_len: int = 30) -> str:
    """Sanitize message for logging - truncate and redact potential PII."""
    if not message:
        return "[empty]"
    truncated = message[:max_len].replace("\n", " ")
    return f"{truncated}..." if len(message) > max_len else truncated


@router.post("/contextual")
async def contextual_chat(request: ContextualChatRequest):
    """
    Contextual chat with page and flow awareness.

    This endpoint provides AI chat responses that are aware of:
    - Current page context (features, actions, help topics)
    - Active flow state (flow ID, phase, progress)
    - Page-specific guidance and tips

    Issue: #1220 - [Backend] Contextual Chat API Endpoint
    Milestone: Contextual AI Chat Assistant
    """
    try:
        # Input validation
        if len(request.message) > MAX_MESSAGE_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH}",
            )

        # Secure logging - don't log full user messages
        logger.info(
            f"Contextual chat request - Message: {_sanitize_log_message(request.message)} "
            f"Page: {request.page_context.page_name if request.page_context else 'Unknown'}"
        )

        # Use the contextual chat service
        result = await contextual_chat_service.chat_with_context(request)

        return {
            "status": result.status,
            "response": result.response,
            "model_used": result.model_used,
            "timestamp": result.timestamp,
            "context_used": result.context_used,
            "suggested_actions": result.suggested_actions,
            "related_help_topics": result.related_help_topics,
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Error in contextual chat endpoint: {e}")
        # Don't expose internal error details to users
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your contextual chat request",
        )


@router.get("/page-greeting")
async def get_page_greeting(route: str):
    """
    Get a contextual greeting for the current page.

    This returns a page-specific welcome message that helps users
    understand what they can do on the current page.
    """
    # Create a minimal page context from route
    # In production, this could fetch from a database or cache
    page_context = PageContext(
        page_name=route.split("/")[-1].replace("-", " ").title() or "Home",
        route=route,
        flow_type=_detect_flow_type(route),
        description="",
        features=[],
        actions=[],
        help_topics=[],
        faq=[],
    )

    greeting = contextual_chat_service.get_page_greeting(page_context)

    return {
        "greeting": greeting,
        "page_name": page_context.page_name,
        "route": route,
    }


def _detect_flow_type(route: str) -> str:
    """Detect flow type from route path."""
    if route.startswith("/discovery"):
        return "discovery"
    if route.startswith("/collection"):
        return "collection"
    if route.startswith("/assessment"):
        return "assessment"
    if route.startswith("/plan"):
        return "planning"
    if route.startswith("/execute"):
        return "execute"
    if route.startswith("/modernize"):
        return "modernize"
    if route.startswith("/decommission") or route.startswith("/decom"):
        return "decommission"
    if route.startswith("/finops"):
        return "finops"
    if route.startswith("/observability"):
        return "observability"
    if route.startswith("/admin"):
        return "admin"
    return "general"
