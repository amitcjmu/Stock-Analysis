"""
Optimized Agent Configuration for CrewAI
Provides optimized settings and configurations for CrewAI agents based on:
- Performance analysis from monitoring
- Memory usage patterns
- Learning system feedback
- Best practices for enterprise deployment
"""

import logging
from dataclasses import dataclass
from typing import Dict


logger = logging.getLogger(__name__)


@dataclass
class AgentOptimizationConfig:
    """Configuration for agent optimizations"""

    # Performance settings
    max_execution_time: int = 60
    max_iterations: int = 3
    max_retry_attempts: int = 2
    enable_timeout_protection: bool = True

    # Memory settings
    enable_long_term_memory: bool = False  # Per ADR-024: Use TenantMemoryManager
    enable_short_term_memory: bool = False  # Per ADR-024: Use TenantMemoryManager
    enable_entity_memory: bool = False  # Per ADR-024: Use TenantMemoryManager
    memory_similarity_threshold: float = 0.7
    max_memory_items: int = 1000

    # LLM settings
    temperature: float = 0.3
    max_tokens: int = 2000
    enable_streaming: bool = False

    # Collaboration settings
    allow_delegation: bool = False
    enable_collaboration: bool = False
    share_crew: bool = False

    # Performance optimizations
    enable_caching: bool = True
    enable_parallel_execution: bool = False
    cache_ttl_seconds: int = 3600

    # Learning integration
    enable_learning: bool = True
    confidence_threshold: float = 0.8
    learning_rate: float = 0.1

    # Monitoring settings
    enable_performance_monitoring: bool = True
    enable_error_tracking: bool = True
    enable_metrics_collection: bool = True


class OptimizedAgentConfigurator:
    """
    Service for creating optimized agent configurations based on performance data and learning
    """

    def __init__(self):
        self.default_config = AgentOptimizationConfig()
        self.operation_configs: Dict[str, AgentOptimizationConfig] = {}
        self.performance_baselines = self._load_performance_baselines()

        logger.info("🎯 Optimized Agent Configurator initialized")
