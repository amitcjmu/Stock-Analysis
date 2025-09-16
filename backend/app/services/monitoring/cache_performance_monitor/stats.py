"""
Statistics calculation and analysis for Cache Performance Monitor

Handles statistical calculations, performance metrics, and trend analysis.
"""

import statistics
import time
from collections import defaultdict, deque
from typing import Any, Dict, List

from .base import (
    CacheLayer,
    CacheLayerStats,
    CacheResult,
)


class CacheStatsCalculator:
    """Calculator for cache statistics and performance metrics"""

    def __init__(self):
        pass

    def get_cache_layer_stats(
        self, events: deque, cache_layer: CacheLayer, time_window_seconds: int = 3600
    ) -> CacheLayerStats:
        """Calculate statistics for a specific cache layer within time window"""
        current_time = time.time()
        cutoff_time = current_time - time_window_seconds

        # Filter events by layer and time window
        layer_events = [
            event
            for event in events
            if event.cache_layer == cache_layer and event.start_time >= cutoff_time
        ]

        stats = CacheLayerStats(layer=cache_layer)

        for event in layer_events:
            stats.total_operations += 1
            stats.total_response_time_ms += event.duration_ms
            stats.total_data_size_bytes += event.data_size_bytes

            if event.result == CacheResult.HIT:
                stats.hit_count += 1
            elif event.result == CacheResult.MISS:
                stats.miss_count += 1
            elif event.result in [CacheResult.ERROR, CacheResult.TIMEOUT]:
                stats.error_count += 1

            if not stats.last_operation or event.start_time > stats.last_operation:
                stats.last_operation = event.start_time

        return stats

    def get_key_pattern_analysis(
        self, events: deque, time_window_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Analyze cache key patterns and their performance"""
        current_time = time.time()
        cutoff_time = current_time - time_window_seconds

        recent_events = [event for event in events if event.start_time >= cutoff_time]

        pattern_stats = defaultdict(
            lambda: {
                "count": 0,
                "hits": 0,
                "misses": 0,
                "errors": 0,
                "total_time_ms": 0.0,
                "data_size_bytes": 0,
            }
        )

        for event in recent_events:
            pattern = event.key_pattern
            stats = pattern_stats[pattern]

            stats["count"] += 1
            stats["total_time_ms"] += event.duration_ms
            stats["data_size_bytes"] += event.data_size_bytes

            if event.result == CacheResult.HIT:
                stats["hits"] += 1
            elif event.result == CacheResult.MISS:
                stats["misses"] += 1
            elif event.result in [CacheResult.ERROR, CacheResult.TIMEOUT]:
                stats["errors"] += 1

        # Convert to final format with calculated metrics
        analysis = {}
        for pattern, stats in pattern_stats.items():
            total_gets = stats["hits"] + stats["misses"]
            hit_rate = (stats["hits"] / total_gets * 100) if total_gets > 0 else 0.0
            avg_time_ms = (
                stats["total_time_ms"] / stats["count"] if stats["count"] > 0 else 0.0
            )

            analysis[pattern] = {
                "total_operations": stats["count"],
                "hit_rate": hit_rate,
                "average_response_time_ms": avg_time_ms,
                "total_data_size_bytes": stats["data_size_bytes"],
                "error_count": stats["errors"],
            }

        return analysis

    def get_performance_trends(self, events: deque, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance trends over specified time period"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)

        recent_events = [event for event in events if event.start_time >= cutoff_time]

        if not recent_events:
            return {}

        # Group by hour
        hourly_stats = defaultdict(
            lambda: {"count": 0, "hits": 0, "total_time_ms": 0.0, "errors": 0}
        )

        for event in recent_events:
            hour_key = int(event.start_time // 3600)
            stats = hourly_stats[hour_key]

            stats["count"] += 1
            stats["total_time_ms"] += event.duration_ms

            if event.result == CacheResult.HIT:
                stats["hits"] += 1
            elif event.result in [CacheResult.ERROR, CacheResult.TIMEOUT]:
                stats["errors"] += 1

        # Calculate trends
        response_times = []
        hit_rates = []

        for hour_stats in hourly_stats.values():
            if hour_stats["count"] > 0:
                avg_time = hour_stats["total_time_ms"] / hour_stats["count"]
                response_times.append(avg_time)

                hit_rate = hour_stats["hits"] / hour_stats["count"] * 100
                hit_rates.append(hit_rate)

        return {
            "response_time_trend": {
                "values": response_times,
                "trend_direction": self._calculate_trend_direction(response_times),
                "average": statistics.mean(response_times) if response_times else 0.0,
            },
            "hit_rate_trend": {
                "values": hit_rates,
                "trend_direction": self._calculate_trend_direction(hit_rates),
                "average": statistics.mean(hit_rates) if hit_rates else 0.0,
            },
        }

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 2:
            return "stable"

        # Simple trend detection: compare first half to second half
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid])
        second_half_avg = statistics.mean(values[mid:])

        change_percent = (
            ((second_half_avg - first_half_avg) / first_half_avg * 100)
            if first_half_avg > 0
            else 0
        )

        if abs(change_percent) < 5:
            return "stable"
        elif change_percent > 0:
            return "increasing"
        else:
            return "decreasing"
