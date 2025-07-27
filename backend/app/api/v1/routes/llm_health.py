"""
LLM Health Check API endpoints
Provides health status and testing for all configured LLM models.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.llm_config import llm_config, test_all_llm_connections

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def get_llm_health():
    """
    Get health status of all configured LLM models.

    Returns:
        Dict containing health status for each LLM type
    """
    try:
        # Test all LLM connections
        connection_results = test_all_llm_connections()

        # Get configuration details
        config_details = {
            "crewai_model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "embedding_model": "thenlper/gte-large",
            "chat_model": "google/gemma-3-4b-it",
            "api_provider": "DeepInfra",
            "base_url": llm_config.deepinfra_base_url,
            "api_key_configured": bool(llm_config.deepinfra_api_key),
        }

        # Calculate overall health
        all_healthy = all(connection_results.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "llm_connections": connection_results,
            "configuration": config_details,
            "total_llms": len(connection_results),
            "healthy_llms": sum(connection_results.values()),
            "message": (
                "All LLMs configured and ready"
                if all_healthy
                else "Some LLMs may have issues"
            ),
        }

    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"LLM health check failed: {str(e)}"
        )


@router.get("/test-connections", response_model=Dict[str, Any])
async def test_llm_connections():
    """
    Test actual connections to all LLM models.

    Returns:
        Dict containing detailed test results for each LLM
    """
    try:
        # Test connections
        connection_results = test_all_llm_connections()

        # Get detailed LLM instances for testing
        llm_instances = llm_config.get_all_llms()

        test_results = {}
        for llm_type, llm_instance in llm_instances.items():
            test_results[llm_type] = {
                "connection_test": connection_results.get(llm_type, False),
                "model_info": {
                    "model": getattr(llm_instance, "model", "unknown"),
                    "base_url": getattr(llm_instance, "base_url", "unknown"),
                    "api_key_configured": bool(getattr(llm_instance, "api_key", None)),
                },
                "status": (
                    "ready" if connection_results.get(llm_type, False) else "error"
                ),
            }

        overall_status = (
            "all_ready" if all(connection_results.values()) else "some_errors"
        )

        return {
            "overall_status": overall_status,
            "test_results": test_results,
            "timestamp": "2025-01-30T00:00:00Z",
            "provider": "DeepInfra",
        }

    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"LLM connection test failed: {str(e)}"
        )


@router.get("/configuration", response_model=Dict[str, Any])
async def get_llm_configuration():
    """
    Get current LLM configuration details.

    Returns:
        Dict containing configuration information
    """
    try:
        from app.core.config import settings

        config_info = {
            "models": {
                "crewai": getattr(
                    settings,
                    "CREWAI_LLM_MODEL",
                    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                ),
                "embedding": getattr(
                    settings, "EMBEDDING_LLM_MODEL", "thenlper/gte-large"
                ),
                "chat": getattr(settings, "CHAT_LLM_MODEL", "google/gemma-3-4b-it"),
            },
            "provider": "DeepInfra",
            "base_url": llm_config.deepinfra_base_url,
            "api_key_configured": bool(llm_config.deepinfra_api_key),
            "environment_variables": {
                "OPENAI_API_KEY": (
                    "configured" if llm_config.deepinfra_api_key else "missing"
                ),
                "OPENAI_API_BASE": llm_config.deepinfra_base_url,
                "DEEPINFRA_API_KEY": (
                    "configured" if llm_config.deepinfra_api_key else "missing"
                ),
            },
            "crewai_settings": {
                "temperature": getattr(settings, "CREWAI_TEMPERATURE", 0.7),
                "max_tokens": getattr(settings, "CREWAI_MAX_TOKENS", 2048),
                "enabled": getattr(settings, "CREWAI_ENABLED", True),
            },
        }

        return {
            "status": "configured",
            "configuration": config_info,
            "documentation": "Following CrewAI LLM connections best practices",
            "models_configured": len(config_info["models"]),
        }

    except Exception as e:
        logger.error(f"Failed to get LLM configuration: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get LLM configuration: {str(e)}"
        )
