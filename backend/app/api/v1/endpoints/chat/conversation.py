"""
Conversation management endpoints for persistent chat sessions.

Uses Redis for persistent storage with in-memory fallback.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.context import RequestContext, get_request_context
from app.core.redis_config import get_redis_manager
from app.services.multi_model_service import multi_model_service

from .base import ChatMessage, ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
MAX_CONVERSATIONS_PER_TENANT = 100
MAX_MESSAGES_PER_CONVERSATION = 50
CONVERSATION_TTL_SECONDS = 86400 * 7  # 7 days
REDIS_KEY_PREFIX = "chat:conversation:"

# Fallback in-memory storage (used when Redis unavailable)
_fallback_store: Dict[str, List[ChatMessage]] = {}


def _get_tenant_key(context: RequestContext, conversation_id: str) -> str:
    """Generate tenant-scoped key for conversation storage."""
    client_id = context.client_account_id if context else 0
    engagement_id = context.engagement_id if context else 0
    return f"{REDIS_KEY_PREFIX}{client_id}:{engagement_id}:{conversation_id}"


def _get_tenant_prefix(context: RequestContext) -> str:
    """Get tenant prefix for scanning conversations."""
    client_id = context.client_account_id if context else 0
    engagement_id = context.engagement_id if context else 0
    return f"{REDIS_KEY_PREFIX}{client_id}:{engagement_id}:"


async def _get_conversation(key: str) -> Optional[List[ChatMessage]]:
    """Get conversation from Redis or fallback store."""
    redis = get_redis_manager()

    if redis.is_available():
        try:
            if redis.client_type == "upstash":
                data = redis.client.get(key)
            else:
                data = await redis.client.get(key)

            if data:
                messages_data = json.loads(data)
                return [ChatMessage(**msg) for msg in messages_data]
            return None
        except Exception as e:
            logger.warning(f"Redis get failed, using fallback: {e}")

    # Fallback to in-memory
    return _fallback_store.get(key)


async def _set_conversation(key: str, messages: List[ChatMessage]) -> None:
    """Store conversation in Redis or fallback store."""
    redis = get_redis_manager()

    if redis.is_available():
        try:
            messages_data = [msg.model_dump() for msg in messages]
            data = json.dumps(messages_data)

            if redis.client_type == "upstash":
                redis.client.set(key, data, ex=CONVERSATION_TTL_SECONDS)
            else:
                await redis.client.set(key, data, ex=CONVERSATION_TTL_SECONDS)
            return
        except Exception as e:
            logger.warning(f"Redis set failed, using fallback: {e}")

    # Fallback to in-memory
    _fallback_store[key] = messages


async def _delete_conversation(key: str) -> None:
    """Delete conversation from Redis or fallback store."""
    redis = get_redis_manager()

    if redis.is_available():
        try:
            if redis.client_type == "upstash":
                redis.client.delete(key)
            else:
                await redis.client.delete(key)
            return
        except Exception as e:
            logger.warning(f"Redis delete failed, using fallback: {e}")

    # Fallback to in-memory
    _fallback_store.pop(key, None)


async def _count_tenant_conversations(context: RequestContext) -> int:
    """Count conversations for a tenant (DoS protection)."""
    prefix = _get_tenant_prefix(context)
    redis = get_redis_manager()

    if redis.is_available():
        try:
            count = 0
            cursor = 0
            while True:
                if redis.client_type == "upstash":
                    result = redis.client.scan(cursor, match=f"{prefix}*", count=100)
                else:
                    result = await redis.client.scan(
                        cursor, match=f"{prefix}*", count=100
                    )

                cursor = result[0]
                count += len(result[1])
                if cursor == 0:
                    break
            return count
        except Exception as e:
            logger.warning(f"Redis scan failed, using fallback: {e}")

    # Fallback to in-memory
    return sum(1 for key in _fallback_store if key.startswith(prefix))


@router.post("/conversation/{conversation_id}")
async def chat_with_conversation(
    conversation_id: str,
    request: ChatRequest,
    context: RequestContext = Depends(get_request_context),
):
    """
    Continue a conversation with persistent context.
    Scoped to tenant (client_account_id + engagement_id).
    Uses Redis for persistent storage with in-memory fallback.
    """
    try:
        # Generate tenant-scoped key
        tenant_key = _get_tenant_key(context, conversation_id)

        # Get existing conversation or create new one
        conversation = await _get_conversation(tenant_key)
        if conversation is None:
            # Check tenant conversation limit (DoS protection)
            if context:
                count = await _count_tenant_conversations(context)
                if count >= MAX_CONVERSATIONS_PER_TENANT:
                    raise HTTPException(
                        status_code=429,
                        detail=f"Maximum conversations ({MAX_CONVERSATIONS_PER_TENANT}) reached",
                    )
            conversation = []

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

            # Persist conversation to Redis
            await _set_conversation(tenant_key, conversation)

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
            # Still persist the user message even on AI error
            await _set_conversation(tenant_key, conversation)
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "conversation_id": conversation_id,
            }

    except HTTPException:
        raise  # Re-raise HTTPExceptions as-is
    except Exception as e:
        logger.error(f"Error in conversation chat: {e}")
        # Don't expose internal error details to users
        raise HTTPException(
            status_code=500, detail="An error occurred processing your chat request"
        )


@router.get("/conversation/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    context: RequestContext = Depends(get_request_context),
):
    """
    Get conversation history (tenant-scoped).
    Uses Redis for persistent storage with in-memory fallback.
    """
    try:
        tenant_key = _get_tenant_key(context, conversation_id)
        conversation = await _get_conversation(tenant_key)

        if conversation is None:
            return {
                "status": "not_found",
                "conversation_id": conversation_id,
                "messages": [],
            }

        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": [msg.model_dump() for msg in conversation],
            "message_count": len(conversation),
            "last_updated": conversation[-1].timestamp if conversation else None,
        }

    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        # Don't expose internal error details to users
        raise HTTPException(
            status_code=500, detail="An error occurred retrieving the conversation"
        )


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    context: RequestContext = Depends(get_request_context),
):
    """
    Clear conversation history (tenant-scoped).
    Uses Redis for persistent storage with in-memory fallback.
    """
    try:
        tenant_key = _get_tenant_key(context, conversation_id)
        await _delete_conversation(tenant_key)

        return {
            "status": "success",
            "message": f"Conversation {conversation_id} cleared",
            "conversation_id": conversation_id,
        }

    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        # Don't expose internal error details to users
        raise HTTPException(
            status_code=500, detail="An error occurred clearing the conversation"
        )
