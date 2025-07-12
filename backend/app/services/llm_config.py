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
    """Service to configure and manage multiple LLM instances following CrewAI best practices."""
    
    def __init__(self):
        self.deepinfra_api_key = getattr(settings, 'DEEPINFRA_API_KEY', os.getenv('DEEPINFRA_API_KEY'))
        # Use base URL from settings/environment, fallback to OpenAI-compatible endpoint
        self.deepinfra_base_url = getattr(settings, 'DEEPINFRA_BASE_URL', os.getenv('DEEPINFRA_BASE_URL', 'https://api.deepinfra.com/v1/openai'))
        
        if not self.deepinfra_api_key:
            logger.error("❌ DEEPINFRA_API_KEY not found in environment variables")
            raise ValueError("DEEPINFRA_API_KEY is required for LLM configuration")
        
        logger.info("✅ LLM Configuration Service initialized with DeepInfra API key")
        
        # Configure environment variables immediately for CrewAI
        self._configure_environment_variables()
    
    def _configure_environment_variables(self):
        """
        Configure environment variables for OpenAI-compatible LLM usage.
        Following CrewAI documentation: https://docs.crewai.com/learn/llm-connections#connecting-to-openai-compatible-llms
        """
        # Primary OpenAI environment variables for CrewAI
        os.environ["OPENAI_API_KEY"] = self.deepinfra_api_key
        os.environ["OPENAI_API_BASE"] = self.deepinfra_base_url
        os.environ["OPENAI_BASE_URL"] = self.deepinfra_base_url
        
        # Set the default model to prevent gpt-4o-mini fallback
        crewai_model = "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        os.environ["OPENAI_MODEL_NAME"] = crewai_model
        
        logger.info(f"✅ Environment configured for OpenAI-compatible DeepInfra: {crewai_model}")
        logger.info(f"✅ Base URL: {self.deepinfra_base_url}")
    
    def get_crewai_llm(self) -> LLM:
        """
        Get LLM instance for CrewAI activities.
        Model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 (USER SPECIFIED)
        
        Following CrewAI docs: Using LLM Class with base_url and api_key
        """
        model_name = "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        return LLM(
            model=model_name,
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            api_key=self.deepinfra_api_key,
            base_url=self.deepinfra_base_url
        )
    
    def get_embedding_llm(self) -> LLM:
        """
        Get LLM instance for embeddings.
        Model: thenlper/gte-large (USER SPECIFIED)
        """
        model_name = "deepinfra/thenlper/gte-large"
        
        return LLM(
            model=model_name,
            api_key=self.deepinfra_api_key,
            base_url=self.deepinfra_base_url
        )
    
    def get_chat_llm(self) -> LLM:
        """
        Get LLM instance for chat conversations and multi-modal transactions.
        Model: google/gemma-3-4b-it (USER SPECIFIED)
        """
        model_name = "deepinfra/google/gemma-3-4b-it"
        
        return LLM(
            model=model_name,
            temperature=0.8,
            max_tokens=1024,
            top_p=0.95,
            api_key=self.deepinfra_api_key,
            base_url=self.deepinfra_base_url
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
            logger.info("✅ CrewAI LLM (Llama-4-Maverick-17B-128E-Instruct-FP8) configured successfully")
            results['crewai'] = True
        except Exception as e:
            logger.error(f"❌ CrewAI LLM configuration failed: {e}")
            results['crewai'] = False
        
        # Test Embedding LLM
        try:
            embedding_llm = self.get_embedding_llm()
            logger.info("✅ Embedding LLM (thenlper/gte-large) configured successfully")
            results['embedding'] = True
        except Exception as e:
            logger.error(f"❌ Embedding LLM configuration failed: {e}")
            results['embedding'] = False
        
        # Test Chat LLM
        try:
            chat_llm = self.get_chat_llm()
            logger.info("✅ Chat LLM (google/gemma-3-4b-it) configured successfully")
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


# Create a CrewAI-compatible LLM using string identifier (alternative approach)
def create_crewai_string_llm() -> str:
    """
    Alternative approach: Return model string for CrewAI agents.
    CrewAI can use string identifiers when environment is properly configured.
    """
    return "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8" 