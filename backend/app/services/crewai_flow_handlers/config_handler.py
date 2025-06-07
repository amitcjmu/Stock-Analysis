"""
Configuration Handler for CrewAI Flow Service
Manages configurable parameters, timeouts, and environment settings.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CrewAIFlowConfig:
    """Configuration handler for CrewAI Flow Service with environment variable support."""
    
    def __init__(self):
        try:
            from app.core.config import settings
            self.settings = settings
        except ImportError:
            self.settings = None
            logger.warning("Settings not available, using defaults")
    
    @property
    def timeout_data_validation(self) -> float:
        """Data validation timeout in seconds."""
        return getattr(self.settings, 'CREWAI_TIMEOUT_DATA_VALIDATION', 15.0)
    
    @property 
    def timeout_field_mapping(self) -> float:
        """Field mapping timeout in seconds."""
        return getattr(self.settings, 'CREWAI_TIMEOUT_FIELD_MAPPING', 20.0)
    
    @property
    def timeout_asset_classification(self) -> float:
        """Asset classification timeout in seconds."""
        return getattr(self.settings, 'CREWAI_TIMEOUT_ASSET_CLASSIFICATION', 15.0)
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """LLM configuration parameters."""
        return {
            "model": getattr(self.settings, 'CREWAI_LLM_MODEL', "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"),
            "temperature": getattr(self.settings, 'CREWAI_LLM_TEMPERATURE', 0.1),
            "max_tokens": getattr(self.settings, 'CREWAI_LLM_MAX_TOKENS', 4000),
            "base_url": getattr(self.settings, 'CREWAI_LLM_BASE_URL', "https://api.deepinfra.com/v1/openai")
        }
    
    @property
    def retry_attempts(self) -> int:
        """Number of retry attempts for failed operations."""
        return getattr(self.settings, 'CREWAI_RETRY_ATTEMPTS', 3)
    
    @property
    def retry_wait_seconds(self) -> int:
        """Wait time between retry attempts in seconds."""
        return getattr(self.settings, 'CREWAI_RETRY_WAIT_SECONDS', 2)
    
    @property
    def flow_ttl_hours(self) -> int:
        """Time-to-live for flow states in hours."""
        return getattr(self.settings, 'CREWAI_FLOW_TTL_HOURS', 1)
    
    @property
    def max_parallel_tasks(self) -> int:
        """Maximum number of parallel tasks to execute."""
        return getattr(self.settings, 'CREWAI_MAX_PARALLEL_TASKS', 3)
    
    @property
    def enable_caching(self) -> bool:
        """Whether to enable LLM response caching."""
        return getattr(self.settings, 'CREWAI_ENABLE_CACHING', False)
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for specific agent type."""
        agent_configs = {
            "data_validator": {
                "role": "Data Validation Specialist",
                "goal": "Rapidly validate CMDB data structure, quality, and migration readiness with actionable feedback",
                "backstory": "You are an expert data validation specialist with 15+ years experience in enterprise data assessment. You provide fast, accurate analysis with specific recommendations.",
                "timeout": self.timeout_data_validation
            },
            "field_mapper": {
                "role": "Field Mapping Intelligence Specialist",
                "goal": "Intelligently map CMDB fields to migration critical attributes using advanced pattern recognition and domain knowledge", 
                "backstory": "You are an AI specialist in field mapping with deep knowledge of CMDB schemas, ITIL standards, and migration requirements. You use intelligent pattern matching to suggest optimal field mappings.",
                "timeout": self.timeout_field_mapping
            },
            "asset_classifier": {
                "role": "Asset Classification Expert",
                "goal": "Rapidly and accurately classify IT assets for migration planning using domain expertise and pattern recognition",
                "backstory": "You are an expert in IT asset management and migration planning with extensive knowledge of asset types, dependencies, and migration complexities. You classify assets with high accuracy and confidence.",
                "timeout": self.timeout_asset_classification
            }
        }
        
        return agent_configs.get(agent_type, {})
    
    def validate_config(self) -> bool:
        """Validate configuration parameters."""
        try:
            # Check timeouts are positive
            if any([
                self.timeout_data_validation <= 0,
                self.timeout_field_mapping <= 0,
                self.timeout_asset_classification <= 0
            ]):
                logger.error("Timeout values must be positive")
                return False
            
            # Check LLM config
            llm_config = self.llm_config
            if not llm_config.get("model") or not llm_config.get("base_url"):
                logger.error("LLM model and base_url must be configured")
                return False
            
            # Check retry parameters
            if self.retry_attempts < 1 or self.retry_wait_seconds < 0:
                logger.error("Retry parameters must be positive")
                return False
            
            logger.info("CrewAI Flow configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for monitoring."""
        return {
            "timeouts": {
                "data_validation": self.timeout_data_validation,
                "field_mapping": self.timeout_field_mapping, 
                "asset_classification": self.timeout_asset_classification
            },
            "retry_config": {
                "attempts": self.retry_attempts,
                "wait_seconds": self.retry_wait_seconds
            },
            "flow_management": {
                "ttl_hours": self.flow_ttl_hours,
                "max_parallel_tasks": self.max_parallel_tasks,
                "caching_enabled": self.enable_caching
            },
            "llm_model": self.llm_config.get("model", "unknown")
        } 