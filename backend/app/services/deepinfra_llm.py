"""
Custom DeepInfra LLM integration for CrewAI.
Implements the DeepInfra OpenAI-compatible API format for Llama 4 Maverick model.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import requests

from app.core.security.cache_encryption import secure_setattr

try:
    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    from langchain_core.language_models.llms import LLM
    from pydantic import Field

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning(
        "LangChain not available. DeepInfra LLM will use basic implementation."
    )

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeepInfraLlama4LLM(LLM if LANGCHAIN_AVAILABLE else object):
    """Custom DeepInfra LLM for Llama 4 Maverick model with proper CrewAI serialization support."""

    api_token: str = Field(default="")
    model_id: str = Field(default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8")
    base_url: str = Field(
        default="https://api.deepinfra.com/v1/openai/chat/completions"
    )
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    top_p: float = Field(default=0.9)
    top_k: int = Field(default=0)
    repetition_penalty: float = Field(default=1.0)
    reasoning_effort: str = Field(default="none")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_token = kwargs.get("api_token", settings.DEEPINFRA_API_KEY)
        self.model_id = kwargs.get("model_id", settings.DEEPINFRA_MODEL)
        self.base_url = kwargs.get(
            "base_url", "https://api.deepinfra.com/v1/openai/chat/completions"
        )
        self.temperature = kwargs.get("temperature", settings.CREWAI_TEMPERATURE)
        self.max_tokens = kwargs.get("max_tokens", settings.CREWAI_MAX_TOKENS)
        self.reasoning_effort = kwargs.get(
            "reasoning_effort", "none"
        )  # Disable reasoning/thinking

    @property
    def _llm_type(self) -> str:
        """Return identifier of llm type."""
        return "deepinfra_llama4"

    @property
    def model(self) -> str:
        """Return the model identifier for CrewAI compatibility."""
        return self.model_id

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the DeepInfra OpenAI-compatible API."""
        try:
            # Prepare the request using OpenAI chat completions format
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}",
            }

            # Create messages in OpenAI format
            messages = [{"role": "user", "content": prompt}]

            # Default stop tokens for Llama 4 Maverick
            default_stop = ["<|eot_id|>", "<|end_of_text|>", "<|eom_id|>"]

            if stop:
                stop_tokens = list(set(default_stop + stop))
            else:
                stop_tokens = default_stop

            payload = {
                "model": self.model_id,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "repetition_penalty": self.repetition_penalty,
                "stop": stop_tokens,
                "reasoning_effort": "none",  # CRITICAL: Disable reasoning/thinking mode
                "stream": False,
                "response_format": {"type": "text"},
            }

            logger.info("Making DeepInfra API call with reasoning_effort=none")

            # Make the API call with reasonable timeout
            response = requests.post(
                self.base_url, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()

            # Parse the response
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]

                # Log usage statistics
                if "usage" in result:
                    usage = result["usage"]
                    logger.info(
                        f"DeepInfra API call completed: "
                        f"prompt_tokens={usage.get('prompt_tokens', 0)}, "
                        f"completion_tokens={usage.get('completion_tokens', 0)}, "
                        f"total_tokens={usage.get('total_tokens', 0)}"
                    )

                return generated_text
            else:
                logger.error(f"Unexpected response format: {result}")
                return "Error: Invalid response format from DeepInfra API"

        except requests.exceptions.RequestException as e:
            logger.error(f"DeepInfra API request failed: {e}")
            return f"Error: API request failed - {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepInfra response: {e}")
            return "Error: Invalid JSON response from DeepInfra API"
        except Exception as e:
            logger.error(f"Unexpected error in DeepInfra LLM call: {e}")
            return f"Error: {str(e)}"

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Async call to DeepInfra API."""
        # For now, use sync call - can be improved with aiohttp later
        return self._call(prompt, stop, run_manager, **kwargs)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (placeholder for future implementation)."""
        return {
            "model": self.model_id,
            "api_calls": 0,  # Could be tracked in future
            "total_tokens": 0,  # Could be tracked in future
            "total_cost": 0.0,  # Could be tracked in future
        }

    def dict(self, **kwargs) -> Dict[str, Any]:
        """Custom serialization for CrewAI compatibility."""
        return {
            "model": self.model_id,
            "api_token": self.api_token,
            "model_id": self.model_id,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "reasoning_effort": self.reasoning_effort,
            "_llm_type": self._llm_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeepInfraLlama4LLM":
        """Custom deserialization for CrewAI compatibility."""
        return cls(**data)

    def __getstate__(self) -> Dict[str, Any]:
        """Custom pickle serialization."""
        return self.dict()

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Custom pickle deserialization."""
        for key, value in state.items():
            secure_setattr(self, key, value)


def create_deepinfra_llm(**kwargs) -> DeepInfraLlama4LLM:
    """Factory function to create DeepInfra LLM instance."""
    # Extract known parameters to avoid conflicts
    config = {
        "api_token": kwargs.get("api_token", settings.DEEPINFRA_API_KEY),
        "model_id": kwargs.get("model_id", settings.DEEPINFRA_MODEL),
        "base_url": kwargs.get(
            "base_url", "https://api.deepinfra.com/v1/openai/chat/completions"
        ),
        "temperature": kwargs.get("temperature", settings.CREWAI_TEMPERATURE),
        "max_tokens": kwargs.get("max_tokens", settings.CREWAI_MAX_TOKENS),
        "reasoning_effort": kwargs.get("reasoning_effort", "none"),
    }

    # Add any additional kwargs that aren't already specified
    for key, value in kwargs.items():
        if key not in config:
            config[key] = value

    return DeepInfraLlama4LLM(**config)


def create_crewai_compatible_llm(**kwargs) -> DeepInfraLlama4LLM:
    """Create a CrewAI-compatible LLM with optimized settings for agent work."""
    # Optimized settings for CrewAI agents
    optimized_config = {
        "temperature": 0.1,  # Lower temperature for more consistent agent responses
        "max_tokens": 500,  # Smaller tokens for faster agent responses
        "reasoning_effort": "none",  # CRITICAL: Explicitly disable reasoning/thinking mode
        **kwargs,  # Allow overrides
    }

    return create_deepinfra_llm(**optimized_config)
