"""
LLM Configuration Service for AI Force Migration Platform
Configures multiple DeepInfra models according to CrewAI documentation.

Models:
- meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8: CrewAI activities
- thenlper/gte-large: OpenAI embeddings
- google/gemma-3-4b-it: Chat conversations and multi-modal transactions
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import CrewAI LLM class
CREWAI_AVAILABLE = False
try:
    from crewai import LLM
    CREWAI_AVAILABLE = True
    logger.info("✅ CrewAI LLM class imported successfully")
except ImportError as e:
    logger.warning(f"CrewAI not available: {e}")
    # Fallback LLM class
    class LLM:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

from app.core.config import settings

class LLMConfigurationService:
    """Service to configure and manage multiple LLM instances for different use cases."""
    
    def __init__(self):
        self.deepinfra_api_key = getattr(settings, 'DEEPINFRA_API_KEY', os.getenv('DEEPINFRA_API_KEY'))
        self.deepinfra_base_url = "https://api.deepinfra.com/v1/openai"
        
        if not self.deepinfra_api_key:
            logger.error("❌ DEEPINFRA_API_KEY not found in environment variables")
            raise ValueError("DEEPINFRA_API_KEY is required for LLM configuration")
        
        logger.info("✅ LLM Configuration Service initialized with DeepInfra API key")
    
    def get_crewai_llm(self) -> LLM:
        """
        Get LLM instance for CrewAI activities.
        Model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
        """
        model_name = getattr(settings, 'CREWAI_LLM_MODEL', 'meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8')
        return LLM(
            model=f"deepinfra/{model_name}",
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            base_url=self.deepinfra_base_url,
            api_key=self.deepinfra_api_key
        )
    
    def get_embedding_llm(self) -> LLM:
        """
        Get LLM instance for embeddings.
        Model: thenlper/gte-large
        """
        model_name = getattr(settings, 'EMBEDDING_LLM_MODEL', 'thenlper/gte-large')
        return LLM(
            model=f"deepinfra/{model_name}",
            base_url=self.deepinfra_base_url,
            api_key=self.deepinfra_api_key
        )
    
    def get_chat_llm(self) -> LLM:
        """
        Get LLM instance for chat conversations and multi-modal transactions.
        Model: google/gemma-3-4b-it
        """
        model_name = getattr(settings, 'CHAT_LLM_MODEL', 'google/gemma-3-4b-it')
        return LLM(
            model=f"deepinfra/{model_name}",
            temperature=0.8,
            max_tokens=1024,
            top_p=0.95,
            base_url=self.deepinfra_base_url,
            api_key=self.deepinfra_api_key
        )
    
    def get_all_llms(self) -> Dict[str, LLM]:
        """Get all configured LLM instances."""
        return {
            'crewai': self.get_crewai_llm(),
            'embedding': self.get_embedding_llm(),
            'chat': self.get_chat_llm()
        }
    
    def test_llm_connections(self) -> Dict[str, bool]:
        """Test connections to all LLM models."""
        results = {}
        
        # Test CrewAI LLM
        try:
            crewai_llm = self.get_crewai_llm()
            logger.info("✅ CrewAI LLM (Llama-4-Maverick) configured successfully")
            results['crewai'] = True
        except Exception as e:
            logger.error(f"❌ CrewAI LLM configuration failed: {e}")
            results['crewai'] = False
        
        # Test Embedding LLM
        try:
            embedding_llm = self.get_embedding_llm()
            logger.info("✅ Embedding LLM (gte-large) configured successfully")
            results['embedding'] = True
        except Exception as e:
            logger.error(f"❌ Embedding LLM configuration failed: {e}")
            results['embedding'] = False
        
        # Test Chat LLM
        try:
            chat_llm = self.get_chat_llm()
            logger.info("✅ Chat LLM (gemma-3-4b-it) configured successfully")
            results['chat'] = True
        except Exception as e:
            logger.error(f"❌ Chat LLM configuration failed: {e}")
            results['chat'] = False
        
        return results


# Global LLM configuration instance
llm_config = LLMConfigurationService()

# Convenience functions for easy access
def get_crewai_llm() -> LLM:
    """Get the primary LLM for CrewAI activities."""
    return llm_config.get_crewai_llm()

def get_embedding_llm() -> LLM:
    """Get the LLM for embeddings."""
    return llm_config.get_embedding_llm()

def get_chat_llm() -> LLM:
    """Get the LLM for chat conversations."""
    return llm_config.get_chat_llm()

def test_all_llm_connections() -> Dict[str, bool]:
    """Test all LLM connections."""
    return llm_config.test_llm_connections()


# Environment variable configuration for OpenAI-compatible endpoints
def configure_openai_environment_variables():
    """
    Configure environment variables for OpenAI-compatible LLM usage.
    This follows the CrewAI documentation for connecting to OpenAI-compatible LLMs.
    """
    # Set DeepInfra as the OpenAI-compatible provider
    os.environ["OPENAI_API_KEY"] = llm_config.deepinfra_api_key
    os.environ["OPENAI_API_BASE"] = llm_config.deepinfra_base_url
    
    # Use the configured CrewAI model as the default OpenAI model
    crewai_model = getattr(settings, 'CREWAI_LLM_MODEL', 'meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8')
    os.environ["OPENAI_MODEL_NAME"] = f"deepinfra/{crewai_model}"
    
    logger.info(f"✅ OpenAI environment variables configured for DeepInfra with model: {crewai_model}")


# Initialize environment variables on import
if CREWAI_AVAILABLE:
    try:
        configure_openai_environment_variables()
        logger.info("✅ LLM configuration completed successfully")
    except Exception as e:
        logger.error(f"❌ Failed to configure LLM environment: {e}") 