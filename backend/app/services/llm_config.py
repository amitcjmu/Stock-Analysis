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
from litellm import ModelResponse
from litellm.caching import Cache
import asyncio
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Start of new implementation ---

def deepinfra_logprobs_fixer(kwargs: Dict[str, Any], completion_obj=None, user_api_key_dict=None) -> Dict[str, Any]:
    """
    Input callback function to forcibly remove 'logprobs' from requests to DeepInfra.
    This is necessary because DeepInfra returns `logprobs: null` which causes
    Pydantic validation errors in litellm when `logprobs: true` is in the request.
    
    This is a pre-API call callback that modifies the request parameters.
    """
    try:
        model_name = kwargs.get("model", "")
        # Check if this is a DeepInfra model
        if "deepinfra" in model_name.lower() or kwargs.get("custom_llm_provider") == "deepinfra":
            # The `logprobs` parameter can be at the top level of the request kwargs
            if "logprobs" in kwargs:
                del kwargs["logprobs"]
                logging.info("DeepInfraLogprobsFixer: Removed 'logprobs' from request for model %s.", model_name)

            # It can also be nested within 'extra_body' for some configurations
            if "extra_body" in kwargs and isinstance(kwargs.get("extra_body"), dict):
                if "logprobs" in kwargs["extra_body"]:
                    del kwargs["extra_body"]["logprobs"]
                    logging.info("DeepInfraLogprobsFixer: Removed 'logprobs' from 'extra_body' for model %s.", model_name)
                    
            # Also check optional_params which is used by litellm internally
            if "optional_params" in kwargs and isinstance(kwargs.get("optional_params"), dict):
                if "logprobs" in kwargs["optional_params"]:
                    del kwargs["optional_params"]["logprobs"]
                    logging.info("DeepInfraLogprobsFixer: Removed 'logprobs' from 'optional_params' for model %s.", model_name)
    except Exception as e:
        # Log any unexpected errors during the callback's execution to avoid silent failures
        logging.error("DeepInfraLogprobsFixer: Encountered an error - %s", e, exc_info=True)

    return kwargs

def register_litellm_callbacks():
    """
    Registers the custom litellm callback handlers.
    Uses litellm's input_callback mechanism for pre-call modifications.
    """
    # Set the input callback function
    # This will be called before every litellm API call
    litellm.input_callback = [deepinfra_logprobs_fixer]
    logging.info("Successfully registered deepinfra_logprobs_fixer as input callback.")

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

# Existing cache setup

# Environment variable for controlling LLM provider.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepinfra").lower()
logging.info(f"LLM Provider set to: {LLM_PROVIDER}")

# Default parameters for DeepInfra models
DEEPINFRA_PARAMS = {
    "temperature": 0.1,
    "max_tokens": 4096,
}

@lru_cache(maxsize=128)
def get_crewai_llm(model: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", temperature: float = 0.1):
    """
    Configures and returns a CrewAI-compatible LLM instance.
    Uses lru_cache for memoization to avoid re-creating instances.
    The deepinfra_logprobs_fixer input callback handles logprobs removal globally.
    
    Returns:
        CrewAI LLM instance configured for DeepInfra
    """
    # Import CrewAI's LLM class
    try:
        from crewai import LLM
    except ImportError:
        logging.error("CrewAI not installed. Please install crewai package.")
        raise ImportError("CrewAI is required for LLM configuration.")
    
    logging.info(f"Configuring CrewAI LLM: Model='{model}', Temperature='{temperature}', Provider='{LLM_PROVIDER}'")

    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        logging.error("DEEPINFRA_API_KEY environment variable not set.")
        raise ValueError("DEEPINFRA_API_KEY is required.")

    # Create the CrewAI LLM instance with DeepInfra configuration
    # The input callback will handle removing logprobs from all DeepInfra requests
    llm = LLM(
        model=f"deepinfra/{model}",  # CrewAI expects the provider prefix
        temperature=temperature,
        api_key=api_key,
        api_base="https://api.deepinfra.com/v1/openai",
        max_tokens=DEEPINFRA_PARAMS["max_tokens"]
    )

    logging.info(f"Successfully created CrewAI LLM instance for model '{model}'.")
    return llm 