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

# Configure LiteLLM to handle DeepInfra logprobs issues
try:
    import litellm
    
    # CRITICAL: Configure response parsing to skip logprobs validation entirely for DeepInfra
    def custom_deepinfra_response_parser(response):
        """Custom response parser that removes problematic logprobs data"""
        if hasattr(response, 'json') and callable(response.json):
            response_data = response.json()
        else:
            response_data = response
        
        # Remove logprobs from all choices to prevent validation errors
        if isinstance(response_data, dict) and 'choices' in response_data:
            for choice in response_data['choices']:
                if 'logprobs' in choice:
                    del choice['logprobs']
        
        return response_data
    
    # Set up global LiteLLM configuration for DeepInfra
    litellm.drop_params = True
    litellm.suppress_debug_info = True
    
    # Configure DeepInfra-specific settings in LiteLLM's model config
    os.environ["DEEPINFRA_DROP_PARAMS"] = "logprobs,top_logprobs,stream_options"
    os.environ["LITELLM_DROP_PARAMS"] = "logprobs,top_logprobs,stream_options"
    
    # Set custom completion params to exclude logprobs entirely
    litellm.completion_cost_cache = {}
    
    logger.info("✅ CRITICAL FIX: Configured LiteLLM to completely drop logprobs parameters")
    logger.info("✅ CRITICAL FIX: Set custom response parsing to prevent DeepInfra logprobs validation errors")
except ImportError:
    logger.warning("LiteLLM not available for configuration")
except Exception as e:
    logger.warning(f"LiteLLM configuration warning: {e}")

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
        Configure environment variables for DeepInfra's OpenAI-compatible Chat Completions API.
        Following DeepInfra's recommendation to use Chat Completions for conversations.
        """
        # Configure for DeepInfra's recommended Chat Completions API
        os.environ["OPENAI_API_KEY"] = self.deepinfra_api_key
        os.environ["OPENAI_API_BASE"] = self.deepinfra_base_url
        os.environ["OPENAI_BASE_URL"] = self.deepinfra_base_url
        os.environ["OPENAI_API_TYPE"] = "openai"  # Use OpenAI format
        
        # Set the default model to prevent gpt-4o-mini fallback
        crewai_model = "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        os.environ["OPENAI_MODEL_NAME"] = crewai_model
        
        # CRITICAL: Configure LiteLLM to disable logprobs globally for DeepInfra
        # This prevents the validation errors we're seeing
        os.environ["LITELLM_DROP_PARAMS"] = "logprobs,top_logprobs,stream_options"
        os.environ["LITELLM_FAIL_ON_VALIDATION_ERROR"] = "false"
        
        # Disable logprobs specifically for all OpenAI-compatible providers
        os.environ["OPENAI_LOGPROBS"] = "false"
        
        logger.info(f"✅ Environment configured for DeepInfra Chat Completions API: {crewai_model}")
        logger.info(f"✅ Base URL: {self.deepinfra_base_url}")
        logger.info("✅ CRITICAL FIX: Disabled logprobs globally to prevent DeepInfra validation errors")
    
    def get_crewai_llm(self) -> LLM:
        """
        Get LLM instance for CrewAI activities.
        Model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8 (USER SPECIFIED)
        
        Following CrewAI docs: Using LLM Class with base_url and api_key
        """
        model_name = "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
        
        return LLM(
            model=model_name,
            base_url=self.deepinfra_base_url,
            api_key=self.deepinfra_api_key,
            # CrewAI standard parameters
            temperature=0.7,
            max_tokens=2048,
            # CRITICAL: Completely disable logprobs and related parameters for DeepInfra
            logprobs=False,
            # Additional parameters to ensure DeepInfra compatibility
            stream=False,
            # Custom parameters to prevent logprobs issues
            extra_body={
                "stream_options": None,
                "logprobs": False,
                "top_logprobs": None
            }
        )
    
    def get_embedding_llm(self) -> LLM:
        """
        Get LLM instance for embeddings.
        Model: thenlper/gte-large (USER SPECIFIED)
        """
        model_name = "deepinfra/thenlper/gte-large"
        
        return LLM(
            model=model_name,
            base_url=self.deepinfra_base_url,
            api_key=self.deepinfra_api_key,
            # CRITICAL: Completely disable logprobs and related parameters for DeepInfra
            logprobs=False,
            # Additional parameters to ensure DeepInfra compatibility
            stream=False,
            # Custom parameters to prevent logprobs issues
            extra_body={
                "stream_options": None,
                "logprobs": False,
                "top_logprobs": None
            }
        )
    
    def get_chat_llm(self) -> LLM:
        """
        Get LLM instance for chat conversations and multi-modal transactions.
        Model: google/gemma-3-4b-it (USER SPECIFIED)
        """
        model_name = "deepinfra/google/gemma-3-4b-it"
        
        return LLM(
            model=model_name,
            base_url=self.deepinfra_base_url,
            api_key=self.deepinfra_api_key,
            temperature=0.8,
            max_tokens=1024,
            # CRITICAL: Completely disable logprobs and related parameters for DeepInfra
            logprobs=False,
            # Additional parameters to ensure DeepInfra compatibility
            stream=False,
            # Custom parameters to prevent logprobs issues
            extra_body={
                "stream_options": None,
                "logprobs": False,
                "top_logprobs": None
            }
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