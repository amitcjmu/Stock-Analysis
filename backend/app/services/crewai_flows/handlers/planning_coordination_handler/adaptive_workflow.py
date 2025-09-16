"""
Adaptive workflow strategy management.

This module handles workflow adaptation based on performance metrics
and dynamic strategy switching.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AdaptiveWorkflowMixin:
    """Mixin for adaptive workflow strategy functionality"""

    def _setup_adaptive_workflow(self) -> Dict[str, Any]:
        """Setup adaptive workflow management"""
        return {
            "adaptation_enabled": True,
            "workflow_strategies": {
                "sequential": {"efficiency": 0.7, "reliability": 0.9},
                "parallel": {"efficiency": 0.9, "reliability": 0.7},
                "hybrid": {"efficiency": 0.8, "reliability": 0.8},
            },
            "adaptation_triggers": {
                "crew_performance_drop": {
                    "threshold": 0.7,
                    "action": "switch_strategy",
                },
                "resource_constraint": {
                    "threshold": 0.8,
                    "action": "optimize_allocation",
                },
                "time_pressure": {"threshold": 0.9, "action": "parallel_execution"},
            },
            "performance_tracking": {
                "crew_execution_times": {},
                "success_rates": {},
                "resource_utilization": {},
            },
        }

    def adapt_workflow_strategy(
        self, current_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt workflow strategy based on performance"""
        if not self.adaptive_workflow:
            self.adaptive_workflow = self._setup_adaptive_workflow()

        try:
            adaptation_result = {
                "adapted": False,
                "current_strategy": "sequential",
                "new_strategy": "sequential",
                "adaptation_reason": None,
                "performance_analysis": current_performance,
                "optimization_actions": [],
            }

            # Analyze current performance
            overall_performance = current_performance.get("overall_performance", 0.8)
            resource_utilization = current_performance.get("resource_utilization", 0.5)
            time_efficiency = current_performance.get("time_efficiency", 0.8)

            # Check adaptation triggers
            for trigger, config in self.adaptive_workflow[
                "adaptation_triggers"
            ].items():
                if (
                    trigger == "crew_performance_drop"
                    and overall_performance < config["threshold"]
                ):
                    adaptation_result["adapted"] = True
                    adaptation_result["adaptation_reason"] = (
                        "Performance below threshold"
                    )
                    adaptation_result["new_strategy"] = "hybrid"
                    adaptation_result["optimization_actions"].append(
                        "Enhanced validation enabled"
                    )

                elif (
                    trigger == "resource_constraint"
                    and resource_utilization > config["threshold"]
                ):
                    adaptation_result["adapted"] = True
                    adaptation_result["adaptation_reason"] = "Resource utilization high"
                    adaptation_result["new_strategy"] = "sequential"
                    adaptation_result["optimization_actions"].append(
                        "Resource allocation optimized"
                    )

                elif (
                    trigger == "time_pressure" and time_efficiency < config["threshold"]
                ):
                    adaptation_result["adapted"] = True
                    adaptation_result["adaptation_reason"] = "Time efficiency low"
                    adaptation_result["new_strategy"] = "parallel"
                    adaptation_result["optimization_actions"].append(
                        "Parallel execution enabled"
                    )

            # Update performance tracking
            current_strategy = adaptation_result["current_strategy"]
            if (
                current_strategy
                in self.adaptive_workflow["performance_tracking"]["success_rates"]
            ):
                self.adaptive_workflow["performance_tracking"]["success_rates"][
                    current_strategy
                ] = overall_performance

            logger.info(
                f"🔄 Workflow adaptation: {'ADAPTED' if adaptation_result['adapted'] else 'NO_CHANGE'}"
            )
            return adaptation_result

        except Exception as e:
            logger.error(f"Failed to adapt workflow strategy: {e}")
            return {
                "adapted": False,
                "error": str(e),
                "current_strategy": "sequential",
                "new_strategy": "sequential",
            }

    def _track_workflow_performance(
        self, strategy: str, execution_time: float, success_rate: float
    ):
        """Track workflow performance for adaptation decisions"""
        if not self.adaptive_workflow:
            self.adaptive_workflow = self._setup_adaptive_workflow()

        performance_tracking = self.adaptive_workflow["performance_tracking"]

        # Update execution times
        if strategy not in performance_tracking["crew_execution_times"]:
            performance_tracking["crew_execution_times"][strategy] = []
        performance_tracking["crew_execution_times"][strategy].append(execution_time)

        # Update success rates
        performance_tracking["success_rates"][strategy] = success_rate

        logger.debug(
            f"📊 Performance tracked for {strategy}: {execution_time}s, {success_rate:.2f} success rate"
        )

    def get_workflow_performance_summary(self) -> Dict[str, Any]:
        """Get summary of workflow performance across strategies"""
        if not self.adaptive_workflow:
            return {"error": "Adaptive workflow not initialized"}

        performance_tracking = self.adaptive_workflow["performance_tracking"]

        summary = {
            "strategies": {},
            "recommendations": [],
            "best_strategy": None,
        }

        for strategy, times in performance_tracking["crew_execution_times"].items():
            if times:
                avg_time = sum(times) / len(times)
                success_rate = performance_tracking["success_rates"].get(strategy, 0.0)

                summary["strategies"][strategy] = {
                    "avg_execution_time": avg_time,
                    "success_rate": success_rate,
                    "execution_count": len(times),
                    "efficiency_score": (success_rate * 0.7)
                    + ((1 / max(avg_time, 1)) * 0.3),
                }

        # Determine best strategy
        if summary["strategies"]:
            best_strategy = max(
                summary["strategies"].items(), key=lambda x: x[1]["efficiency_score"]
            )
            summary["best_strategy"] = best_strategy[0]
            summary["recommendations"].append(
                f"Consider using {best_strategy[0]} strategy for optimal performance"
            )

        return summary
