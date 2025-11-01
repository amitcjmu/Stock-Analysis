"""
LiteLLM Callback for automatic LLM usage tracking.

This callback integrates with LiteLLM (used by CrewAI) to automatically
log all LLM calls to the llm_usage_logs table.

Usage:
    import litellm
    from app.services.litellm_tracking_callback import setup_litellm_tracking

    # Call once at app startup
    setup_litellm_tracking()
"""

import asyncio
import logging
from typing import Any, Optional

try:
    import litellm
    from litellm.integrations.custom_logger import CustomLogger

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    CustomLogger = object  # type: ignore

from app.services.llm_usage_tracker import llm_tracker

logger = logging.getLogger(__name__)


class LLMUsageCallback(CustomLogger):
    """
    Custom LiteLLM callback for usage tracking.

    This callback hooks into LiteLLM's lifecycle to log all LLM calls
    including those made by CrewAI agents.

    Note: start_time and end_time are provided by LiteLLM to the
    success/failure event handlers, so we don't need to track them manually.
    """

    def log_pre_api_call(self, model: str, messages: list, kwargs: dict):
        """Called before LiteLLM makes an API call."""
        logger.debug(f"LiteLLM pre-call: model={model}")

    def log_success_event(
        self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
    ):
        """Called when LiteLLM call succeeds."""
        try:
            # Extract metadata
            model = kwargs.get("model", "unknown")

            # Determine provider from model name
            if "deepinfra" in model.lower():
                provider = "deepinfra"
            elif "openai" in model.lower() or "gpt" in model.lower():
                provider = "openai"
            elif "anthropic" in model.lower() or "claude" in model.lower():
                provider = "anthropic"
            else:
                provider = "unknown"

            # Extract token usage
            usage = getattr(response_obj, "usage", None)
            if usage:
                input_tokens = getattr(usage, "prompt_tokens", 0)
                output_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(
                    usage, "total_tokens", input_tokens + output_tokens
                )
            else:
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0

            # Calculate response time
            # Fix (Issue #801): Handle both datetime and float timestamps
            from datetime import datetime, timedelta

            if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            elif isinstance(end_time - start_time, timedelta):
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            else:
                response_time_ms = int((end_time - start_time) * 1000)

            # Extract feature context from kwargs
            feature_context = kwargs.get("metadata", {}).get(
                "feature_context", "crewai"
            )

            # Log asynchronously
            asyncio.create_task(
                self._log_usage(
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    response_time_ms=response_time_ms,
                    feature_context=feature_context,
                    success=True,
                )
            )

            logger.debug(
                f"LiteLLM success: {provider}/{model}, "
                f"{total_tokens} tokens, {response_time_ms}ms"
            )

        except Exception as e:
            logger.error(f"Failed to log LiteLLM success event: {e}", exc_info=True)

    def log_failure_event(
        self, kwargs: dict, response_obj: Any, start_time: float, end_time: float
    ):
        """Called when LiteLLM call fails."""
        try:
            model = kwargs.get("model", "unknown")
            provider = "deepinfra" if "deepinfra" in model.lower() else "unknown"

            # Get error details
            error_type = type(response_obj).__name__ if response_obj else "UnknownError"
            error_message = str(response_obj) if response_obj else "Unknown error"

            response_time_ms = int((end_time - start_time) * 1000)
            feature_context = kwargs.get("metadata", {}).get(
                "feature_context", "crewai"
            )

            # Log asynchronously
            asyncio.create_task(
                self._log_usage(
                    provider=provider,
                    model=model,
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0,
                    response_time_ms=response_time_ms,
                    feature_context=feature_context,
                    success=False,
                    error_type=error_type,
                    error_message=error_message,
                )
            )

            logger.warning(
                f"LiteLLM failure: {provider}/{model}, "
                f"error={error_type}, {response_time_ms}ms"
            )

        except Exception as e:
            logger.error(f"Failed to log LiteLLM failure event: {e}", exc_info=True)

    async def _log_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        response_time_ms: int,
        feature_context: str,
        success: bool,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Log LLM usage to database."""
        try:
            await llm_tracker.log_llm_usage(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                response_time_ms=response_time_ms,
                success=success,
                error_type=error_type,
                error_message=error_message,
                feature_context=feature_context,
                metadata={"source": "litellm_callback"},
            )
        except Exception as e:
            logger.error(f"Failed to save LiteLLM usage log: {e}", exc_info=True)


# Global callback instance
_callback_instance: Optional[LLMUsageCallback] = None


def setup_litellm_tracking():
    """
    Setup LiteLLM tracking callback.

    Call this once at application startup to enable automatic tracking
    of all LiteLLM calls (including those from CrewAI).
    """
    global _callback_instance

    if not LITELLM_AVAILABLE:
        logger.warning("LiteLLM not available - tracking callback not installed")
        return

    if _callback_instance is not None:
        logger.debug("LiteLLM tracking already setup")
        return

    try:
        _callback_instance = LLMUsageCallback()

        # Use modern LiteLLM callback API (success_callback/failure_callback)
        # instead of legacy callbacks attribute. This matches the proven pattern
        # in llm_config.py:154-158 and preserves existing callbacks.
        # See: https://docs.litellm.ai/docs/observability/custom_callback

        # Register success callback (append to preserve existing callbacks like DeepInfra fixer)
        if not hasattr(litellm, "success_callback") or litellm.success_callback is None:
            litellm.success_callback = []
        litellm.success_callback.append(_callback_instance)

        # Register failure callback (append to preserve existing callbacks)
        if not hasattr(litellm, "failure_callback") or litellm.failure_callback is None:
            litellm.failure_callback = []
        litellm.failure_callback.append(_callback_instance)

        logger.info(
            "✅ LiteLLM tracking callback installed - all LLM calls will be logged"
        )
    except Exception as e:
        logger.error(f"Failed to setup LiteLLM tracking: {e}", exc_info=True)


def is_litellm_tracking_enabled() -> bool:
    """Check if LiteLLM tracking is enabled."""
    return _callback_instance is not None
