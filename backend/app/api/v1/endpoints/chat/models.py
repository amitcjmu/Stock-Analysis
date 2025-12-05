"""
Chat models information and testing endpoints.

Issue: #1220 - [Backend] Contextual Chat API Endpoint
Milestone: Contextual AI Chat Assistant
"""

import logging

from fastapi import APIRouter

from app.services.multi_model_service import TaskComplexity, multi_model_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models")
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
                "multimodal": ["image_processing", "visual_analysis"],
            },
            "recommendations": {
                "user_questions": "Use /chat endpoint with Gemma 3 4B",
                "asset_analysis": "Use /analyze-cmdb endpoint with Llama 4 Maverick",
                "quick_help": "Use /chat/ask-about-assets for context-aware responses",
            },
        }

    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve model information",
        }


@router.post("/test-models")
async def test_chat_models():
    """
    Test endpoint to verify both models are working correctly.
    """
    try:
        test_prompt = "Hello! Please introduce yourself and your capabilities."

        # Test Gemma 3 4B for chat
        gemma_result = await multi_model_service.generate_response(
            prompt=test_prompt, task_type="chat", complexity=TaskComplexity.SIMPLE
        )

        # Test Llama 4 Maverick for agentic tasks
        llama_result = await multi_model_service.generate_response(
            prompt="Analyze the benefits of using multiple AI models for different enterprise tasks.",
            task_type="complex_analysis",
            complexity=TaskComplexity.AGENTIC,
        )

        return {
            "status": "success",
            "tests": {
                "gemma_3_4b_chat": {
                    "status": gemma_result["status"],
                    "model_used": gemma_result.get("model_used"),
                    "response_length": len(gemma_result.get("response", "")),
                    "response_preview": gemma_result.get("response", "")[:150] + "...",
                },
                "llama_4_maverick_agentic": {
                    "status": llama_result["status"],
                    "model_used": llama_result.get("model_used"),
                    "response_length": len(llama_result.get("response", "")),
                    "response_preview": llama_result.get("response", "")[:150] + "...",
                },
            },
            "multi_model_service_status": (
                "operational"
                if all(
                    result["status"] == "success"
                    for result in [gemma_result, llama_result]
                )
                else "partial"
            ),
        }

    except Exception as e:
        logger.error(f"Error testing models: {e}")
        return {"status": "error", "error": str(e), "message": "Model testing failed"}
