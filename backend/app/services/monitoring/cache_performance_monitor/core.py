"""
Core Cache Performance Monitor

Main monitor class that orchestrates all cache monitoring services and provides
the primary interface for cache performance monitoring functionality.
"""

import time
from typing import Any, Dict, List

from app.core.logging import get_logger

from .base import (
    CacheLayer,
    CacheLayerStats,
    CacheOperation,
    CacheResult,
)
from .monitoring import CacheMonitoringService
from .stats import CacheStatsCalculator

logger = get_logger(__name__)


class CachePerformanceMonitor:
    """
    Cache Performance Monitor

    Comprehensive monitoring system for cache performance optimization.
    Integrates with existing Redis and in-memory cache services to provide
    detailed performance analytics, hit/miss tracking, and optimization insights.
    """

    def __init__(self, max_events: int = 50000, analysis_window: int = 3600):
        self.max_events = max_events
        self.analysis_window = analysis_window

        # Core services
        self.monitoring_service = CacheMonitoringService(max_events)
        self.stats_calculator = CacheStatsCalculator()

        # Start background monitoring
        self.monitoring_service.start_background_monitoring()

        logger.info(
            f"CachePerformanceMonitor initialized with {max_events} max events, "
            f"{analysis_window}s analysis window"
        )

    def record_cache_operation(
        self,
        operation: CacheOperation,
        cache_layer: CacheLayer,
        key_pattern: str,
        start_time: float,
        end_time: float,
        result: CacheResult,
        data_size_bytes: int = 0,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Record a cache operation performance event"""
        return self.monitoring_service.record_cache_operation(
            operation=operation,
            cache_layer=cache_layer,
            key_pattern=key_pattern,
            start_time=start_time,
            end_time=end_time,
            result=result,
            data_size_bytes=data_size_bytes,
            metadata=metadata,
        )

    def get_cache_layer_stats(
        self, cache_layer: CacheLayer, time_window_seconds: int = None
    ) -> CacheLayerStats:
        """Get statistics for a specific cache layer"""
        if time_window_seconds is None:
            time_window_seconds = self.analysis_window

        return self.stats_calculator.get_cache_layer_stats(
            self.monitoring_service.get_events(), cache_layer, time_window_seconds
        )

    def get_key_pattern_analysis(
        self, time_window_seconds: int = None
    ) -> Dict[str, Any]:
        """Analyze cache key patterns and their performance"""
        if time_window_seconds is None:
            time_window_seconds = self.analysis_window

        return self.stats_calculator.get_key_pattern_analysis(
            self.monitoring_service.get_events(), time_window_seconds
        )

    def get_comprehensive_stats(
        self, time_window_seconds: int = None
    ) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        if time_window_seconds is None:
            time_window_seconds = self.analysis_window

        events = self.monitoring_service.get_events()

        # Get stats for each cache layer
        cache_layers = {
            "redis": self.get_cache_layer_stats(CacheLayer.REDIS, time_window_seconds),
            "memory": self.get_cache_layer_stats(
                CacheLayer.MEMORY, time_window_seconds
            ),
        }

        # Calculate overall summary
        total_operations = sum(
            stats.total_operations for stats in cache_layers.values()
        )
        total_hits = sum(stats.hit_count for stats in cache_layers.values())
        total_gets = sum(
            stats.hit_count + stats.miss_count for stats in cache_layers.values()
        )

        overall_hit_rate = (total_hits / total_gets * 100) if total_gets > 0 else 0.0

        # Get key pattern analysis
        key_patterns = self.get_key_pattern_analysis(time_window_seconds)

        return {
            "timestamp": time.time(),
            "time_window_seconds": time_window_seconds,
            "overall_summary": {
                "total_operations": total_operations,
                "overall_hit_rate": overall_hit_rate,
                "total_events_tracked": len(events),
            },
            "cache_layers": {
                layer_name: {
                    "total_operations": stats.total_operations,
                    "hit_rate": stats.hit_rate,
                    "error_rate": stats.error_rate,
                    "average_response_time_ms": stats.average_response_time_ms,
                    "total_data_size_bytes": stats.total_data_size_bytes,
                }
                for layer_name, stats in cache_layers.items()
            },
            "key_patterns": key_patterns,
        }

    def get_cache_efficiency_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cache efficiency improvement recommendations"""
        recommendations = []

        # Get current stats
        redis_stats = self.get_cache_layer_stats(CacheLayer.REDIS)
        memory_stats = self.get_cache_layer_stats(CacheLayer.MEMORY)

        # Low hit rate recommendations
        if redis_stats.hit_rate < 70:
            recommendations.append(
                {
                    "type": "hit_rate_optimization",
                    "priority": "high",
                    "title": "Redis Hit Rate Below Optimal",
                    "description": f"Redis hit rate is {redis_stats.hit_rate:.1f}%, below optimal 80%+",
                    "suggestions": [
                        "Review TTL settings for frequently accessed data",
                        "Implement cache warming strategies",
                        "Analyze key patterns for optimization opportunities",
                    ],
                    "estimated_impact": "20-30% performance improvement",
                }
            )

        # High response time recommendations
        if redis_stats.average_response_time_ms > 100:
            recommendations.append(
                {
                    "type": "response_time_optimization",
                    "priority": "medium",
                    "title": "Redis Response Time High",
                    "description": f"Average Redis response time is {redis_stats.average_response_time_ms:.1f}ms",
                    "suggestions": [
                        "Check Redis server resources and network latency",
                        "Implement connection pooling",
                        "Consider data structure optimization",
                    ],
                    "estimated_impact": "15-25% faster response times",
                }
            )

        # Error rate recommendations
        if redis_stats.error_rate > 5:
            recommendations.append(
                {
                    "type": "error_reduction",
                    "priority": "critical",
                    "title": "High Cache Error Rate",
                    "description": f"Cache error rate is {redis_stats.error_rate:.1f}%",
                    "suggestions": [
                        "Investigate Redis connectivity issues",
                        "Review timeout configurations",
                        "Implement better error handling and retries",
                    ],
                    "estimated_impact": "Improved reliability and user experience",
                }
            )

        # Memory fallback usage
        if memory_stats.total_operations > redis_stats.total_operations * 0.1:
            recommendations.append(
                {
                    "type": "fallback_reduction",
                    "priority": "medium",
                    "title": "High Memory Cache Fallback Usage",
                    "description": "Memory cache is being used frequently as fallback",
                    "suggestions": [
                        "Improve Redis availability and reliability",
                        "Optimize cache key distribution",
                        "Consider increasing Redis memory allocation",
                    ],
                    "estimated_impact": "Better cache consistency and performance",
                }
            )

        if not recommendations:
            recommendations.append(
                {
                    "type": "status",
                    "priority": "info",
                    "title": "Cache Performance Optimal",
                    "description": "Cache performance metrics are within acceptable ranges",
                    "suggestions": ["Continue monitoring for trends"],
                    "estimated_impact": "Maintain current performance levels",
                }
            )

        return recommendations

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over specified time period"""
        return self.stats_calculator.get_performance_trends(
            self.monitoring_service.get_events(), hours
        )

    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Clean up old events to prevent memory bloat"""
        return self.monitoring_service.cleanup_old_events(max_age_hours)

    async def shutdown(self) -> None:
        """Shutdown the cache performance monitor"""
        await self.monitoring_service.shutdown()

    def get_monitor_health(self) -> Dict[str, Any]:
        """Get monitor health and status information"""
        events = self.monitoring_service.get_events()

        return {
            "status": "healthy",
            "total_events": len(events),
            "max_events": self.max_events,
            "analysis_window_seconds": self.analysis_window,
            "monitoring_enabled": self.monitoring_service.monitoring_enabled,
            "oldest_event_age_seconds": (
                time.time() - events[0].start_time if events else 0
            ),
        }
