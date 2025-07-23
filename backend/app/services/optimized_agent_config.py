"""
Optimized Agent Configuration for CrewAI
Provides optimized settings and configurations for CrewAI agents based on:
- Performance analysis from monitoring
- Memory usage patterns
- Learning system feedback
- Best practices for enterprise deployment
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.agent_learning_system import LearningContext, agent_learning_system
from app.services.agent_performance_monitor import agent_performance_monitor
from app.services.enhanced_agent_memory import enhanced_agent_memory
from app.services.llm_config import get_crewai_llm

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
    enable_long_term_memory: bool = True
    enable_short_term_memory: bool = True
    enable_entity_memory: bool = True
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
                    f"Applied reliability optimizations for {operation_type} (error rate: {current_metrics.error_rate:.2f})"
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

    def get_crew_configuration(
        self, operation_type: str, agent_configs: List[AgentOptimizationConfig]
    ) -> Dict[str, Any]:
        """Get optimized crew configuration"""
        # Determine best process type based on operation and configs
        enable_parallel = any(
            config.enable_parallel_execution for config in agent_configs
        )
        enable_collaboration = any(
            config.enable_collaboration for config in agent_configs
        )
        allow_delegation = any(config.allow_delegation for config in agent_configs)

        # Calculate optimal crew settings
        max_rpm = self._calculate_optimal_rpm(operation_type, agent_configs)

        crew_config = {
            "verbose": True,
            "max_rpm": max_rpm,
            "share_crew": any(config.share_crew for config in agent_configs),
            "memory": any(config.enable_long_term_memory for config in agent_configs),
            "planning": enable_collaboration and len(agent_configs) > 2,
            "embedder": (
                {"provider": "openai", "model": "text-embedding-3-small"}
                if any(config.enable_long_term_memory for config in agent_configs)
                else None
            ),
        }

        # Add manager LLM if hierarchical process is beneficial
        if len(agent_configs) > 3 and enable_collaboration:
            crew_config["manager_llm"] = get_crewai_llm()
            crew_config["process"] = "hierarchical"
        else:
            crew_config["process"] = "sequential"

        return crew_config

    def _calculate_optimal_rpm(
        self, operation_type: str, agent_configs: List[AgentOptimizationConfig]
    ) -> int:
        """Calculate optimal requests per minute based on configuration"""
        base_rpm = 60  # Conservative default

        # Adjust based on operation complexity
        complexity_multipliers = {
            "field_mapping": 1.5,
            "data_cleansing": 1.2,
            "asset_inventory": 1.0,
            "dependency_analysis": 0.8,
            "tech_debt_analysis": 0.6,
        }

        multiplier = complexity_multipliers.get(operation_type, 1.0)

        # Adjust based on agent configurations
        avg_iterations = sum(config.max_iterations for config in agent_configs) / len(
            agent_configs
        )
        avg_tokens = sum(config.max_tokens for config in agent_configs) / len(
            agent_configs
        )

        # Reduce RPM for more complex configurations
        if avg_iterations > 3:
            multiplier *= 0.8
        if avg_tokens > 2000:
            multiplier *= 0.9

        optimal_rpm = int(base_rpm * multiplier)
        return max(10, min(200, optimal_rpm))  # Clamp between 10 and 200

    async def analyze_configuration_performance(
        self,
        operation_type: str,
        config: AgentOptimizationConfig,
        actual_performance: Dict[str, float],
    ) -> Dict[str, Any]:
        """Analyze how well a configuration performed and suggest improvements"""
        try:
            baseline = self.performance_baselines.get(operation_type, {})
            target_duration = baseline.get("target_duration", 60.0)
            target_accuracy = baseline.get("target_accuracy", 0.9)

            actual_duration = actual_performance.get("duration", 0)
            actual_accuracy = actual_performance.get("accuracy", 0)
            actual_error_rate = actual_performance.get("error_rate", 0)

            analysis = {
                "performance_vs_target": {
                    "duration_ratio": (
                        actual_duration / target_duration
                        if target_duration > 0
                        else 1.0
                    ),
                    "accuracy_ratio": (
                        actual_accuracy / target_accuracy
                        if target_accuracy > 0
                        else 1.0
                    ),
                    "error_rate": actual_error_rate,
                },
                "configuration_effectiveness": {},
                "improvement_suggestions": [],
            }

            # Analyze configuration effectiveness
            if actual_duration > target_duration * 1.2:
                analysis["improvement_suggestions"].extend(
                    [
                        "Reduce max_iterations to improve speed",
                        "Enable more aggressive caching",
                        "Consider reducing max_tokens",
                    ]
                )
                analysis["configuration_effectiveness"]["speed"] = "needs_improvement"
            else:
                analysis["configuration_effectiveness"]["speed"] = "adequate"

            if actual_accuracy < target_accuracy * 0.9:
                analysis["improvement_suggestions"].extend(
                    [
                        "Increase max_iterations for better accuracy",
                        "Enable collaboration between agents",
                        "Increase confidence threshold",
                    ]
                )
                analysis["configuration_effectiveness"][
                    "accuracy"
                ] = "needs_improvement"
            else:
                analysis["configuration_effectiveness"]["accuracy"] = "adequate"

            if actual_error_rate > 0.1:
                analysis["improvement_suggestions"].extend(
                    [
                        "Increase max_retry_attempts",
                        "Enable timeout protection",
                        "Add more robust error handling",
                    ]
                )
                analysis["configuration_effectiveness"][
                    "reliability"
                ] = "needs_improvement"
            else:
                analysis["configuration_effectiveness"]["reliability"] = "adequate"

            # Store analysis for learning
            await enhanced_agent_memory.store_memory(
                {
                    "type": "configuration_analysis",
                    "operation_type": operation_type,
                    "configuration": asdict(config),
                    "actual_performance": actual_performance,
                    "analysis_results": analysis,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                memory_type="performance_analysis",
                context=LearningContext(),
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze configuration performance: {e}")
            return {"error": str(e)}

    def get_configuration_report(self) -> Dict[str, Any]:
        """Get comprehensive configuration optimization report"""
        try:
            report = {
                "operation_configs": {
                    op_type: asdict(config)
                    for op_type, config in self.operation_configs.items()
                },
                "performance_baselines": self.performance_baselines,
                "optimization_statistics": {
                    "total_operations_configured": len(self.operation_configs),
                    "default_config": asdict(self.default_config),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate configuration report: {e}")
            return {"error": str(e)}


# Global configurator instance
optimized_agent_configurator = OptimizedAgentConfigurator()
