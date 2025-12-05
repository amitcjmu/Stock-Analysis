"""
Chat API endpoints - Modularized for maintainability.

This module preserves backward compatibility by aggregating all chat routers
into a single router that can be imported as before.

Original file: chat.py (830 lines) -> split into:
- base.py: Schemas and base classes
- simple_chat.py: Basic chat endpoints
- contextual_chat.py: Contextual chat with page awareness
- conversation.py: Conversation management
- flow_context.py: Flow state context for chat
- models.py: Model information endpoints
- feedback.py: Feedback submission and retrieval

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from fastapi import APIRouter

# Import all sub-routers
from .simple_chat import router as simple_chat_router
from .contextual_chat import router as contextual_chat_router
from .conversation import router as conversation_router
from .flow_context import router as flow_context_router
from .models import router as models_router
from .feedback import router as feedback_router

# Import base schemas for backward compatibility
from .base import ChatMessage, ChatRequest, ChatResponse

# Create main router and include all sub-routers
router = APIRouter()

# Include all endpoints from modularized files
# Tags will be added at the router_imports.py level, not here
router.include_router(simple_chat_router)
router.include_router(contextual_chat_router)
router.include_router(conversation_router)
router.include_router(flow_context_router)
router.include_router(models_router)
router.include_router(feedback_router)

# Export router and schemas for backward compatibility
__all__ = [
    "router",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
]
