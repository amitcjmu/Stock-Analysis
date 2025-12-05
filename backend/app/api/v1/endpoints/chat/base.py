"""
Base schemas and utilities for chat endpoints.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat interactions."""

    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    context: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat interactions."""

    response: str
    model_used: str
    timestamp: str
    conversation_id: Optional[str] = None
