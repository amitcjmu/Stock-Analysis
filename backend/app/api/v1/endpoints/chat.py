"""
Chat API endpoints for user interactions using Gemma 3 4B model.
Provides conversational interface for getting help and information.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.multi_model_service import TaskComplexity, multi_model_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for chat requests/responses
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model_used: str
    timestamp: str
    conversation_id: Optional[str] = None

# Simple in-memory storage for conversations (in production, use database)
conversations_store: Dict[str, List[ChatMessage]] = {}

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Chat with AI assistant using Gemma 3 4B model.
    Provides conversational interface for user questions and help.
    """
    try:
        logger.info(f"Received chat message: {request.message[:100]}...")
        
        # Convert conversation history to dict format
        history = []
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.conversation_history
            ]
        
        # Generate response using multi-model service
        result = await multi_model_service.chat_with_context(
            message=request.message,
            conversation_history=history,
            context=request.context
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "response": result["response"],
                "model_used": result["model_used"],
                "timestamp": result["timestamp"],
                "tokens_used": result.get("tokens_used", 0),
                "conversation_context": len(history) if history else 0
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "message": "Chat response generation failed"
            }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/chat/conversation/{conversation_id}")
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
            timestamp=datetime.utcnow().isoformat()
        )
        conversation.append(user_message)
        
        # Convert to dict format for the service
        history = [
            {"role": msg.role, "content": msg.content} 
            for msg in conversation
        ]
        
        # Generate response
        result = await multi_model_service.chat_with_context(
            message=request.message,
            conversation_history=history[:-1],  # Exclude the current message
            context=request.context
        )
        
        if result["status"] == "success":
            # Add assistant response to conversation
            assistant_message = ChatMessage(
                role="assistant",
                content=result["response"],
                timestamp=result["timestamp"]
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
                "tokens_used": result.get("tokens_used", 0)
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "conversation_id": conversation_id
            }
        
    except Exception as e:
        logger.error(f"Error in conversation chat: {e}")
        raise HTTPException(status_code=500, detail=f"Conversation chat failed: {str(e)}")

@router.get("/chat/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history.
    """
    try:
        if conversation_id not in conversations_store:
            return {
                "status": "not_found",
                "conversation_id": conversation_id,
                "messages": []
            }
        
        conversation = conversations_store[conversation_id]
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": conversation,
            "message_count": len(conversation),
            "last_updated": conversation[-1].timestamp if conversation else None
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")

@router.delete("/chat/conversation/{conversation_id}")
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
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")

@router.post("/chat/ask-about-assets")
async def ask_about_assets(request: ChatRequest):
    """
    Specialized chat endpoint for asking questions about discovered assets.
    Provides context from the current asset inventory.
    """
    try:
        # Get current asset context
        from app.api.v1.discovery.persistence import get_processed_assets
        
        processed_assets_store = get_processed_assets()
        asset_context = ""
        if processed_assets_store:
            total_assets = len(processed_assets_store)
            asset_types = {}
            environments = set()
            
            for asset in processed_assets_store:
                asset_type = asset.get("asset_type", "Unknown")
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
                
                env = asset.get("environment", "Unknown")
                if env != "Unknown":
                    environments.add(env)
            
            asset_context = f"""Current Asset Inventory Context:
- Total Assets: {total_assets}
- Asset Types: {dict(asset_types)}
- Environments: {list(environments)}
- Data Source: Live CMDB Import Data"""
        else:
            asset_context = "No assets have been imported yet. Using demo data for examples."
        
        # Generate response with asset context
        result = await multi_model_service.chat_with_context(
            message=request.message,
            conversation_history=[
                {"role": msg.role, "content": msg.content} 
                for msg in (request.conversation_history or [])
            ],
            context=asset_context
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "response": result["response"],
                "model_used": result["model_used"],
                "timestamp": result["timestamp"],
                "asset_context_provided": bool(processed_assets_store),
                "total_assets_referenced": len(processed_assets_store) if processed_assets_store else 0
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "message": "Asset-related chat failed"
            }
        
    except Exception as e:
        logger.error(f"Error in asset chat: {e}")
        raise HTTPException(status_code=500, detail=f"Asset chat failed: {str(e)}")

@router.get("/chat/models")
async def get_chat_models():
    """
    Get information about available chat models and their capabilities.
    """
    try:
        model_info = multi_model_service.get_model_info()
        
        return {
            "status": "success",
            "models": model_info,
            "chat_model": "gemma3_4b",
            "agentic_model": "llama4_maverick",
            "capabilities": {
                "chat": ["conversational", "helpful", "concise"],
                "agentic": ["complex_analysis", "field_mapping", "reasoning"],
                "multimodal": ["image_processing", "visual_analysis"]
            },
            "recommendations": {
                "user_questions": "Use /chat endpoint with Gemma 3 4B",
                "asset_analysis": "Use /analyze-cmdb endpoint with Llama 4 Maverick",
                "quick_help": "Use /chat/ask-about-assets for context-aware responses"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve model information"
        }

@router.post("/chat/test-models")
async def test_chat_models():
    """
    Test endpoint to verify both models are working correctly.
    """
    try:
        test_prompt = "Hello! Please introduce yourself and your capabilities."
        
        # Test Gemma 3 4B for chat
        gemma_result = await multi_model_service.generate_response(
            prompt=test_prompt,
            task_type="chat",
            complexity=TaskComplexity.SIMPLE
        )
        
        # Test Llama 4 Maverick for agentic tasks
        llama_result = await multi_model_service.generate_response(
            prompt="Analyze the benefits of using multiple AI models for different enterprise tasks.",
            task_type="complex_analysis",
            complexity=TaskComplexity.AGENTIC
        )
        
        return {
            "status": "success",
            "tests": {
                "gemma_3_4b_chat": {
                    "status": gemma_result["status"],
                    "model_used": gemma_result.get("model_used"),
                    "response_length": len(gemma_result.get("response", "")),
                    "response_preview": gemma_result.get("response", "")[:150] + "..."
                },
                "llama_4_maverick_agentic": {
                    "status": llama_result["status"],
                    "model_used": llama_result.get("model_used"),
                    "response_length": len(llama_result.get("response", "")),
                    "response_preview": llama_result.get("response", "")[:150] + "..."
                }
            },
            "multi_model_service_status": "operational" if all(
                result["status"] == "success" 
                for result in [gemma_result, llama_result]
            ) else "partial"
        }
        
    except Exception as e:
        logger.error(f"Error testing models: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Model testing failed"
        } 