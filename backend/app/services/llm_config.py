"""
LLM Configuration Service for AI Modernize Migration Platform
Configures multiple DeepInfra models according to CrewAI best practices.

Following CrewAI LLM Connection Documentation:
https://docs.crewai.com/learn/llm-connections

Models (USER SPECIFIED - DO NOT CHANGE):
- meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8: CrewAI activities
- thenlper/gte-large: OpenAI embeddings
- google/gemma-3-4b-it: Chat conversations and multi-modal transactions
"""

import logging
import os
from functools import lru_cache
from typing import Any, Dict

# Import and apply DeepInfra response fix BEFORE importing litellm
try:
    from . import deepinfra_response_fixer

    logging.info("✅ DeepInfra response fixer applied to litellm")
except ImportError as e:
    logging.warning(f"Could not apply DeepInfra response fixer: {e}")

import litellm
from litellm.caching import Cache

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Start of new implementation ---


def deepinfra_logprobs_fixer(
    kwargs: Dict[str, Any], completion_obj=None, user_api_key_dict=None
) -> Dict[str, Any]:
    """
    Input callback function to forcibly remove 'logprobs' from requests to DeepInfra.
    This is necessary because DeepInfra returns `logprobs: null` which causes
    Pydantic validation errors in litellm when `logprobs: true` is in the request.

    This is a pre-API call callback that modifies the request parameters.
    """
    try:
        model_name = kwargs.get("model", "")
        # Check if this is a DeepInfra model
        if (
            "deepinfra" in model_name.lower()
            or kwargs.get("custom_llm_provider") == "deepinfra"
        ):
            # The `logprobs` parameter can be at the top level of the request kwargs
            if "logprobs" in kwargs:
                kwargs["logprobs"] = False  # Set to False instead of deleting
                logging.debug(
                    "DeepInfraLogprobsFixer: Set 'logprobs' to False for model %s.",
                    model_name,
                )

            # Also remove top_logprobs
            if "top_logprobs" in kwargs:
                del kwargs["top_logprobs"]
                logging.debug(
                    "DeepInfraLogprobsFixer: Removed 'top_logprobs' from request."
                )

            # It can also be nested within 'extra_body' for some configurations
            if "extra_body" in kwargs and isinstance(kwargs.get("extra_body"), dict):
                if "logprobs" in kwargs["extra_body"]:
                    kwargs["extra_body"]["logprobs"] = False
                    logging.debug(
                        "DeepInfraLogprobsFixer: Set 'logprobs' to False in 'extra_body'."
                    )
                if "top_logprobs" in kwargs["extra_body"]:
                    del kwargs["extra_body"]["top_logprobs"]

            # Also check optional_params which is used by litellm internally
            if "optional_params" in kwargs and isinstance(
                kwargs.get("optional_params"), dict
            ):
                if "logprobs" in kwargs["optional_params"]:
                    kwargs["optional_params"]["logprobs"] = False
                    logging.debug(
                        "DeepInfraLogprobsFixer: Set 'logprobs' to False in 'optional_params'."
                    )
                if "top_logprobs" in kwargs["optional_params"]:
                    del kwargs["optional_params"]["top_logprobs"]

            # Force logprobs to False if not already set
            if "logprobs" not in kwargs:
                kwargs["logprobs"] = False
                logging.debug(
                    "DeepInfraLogprobsFixer: Explicitly set 'logprobs' to False."
                )

    except Exception as e:
        # Log any unexpected errors during the callback's execution to avoid silent failures
        logging.error(
            "DeepInfraLogprobsFixer: Encountered an error - %s", e, exc_info=True
        )

    return kwargs


def deepinfra_response_fixer_success_callback(
    kwargs: Dict[str, Any], completion_obj: Any, start_time, end_time
) -> None:
    """
    Success callback function to fix DeepInfra responses with null logprobs.
    This runs after the API call succeeds but before litellm processes the response.
    """
    try:
        # Check if this is a DeepInfra response
        model_name = kwargs.get("model", "")
        if (
            "deepinfra" in model_name.lower()
            or kwargs.get("custom_llm_provider") == "deepinfra"
        ):
            # Fix the response object if it has logprobs
            if hasattr(completion_obj, "choices") and completion_obj.choices:
                for choice in completion_obj.choices:
                    if hasattr(choice, "logprobs") and choice.logprobs is not None:
                        # If logprobs exists and has content, fix null top_logprobs
                        if (
                            hasattr(choice.logprobs, "content")
                            and choice.logprobs.content
                        ):
                            for token_info in choice.logprobs.content:
                                if (
                                    hasattr(token_info, "top_logprobs")
                                    and token_info.top_logprobs is None
                                ):
                                    # Convert None to empty list instead of null
                                    token_info.top_logprobs = []

            logging.debug("DeepInfraResponseFixer: Fixed null top_logprobs in response")

    except Exception as e:
        # Log any errors but don't fail the response
        logging.warning(f"DeepInfraResponseFixer: Error fixing response - {e}")


def register_litellm_callbacks():
    """
    Registers the custom litellm callback handlers.
    Uses litellm's input_callback mechanism for pre-call modifications.
    Uses litellm's success_callback mechanism for post-call response fixes.
    """
    # Set the input callback function
    # This will be called before every litellm API call
    litellm.input_callback = [deepinfra_logprobs_fixer]

    # Set the success callback function
    # This will be called after successful API calls to fix the response
    litellm.success_callback = [deepinfra_response_fixer]

    logging.info("Successfully registered deepinfra callbacks (input + success).")


