"""
Chat Services Package

Provides AI-powered chat functionality with context awareness.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from app.services.chat.contextual_chat_service import (
    ChatMessage,
    ContextualChatRequest,
    ContextualChatResponse,
    ContextualChatService,
    FAQ,
    FlowContext,
    PageContext,
    WorkflowInfo,
    contextual_chat_service,
)
from app.services.chat.help_content_service import (
    HelpContentService,
    help_content_service,
)

__all__ = [
    # Contextual Chat
    "ContextualChatService",
    "contextual_chat_service",
    "ContextualChatRequest",
    "ContextualChatResponse",
    "PageContext",
    "FlowContext",
    "WorkflowInfo",
    "FAQ",
    "ChatMessage",
    # Help Content RAG
    "HelpContentService",
    "help_content_service",
]
