"""
CrewAI Embedder Configuration Helper

This module provides a formal configuration for CrewAI memory embeddings
to work with DeepInfra instead of OpenAI. This is a cleaner alternative
to the monkey patch approach, though the patch remains as a fallback.

References:
- ADR-019: CrewAI DeepInfra Embeddings Monkey Patch
- app/services/crewai_memory_patch.py (current implementation)
"""

import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EmbedderConfig:
    """
    Provides formal embedder configuration for CrewAI memory system.

    This configuration enables CrewAI to use DeepInfra's embedding service
    instead of OpenAI's, maintaining compatibility while reducing costs.
    """

    @staticmethod
    def get_deepinfra_config() -> Dict[str, Any]:
        """
        Get DeepInfra embedder configuration for CrewAI memory.

        Returns:
            Configuration dictionary for CrewAI memory initialization
        """
        api_key = os.getenv("DEEPINFRA_API_KEY")
        if not api_key:
            logger.warning("DEEPINFRA_API_KEY not set - memory features may not work")

        return {
            "provider": "openai",  # DeepInfra provides OpenAI-compatible API
            "config": {
                "model": "thenlper/gte-large",  # DeepInfra's embedding model
                "api_key": api_key,
                "api_base": "https://api.deepinfra.com/v1/openai",
                "base_url": "https://api.deepinfra.com/v1/openai",  # Some versions use base_url
                "encoding_format": "float",  # Required for DeepInfra compatibility
                "dimensions": 1024,  # gte-large embedding dimensions
            },
        }

    @staticmethod
    def get_embedder_for_crew(memory_enabled: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get embedder configuration for CrewAI Crew initialization.

        Args:
            memory_enabled: Whether memory should be enabled for the crew

        Returns:
            Embedder configuration or None if memory is disabled
        """
        if not memory_enabled:
            return None

        # Check if we should use DeepInfra (default) or OpenAI
        use_openai = os.getenv("USE_OPENAI_EMBEDDINGS", "false").lower() == "true"

        if use_openai:
            return EmbedderConfig.get_openai_config()
        else:
            return EmbedderConfig.get_deepinfra_config()

    @staticmethod
    def get_openai_config() -> Dict[str, Any]:
        """
        Get OpenAI embedder configuration (for comparison/testing).

        Returns:
            Configuration dictionary for OpenAI embeddings
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - falling back to DeepInfra")
            return EmbedderConfig.get_deepinfra_config()

        return {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": api_key,
                "encoding_format": "float",
                "dimensions": 1536,  # OpenAI embedding dimensions
            },
        }

    @staticmethod
    def apply_to_agent(
        agent_config: Dict[str, Any], memory_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Apply embedder configuration to an agent configuration.

        Args:
            agent_config: Existing agent configuration dictionary
            memory_enabled: Whether to enable memory for this agent

        Returns:
            Updated agent configuration with embedder settings
        """
        if memory_enabled:
            agent_config["memory"] = True
            agent_config["embedder"] = EmbedderConfig.get_embedder_for_crew(True)
            logger.debug(
                f"Enabled memory with {agent_config['embedder']['config']['model']} embeddings"
            )
        else:
            agent_config["memory"] = False
            agent_config.pop("embedder", None)

        return agent_config

    @staticmethod
    def apply_to_crew(
        crew_config: Dict[str, Any], memory_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Apply embedder configuration to a crew configuration.

        Args:
            crew_config: Existing crew configuration dictionary
            memory_enabled: Whether to enable memory for this crew

        Returns:
            Updated crew configuration with embedder settings
        """
        if memory_enabled:
            crew_config["memory"] = True
            crew_config["embedder"] = EmbedderConfig.get_embedder_for_crew(True)

            # Also set memory_config for compatibility
            crew_config["memory_config"] = {
                "provider": crew_config["embedder"]["provider"],
                "config": crew_config["embedder"]["config"].copy(),
            }

            logger.debug(
                f"Enabled crew memory with {crew_config['embedder']['config']['model']} embeddings"
            )
        else:
            crew_config["memory"] = False
            crew_config.pop("embedder", None)
            crew_config.pop("memory_config", None)

        return crew_config


class EmbedderHealthCheck:
    """Health check utilities for embedder configuration."""

    @staticmethod
    async def verify_deepinfra_connection() -> bool:
        """
        Verify that DeepInfra embedding endpoint is accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            import httpx

            config = EmbedderConfig.get_deepinfra_config()
            api_key = config["config"]["api_key"]
            base_url = config["config"]["api_base"]

            if not api_key:
                logger.error("Cannot verify DeepInfra connection - API key not set")
                return False

            async with httpx.AsyncClient() as client:
                # Test with a simple embedding request
                response = await client.post(
                    f"{base_url}/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": config["config"]["model"],
                        "input": "test",
                        "encoding_format": "float",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info("✅ DeepInfra embedding endpoint verified")
                    return True
                else:
                    logger.error(f"DeepInfra endpoint returned {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Failed to verify DeepInfra connection: {e}")
            return False

    @staticmethod
    def check_configuration() -> Dict[str, Any]:
        """
        Check current embedder configuration status.

        Returns:
            Status dictionary with configuration details
        """
        config = EmbedderConfig.get_embedder_for_crew()

        return {
            "provider": config["provider"] if config else None,
            "model": config["config"]["model"] if config else None,
            "api_key_set": bool(config and config["config"].get("api_key")),
            "endpoint": config["config"]["api_base"] if config else None,
            "memory_patch_active": "crewai_memory_patch"
            in [m.__name__ for m in __import__("sys").modules],
            "recommended_action": (
                "Configuration looks good"
                if config and config["config"].get("api_key")
                else "Set DEEPINFRA_API_KEY environment variable"
            ),
        }


# Usage Example:
"""
from app.services.crewai_flows.config.embedder_config import EmbedderConfig

# When creating an agent with memory
agent_config = {
    "role": "Data Analyst",
    "goal": "Analyze data patterns",
    # ... other config
}

# Apply embedder configuration
agent_config = EmbedderConfig.apply_to_agent(agent_config, memory_enabled=True)

# When creating a crew
crew_config = {
    "agents": [agent1, agent2],
    "tasks": [task1, task2],
    # ... other config
}

# Apply embedder configuration to crew
crew_config = EmbedderConfig.apply_to_crew(crew_config, memory_enabled=True)

# Create crew with proper memory configuration
crew = Crew(**crew_config)
"""
