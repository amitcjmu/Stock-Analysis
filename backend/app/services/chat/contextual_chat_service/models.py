"""
Pydantic models for contextual chat service.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FAQ(BaseModel):
    """Frequently asked question model."""

    question: str
    answer: str


class WorkflowInfo(BaseModel):
    """Workflow phase information."""

    phase: str
    step: int
    total_steps: int
    next_step: Optional[str] = None
    previous_step: Optional[str] = None


class PageContext(BaseModel):
    """Structured context about the current page."""

    page_name: str
    route: str
    flow_type: str
    description: str
    features: List[str] = []
    actions: List[str] = []
    help_topics: List[str] = []
    workflow: Optional[WorkflowInfo] = None
    faq: List[FAQ] = []
    related_docs: List[str] = []
    tips: List[str] = []


class FlowContext(BaseModel):
    """Context about the current flow state."""

    flow_id: Optional[str] = None
    flow_type: Optional[str] = None
    current_phase: Optional[str] = None
    completion_percentage: Optional[int] = None
    status: Optional[str] = None
    pending_actions: List[str] = []


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str  # "user" or "assistant"
    content: str


class ContextualChatRequest(BaseModel):
    """Request model for contextual chat."""

    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    page_context: Optional[PageContext] = None
    flow_context: Optional[FlowContext] = None
    breadcrumb: Optional[str] = None


class ContextualChatResponse(BaseModel):
    """Response model for contextual chat."""

    status: str
    response: str
    model_used: str
    timestamp: str
    context_used: Dict[str, Any]
    suggested_actions: List[str] = []
    related_help_topics: List[str] = []
