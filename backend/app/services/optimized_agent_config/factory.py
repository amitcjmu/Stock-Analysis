"""
Optimized Agent Config - Factory Module
Contains configuration generation and optimization methods.
"""

import logging
from typing import Dict, Optional

from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.agent_performance_monitor import agent_performance_monitor
from app.services.enhanced_agent_memory import enhanced_agent_memory
from app.services.optimized_agent_config.base import AgentOptimizationConfig

logger = logging.getLogger(__name__)


class ConfigFactoryMixin:
    """Mixin for configuration factory methods"""

    def _load_performance_baselines(self) -> Dict[str, Dict[str, float]]:
        """Load performance baselines for different operation types"""
        return {
            "field_mapping": {
                "target_duration": 30.0,
                "max_duration": 60.0,
                "target_accuracy": 0.95,
                "memory_efficiency": 0.9,
            },
            "data_cleansing": {
                "target_duration": 45.0,
                "max_duration": 90.0,
                "target_accuracy": 0.92,
                "memory_efficiency": 0.85,
            },
            "asset_inventory": {
                "target_duration": 60.0,
                "max_duration": 120.0,
                "target_accuracy": 0.93,
                "memory_efficiency": 0.87,
            },
            "dependency_analysis": {
                "target_duration": 90.0,
                "max_duration": 180.0,
                "target_accuracy": 0.90,
                "memory_efficiency": 0.80,
            },
            "tech_debt_analysis": {
                "target_duration": 120.0,
                "max_duration": 240.0,
                "target_accuracy": 0.88,
                "memory_efficiency": 0.75,
            },
        }

    async def get_optimized_config(
        self,
        operation_type: str,
        context: Optional[LearningContext] = None,
        performance_priority: str = "balanced",  # "speed", "accuracy", "memory", "balanced"
    ) -> AgentOptimizationConfig:
        """Get optimized configuration for specific operation type"""
        try:
            # Start with default configuration
            config = AgentOptimizationConfig()

            # Apply operation-specific optimizations
            config = await self._apply_operation_optimizations(config, operation_type)

            # Apply performance-based optimizations
            config = await self._apply_performance_optimizations(
                config, operation_type, context
            )

            # Apply learning-based optimizations
            config = await self._apply_learning_optimizations(
                config, operation_type, context
            )

            # Apply priority-based optimizations
            config = self._apply_priority_optimizations(config, performance_priority)

            # Validate and adjust configuration
            config = self._validate_configuration(config, operation_type)

            # Cache configuration for future use
            self.operation_configs[operation_type] = config

            logger.info(
                f"Generated optimized config for {operation_type} with {performance_priority} priority"
            )
            return config

        except Exception as e:
            logger.error(f"Failed to generate optimized config: {e}")
            return self.default_config

    async def _apply_operation_optimizations(
        self, config: AgentOptimizationConfig, operation_type: str
    ) -> AgentOptimizationConfig:
        """Apply operation-specific optimizations"""
        self.performance_baselines.get(operation_type, {})

        # Adjust timeouts based on operation complexity
        if operation_type == "field_mapping":
            config.max_execution_time = 45
            config.max_iterations = 2
            config.temperature = 0.2  # Lower for consistency
            config.enable_parallel_execution = False  # Sequential for accuracy

        elif operation_type == "data_cleansing":
            config.max_execution_time = 75
            config.max_iterations = 3
            config.temperature = 0.3
            config.enable_parallel_execution = True

        elif operation_type == "asset_inventory":
            config.max_execution_time = 90
            config.max_iterations = 3
            config.temperature = 0.3
            config.enable_parallel_execution = True
            config.max_memory_items = 2000  # More memory for complex inventory

        elif operation_type == "dependency_analysis":
            config.max_execution_time = 150
            config.max_iterations = 4
            config.temperature = 0.4  # Slightly higher for creativity
            config.enable_collaboration = True  # Benefit from collaboration
            config.max_memory_items = 3000

        elif operation_type == "tech_debt_analysis":
            config.max_execution_time = 180
            config.max_iterations = 4
            config.temperature = 0.4
            config.enable_collaboration = True
            config.allow_delegation = True  # Complex analysis benefits from delegation
            config.max_memory_items = 5000

        return config

    async def _apply_performance_optimizations(
        self,
        config: AgentOptimizationConfig,
        operation_type: str,
        context: Optional[LearningContext],
    ) -> AgentOptimizationConfig:
        """Apply optimizations based on performance monitoring data"""
        try:
            # Get recent performance metrics
            metrics = agent_performance_monitor.get_performance_metrics(operation_type)
            current_metrics = metrics.get(operation_type)

            if not current_metrics:
                return config  # No performance data available

            baseline = self.performance_baselines.get(operation_type, {})
            target_duration = baseline.get("target_duration", 60.0)

            # Optimize based on performance trends
            if current_metrics.avg_duration > target_duration * 1.5:
                # Performance is slow - optimize for speed
                config.max_iterations = max(1, config.max_iterations - 1)
                config.max_tokens = min(1500, config.max_tokens)
                config.enable_caching = True
                config.cache_ttl_seconds = 7200  # Longer cache for slow operations

                logger.info(
                    f"Applied speed optimizations for {operation_type} (avg: {current_metrics.avg_duration:.1f}s)"
                )

            elif current_metrics.avg_duration < target_duration * 0.7:
                # Performance is fast - can afford more thorough processing
                config.max_iterations = min(5, config.max_iterations + 1)
                config.max_tokens = min(3000, config.max_tokens + 500)
                config.temperature = min(0.5, config.temperature + 0.1)

                logger.info(f"Applied thoroughness optimizations for {operation_type}")

            # Optimize based on error rate
            if current_metrics.error_rate > 0.1:  # More than 10% error rate
                config.max_retry_attempts = min(5, config.max_retry_attempts + 1)
                config.enable_timeout_protection = True
                config.max_execution_time = int(config.max_execution_time * 1.2)

                logger.info(
                    f"Applied reliability optimizations for {operation_type} "
                    f"(error rate: {current_metrics.error_rate:.2f})"
                )

            # Optimize based on cache hit rate
            if current_metrics.cache_hit_rate < 0.3:
                config.enable_caching = True
                config.cache_ttl_seconds = min(14400, config.cache_ttl_seconds * 2)

            return config

        except Exception as e:
            logger.error(f"Failed to apply performance optimizations: {e}")
            return config

    async def _apply_learning_optimizations(
        self,
        config: AgentOptimizationConfig,
        operation_type: str,
        context: Optional[LearningContext],
    ) -> AgentOptimizationConfig:
        """Apply optimizations based on learning system data"""
        try:
            if not context:
                return config

            # Get learning statistics for this operation type
            learning_stats = agent_learning_system.get_learning_statistics()

            # Check for learned patterns that might improve performance
            past_patterns = await enhanced_agent_memory.retrieve_memories(
                {"type": "optimization_pattern", "operation_type": operation_type},
                context=context,
                limit=5,
            )

            successful_patterns = [
                p for p in past_patterns if p.content.get("success", False)
            ]

            if successful_patterns:
                # Apply learned optimizations
                for pattern in successful_patterns:
                    optimization_type = pattern.content.get("optimization_type")
                    improvement_factor = pattern.content.get("improvement_factor", 1.0)

                    if improvement_factor > 1.2:  # Significant improvement
                        if optimization_type == "reduced_iterations":
                            config.max_iterations = max(1, config.max_iterations - 1)
                        elif optimization_type == "increased_cache_ttl":
                            config.cache_ttl_seconds = min(
                                14400, int(config.cache_ttl_seconds * 1.5)
                            )
                        elif optimization_type == "parallel_processing":
                            config.enable_parallel_execution = True
                        elif optimization_type == "reduced_temperature":
                            config.temperature = max(0.1, config.temperature - 0.1)

                logger.info(
                    f"Applied {len(successful_patterns)} learned optimizations for {operation_type}"
                )

            # Adjust confidence threshold based on learning accuracy
            if learning_stats.get("field_mapping_patterns", 0) > 50:
                # Enough patterns to be more confident
                config.confidence_threshold = max(
                    0.7, config.confidence_threshold - 0.1
                )

            return config

        except Exception as e:
            logger.error(f"Failed to apply learning optimizations: {e}")
            return config

    def _apply_priority_optimizations(
        self, config: AgentOptimizationConfig, priority: str
    ) -> AgentOptimizationConfig:
        """Apply optimizations based on performance priority"""
        if priority == "speed":
            # Optimize for fastest response
            config.max_iterations = min(2, config.max_iterations)
            config.max_tokens = min(1000, config.max_tokens)
            config.temperature = 0.1
            config.enable_caching = True
            config.enable_parallel_execution = True
            config.allow_delegation = False
            config.enable_collaboration = False

        elif priority == "accuracy":
            # Optimize for highest accuracy
            config.max_iterations = min(5, config.max_iterations + 2)
            config.max_tokens = min(4000, config.max_tokens + 1000)
            config.temperature = max(0.3, config.temperature)
            config.max_retry_attempts = min(5, config.max_retry_attempts + 1)
            config.enable_collaboration = True
            config.confidence_threshold = min(0.9, config.confidence_threshold + 0.1)

        elif priority == "memory":
            # Optimize for memory efficiency
            config.max_memory_items = max(500, config.max_memory_items // 2)
            config.max_tokens = min(1500, config.max_tokens)
            config.cache_ttl_seconds = max(1800, config.cache_ttl_seconds // 2)
            config.enable_long_term_memory = False  # Disable for memory efficiency

        # "balanced" uses default settings with minor adjustments

        return config

    def _validate_configuration(
        self, config: AgentOptimizationConfig, operation_type: str
    ) -> AgentOptimizationConfig:
        """Validate and adjust configuration to ensure reasonable values"""
        # Ensure minimum viable settings
        config.max_execution_time = max(30, min(300, config.max_execution_time))
        config.max_iterations = max(1, min(10, config.max_iterations))
        config.max_retry_attempts = max(1, min(5, config.max_retry_attempts))
        config.temperature = max(0.0, min(1.0, config.temperature))
        config.max_tokens = max(500, min(8000, config.max_tokens))
        config.confidence_threshold = max(0.5, min(0.99, config.confidence_threshold))
        config.learning_rate = max(0.01, min(0.5, config.learning_rate))
        config.memory_similarity_threshold = max(
            0.5, min(0.95, config.memory_similarity_threshold)
        )
        config.max_memory_items = max(100, min(10000, config.max_memory_items))
        config.cache_ttl_seconds = max(300, min(86400, config.cache_ttl_seconds))

        return config
