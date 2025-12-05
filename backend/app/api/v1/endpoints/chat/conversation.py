"""
Conversation management endpoints for persistent chat sessions.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from app.core.context import RequestContext, get_request_context
from app.services.multi_model_service import multi_model_service

from .base import ChatMessage, ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# Tenant-scoped in-memory storage for conversations
# Key format: "{client_account_id}:{engagement_id}:{conversation_id}"
# This ensures conversations are isolated per tenant
conversations_store: Dict[str, List[ChatMessage]] = {}

# Maximum conversations per tenant (DoS protection)
MAX_CONVERSATIONS_PER_TENANT = 100
MAX_MESSAGES_PER_CONVERSATION = 50


def _get_tenant_key(context: RequestContext, conversation_id: str) -> str:
    """Generate tenant-scoped key for conversation storage."""
    client_id = context.client_account_id if context else 0
    engagement_id = context.engagement_id if context else 0
    return f"{client_id}:{engagement_id}:{conversation_id}"


def _count_tenant_conversations(context: RequestContext) -> int:
    """Count conversations for a tenant (DoS protection)."""
    prefix = f"{context.client_account_id}:{context.engagement_id}:"
    return sum(1 for key in conversations_store if key.startswith(prefix))


@router.post("/conversation/{conversation_id}")
async def chat_with_conversation(
    conversation_id: str,
    request: ChatRequest,
    context: RequestContext = Depends(get_request_context),
):
    """
    Continue a conversation with persistent context.
    Scoped to tenant (client_account_id + engagement_id).
    """
    try:
        # Generate tenant-scoped key
        tenant_key = _get_tenant_key(context, conversation_id)

        # Get existing conversation or create new one
        if tenant_key not in conversations_store:
            # Check tenant conversation limit (DoS protection)
            if (
                context
                and _count_tenant_conversations(context) >= MAX_CONVERSATIONS_PER_TENANT
            ):
                raise HTTPException(
                    status_code=429,
                    detail=f"Maximum conversations ({MAX_CONVERSATIONS_PER_TENANT}) reached",
                )
            conversations_store[tenant_key] = []

        conversation = conversations_store[tenant_key]

        # Add user message to conversation
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation.append(user_message)

        # Convert to dict format for the service
        history = [{"role": msg.role, "content": msg.content} for msg in conversation]

        # Generate response
        result = await multi_model_service.chat_with_context(
            message=request.message,
            conversation_history=history[:-1],  # Exclude the current message
            context=request.context,
        )

        if result["status"] == "success":
            # Add assistant response to conversation
            assistant_message = ChatMessage(
                role="assistant",
                content=result["response"],
                timestamp=result["timestamp"],
            )
            conversation.append(assistant_message)

            # Keep only last MAX_MESSAGES_PER_CONVERSATION to manage memory
            if len(conversation) > MAX_MESSAGES_PER_CONVERSATION:
                conversation = conversation[-MAX_MESSAGES_PER_CONVERSATION:]
                conversations_store[tenant_key] = conversation

            return {
                "status": "success",
                "response": result["response"],
                "model_used": result["model_used"],
                "timestamp": result["timestamp"],
                "conversation_id": conversation_id,
                "conversation_length": len(conversation),
                "tokens_used": result.get("tokens_used", 0),
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "conversation_id": conversation_id,
            }

    except Exception as e:
        logger.error(f"Error in conversation chat: {e}")
        raise HTTPException(
            status_code=500, detail=f"Conversation chat failed: {str(e)}"
        )


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    context: RequestContext = Depends(get_request_context),
):
    """
    Get conversation history (tenant-scoped).
    """
    try:
        tenant_key = _get_tenant_key(context, conversation_id)

        if tenant_key not in conversations_store:
            return {
                "status": "not_found",
                "conversation_id": conversation_id,
                "messages": [],
            }

        conversation = conversations_store[tenant_key]
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": conversation,
            "message_count": len(conversation),
            "last_updated": conversation[-1].timestamp if conversation else None,
        }

    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    context: RequestContext = Depends(get_request_context),
):
    """
    Clear conversation history (tenant-scoped).
    """
    try:
        tenant_key = _get_tenant_key(context, conversation_id)

        if tenant_key in conversations_store:
            del conversations_store[tenant_key]

        return {
            "status": "success",
            "message": f"Conversation {conversation_id} cleared",
            "conversation_id": conversation_id,
        }

    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear conversation: {str(e)}"
        )
