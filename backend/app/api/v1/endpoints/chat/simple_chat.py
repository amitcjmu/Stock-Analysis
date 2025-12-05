"""
Simple chat endpoints for basic AI interactions.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import logging

from fastapi import APIRouter, HTTPException

from app.services.multi_model_service import multi_model_service

from .base import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/")
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
            context=request.context,
        )

        if result["status"] == "success":
            return {
                "status": "success",
                "response": result["response"],
                "model_used": result["model_used"],
                "timestamp": result["timestamp"],
                "tokens_used": result.get("tokens_used", 0),
                "conversation_context": len(history) if history else 0,
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "message": "Chat response generation failed",
            }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/ask-about-assets")
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
            asset_context = (
                "No assets have been imported yet. Using demo data for examples."
            )

        # Generate response with asset context
        result = await multi_model_service.chat_with_context(
            message=request.message,
            conversation_history=[
                {"role": msg.role, "content": msg.content}
                for msg in (request.conversation_history or [])
            ],
            context=asset_context,
        )

        if result["status"] == "success":
            return {
                "status": "success",
                "response": result["response"],
                "model_used": result["model_used"],
                "timestamp": result["timestamp"],
                "asset_context_provided": bool(processed_assets_store),
                "total_assets_referenced": (
                    len(processed_assets_store) if processed_assets_store else 0
                ),
            }
        else:
            return {
                "status": "error",
                "error": result.get("error", "Unknown error"),
                "message": "Asset-related chat failed",
            }

    except Exception as e:
        logger.error(f"Error in asset chat: {e}")
        raise HTTPException(status_code=500, detail=f"Asset chat failed: {str(e)}")
