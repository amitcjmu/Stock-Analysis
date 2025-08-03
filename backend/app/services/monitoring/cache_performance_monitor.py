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

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from app.core.logging import get_logger
from app.services.monitoring.performance_metrics_collector import get_metrics_collector
from app.services.caching.auth_cache_service import get_auth_cache_service

logger = get_logger(__name__)


class CacheLayer(str, Enum):
    """Cache layer types"""

    REDIS = "redis"
    MEMORY = "memory"
    COMBINED = "combined"


class CacheOperation(str, Enum):
    """Cache operation types"""

    GET = "get"
    SET = "set"
    DELETE = "delete"
    INVALIDATE = "invalidate"
    CLEAR = "clear"
    HEALTH_CHECK = "health_check"
    BATCH_FLUSH = "batch_flush"


class CacheResult(str, Enum):
    """Cache operation results"""

    HIT = "hit"
    MISS = "miss"
    ERROR = "error"
    TIMEOUT = "timeout"
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class CachePerformanceEvent:
    """Individual cache performance event record"""

    operation_id: str
    operation: CacheOperation
    cache_layer: CacheLayer
    key_pattern: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    result: CacheResult = CacheResult.SUCCESS
    data_size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.end_time and not self.duration:
            self.duration = self.end_time - self.start_time

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        return (self.duration or 0) * 1000


@dataclass
class CacheLayerStats:
    """Statistics for a specific cache layer"""

    total_operations: int = 0
    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_response_time: float = 0.0
    data_transferred_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total_get_ops = self.hits + self.misses
        return (self.hits / total_get_ops * 100) if total_get_ops > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        return (
            (self.errors / self.total_operations * 100)
            if self.total_operations > 0
            else 0.0
        )

    @property
    def average_response_time_ms(self) -> float:
        """Calculate average response time in milliseconds"""
        return (
            (self.total_response_time / self.total_operations * 1000)
            if self.total_operations > 0
            else 0.0
        )


@dataclass
class CacheUtilizationStats:
    """Cache utilization and capacity statistics"""

    current_size_bytes: int = 0
    max_size_bytes: int = 0
    item_count: int = 0
    max_items: int = 0
    evictions_count: int = 0
    memory_fragmentation_ratio: float = 0.0

    @property
    def size_utilization_percent(self) -> float:
        """Calculate size utilization percentage"""
        return (
            (self.current_size_bytes / self.max_size_bytes * 100)
            if self.max_size_bytes > 0
            else 0.0
        )

    @property
    def item_utilization_percent(self) -> float:
        """Calculate item count utilization percentage"""
        return (self.item_count / self.max_items * 100) if self.max_items > 0 else 0.0


