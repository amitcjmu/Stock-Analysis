"""
Conversation management endpoints for persistent chat sessions.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.services.multi_model_service import multi_model_service

from .base import ChatMessage, ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory storage for conversations (in production, use database)
conversations_store: Dict[str, List[ChatMessage]] = {}


@router.post("/conversation/{conversation_id}")
async def chat_with_conversation(conversation_id: str, request: ChatRequest):
    """
    Continue a conversation with persistent context.
    """
    try:
        # Get existing conversation or create new one
        if conversation_id not in conversations_store:
            conversations_store[conversation_id] = []

        conversation = conversations_store[conversation_id]

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

            # Keep only last 20 messages to manage memory
            if len(conversation) > 20:
                conversation = conversation[-20:]
                conversations_store[conversation_id] = conversation

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
async def get_conversation(conversation_id: str):
    """
    Get conversation history.
    """
    try:
        if conversation_id not in conversations_store:
            return {
                "status": "not_found",
                "conversation_id": conversation_id,
                "messages": [],
            }

        conversation = conversations_store[conversation_id]
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
async def clear_conversation(conversation_id: str):
    """
    Clear conversation history.
    """
    try:
        if conversation_id in conversations_store:
            del conversations_store[conversation_id]

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
