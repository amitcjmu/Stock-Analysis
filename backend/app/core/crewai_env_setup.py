"""
CrewAI Environment Setup Utility

Ensures CrewAI environment variables are properly configured in any execution context.
This is critical for Railway and other environments where environment variables
may not propagate correctly to async tasks or subprocess contexts.

Per CLAUDE.md ADR-024: All CrewAI invocations must use DeepInfra configuration.
"""

import logging
import os
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def ensure_crewai_environment() -> None:
    """
    Ensure CrewAI environment variables are properly set from DeepInfra credentials.

    This function MUST be called before any CrewAI agent/crew instantiation to prevent
    "OPENAI_API_KEY is required" errors in production environments like Railway.

    Sets:
    - OPENAI_API_KEY from DEEPINFRA_API_KEY (CrewAI fallback compatibility)
    - OPENAI_API_BASE to DeepInfra endpoint
    - OPENAI_BASE_URL to DeepInfra endpoint

    Raises:
        ValueError: If DEEPINFRA_API_KEY is not set
    """
    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")

    if not deepinfra_key:
        error_msg = (
            "DEEPINFRA_API_KEY environment variable not set. "
            "Cannot configure CrewAI environment."
        )
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)

    # Only set OPENAI_API_KEY if not already set (preserve explicit OpenAI configs)
    existing_openai_key = os.getenv("OPENAI_API_KEY")

    if not existing_openai_key:
        os.environ["OPENAI_API_KEY"] = deepinfra_key
        os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"
        os.environ["OPENAI_BASE_URL"] = "https://api.deepinfra.com/v1/openai"
        logger.debug(
            "✅ Set OPENAI_API_KEY from DEEPINFRA_API_KEY for CrewAI compatibility"
        )
    else:
        logger.debug(
            "ℹ️ OPENAI_API_KEY already set, preserving existing configuration"
        )


def with_crewai_environment(func: Callable) -> Callable:
    """
    Decorator that ensures CrewAI environment is configured before function execution.

    Usage:
        @with_crewai_environment
        async def create_discovery_flow(...):
            # CrewAI environment is guaranteed to be set up
            flow = UnifiedDiscoveryFlow(...)

    Args:
        func: Function to decorate (sync or async)

    Returns:
        Wrapped function with environment setup
    """
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        ensure_crewai_environment()
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        ensure_crewai_environment()
        return func(*args, **kwargs)

    # Return appropriate wrapper based on function type
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def get_crewai_compatible_llm_config() -> dict:
    """
    Get LLM configuration that's compatible with CrewAI's expectations.

    Returns dict with:
    - model: DeepInfra model name in litellm format
    - api_key: DeepInfra API key
    - base_url: DeepInfra API endpoint
    - temperature: Default temperature setting

    This configuration can be passed directly to CrewAI Agent/Crew constructors
    to avoid environment variable fallback.

    Returns:
        Dictionary with LLM configuration

    Raises:
        ValueError: If DEEPINFRA_API_KEY is not set
    """
    ensure_crewai_environment()  # Ensure env is set up first

    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
    deepinfra_model = os.getenv(
        "DEEPINFRA_MODEL",
        "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    )

    return {
        "model": f"deepinfra/{deepinfra_model}",
        "api_key": deepinfra_key,
        "base_url": "https://api.deepinfra.com/v1/openai",
        "temperature": 0.1,
        "max_tokens": 4096,
    }