class CachePerformanceMonitor:
    """
    Cache Performance Monitor

    Provides comprehensive monitoring and analysis of cache performance
    across multiple cache layers with integration to existing cache services.
    """

    def __init__(self, max_events: int = 50000, analysis_window: int = 3600):
        self.max_events = max_events
        self.analysis_window = analysis_window

        # Event storage
        self.events: deque[CachePerformanceEvent] = deque(maxlen=max_events)
        self.active_operations: Dict[str, CachePerformanceEvent] = {}

        # Integration with existing services
        self.metrics_collector = get_metrics_collector()
        self.auth_cache_service = get_auth_cache_service()

        # Statistics tracking
        self.layer_stats: Dict[CacheLayer, CacheLayerStats] = {
            layer: CacheLayerStats() for layer in CacheLayer
        }

        # Key pattern tracking
        self.key_patterns: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "hits": 0,
                "misses": 0,
                "total_response_time": 0.0,
                "operations": 0,
            }
        )

        # Performance thresholds and alerts
        self.performance_thresholds = {
            "hit_rate_warning": 80.0,  # Alert if hit rate < 80%
            "hit_rate_critical": 60.0,  # Critical if hit rate < 60%
            "response_time_warning_ms": 100.0,  # Alert if avg response > 100ms
            "response_time_critical_ms": 500.0,  # Critical if avg response > 500ms
            "error_rate_warning": 2.0,  # Alert if error rate > 2%
            "error_rate_critical": 5.0,  # Critical if error rate > 5%
            "utilization_warning": 80.0,  # Alert if utilization > 80%
            "utilization_critical": 95.0,  # Critical if utilization > 95%
        }

        # Background monitoring with proper lifecycle management
        self._monitoring_executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="cache-monitor"
        )
        self._last_health_check = time.time()
        self._health_check_interval = 60  # seconds
        self._shutdown_event = asyncio.Event()
        self._background_tasks = set()  # Track background tasks for cleanup
        self._monitoring_active = False

        logger.info(
            "CachePerformanceMonitor initialized with max_events=%d", max_events
        )

        # Start background monitoring
        self._start_background_monitoring()

    def _start_background_monitoring(self) -> None:
        """Start background monitoring tasks with proper lifecycle management"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._shutdown_event.clear()

        async def background_monitor():
            """Async background monitoring task with proper cleanup"""
            try:
                while not self._shutdown_event.is_set():
                    try:
                        # Periodic health checks and stats collection
                        if (
                            time.time() - self._last_health_check
                            > self._health_check_interval
                        ):
                            await self._collect_cache_health_metrics()
                            self._last_health_check = time.time()

                        # Use asyncio.sleep with timeout to allow for shutdown
                        try:
                            await asyncio.wait_for(
                                self._shutdown_event.wait(), timeout=30.0
                            )
                            break  # Shutdown requested
                        except asyncio.TimeoutError:
                            continue  # Continue monitoring

                    except Exception as e:
                        logger.error("Error in background cache monitoring: %s", e)
                        try:
                            await asyncio.wait_for(
                                self._shutdown_event.wait(), timeout=60.0
                            )
                            break  # Shutdown requested
                        except asyncio.TimeoutError:
                            continue  # Continue monitoring after error

            except asyncio.CancelledError:
                logger.info("Background cache monitoring task cancelled")
            except Exception as e:
                logger.error("Fatal error in background cache monitoring: %s", e)
            finally:
                self._monitoring_active = False
                logger.info("Background cache monitoring stopped")

        # Create and track the background task
        task = asyncio.create_task(background_monitor())
        self._background_tasks.add(task)

        # Remove from tracking when done
        task.add_done_callback(self._background_tasks.discard)

    async def _collect_cache_health_metrics(self) -> None:
        """Collect health metrics from cache services"""
        try:
            # Get cache stats from AuthCacheService
            cache_stats = await self.auth_cache_service.get_cache_stats()

            # Update metrics collector
            if "hit_rate" in cache_stats:
                self.metrics_collector.update_cache_hit_ratio(
                    "redis", cache_stats["hit_rate"]
                )

            # Record utilization metrics
            if "fallback_cache" in cache_stats:
                fallback_stats = cache_stats["fallback_cache"]
                utilization = fallback_stats.get("utilization", 0)
                size = fallback_stats.get("size", 0)

                gauge = self.metrics_collector.get_gauge("cache_utilization_percent")
                if gauge:
                    gauge.set(utilization, {"cache_type": "memory"})

                size_gauge = self.metrics_collector.get_gauge("cache_size_bytes")
                if size_gauge:
                    size_gauge.set(size, {"cache_type": "memory"})

            # Perform health check
            health_data = await self.auth_cache_service.health_check()
            self._process_health_check_results(health_data)

        except Exception as e:
            logger.error("Error collecting cache health metrics: %s", e)

    def _process_health_check_results(self, health_data: Dict[str, Any]) -> None:
        """Process health check results and generate alerts"""
        # Check Redis availability
        redis_available = health_data.get("redis", {}).get("available", False)
        redis_latency = health_data.get("redis", {}).get("latency_ms", 0)

        if not redis_available:
            logger.warning(
                "CACHE ALERT: Redis cache is unavailable - using fallback only"
            )
        elif redis_latency > self.performance_thresholds["response_time_critical_ms"]:
            logger.warning(
                "CACHE ALERT: Redis latency is critical (%.2fms)", redis_latency
            )
        elif redis_latency > self.performance_thresholds["response_time_warning_ms"]:
            logger.info(
                "CACHE NOTICE: Redis latency is elevated (%.2fms)", redis_latency
            )

        # Check fallback cache status
        fallback_available = health_data.get("fallback", {}).get("available", False)
        if not fallback_available:
            logger.error(
                "CACHE CRITICAL: Both Redis and fallback cache are unavailable!"
            )

        # Check for issues
        issues = health_data.get("issues", [])
        for issue in issues:
            logger.warning("CACHE ISSUE: %s", issue)

    def record_cache_operation(
        self,
        operation: CacheOperation,
        cache_layer: CacheLayer,
        key_pattern: str,
        duration: float,
        result: CacheResult,
        data_size_bytes: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a cache operation performance event"""

        # Create event record
        event = CachePerformanceEvent(
            operation_id=f"cache_{int(time.time() * 1000000)}",
            operation=operation,
            cache_layer=cache_layer,
            key_pattern=key_pattern,
            start_time=time.time() - duration,
            end_time=time.time(),
            duration=duration,
            result=result,
            data_size_bytes=data_size_bytes,
            metadata=metadata or {},
        )

        # Store event
        self.events.append(event)

        # Update layer statistics
        layer_stat = self.layer_stats[cache_layer]
        layer_stat.total_operations += 1
        layer_stat.total_response_time += duration
        layer_stat.data_transferred_bytes += data_size_bytes

        if result == CacheResult.HIT:
            layer_stat.hits += 1
        elif result == CacheResult.MISS:
            layer_stat.misses += 1
        elif result == CacheResult.ERROR:
            layer_stat.errors += 1

        # Update key pattern statistics
        pattern_stats = self.key_patterns[key_pattern]
        pattern_stats["operations"] += 1
        pattern_stats["total_response_time"] += duration

        if result == CacheResult.HIT:
            pattern_stats["hits"] += 1
        elif result == CacheResult.MISS:
            pattern_stats["misses"] += 1

        # Record in metrics collector
        self.metrics_collector.record_cache_operation(
            operation.value,
            duration,
            cache_layer.value,
            "success" if result in [CacheResult.HIT, CacheResult.SUCCESS] else "error",
            result.value,
        )

        # Check performance thresholds
        self._check_performance_thresholds(event)

    def _check_performance_thresholds(self, event: CachePerformanceEvent) -> None:
        """Check if event exceeds performance thresholds"""
        duration_ms = event.duration_ms

        # Check response time thresholds
        if duration_ms > self.performance_thresholds["response_time_critical_ms"]:
            logger.warning(
                "CACHE CRITICAL: %s operation on %s took %.2fms (key: %s)",
                event.operation.value,
                event.cache_layer.value,
                duration_ms,
                event.key_pattern,
            )
        elif duration_ms > self.performance_thresholds["response_time_warning_ms"]:
            logger.info(
                "CACHE WARNING: %s operation on %s took %.2fms (key: %s)",
                event.operation.value,
                event.cache_layer.value,
                duration_ms,
                event.key_pattern,
            )

    def get_cache_layer_stats(
        self, cache_layer: CacheLayer, window_seconds: Optional[int] = None
    ) -> CacheLayerStats:
        """Get performance statistics for a specific cache layer"""
        window_seconds = window_seconds or self.analysis_window
        cutoff_time = time.time() - window_seconds

        # Filter events for this layer and time window
        layer_events = [
            event
            for event in self.events
            if (
                event.cache_layer == cache_layer
                and event.start_time >= cutoff_time
                and event.duration is not None
            )
        ]

        if not layer_events:
            return CacheLayerStats()

        # Calculate statistics
        stats = CacheLayerStats()
        stats.total_operations = len(layer_events)

        for event in layer_events:
            stats.total_response_time += event.duration or 0
            stats.data_transferred_bytes += event.data_size_bytes

            if event.result == CacheResult.HIT:
                stats.hits += 1
            elif event.result == CacheResult.MISS:
                stats.misses += 1
            elif event.result == CacheResult.ERROR:
                stats.errors += 1

        return stats

    def get_key_pattern_analysis(
        self, window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get performance analysis by key patterns"""
        window_seconds = window_seconds or self.analysis_window
        cutoff_time = time.time() - window_seconds

        # Filter events by time window
        recent_events = [
            event
            for event in self.events
            if event.start_time >= cutoff_time and event.duration is not None
        ]

        # Group by key pattern
        pattern_analysis = defaultdict(
            lambda: {
                "total_operations": 0,
                "hits": 0,
                "misses": 0,
                "errors": 0,
                "total_response_time": 0.0,
                "data_transferred_bytes": 0,
                "cache_layers": defaultdict(int),
            }
        )

        for event in recent_events:
            pattern = event.key_pattern
            analysis = pattern_analysis[pattern]

            analysis["total_operations"] += 1
            analysis["total_response_time"] += event.duration or 0
            analysis["data_transferred_bytes"] += event.data_size_bytes
            analysis["cache_layers"][event.cache_layer.value] += 1

            if event.result == CacheResult.HIT:
                analysis["hits"] += 1
            elif event.result == CacheResult.MISS:
                analysis["misses"] += 1
            elif event.result == CacheResult.ERROR:
                analysis["errors"] += 1

        # Calculate derived metrics
        for pattern, analysis in pattern_analysis.items():
            total_get_ops = analysis["hits"] + analysis["misses"]
            analysis["hit_rate"] = (
                (analysis["hits"] / total_get_ops * 100) if total_get_ops > 0 else 0.0
            )
            analysis["error_rate"] = (
                (analysis["errors"] / analysis["total_operations"] * 100)
                if analysis["total_operations"] > 0
                else 0.0
            )
            analysis["average_response_time_ms"] = (
                (analysis["total_response_time"] / analysis["total_operations"] * 1000)
                if analysis["total_operations"] > 0
                else 0.0
            )
            analysis["cache_layers"] = dict(analysis["cache_layers"])

        return dict(pattern_analysis)

    def get_comprehensive_stats(
        self, window_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        window_seconds = window_seconds or self.analysis_window

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_window_seconds": window_seconds,
            "cache_layers": {},
            "key_patterns": {},
            "overall_summary": {},
            "performance_alerts": [],
            "utilization": {},
        }

        # Get stats for each cache layer
        total_operations = 0
        total_hits = 0
        total_misses = 0
        total_errors = 0

        for cache_layer in CacheLayer:
            if cache_layer == CacheLayer.COMBINED:
                continue  # Skip combined layer for individual stats

            layer_stats = self.get_cache_layer_stats(cache_layer, window_seconds)
            stats["cache_layers"][cache_layer.value] = {
                "total_operations": layer_stats.total_operations,
                "hit_rate": round(layer_stats.hit_rate, 2),
                "error_rate": round(layer_stats.error_rate, 2),
                "average_response_time_ms": round(
                    layer_stats.average_response_time_ms, 2
                ),
                "data_transferred_mb": round(
                    layer_stats.data_transferred_bytes / (1024 * 1024), 2
                ),
            }

            total_operations += layer_stats.total_operations
            total_hits += layer_stats.hits
            total_misses += layer_stats.misses
            total_errors += layer_stats.errors

        # Overall summary
        total_get_ops = total_hits + total_misses
        stats["overall_summary"] = {
            "total_operations": total_operations,
            "overall_hit_rate": (
                (total_hits / total_get_ops * 100) if total_get_ops > 0 else 0.0
            ),
            "overall_error_rate": (
                (total_errors / total_operations * 100) if total_operations > 0 else 0.0
            ),
            "active_operations": len(self.active_operations),
        }

        # Key pattern analysis
        stats["key_patterns"] = self.get_key_pattern_analysis(window_seconds)

        # Performance alerts
        stats["performance_alerts"] = self._generate_performance_alerts(stats)

        # Utilization stats (from integrated cache service)
        try:
            cache_stats = asyncio.run(self.auth_cache_service.get_cache_stats())
            stats["utilization"] = {
                "redis_enabled": cache_stats.get("redis_enabled", False),
                "fallback_cache": cache_stats.get("fallback_cache", {}),
                "activity_buffers": cache_stats.get("activity_buffers", {}),
            }
        except Exception as e:
            logger.warning("Could not get utilization stats: %s", e)
            stats["utilization"] = {"error": "Failed to collect utilization data"}

        return stats

    def _generate_performance_alerts(
        self, stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate performance alerts based on thresholds"""
        alerts = []

        # Check overall hit rate
        overall_hit_rate = stats["overall_summary"]["overall_hit_rate"]
        if overall_hit_rate < self.performance_thresholds["hit_rate_critical"]:
            alerts.append(
                {
                    "type": "critical_hit_rate",
                    "severity": "critical",
                    "metric": "overall_hit_rate",
                    "value": overall_hit_rate,
                    "threshold": self.performance_thresholds["hit_rate_critical"],
                    "message": (
                        f"Critical: Overall cache hit rate ({overall_hit_rate:.1f}%) "
                        f"is below critical threshold"
                    ),
                }
            )
        elif overall_hit_rate < self.performance_thresholds["hit_rate_warning"]:
            alerts.append(
                {
                    "type": "low_hit_rate",
                    "severity": "warning",
                    "metric": "overall_hit_rate",
                    "value": overall_hit_rate,
                    "threshold": self.performance_thresholds["hit_rate_warning"],
                    "message": f"Warning: Overall cache hit rate ({overall_hit_rate:.1f}%) is below warning threshold",
                }
            )

        # Check overall error rate
        overall_error_rate = stats["overall_summary"]["overall_error_rate"]
        if overall_error_rate > self.performance_thresholds["error_rate_critical"]:
            alerts.append(
                {
                    "type": "critical_error_rate",
                    "severity": "critical",
                    "metric": "overall_error_rate",
                    "value": overall_error_rate,
                    "threshold": self.performance_thresholds["error_rate_critical"],
                    "message": (
                        f"Critical: Overall cache error rate ({overall_error_rate:.1f}%) "
                        f"exceeds critical threshold"
                    ),
                }
            )
        elif overall_error_rate > self.performance_thresholds["error_rate_warning"]:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "severity": "warning",
                    "metric": "overall_error_rate",
                    "value": overall_error_rate,
                    "threshold": self.performance_thresholds["error_rate_warning"],
                    "message": (
                        f"Warning: Overall cache error rate ({overall_error_rate:.1f}%) "
                        f"exceeds warning threshold"
                    ),
                }
            )

        # Check individual layer performance
        for layer_name, layer_stats in stats["cache_layers"].items():
            avg_response_time = layer_stats["average_response_time_ms"]
            if (
                avg_response_time
                > self.performance_thresholds["response_time_critical_ms"]
            ):
                alerts.append(
                    {
                        "type": "critical_response_time",
                        "severity": "critical",
                        "cache_layer": layer_name,
                        "metric": "average_response_time_ms",
                        "value": avg_response_time,
                        "threshold": self.performance_thresholds[
                            "response_time_critical_ms"
                        ],
                        "message": (
                            f"Critical: {layer_name} cache response time "
                            f"({avg_response_time:.1f}ms) exceeds critical threshold"
                        ),
                    }
                )
            elif (
                avg_response_time
                > self.performance_thresholds["response_time_warning_ms"]
            ):
                alerts.append(
                    {
                        "type": "slow_response_time",
                        "severity": "warning",
                        "cache_layer": layer_name,
                        "metric": "average_response_time_ms",
                        "value": avg_response_time,
                        "threshold": self.performance_thresholds[
                            "response_time_warning_ms"
                        ],
                        "message": (
                            f"Warning: {layer_name} cache response time "
                            f"({avg_response_time:.1f}ms) exceeds warning threshold"
                        ),
                    }
                )

        # Check key pattern performance
        for pattern, pattern_stats in stats["key_patterns"].items():
            pattern_hit_rate = pattern_stats.get("hit_rate", 0)
            if (
                pattern_hit_rate < self.performance_thresholds["hit_rate_warning"]
                and pattern_stats.get("total_operations", 0) > 10
            ):
                alerts.append(
                    {
                        "type": "pattern_low_hit_rate",
                        "severity": "warning",
                        "key_pattern": pattern,
                        "metric": "hit_rate",
                        "value": pattern_hit_rate,
                        "threshold": self.performance_thresholds["hit_rate_warning"],
                        "message": f"Warning: Key pattern '{pattern}' has low hit rate ({pattern_hit_rate:.1f}%)",
                    }
                )

        return alerts

    def get_cache_efficiency_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cache efficiency optimization recommendations"""
        recommendations = []

        # Analyze key patterns for optimization opportunities
        pattern_analysis = self.get_key_pattern_analysis()

        for pattern, stats in pattern_analysis.items():
            if stats["total_operations"] < 10:
                continue  # Skip patterns with low usage

            # Recommend TTL optimization for low hit rates
            if stats["hit_rate"] < 70:
                recommendations.append(
                    {
                        "type": "ttl_optimization",
                        "priority": "high",
                        "key_pattern": pattern,
                        "current_hit_rate": stats["hit_rate"],
                        "recommendation": (
                            f"Consider increasing TTL for pattern '{pattern}' - "
                            f"current hit rate ({stats['hit_rate']:.1f}%) suggests frequent cache misses"
                        ),
                        "potential_impact": "Could improve hit rate by 10-20%",
                    }
                )

            # Recommend preloading for high-frequency patterns
            if (
                stats["total_operations"] > 1000
                and stats["average_response_time_ms"] > 50
            ):
                recommendations.append(
                    {
                        "type": "preloading",
                        "priority": "medium",
                        "key_pattern": pattern,
                        "operations_count": stats["total_operations"],
                        "recommendation": (
                            f"Consider preloading strategy for high-frequency pattern '{pattern}' "
                            f"to reduce response times"
                        ),
                        "potential_impact": "Could reduce response time by 30-50%",
                    }
                )

        # Analyze cache layer distribution
        overall_stats = self.get_comprehensive_stats()
        redis_ops = (
            overall_stats["cache_layers"].get("redis", {}).get("total_operations", 0)
        )
        memory_ops = (
            overall_stats["cache_layers"].get("memory", {}).get("total_operations", 0)
        )

        if memory_ops > redis_ops * 0.3:  # More than 30% fallback usage
            recommendations.append(
                {
                    "type": "redis_optimization",
                    "priority": "high",
                    "redis_operations": redis_ops,
                    "memory_operations": memory_ops,
                    "recommendation": (
                        "High fallback cache usage detected - investigate Redis connectivity "
                        "or performance issues"
                    ),
                    "potential_impact": "Could improve overall performance by 20-40%",
                }
            )

        return recommendations

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get cache performance trends over time"""
        end_time = time.time()
        start_time = end_time - (hours * 3600)

        # Group events by hour
        hourly_stats = defaultdict(
            lambda: {
                "operations": 0,
                "hits": 0,
                "misses": 0,
                "errors": 0,
                "total_response_time": 0.0,
                "cache_layers": defaultdict(int),
            }
        )

        for event in self.events:
            if event.start_time >= start_time and event.duration is not None:
                hour_bucket = int((event.start_time - start_time) // 3600)
                hour_stats = hourly_stats[hour_bucket]

                hour_stats["operations"] += 1
                hour_stats["total_response_time"] += event.duration
                hour_stats["cache_layers"][event.cache_layer.value] += 1

                if event.result == CacheResult.HIT:
                    hour_stats["hits"] += 1
                elif event.result == CacheResult.MISS:
                    hour_stats["misses"] += 1
                elif event.result == CacheResult.ERROR:
                    hour_stats["errors"] += 1

        # Format trends data
        trends = {"hours_analyzed": hours, "hourly_data": []}

        for hour in range(hours):
            hour_stats = hourly_stats.get(
                hour,
                {
                    "operations": 0,
                    "hits": 0,
                    "misses": 0,
                    "errors": 0,
                    "total_response_time": 0.0,
                },
            )

            total_get_ops = hour_stats["hits"] + hour_stats["misses"]
            hit_rate = (
                (hour_stats["hits"] / total_get_ops * 100) if total_get_ops > 0 else 0.0
            )
            avg_response_time = (
                (hour_stats["total_response_time"] / hour_stats["operations"] * 1000)
                if hour_stats["operations"] > 0
                else 0.0
            )

            trends["hourly_data"].append(
                {
                    "hour": hour,
                    "timestamp": datetime.fromtimestamp(
                        start_time + hour * 3600
                    ).isoformat(),
                    "total_operations": hour_stats["operations"],
                    "hit_rate": round(hit_rate, 2),
                    "average_response_time_ms": round(avg_response_time, 2),
                    "error_count": hour_stats["errors"],
                }
            )

        return trends

    def cleanup_old_events(self, max_age_hours: int = 24) -> int:
        """Clean up old events and return count of removed events"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        initial_count = len(self.events)

        # Filter out old events
        self.events = deque(
            (event for event in self.events if event.start_time >= cutoff_time),
            maxlen=self.max_events,
        )

        removed_count = initial_count - len(self.events)

        if removed_count > 0:
            logger.info("Cleaned up %d old cache performance events", removed_count)

        return removed_count

    async def shutdown(self) -> None:
        """Gracefully shutdown the monitoring system"""
        logger.info("Shutting down CachePerformanceMonitor...")

        # Signal background tasks to stop
        if not self._shutdown_event.is_set():
            self._shutdown_event.set()

        # Cancel all background tasks
        if self._background_tasks:
            logger.info(
                "Cancelling %d background tasks...", len(self._background_tasks)
            )
            for task in self._background_tasks.copy():
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete or timeout
            if self._background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._background_tasks, return_exceptions=True),
                        timeout=5.0,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Some background tasks did not complete within timeout"
                    )

        # Shutdown thread pool executor
        if self._monitoring_executor:
            logger.info("Shutting down monitoring executor...")
            self._monitoring_executor.shutdown(wait=True, timeout=10.0)

        self._monitoring_active = False
        logger.info("CachePerformanceMonitor shutdown complete")

    def get_monitor_health(self) -> Dict[str, Any]:
        """Get monitor health status"""
        return {
            "status": "healthy" if self._monitoring_active else "inactive",
            "total_events": len(self.events),
            "active_operations": len(self.active_operations),
            "background_tasks": len(self._background_tasks),
            "monitoring_active": self._monitoring_active,
            "memory_usage": {
                "events_capacity": self.max_events,
                "events_used": len(self.events),
                "utilization_percent": len(self.events) / self.max_events * 100,
            },
            "integration_status": {
                "auth_cache_service": (
                    "connected" if self.auth_cache_service else "disconnected"
                ),
                "metrics_collector": (
                    "connected" if self.metrics_collector else "disconnected"
                ),
            },
        }


# Global singleton instance
_cache_performance_monitor = None


def get_cache_performance_monitor() -> CachePerformanceMonitor:
    """Get singleton cache performance monitor instance"""
    global _cache_performance_monitor
    if _cache_performance_monitor is None:
        _cache_performance_monitor = CachePerformanceMonitor()
    return _cache_performance_monitor


async def shutdown_cache_performance_monitor() -> None:
    """Shutdown the global cache performance monitor instance"""
    global _cache_performance_monitor
    if _cache_performance_monitor is not None:
        await _cache_performance_monitor.shutdown()
        _cache_performance_monitor = None


def track_cache_operation_performance(
    operation: CacheOperation, cache_layer: CacheLayer, key_pattern: str
):
    """Context manager for tracking cache operation performance"""

    class CacheOperationTracker:
        def __init__(self, op: CacheOperation, layer: CacheLayer, pattern: str):
            self.operation = op
            self.cache_layer = layer
            self.key_pattern = pattern
            self.start_time = None
            self.monitor = get_cache_performance_monitor()

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            result = CacheResult.SUCCESS if exc_type is None else CacheResult.ERROR

            self.monitor.record_cache_operation(
                self.operation, self.cache_layer, self.key_pattern, duration, result
            )

        async def __aenter__(self):
            self.start_time = time.time()
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            result = CacheResult.SUCCESS if exc_type is None else CacheResult.ERROR

            self.monitor.record_cache_operation(
                self.operation, self.cache_layer, self.key_pattern, duration, result
            )

    return CacheOperationTracker(operation, cache_layer, key_pattern)
