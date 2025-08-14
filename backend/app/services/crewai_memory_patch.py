"""
Patch for CrewAI memory to work with DeepInfra embeddings.

CrewAI's memory system uses OpenAI embeddings with encoding_format='base64',
but DeepInfra requires encoding_format='float'. This patch intercepts the
embedding calls and fixes the format.
"""

import logging
import os
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


def patch_crewai_memory_for_deepinfra():
    """
    Monkey patch CrewAI's memory system to work with DeepInfra embeddings.

    This fixes two issues:
    1. Sets OpenAI environment variables to use DeepInfra
    2. Patches the embeddings call to use 'float' encoding instead of 'base64'
    """

    # Set environment variables for OpenAI client to use DeepInfra
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_API_BASE"] = "https://api.deepinfra.com/v1/openai"
        os.environ["OPENAI_BASE_URL"] = "https://api.deepinfra.com/v1/openai"
        logger.info("✅ Set OpenAI env vars to use DeepInfra for CrewAI memory")
    else:
        logger.warning("⚠️ DEEPINFRA_API_KEY not found, memory may not work")
        return False

    # Monkey patch the OpenAI embeddings create method
    try:
        from openai import OpenAI
        from openai.resources.embeddings import Embeddings

        # Store the original create method
        original_create = Embeddings.create

        def patched_create(self, *args, **kwargs):
            """Patched embeddings.create that forces DeepInfra model and encoding"""
            # Force the correct DeepInfra embedding model
            if "model" in kwargs:
                original_model = kwargs["model"]
                if original_model in [
                    "text-embedding-3-small",
                    "text-embedding-ada-002",
                ]:
                    logger.debug(
                        f"Patching model from '{original_model}' to 'thenlper/gte-large' for DeepInfra"
                    )
                    kwargs["model"] = "thenlper/gte-large"
            else:
                # Force DeepInfra model if none specified
                kwargs["model"] = "thenlper/gte-large"

            # Force encoding_format to 'float' for DeepInfra compatibility
            if "encoding_format" in kwargs:
                original_format = kwargs["encoding_format"]
                if original_format != "float":
                    logger.debug(
                        f"Patching encoding_format from '{original_format}' to 'float' for DeepInfra"
                    )
                    kwargs["encoding_format"] = "float"
            else:
                # DeepInfra requires explicit encoding_format
                kwargs["encoding_format"] = "float"

            # Call the original method with modified kwargs
            return original_create(self, *args, **kwargs)

        # Apply the monkey patch
        Embeddings.create = patched_create
        logger.info("✅ Patched OpenAI embeddings.create for DeepInfra compatibility")

        # Also patch the RAGStorage if it exists
        try:
            from crewai.memory.storage.rag_storage import RAGStorage

            # Store original methods
            original_rag_init = RAGStorage.__init__

            def patched_rag_init(self, *args, **kwargs):
                """Patched RAGStorage.__init__ to ensure proper embedder config"""
                # Ensure the embedder uses our configuration
                if "embedder_config" in kwargs:
                    config = kwargs["embedder_config"]
                    if isinstance(config, dict) and "config" in config:
                        # Update the config to use float encoding
                        config["config"]["encoding_format"] = "float"

                # Call original init
                return original_rag_init(self, *args, **kwargs)

            RAGStorage.__init__ = patched_rag_init
            logger.info("✅ Patched RAGStorage for DeepInfra compatibility")

        except ImportError:
            logger.warning("Could not patch RAGStorage (might not be used)")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to patch CrewAI memory: {e}")
        return False


def apply_memory_patch():
    """Apply the memory patch and return success status"""
    success = patch_crewai_memory_for_deepinfra()
    if success:
        logger.info("✅ CrewAI memory system patched for DeepInfra")
    else:
        logger.warning("⚠️ CrewAI memory patch partially applied or failed")
    return success
