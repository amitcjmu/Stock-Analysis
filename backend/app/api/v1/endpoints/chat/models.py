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
    Get information about the LLM gateway (Anthropic Claude only).
    """
    try:
        model_info = multi_model_service.get_model_info()

        return {
            "status": "success",
            "models": model_info,
            "llm_provider": "anthropic",
            "default_model": model_info["model_configs"]
            .get("claude_opus_4_6", {})
            .get("model_name", "claude-opus-4-6"),
            "capabilities": {
                "chat": ["conversational", "helpful", "reasoning"],
                "agentic": ["complex_analysis", "field_mapping", "reasoning"],
            },
            "recommendations": {
                "user_questions": "Use /chat — routed to Anthropic Claude",
                "asset_analysis": "Use task-specific endpoints — Anthropic Claude",
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
    Verify Anthropic Claude is reachable via multi_model_service.
    """
    try:
        test_prompt = "Reply with one short sentence confirming you are ready to help."

        claude_result = await multi_model_service.generate_response(
            prompt=test_prompt,
            task_type="chat",
            complexity=TaskComplexity.SIMPLE,
        )

        return {
            "status": "success",
            "tests": {
                "anthropic_claude": {
                    "status": claude_result["status"],
                    "model_used": claude_result.get("model_used"),
                    "response_length": len(claude_result.get("response", "")),
                    "response_preview": (claude_result.get("response", "") or "")[:150]
                    + (
                        "..."
                        if len(claude_result.get("response", "") or "") > 150
                        else ""
                    ),
                },
            },
            "multi_model_service_status": (
                "operational" if claude_result["status"] == "success" else "partial"
            ),
        }

    except Exception as e:
        logger.error(f"Error testing models: {e}")
        return {"status": "error", "error": str(e), "message": "Model testing failed"}
