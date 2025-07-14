"""
LLM Configuration Service for AI Force Migration Platform
Configures multiple DeepInfra models according to CrewAI best practices.

Following CrewAI LLM Connection Documentation:
https://docs.crewai.com/learn/llm-connections

Models (USER SPECIFIED - DO NOT CHANGE):
- meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8: CrewAI activities
- thenlper/gte-large: OpenAI embeddings
- google/gemma-3-4b-it: Chat conversations and multi-modal transactions
"""

import litellm
import json
import os
from typing import Any, Dict, Optional, List, Union, Callable
import logging
from litellm import ModelResponse, CustomLLM
from litellm.caching import Cache
import asyncio
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Start of new implementation ---

class DeepInfraLogprobsFixer(litellm.Callback):
    """
    Callback handler to forcibly remove 'logprobs' from requests to DeepInfra.
    This is necessary because DeepInfra returns `logprobs: null` which causes
    Pydantic validation errors in litellm when `logprobs: true` is in the request.
    The standard `drop_params` mechanism in litellm did not prove effective.
    """
    def __init__(self):
        super().__init__()
        # Give it a name for easier identification in logs/debug
        self.name = "DeepInfra Logprobs Fixer"

    def pre_call_hook(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        This hook is executed by litellm before making the API call to the provider.
        It inspects the request parameters and removes 'logprobs' if the target model is from DeepInfra.
        """
        try:
            model_name = kwargs.get("model", "")
            if "deepinfra" in model_name:
                # The `logprobs` parameter can be at the top level of the request kwargs
                if "logprobs" in kwargs:
                    del kwargs["logprobs"]
                    logging.info("DeepInfraLogprobsFixer: Removed 'logprobs' from request for model %s.", model_name)

                # It can also be nested within 'extra_body' for some configurations
                if "extra_body" in kwargs and isinstance(kwargs.get("extra_body"), dict):
                    if "logprobs" in kwargs["extra_body"]:
                        del kwargs["extra_body"]["logprobs"]
                        logging.info("DeepInfraLogprobsFixer: Removed 'logprobs' from 'extra_body' for model %s.", model_name)
        except Exception as e:
            # Log any unexpected errors during the hook's execution to avoid silent failures
            logging.error("DeepInfraLogprobsFixer: Encountered an error in pre_call_hook - %s", e, exc_info=True)

        return kwargs

def register_litellm_callbacks():
    """
    Registers the custom litellm callback handlers.
    Ensures that callbacks are only registered once, even with hot-reloading.
    """
    deepinfra_fixer = DeepInfraLogprobsFixer()
    
    # litellm.callbacks is a list that holds all registered callback handlers.
    if not hasattr(litellm, 'callbacks') or not isinstance(litellm.callbacks, list):
        litellm.callbacks = []

    # Check if a callback of this type is already registered to prevent duplicates.
    if not any(isinstance(cb, DeepInfraLogprobsFixer) for cb in litellm.callbacks):
        litellm.callbacks.append(deepinfra_fixer)
        logging.info("Successfully registered DeepInfraLogprobsFixer callback.")
    
    # Log the current state of registered callbacks for debugging purposes.
    callback_names = [getattr(cb, 'name', cb.__class__.__name__) for cb in litellm.callbacks]
    logging.info(f"Current litellm callbacks: {callback_names}")

# Register the callback immediately when this module is loaded.
register_litellm_callbacks()

# --- End of new implementation ---


# Existing cache setup - remains unchanged
cache_client = Cache(
    type="redis",
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=os.environ.get("REDIS_PORT", 6379),
    db=int(os.environ.get("REDIS_DB", 1))
) if os.getenv("LITELLM_CACHE_ENABLED", "False").lower() == "true" else None

# This parser is now obsolete due to the callback handler, but we can keep it for documentation.
def custom_deepinfra_response_parser(response_str: str) -> Dict[str, Any]:
    """
    DEPRECATED: This parser was designed to handle the `logprobs: null` issue from DeepInfra.
    It has been replaced by the `DeepInfraLogprobsFixer` callback handler, which prevents
    the invalid parameter from being sent in the first place.
    """
    try:
        data = json.loads(response_str)
        if 'choices' in data and isinstance(data['choices'], list):
            for choice in data['choices']:
                if 'logprobs' in choice and choice['logprobs'] is None:
                    # Replace null logprobs with an empty list or simply delete it
                    # Deleting is safer to prevent any downstream validation issues.
                    del choice['logprobs']
        return data
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON from DeepInfra response.")
        # Return a structure that won't break litellm's parsing if possible
        return {"choices": [{"message": {"content": ""}}]}
    except Exception as e:
        logging.error(f"Error in custom_deepinfra_response_parser: {e}")
        return {"choices": [{"message": {"content": ""}}]}

# Environment variable for controlling LLM provider.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepinfra").lower()
logging.info(f"LLM Provider set to: {LLM_PROVIDER}")

# Deprecated parameters dictionary
DEEPINFRA_PARAMS = {
    "temperature": 0.1,
    "max_tokens": 4096,
}

@lru_cache(maxsize=128)
def get_crewai_llm(model: str, temperature: float = 0.1) -> CustomLLM:
    """
    Configures and returns a CrewAI-compatible LLM instance.
    Uses lru_cache for memoization to avoid re-creating instances.
    The `DeepInfraLogprobsFixer` callback handles request modifications globally.
    """
    logging.info(f"Configuring LLM: Model='{model}', Temperature='{temperature}', Provider='{LLM_PROVIDER}'")

    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        logging.error("DEEPINFRA_API_KEY environment variable not set.")
        raise ValueError("DEEPINFRA_API_KEY is required.")

    # The logic for `drop_params` and custom parsers is now handled by the callback.
    # This simplifies the LLM instantiation significantly.
    llm = CustomLLM(
        model=model,
        temperature=temperature,
        api_key=api_key,
        api_base="https://api.deepinfra.com/v1/openai",
        # The `pre_call_hook` in our registered callback now handles removing `logprobs`,
        # making `drop_params` and other measures here redundant.
    )

    logging.info(f"Successfully created LLM instance for model '{model}'.")
    return llm 