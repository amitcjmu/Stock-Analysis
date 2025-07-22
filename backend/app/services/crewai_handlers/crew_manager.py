"""
Crew Manager Handler
Handles core crew management and initialization operations.
"""

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class CrewManager:
    """Handles crew management operations with graceful fallbacks."""
    
    def __init__(self):
        self.service_available = False
        self.llm = None
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Initialize dependencies with graceful fallbacks."""
        try:
            from app.core.config import settings
            self.settings = settings
            
            # Check for CrewAI availability
            try:
                from crewai import LLM
                self.LLM = LLM
                self.crewai_available = True
            except ImportError:
                self.crewai_available = False
                logger.warning("CrewAI not available. Using placeholder mode.")
            
            # Configure environment
            self._configure_environment()
            
            # Initialize LLM if possible
            if (self.crewai_available and 
                hasattr(self.settings, 'DEEPINFRA_API_KEY') and 
                self.settings.DEEPINFRA_API_KEY and
                getattr(self.settings, 'CREWAI_ENABLED', True)):
                self._initialize_llm()
                self.service_available = True
            
            logger.info("Crew manager initialized successfully")
        except Exception as e:
            logger.warning(f"Crew manager services not available: {e}")
            self.service_available = False
    
    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks
    
    def _configure_environment(self):
        """Configure environment variables for CrewAI."""
        try:
            # Set up proper environment for CrewAI with local embeddings
            if not os.getenv('CHROMA_OPENAI_API_KEY'):
                os.environ['CHROMA_OPENAI_API_KEY'] = 'not_needed_using_local_embeddings'
            
            # Configure Chroma to use local embeddings
            os.environ['CHROMA_CLIENT_TYPE'] = 'local'
            os.environ['CHROMA_PERSIST_DIRECTORY'] = './data/chroma_db'
            
            # Set embedding model to use local sentence transformers
            os.environ['EMBEDDING_MODEL'] = 'sentence-transformers/all-MiniLM-L6-v2'
            os.environ['EMBEDDING_PROVIDER'] = 'local'
            
            # Configure DeepInfra following CrewAI documentation best practices
            if hasattr(self.settings, 'DEEPINFRA_API_KEY') and self.settings.DEEPINFRA_API_KEY:
                # CrewAI recommends using OPENAI_API_BASE for custom endpoints
                os.environ['OPENAI_API_KEY'] = self.settings.DEEPINFRA_API_KEY
                os.environ['OPENAI_API_BASE'] = 'https://api.deepinfra.com/v1/openai'
                os.environ['OPENAI_BASE_URL'] = 'https://api.deepinfra.com/v1/openai'
                # Set model name to prevent gpt-4o-mini fallback
                os.environ['OPENAI_MODEL_NAME'] = 'deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8'
            
            logger.info("CrewAI environment configured")
        except Exception as e:
            logger.warning(f"Error configuring environment: {e}")
    
    def _initialize_llm(self):
        """Initialize the CrewAI LLM configuration for DeepInfra."""
        try:
            if not self.settings.DEEPINFRA_API_KEY:
                logger.error("DeepInfra API key is required but not provided")
                self.llm = None
                return
            
            # Initialize CrewAI LLM following CrewAI documentation patterns
            self.llm = self.LLM(
                model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                base_url="https://api.deepinfra.com/v1/openai",
                api_key=self.settings.DEEPINFRA_API_KEY,
                # Standard CrewAI LLM parameters
                temperature=0.7,
                max_tokens=1500
            )
            
            logger.info("CrewAI LLM initialized successfully with DeepInfra")
            
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI LLM: {e}")
            self.llm = None
    
    def reinitialize_with_fresh_llm(self) -> None:
        """Reinitialize the LLM for fresh context."""
        try:
            if self.service_available and self.settings.DEEPINFRA_API_KEY:
                self._initialize_llm()
                logger.info("LLM reinitialized with fresh context")
            else:
                logger.warning("Cannot reinitialize LLM - service not available")
        except Exception as e:
            logger.error(f"Error reinitializing LLM: {e}")
    
    def get_llm(self):
        """Get the current LLM instance."""
        return self.llm
    
    def is_llm_available(self) -> bool:
        """Check if LLM is available."""
        return self.llm is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get crew manager status."""
        return {
            "service_available": self.service_available,
            "crewai_available": getattr(self, 'crewai_available', False),
            "llm_available": self.is_llm_available(),
            "deepinfra_configured": bool(getattr(self.settings, 'DEEPINFRA_API_KEY', None)),
            "environment_configured": True
        } 