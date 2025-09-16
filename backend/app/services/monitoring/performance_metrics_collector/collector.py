"""
Main performance metrics collector implementation.

This module contains the core PerformanceMetricsCollector class that orchestrates
metric collection, storage, and export. It provides the primary interface for
metrics collection operations.
"""

import threading
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .aggregators import Counter, Gauge, Histogram
from .exporters import PerformanceSummaryExporter, PrometheusExporter
from .initializers import (
    initialize_auth_metrics,
    initialize_cache_metrics,
    initialize_system_metrics,
)
from .storage import MetricsStorage

logger = get_logger(__name__)


class PerformanceMetricsCollector:
    """
    Comprehensive performance metrics collector for auth optimization monitoring.

    Provides centralized metric collection, storage, and export capabilities with
    minimal performance overhead and integration with existing monitoring systems.
    """

    def __init__(self, max_samples: int = 10000, cleanup_interval: int = 300):
        self.max_samples = max_samples
        self.cleanup_interval = cleanup_interval

        # Metric registries
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}

        # Thread-safe access
        self._lock = threading.Lock()

        # Storage and exporters
        self._storage = MetricsStorage(max_samples, cleanup_interval)
        self._prometheus_exporter = PrometheusExporter()
        self._summary_exporter = PerformanceSummaryExporter()

        logger.info(
            "PerformanceMetricsCollector initialized with max_samples=%d", max_samples
        )

        # Initialize core metrics using external initializers
        initialize_auth_metrics(self)
        initialize_cache_metrics(self)
        initialize_system_metrics(self)

    def register_counter(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> Counter:
        """Register a new counter metric"""
        with self._lock:
            if name in self._counters:
                return self._counters[name]

            counter = Counter(name, description, labels)
            self._counters[name] = counter
            logger.debug("Registered counter metric: %s", name)
            return counter

    def register_gauge(
        self, name: str, description: str, labels: Optional[List[str]] = None
    ) -> Gauge:
        """Register a new gauge metric"""
        with self._lock:
            if name in self._gauges:
                return self._gauges[name]

            gauge = Gauge(name, description, labels)
            self._gauges[name] = gauge
            logger.debug("Registered gauge metric: %s", name)
            return gauge

    def register_histogram(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ) -> Histogram:
        """Register a new histogram metric"""
        with self._lock:
            if name in self._histograms:
                return self._histograms[name]

            histogram = Histogram(name, description, labels, buckets)
            self._histograms[name] = histogram
            logger.debug("Registered histogram metric: %s", name)
            return histogram

    def get_counter(self, name: str) -> Optional[Counter]:
        """Get counter metric by name"""
        with self._lock:
            return self._counters.get(name)

    def get_gauge(self, name: str) -> Optional[Gauge]:
        """Get gauge metric by name"""
        with self._lock:
            return self._gauges.get(name)

    def get_histogram(self, name: str) -> Optional[Histogram]:
        """Get histogram metric by name"""
        with self._lock:
            return self._histograms.get(name)

    def record_auth_login_duration(
        self, duration: float, status: str = "success", auth_method: str = "password"
    ) -> None:
        """Record authentication login duration"""
        histogram = self.get_histogram("auth_login_duration_seconds")
        if histogram:
            histogram.observe(duration, {"status": status, "auth_method": auth_method})

        counter = self.get_counter("auth_login_attempts_total")
        if counter:
            counter.inc(labels={"status": status, "auth_method": auth_method})

    def record_session_validation_duration(
        self, duration: float, status: str = "success", cache_hit: bool = False
    ) -> None:
        """Record session validation duration"""
        histogram = self.get_histogram("auth_session_validation_duration_seconds")
        if histogram:
            histogram.observe(duration, {"status": status, "cache_hit": str(cache_hit)})

        counter = self.get_counter("auth_session_validations_total")
        if counter:
            counter.inc(labels={"status": status, "cache_hit": str(cache_hit)})

    def record_context_switch_duration(
        self, duration: float, context_type: str = "client", status: str = "success"
    ) -> None:
        """Record context switching duration"""
        histogram = self.get_histogram("auth_context_switch_duration_seconds")
        if histogram:
            histogram.observe(
                duration, {"context_type": context_type, "status": status}
            )

        counter = self.get_counter("auth_context_switches_total")
        if counter:
            counter.inc(labels={"context_type": context_type, "status": status})

    def record_cache_operation(
        self,
        operation: str,
        duration: float,
        cache_type: str = "redis",
        status: str = "success",
        result: str = "hit",
    ) -> None:
        """Record cache operation performance"""
        histogram = self.get_histogram("cache_operation_duration_seconds")
        if histogram:
            histogram.observe(
                duration,
                {"operation": operation, "cache_type": cache_type, "status": status},
            )

        counter = self.get_counter("cache_operations_total")
        if counter:
            counter.inc(
                labels={
                    "operation": operation,
                    "cache_type": cache_type,
                    "result": result,
                }
            )

        # Update hit/miss counters
        if result == "hit":
            hit_counter = self.get_counter("cache_hits_total")
            if hit_counter:
                hit_counter.inc(
                    labels={"cache_type": cache_type, "key_pattern": "auth"}
                )
        elif result == "miss":
            miss_counter = self.get_counter("cache_misses_total")
            if miss_counter:
                miss_counter.inc(
                    labels={"cache_type": cache_type, "key_pattern": "auth"}
                )

    def update_cache_hit_ratio(self, cache_type: str, hit_ratio: float) -> None:
        """Update cache hit ratio gauge"""
        gauge = self.get_gauge("cache_hit_ratio")
        if gauge:
            gauge.set(hit_ratio, {"cache_type": cache_type})

    def update_active_sessions(self, count: int) -> None:
        """Update active sessions gauge"""
        gauge = self.get_gauge("auth_active_sessions")
        if gauge:
            gauge.set(count)

    def update_system_resource_usage(
        self, memory_bytes: int, cpu_percent: float, active_connections: int
    ) -> None:
        """Update system resource usage gauges"""
        memory_gauge = self.get_gauge("system_memory_usage_bytes")
        if memory_gauge:
            memory_gauge.set(memory_bytes, {"type": "total"})

        cpu_gauge = self.get_gauge("system_cpu_usage_percent")
        if cpu_gauge:
            cpu_gauge.set(cpu_percent)

        conn_gauge = self.get_gauge("system_active_connections")
        if conn_gauge:
            conn_gauge.set(active_connections, {"type": "http"})

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return self._summary_exporter.export_performance_summary(
            self._counters, self._gauges, self._histograms
        )

    def export_prometheus_metrics(self) -> str:
        """Export all metrics in Prometheus format"""
        return self._prometheus_exporter.export_metrics(
            self._counters, self._gauges, self._histograms
        )

    def cleanup_old_metrics(self) -> None:
        """Clean up old metric samples to prevent memory growth"""
        self._storage.cleanup_old_metrics()

    def get_collector_stats(self) -> Dict[str, Any]:
        """Get collector performance statistics"""
        stats = {
            "registered_metrics": {
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms),
            },
        }

        # Add storage stats
        stats.update(self._storage.get_storage_stats())

        return stats


# Global singleton instance
_metrics_collector = None


def get_metrics_collector() -> PerformanceMetricsCollector:
    """Get singleton metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PerformanceMetricsCollector()
    return _metrics_collector
