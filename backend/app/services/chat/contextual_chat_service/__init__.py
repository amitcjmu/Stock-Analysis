"""
Contextual Chat Service - Modularized for maintainability.

This module preserves backward compatibility by exporting all models and the service
instance that were previously in contextual_chat_service.py.

Original file: contextual_chat_service.py (689 lines) -> split into:
- models.py: Pydantic models for requests/responses
- prompts.py: System prompts (BASE, FLOW_TYPE, PAGE_SPECIFIC, GUIDED_WORKFLOW)
- service.py: Main ContextualChatService class
- __init__.py: Backward compatibility exports

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

# Import all models for backward compatibility
from .models import (
    FAQ,
    WorkflowInfo,
    PageContext,
    FlowContext,
    ChatMessage,
    ContextualChatRequest,
    ContextualChatResponse,
)

# Import prompts from modularized subdirectory (backward compatibility)
from .prompts import (
    BASE_SYSTEM_PROMPT,
    FLOW_TYPE_PROMPTS,
    PAGE_SPECIFIC_PROMPTS,
    GUIDED_WORKFLOW_PROMPTS,
)

# Import service and singleton instance
from .service import ContextualChatService, contextual_chat_service

# Export all for backward compatibility
__all__ = [
    # Models
    "FAQ",
    "WorkflowInfo",
    "PageContext",
    "FlowContext",
    "ChatMessage",
    "ContextualChatRequest",
    "ContextualChatResponse",
    # Prompts (optional, for advanced usage)
    "BASE_SYSTEM_PROMPT",
    "FLOW_TYPE_PROMPTS",
    "PAGE_SPECIFIC_PROMPTS",
    "GUIDED_WORKFLOW_PROMPTS",
    # Service
    "ContextualChatService",
    "contextual_chat_service",
]
