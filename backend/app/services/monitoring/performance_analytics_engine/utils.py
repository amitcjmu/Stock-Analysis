"""
Utility functions for Performance Analytics Engine

Contains helper functions for report generation, calculations, and data processing.
"""

from datetime import datetime
from typing import Any, Dict, List

from .base import ImpactLevel, TrendDirection


class ReportingUtils:
    """Utility class for report generation and data formatting"""

    @staticmethod
    def calculate_improvement_achievements(
        auth_monitor,
        cache_monitor,
        performance_baselines: Dict,
        performance_targets: Dict,
    ) -> Dict[str, Any]:
        """Calculate achieved performance improvements vs baselines"""
        achievements = {}

        # Get current performance data
        auth_stats = auth_monitor.get_comprehensive_stats()
        cache_stats = cache_monitor.get_comprehensive_stats()

        # Login performance achievement
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats:
            current_login_p95 = login_stats.get("p95_duration_ms", 0)
            baseline_login = performance_baselines["login_p95_ms"]
            target_login = performance_targets["login_p95_ms"]

            if current_login_p95 > 0:
                improvement_achieved = (
                    (baseline_login - current_login_p95) / baseline_login
                ) * 100
                target_progress = (
                    (baseline_login - current_login_p95)
                    / (baseline_login - target_login)
                ) * 100

                achievements["login_performance"] = {
                    "improvement_achieved_percent": max(0, improvement_achieved),
                    "target_progress_percent": min(100, max(0, target_progress)),
                    "current_value_ms": current_login_p95,
                    "target_value_ms": target_login,
                    "baseline_value_ms": baseline_login,
                }

        # Cache performance achievement
        current_hit_rate = cache_stats.get("overall_summary", {}).get(
            "overall_hit_rate", 0
        )
        baseline_hit_rate = performance_baselines["cache_hit_rate"]
        target_hit_rate = performance_targets["cache_hit_rate"]

        if current_hit_rate > 0:
            improvement_achieved = (
                (current_hit_rate - baseline_hit_rate) / baseline_hit_rate
            ) * 100
            target_progress = (
                (current_hit_rate - baseline_hit_rate)
                / (target_hit_rate - baseline_hit_rate)
            ) * 100

            achievements["cache_performance"] = {
                "improvement_achieved_percent": max(0, improvement_achieved),
                "target_progress_percent": min(100, max(0, target_progress)),
                "current_value_percent": current_hit_rate,
                "target_value_percent": target_hit_rate,
                "baseline_value_percent": baseline_hit_rate,
            }

        return achievements

    @staticmethod
    def generate_executive_summary(
        trends: Dict, bottlenecks: List, achievements: Dict
    ) -> str:
        """Generate executive summary of performance analysis"""
        improving_metrics = len(
            [t for t in trends.values() if t.direction == TrendDirection.IMPROVING]
        )
        degrading_metrics = len(
            [t for t in trends.values() if t.direction == TrendDirection.DEGRADING]
        )
        critical_bottlenecks = len(
            [b for b in bottlenecks if b.impact_level == ImpactLevel.CRITICAL]
        )

        summary_parts = []

        # Overall trend assessment
        if improving_metrics > degrading_metrics:
            summary_parts.append(
                f"System performance shows positive trends with {improving_metrics} metrics improving"
            )
        elif degrading_metrics > improving_metrics:
            summary_parts.append(
                f"Performance concerns identified with {degrading_metrics} metrics degrading"
            )
        else:
            summary_parts.append("System performance is stable with mixed trends")

        # Bottleneck summary
        if critical_bottlenecks > 0:
            summary_parts.append(
                f"{critical_bottlenecks} critical bottlenecks require immediate attention"
            )
        elif len(bottlenecks) > 0:
            summary_parts.append(
                f"{len(bottlenecks)} performance bottlenecks identified for optimization"
            )

        # Achievement summary
        if achievements:
            login_achievement = achievements.get("login_performance", {}).get(
                "improvement_achieved_percent", 0
            )
            if login_achievement > 50:
                summary_parts.append(
                    f"Significant login performance improvement achieved ({login_achievement:.0f}%)"
                )

        return ". ".join(summary_parts) + "."

    @staticmethod
    def get_analytics_health_status(
        trend_history: Dict,
        bottleneck_history,
        recommendation_history,
        last_analysis: float,
        analysis_interval: int,
    ) -> Dict[str, Any]:
        """Get analytics engine health status"""
        return {
            "status": "healthy",
            "trend_data_points": {
                metric: len(data) for metric, data in trend_history.items()
            },
            "bottleneck_history_size": len(bottleneck_history),
            "recommendation_history_size": len(recommendation_history),
            "last_analysis": datetime.fromtimestamp(last_analysis).isoformat(),
            "analysis_interval_seconds": analysis_interval,
        }
