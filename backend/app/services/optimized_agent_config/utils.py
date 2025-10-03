"""
Optimized Agent Config - Utility Methods Module
Contains crew configuration and analysis methods.
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List

from app.services.agent_learning_system import LearningContext
from app.services.enhanced_agent_memory import enhanced_agent_memory
from app.services.llm_config import get_crewai_llm
from app.services.optimized_agent_config.base import AgentOptimizationConfig

logger = logging.getLogger(__name__)


class ConfigUtilsMixin:
    """Mixin for configuration utility methods"""

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
            "enable_parallel_execution": enable_parallel,
            "allow_delegation": allow_delegation,
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
