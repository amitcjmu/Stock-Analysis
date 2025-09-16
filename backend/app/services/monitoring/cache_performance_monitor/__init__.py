"""
Cache Performance Monitor

Comprehensive monitoring system for cache performance optimization.
Integrates with existing Redis and in-memory cache services to provide
detailed performance analytics, hit/miss tracking, and optimization insights.

Key Features:
- Multi-layer cache performance tracking (Redis + in-memory fallback)
- Real-time hit/miss ratio monitoring and alerting
- Cache response time distribution analysis
- Cache utilization and memory usage tracking
- Cache invalidation effectiveness monitoring
- Performance optimization recommendations
- Integration with existing AuthCacheService

Performance Metrics Tracked:
- Cache hit rates by cache layer (Redis vs in-memory)
- Response time percentiles for cache operations
- Cache size utilization and memory efficiency
- Cache invalidation patterns and effectiveness
- Error rates and fallback activation frequency
- Queue sizes for batched operations
"""

# Import all base types and enums
from .base import (
    CacheLayer,
    CacheLayerStats,
    CacheOperation,
    CachePerformanceEvent,
    CacheResult,
    CacheUtilizationStats,
)

# Import main monitor class
from .core import CachePerformanceMonitor

# Import service components (for advanced usage)
from .monitoring import CacheMonitoringService
from .stats import CacheStatsCalculator

# Global singleton instance
_cache_performance_monitor = None


def get_cache_performance_monitor() -> CachePerformanceMonitor:
    """Get singleton cache performance monitor instance"""
    global _cache_performance_monitor
    if _cache_performance_monitor is None:
        _cache_performance_monitor = CachePerformanceMonitor()
    return _cache_performance_monitor


async def shutdown_cache_performance_monitor() -> None:
    """Shutdown the cache performance monitor"""
    global _cache_performance_monitor
    if _cache_performance_monitor is not None:
        await _cache_performance_monitor.shutdown()
        _cache_performance_monitor = None


def track_cache_operation_performance(
    operation: CacheOperation,
    cache_layer: CacheLayer,
    key_pattern: str,
    start_time: float,
    end_time: float,
    result: CacheResult,
    data_size_bytes: int = 0,
    metadata: dict = None,
) -> str:
    """Convenience function to track cache operation performance"""
    monitor = get_cache_performance_monitor()
    return monitor.record_cache_operation(
        operation=operation,
        cache_layer=cache_layer,
        key_pattern=key_pattern,
        start_time=start_time,
        end_time=end_time,
        result=result,
        data_size_bytes=data_size_bytes,
        metadata=metadata,
    )


# Public API exports - maintains backward compatibility
__all__ = [
    # Main monitor
    "CachePerformanceMonitor",
    "get_cache_performance_monitor",
    "shutdown_cache_performance_monitor",
    "track_cache_operation_performance",
    # Base types and enums
    "CacheLayer",
    "CacheOperation",
    "CacheResult",
    "CachePerformanceEvent",
    "CacheLayerStats",
    "CacheUtilizationStats",
    # Service components (for advanced usage)
    "CacheMonitoringService",
    "CacheStatsCalculator",
]
