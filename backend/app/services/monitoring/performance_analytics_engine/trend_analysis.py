"""
Trend Analysis module for Performance Analytics Engine

Handles performance trend analysis, data processing, and pattern detection.
"""

import math
import statistics
import time
from typing import Dict, List

from .base import PerformanceTrend, TrendDirection


class TrendAnalysisService:
    """Service for analyzing performance trends and patterns"""

    def __init__(self, trend_history: Dict, analysis_window_hours: int = 168):
        self.trend_history = trend_history
        self.analysis_window_hours = analysis_window_hours

    def analyze_performance_trends(
        self, hours: int = 24
    ) -> Dict[str, PerformanceTrend]:
        """Analyze performance trends over specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        trends = {}

        for metric_name, trend_data in self.trend_history.items():
            # Filter data within time window
            recent_data = [
                point
                for point in trend_data
                if point["timestamp"] >= cutoff_time and point["value"] > 0
            ]

            if len(recent_data) < 3:  # Need minimum data points
                continue

            # Calculate trend
            trend = self._calculate_trend(recent_data, metric_name, hours)
            trends[metric_name] = trend

        return trends

    def _calculate_trend(
        self, data_points: List[Dict], metric_name: str, hours: int
    ) -> PerformanceTrend:
        """Calculate trend analysis for a metric"""
        if len(data_points) < 3:
            return PerformanceTrend(
                metric_name=metric_name,
                time_period_hours=hours,
                direction=TrendDirection.UNKNOWN,
                change_percentage=0.0,
                confidence_score=0.0,
                data_points=len(data_points),
            )

        # Sort by timestamp
        data_points.sort(key=lambda x: x["timestamp"])
        values = [point["value"] for point in data_points]

        # Calculate linear trend
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))

        # Linear regression slope
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Calculate percentage change
        start_value = statistics.mean(values[: max(1, n // 4)])  # First quarter average
        end_value = statistics.mean(values[-max(1, n // 4) :])  # Last quarter average

        if start_value > 0:
            change_percentage = ((end_value - start_value) / start_value) * 100
        else:
            change_percentage = 0.0

        # Determine trend direction
        if abs(change_percentage) < 5:
            direction = TrendDirection.STABLE
        elif change_percentage > 0:
            # For performance metrics, positive change might be bad (higher response times)
            if metric_name.endswith("_ms") or metric_name.endswith("_time"):
                direction = TrendDirection.DEGRADING
            else:
                direction = TrendDirection.IMPROVING
        else:
            # Negative change
            if metric_name.endswith("_ms") or metric_name.endswith("_time"):
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DEGRADING

        # Calculate confidence score based on data consistency
        variance = statistics.variance(values) if len(values) > 1 else 0
        mean_value = statistics.mean(values)
        coefficient_of_variation = (
            (math.sqrt(variance) / mean_value) if mean_value > 0 else 0
        )

        # Higher confidence for more data points and lower variability
        confidence_score = min(
            100, (n / 10) * 100 * (1 - min(1, coefficient_of_variation))
        )

        # Volatility check
        if coefficient_of_variation > 0.5:  # High variability
            direction = TrendDirection.VOLATILE

        return PerformanceTrend(
            metric_name=metric_name,
            time_period_hours=hours,
            direction=direction,
            change_percentage=change_percentage,
            confidence_score=confidence_score,
            data_points=n,
            trend_details={
                "slope": slope,
                "start_value": start_value,
                "end_value": end_value,
                "mean_value": mean_value,
                "variance": variance,
                "coefficient_of_variation": coefficient_of_variation,
            },
        )

    async def update_trend_data(self, auth_monitor, cache_monitor):
        """Update performance trend data with latest metrics"""
        # Get current performance data
        auth_stats = auth_monitor.get_comprehensive_stats()
        cache_stats = cache_monitor.get_comprehensive_stats()

        # Update trend data
        current_time = time.time()

        # Auth performance trends
        login_stats = auth_stats.get("operations", {}).get("login", {})
        if login_stats:
            self.trend_history["login_p95_ms"].append(
                {
                    "timestamp": current_time,
                    "value": login_stats.get("p95_duration_ms", 0),
                }
            )

        session_stats = auth_stats.get("operations", {}).get("session_validation", {})
        if session_stats:
            self.trend_history["session_validation_p95_ms"].append(
                {
                    "timestamp": current_time,
                    "value": session_stats.get("p95_duration_ms", 0),
                }
            )

        context_stats = auth_stats.get("operations", {}).get("context_switch", {})
        if context_stats:
            self.trend_history["context_switch_p95_ms"].append(
                {
                    "timestamp": current_time,
                    "value": context_stats.get("p95_duration_ms", 0),
                }
            )

        # Cache performance trends
        cache_summary = cache_stats.get("overall_summary", {})
        self.trend_history["cache_hit_rate"].append(
            {
                "timestamp": current_time,
                "value": cache_summary.get("overall_hit_rate", 0),
            }
        )

        redis_stats = cache_stats.get("cache_layers", {}).get("redis", {})
        if redis_stats:
            self.trend_history["redis_response_ms"].append(
                {
                    "timestamp": current_time,
                    "value": redis_stats.get("average_response_time_ms", 0),
                }
            )