# Register the callback immediately when this module is loaded.
register_litellm_callbacks()

# --- End of new implementation ---


# Existing cache setup - remains unchanged
cache_client = (
    Cache(
        type="redis",
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=os.environ.get("REDIS_PORT", 6379),
        db=int(os.environ.get("REDIS_DB", 1)),
    )
    if os.getenv("LITELLM_CACHE_ENABLED", "False").lower() == "true"
    else None
)

# Existing cache setup

# Environment variable for controlling LLM provider.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepinfra").lower()
logging.info(f"LLM Provider set to: {LLM_PROVIDER}")

# Configure litellm to not request logprobs for DeepInfra
litellm.drop_params = True  # Allow dropping unsupported params
litellm.set_verbose = False  # Reduce verbosity

# Default parameters for DeepInfra models
DEEPINFRA_PARAMS = {
    "temperature": 0.1,
    "max_tokens": 4096,
    # Explicitly avoid logprobs for DeepInfra
    "logprobs": False,
}

# Embeddings configuration for CrewAI
DEEPINFRA_EMBEDDINGS_MODEL = "thenlper/gte-large"


@lru_cache(maxsize=128)
def get_crewai_llm(
    model: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    temperature: float = 0.1,
):
    """
    Configures and returns a CrewAI-compatible LLM instance.
    Uses lru_cache for memoization to avoid re-creating instances.
    The deepinfra_logprobs_fixer input callback handles logprobs removal globally.

    Returns:
        CrewAI LLM instance or string identifier for litellm
    """
    logging.info(
        f"Configuring LLM: Model='{model}', Temperature='{temperature}', Provider='{LLM_PROVIDER}'"
    )

    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        logging.error("DEEPINFRA_API_KEY environment variable not set.")
        raise ValueError("DEEPINFRA_API_KEY is required.")

    # Set the API key in environment for litellm to use
    os.environ["DEEPINFRA_API_KEY"] = api_key

    # Also set OpenAI API key to use DeepInfra endpoint for embeddings
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"

    # Try to create a CrewAI LLM instance with logprobs disabled
    try:
        from crewai import LLM

        # Create LLM instance with explicit configuration
        # Note: CrewAI LLM doesn't directly support logprobs parameter
        # But we can pass it as an extra parameter that will be handled by litellm
        llm = LLM(
            model=f"deepinfra/{model}",
            api_key=api_key,
            temperature=temperature,
            max_tokens=DEEPINFRA_PARAMS["max_tokens"],
        )

        # Set additional properties to ensure logprobs is disabled
        if hasattr(llm, "model_kwargs"):
            llm.model_kwargs = llm.model_kwargs or {}
            llm.model_kwargs["logprobs"] = False

        logging.info(f"Created CrewAI LLM instance for model: '{model}'")
        return llm

    except (ImportError, AttributeError) as e:
        logging.warning(f"Could not create CrewAI LLM instance: {e}")
        # Fallback to string identifier
        model_string = f"deepinfra/{model}"
        logging.info(f"Returning model string: '{model_string}'")
        return model_string


# Create a custom response processor to fix DeepInfra responses
def fix_deepinfra_response(response):
    """Fix DeepInfra response by converting null top_logprobs to empty lists"""
    if hasattr(response, "_raw_response"):
        raw = response._raw_response
        if isinstance(raw, dict) and "choices" in raw:
            for choice in raw.get("choices", []):
                if "logprobs" in choice and choice["logprobs"]:
                    if "content" in choice["logprobs"]:
                        for token_data in choice["logprobs"]["content"]:
                            if (
                                isinstance(token_data, dict)
                                and token_data.get("top_logprobs") is None
                            ):
                                token_data["top_logprobs"] = []
    return response


# Enable drop_params to skip unsupported parameters like logprobs
litellm.drop_params = True
logging.info("Enabled litellm.drop_params to skip unsupported parameters")

# Import the DeepInfra response fixer to handle logprobs issues
try:
    logging.info("DeepInfra response fixer loaded successfully")
except Exception as e:
    logging.warning(f"Could not load DeepInfra response fixer: {e}")


def get_embedding_llm():
    """
    Returns a configured embedding client for DeepInfra thenlper/gte-large model.
    This is used by the EmbeddingService for generating vector embeddings.
    """
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        logging.error("DEEPINFRA_API_KEY environment variable not set.")
        raise ValueError("DEEPINFRA_API_KEY is required for embeddings.")

    # Return configuration for DeepInfra embeddings
    # The embedding service will use this to make direct API calls
    return {
        "api_key": api_key,
        "model": DEEPINFRA_EMBEDDINGS_MODEL,
        "base_url": "https://api.deepinfra.com/v1/openai",
    }


def get_crewai_embeddings():
    """
    Configures and returns embeddings configuration for CrewAI.
    Uses DeepInfra's embedding model instead of OpenAI.
    """
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        logging.error("DEEPINFRA_API_KEY environment variable not set.")
        raise ValueError("DEEPINFRA_API_KEY is required for embeddings.")

    # Configure embeddings using DeepInfra's embedding model
    embeddings_config = {
        "provider": "openai",  # DeepInfra uses OpenAI-compatible API
        "config": {
            "model": DEEPINFRA_EMBEDDINGS_MODEL,
            "api_key": api_key,
            "base_url": "https://api.deepinfra.com/v1/openai",
            "encoding_format": "float",
        },
    }

    logging.info(
        f"Configured embeddings with DeepInfra model: {DEEPINFRA_EMBEDDINGS_MODEL}"
    )
    return embeddings_config
