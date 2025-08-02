"""
Performance Metrics Collector

Comprehensive metrics collection system for auth performance optimization monitoring.
Provides Prometheus-compatible metrics, performance tracking, and observability for
authentication operations, cache performance, and system health.

Key Features:
- Authentication flow performance tracking (login, session validation, context switching)
- Cache performance metrics (hit/miss ratios, response times, utilization)
- System resource monitoring (CPU, memory, network I/O)
- Real-time metric collection with minimal overhead
- Histogram tracking for response time analysis
- Custom metric types for business-specific KPIs
- Integration with existing monitoring infrastructure

Metrics Categories:
1. Authentication Metrics: Login times, session validation, token refresh
2. Cache Metrics: Hit rates, response times, cache size utilization
3. Context Metrics: Client/engagement switching performance
4. Error Metrics: Failure rates, retry counts, fallback activation
5. Resource Metrics: Memory usage, CPU usage, network I/O
"""

import asyncio
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from concurrent.futures import ThreadPoolExecutor

from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricType(str, Enum):
    """Metric type enumeration following Prometheus conventions"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricUnit(str, Enum):
    """Standard metric units"""

    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    BYTES = "bytes"
    PERCENT = "percent"
    COUNT = "count"
    RATE = "rate"


@dataclass
class MetricSample:
    """Individual metric sample with timestamp and labels"""

    value: Union[float, int]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class HistogramBucket:
    """Histogram bucket for response time distribution tracking"""

    upper_bound: float
    count: int = 0

    def increment(self):
        self.count += 1


class Counter:
    """Counter metric - monotonically increasing value"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment counter by amount"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += amount

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from labels"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_samples(self) -> List[MetricSample]:
        """Get all samples for Prometheus export"""
        samples = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = {}
                if label_key:
                    for pair in label_key.split(","):
                        k, v = pair.split("=", 1)
                        labels[k] = v
                samples.append(
                    MetricSample(value=value, timestamp=time.time(), labels=labels)
                )
        return samples


class Gauge:
    """Gauge metric - value that can go up and down"""

    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.labels = labels or []
        self._values: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge to specific value"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment gauge by amount"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement gauge by amount"""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] -= amount

    def get_value(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values.get(label_key, 0.0)

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from labels"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_samples(self) -> List[MetricSample]:
        """Get all samples for Prometheus export"""
        samples = []
        with self._lock:
            for label_key, value in self._values.items():
                labels = {}
                if label_key:
                    for pair in label_key.split(","):
                        k, v = pair.split("=", 1)
                        labels[k] = v
                samples.append(
                    MetricSample(value=value, timestamp=time.time(), labels=labels)
                )
        return samples


class Histogram:
    """Histogram metric for response time distribution tracking"""

    # Default buckets optimized for auth performance (in seconds)
    DEFAULT_BUCKETS = [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")]

    def __init__(
        self,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[List[float]] = None,
    ):
        self.name = name
        self.description = description
        self.labels = labels or []
        self.buckets = buckets or self.DEFAULT_BUCKETS

        # Initialize buckets for each label combination
        self._buckets: Dict[str, List[HistogramBucket]] = defaultdict(
            lambda: [HistogramBucket(b) for b in self.buckets]
        )
        self._counts: Dict[str, int] = defaultdict(int)
        self._sums: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record an observation in the histogram"""
        label_key = self._make_label_key(labels)

        with self._lock:
            # Update count and sum
            self._counts[label_key] += 1
            self._sums[label_key] += value

            # Update buckets
            for bucket in self._buckets[label_key]:
                if value <= bucket.upper_bound:
                    bucket.increment()

    def get_count(self, labels: Optional[Dict[str, str]] = None) -> int:
        """Get total number of observations"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._counts.get(label_key, 0)

    def get_sum(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get sum of all observed values"""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._sums.get(label_key, 0.0)

    def get_average(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get average of all observed values"""
        count = self.get_count(labels)
        if count == 0:
            return 0.0
        return self.get_sum(labels) / count

    def get_percentile(
        self, percentile: float, labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Estimate percentile from histogram buckets"""
        label_key = self._make_label_key(labels)
        total_count = self.get_count(labels)

        if total_count == 0:
            return 0.0

        target_count = total_count * (percentile / 100.0)
        cumulative_count = 0

        with self._lock:
            buckets = self._buckets.get(label_key, [])
            for i, bucket in enumerate(buckets):
                cumulative_count += bucket.count
                if cumulative_count >= target_count:
                    if i == 0:
                        return bucket.upper_bound
                    # Linear interpolation between buckets
                    prev_bucket = buckets[i - 1]
                    prev_count = cumulative_count - bucket.count
                    ratio = (
                        (target_count - prev_count) / bucket.count
                        if bucket.count > 0
                        else 0
                    )
                    return prev_bucket.upper_bound + ratio * (
                        bucket.upper_bound - prev_bucket.upper_bound
                    )

        return self.buckets[-1] if self.buckets else 0.0

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from labels"""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def get_samples(self) -> List[MetricSample]:
        """Get all samples for Prometheus export"""
        samples = []
        with self._lock:
            for label_key in self._counts.keys():
                labels = {}
                if label_key:
                    for pair in label_key.split(","):
                        k, v = pair.split("=", 1)
                        labels[k] = v

                # Add count and sum samples
                samples.append(
                    MetricSample(
                        value=self._counts[label_key],
                        timestamp=time.time(),
                        labels={**labels, "__name__": f"{self.name}_count"},
                    )
                )
                samples.append(
                    MetricSample(
                        value=self._sums[label_key],
                        timestamp=time.time(),
                        labels={**labels, "__name__": f"{self.name}_sum"},
                    )
                )

                # Add bucket samples
                for bucket in self._buckets[label_key]:
                    bucket_labels = {**labels, "le": str(bucket.upper_bound)}
                    samples.append(
                        MetricSample(
                            value=bucket.count,
                            timestamp=time.time(),
                            labels={**bucket_labels, "__name__": f"{self.name}_bucket"},
                        )
                    )

        return samples


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

        # Background cleanup
        self._cleanup_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="metrics-cleanup"
        )
        self._last_cleanup = time.time()

        # Performance tracking
        self._collection_times = deque(maxlen=1000)

        logger.info(
            "PerformanceMetricsCollector initialized with max_samples=%d", max_samples
        )

        # Initialize core authentication metrics
        self._initialize_auth_metrics()
        self._initialize_cache_metrics()
        self._initialize_system_metrics()

    def _initialize_auth_metrics(self) -> None:
        """Initialize authentication-related metrics"""

        # Authentication response time histograms
        self.register_histogram(
            "auth_login_duration_seconds",
            "Time taken for user login operations",
            labels=["status", "auth_method"],
        )

        self.register_histogram(
            "auth_session_validation_duration_seconds",
            "Time taken for session validation",
            labels=["status", "cache_hit"],
        )

        self.register_histogram(
            "auth_context_switch_duration_seconds",
            "Time taken for client/engagement context switching",
            labels=["context_type", "status"],
        )

        self.register_histogram(
            "auth_token_refresh_duration_seconds",
            "Time taken for token refresh operations",
            labels=["status"],
        )

        # Authentication operation counters
        self.register_counter(
            "auth_login_attempts_total",
            "Total number of login attempts",
            labels=["status", "auth_method"],
        )

        self.register_counter(
            "auth_login_failures_total",
            "Total number of failed login attempts",
            labels=["reason", "auth_method"],
        )

        self.register_counter(
            "auth_session_validations_total",
            "Total number of session validations",
            labels=["status", "cache_hit"],
        )

        self.register_counter(
            "auth_context_switches_total",
            "Total number of context switches",
            labels=["context_type", "status"],
        )

        # Authentication state gauges
        self.register_gauge(
            "auth_active_sessions", "Number of currently active user sessions"
        )

        self.register_gauge(
            "auth_concurrent_logins", "Number of concurrent login operations"
        )

        self.register_gauge(
            "auth_session_avg_duration_seconds", "Average session duration in seconds"
        )

    def _initialize_cache_metrics(self) -> None:
        """Initialize cache performance metrics"""

        # Cache operation histograms
        self.register_histogram(
            "cache_operation_duration_seconds",
            "Time taken for cache operations",
            labels=["operation", "cache_type", "status"],
        )

        # Cache operation counters
        self.register_counter(
            "cache_operations_total",
            "Total cache operations",
            labels=["operation", "cache_type", "result"],
        )

        self.register_counter(
            "cache_hits_total", "Total cache hits", labels=["cache_type", "key_pattern"]
        )

        self.register_counter(
            "cache_misses_total",
            "Total cache misses",
            labels=["cache_type", "key_pattern"],
        )

        self.register_counter(
            "cache_errors_total",
            "Total cache errors",
            labels=["cache_type", "operation", "error_type"],
        )

        # Cache state gauges
        self.register_gauge(
            "cache_hit_ratio", "Cache hit ratio by cache layer", labels=["cache_type"]
        )

        self.register_gauge(
            "cache_size_bytes", "Current cache size in bytes", labels=["cache_type"]
        )

        self.register_gauge(
            "cache_utilization_percent",
            "Cache utilization percentage",
            labels=["cache_type"],
        )

        self.register_gauge(
            "cache_evictions_total",
            "Total cache evictions",
            labels=["cache_type", "reason"],
        )

    def _initialize_system_metrics(self) -> None:
        """Initialize system resource metrics"""

        # System resource gauges
        self.register_gauge(
            "system_memory_usage_bytes", "System memory usage in bytes", labels=["type"]
        )

        self.register_gauge("system_cpu_usage_percent", "System CPU usage percentage")

        self.register_gauge(
            "system_active_connections",
            "Number of active system connections",
            labels=["type"],
        )

        self.register_gauge(
            "system_queue_size", "Size of system queues", labels=["queue_type"]
        )

        # Performance threshold gauges
        self.register_gauge(
            "performance_threshold_breaches_total",
            "Number of performance threshold breaches",
            labels=["metric_type", "threshold_type"],
        )

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
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_count": {
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms),
            },
            "auth_performance": {},
            "cache_performance": {},
            "system_performance": {},
        }

        # Authentication performance summary
        login_histogram = self.get_histogram("auth_login_duration_seconds")
        if login_histogram:
            summary["auth_performance"]["login"] = {
                "average_duration_ms": login_histogram.get_average() * 1000,
                "p95_duration_ms": login_histogram.get_percentile(95) * 1000,
                "p99_duration_ms": login_histogram.get_percentile(99) * 1000,
                "total_attempts": login_histogram.get_count(),
            }

        session_histogram = self.get_histogram(
            "auth_session_validation_duration_seconds"
        )
        if session_histogram:
            summary["auth_performance"]["session_validation"] = {
                "average_duration_ms": session_histogram.get_average() * 1000,
                "p95_duration_ms": session_histogram.get_percentile(95) * 1000,
                "total_validations": session_histogram.get_count(),
            }

        context_histogram = self.get_histogram("auth_context_switch_duration_seconds")
        if context_histogram:
            summary["auth_performance"]["context_switching"] = {
                "average_duration_ms": context_histogram.get_average() * 1000,
                "p95_duration_ms": context_histogram.get_percentile(95) * 1000,
                "total_switches": context_histogram.get_count(),
            }

        # Cache performance summary
        cache_ops_histogram = self.get_histogram("cache_operation_duration_seconds")
        if cache_ops_histogram:
            summary["cache_performance"]["operations"] = {
                "average_duration_ms": cache_ops_histogram.get_average() * 1000,
                "p95_duration_ms": cache_ops_histogram.get_percentile(95) * 1000,
                "total_operations": cache_ops_histogram.get_count(),
            }

        hit_ratio_gauge = self.get_gauge("cache_hit_ratio")
        if hit_ratio_gauge:
            summary["cache_performance"]["hit_ratio"] = hit_ratio_gauge.get_value()

        # System performance summary
        active_sessions_gauge = self.get_gauge("auth_active_sessions")
        if active_sessions_gauge:
            summary["system_performance"][
                "active_sessions"
            ] = active_sessions_gauge.get_value()

        cpu_gauge = self.get_gauge("system_cpu_usage_percent")
        if cpu_gauge:
            summary["system_performance"]["cpu_usage"] = cpu_gauge.get_value()

        return summary

    def export_prometheus_metrics(self) -> str:
        """Export all metrics in Prometheus format"""
        lines = []

        # Export counters
        for counter in self._counters.values():
            lines.append(f"# HELP {counter.name} {counter.description}")
            lines.append(f"# TYPE {counter.name} counter")
            for sample in counter.get_samples():
                label_str = ""
                if sample.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"
                lines.append(
                    f"{counter.name}{label_str} {sample.value} {int(sample.timestamp * 1000)}"
                )

        # Export gauges
        for gauge in self._gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.description}")
            lines.append(f"# TYPE {gauge.name} gauge")
            for sample in gauge.get_samples():
                label_str = ""
                if sample.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"
                lines.append(
                    f"{gauge.name}{label_str} {sample.value} {int(sample.timestamp * 1000)}"
                )

        # Export histograms
        for histogram in self._histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.description}")
            lines.append(f"# TYPE {histogram.name} histogram")
            for sample in histogram.get_samples():
                metric_name = sample.labels.pop("__name__", histogram.name)
                label_str = ""
                if sample.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in sample.labels.items()]
                    label_str = "{" + ",".join(label_pairs) + "}"
                lines.append(
                    f"{metric_name}{label_str} {sample.value} {int(sample.timestamp * 1000)}"
                )

        return "\n".join(lines)

    def cleanup_old_metrics(self) -> None:
        """Clean up old metric samples to prevent memory growth"""
        if time.time() - self._last_cleanup < self.cleanup_interval:
            return

        start_time = time.time()

        # This is a placeholder for metric cleanup logic
        # In a production system, you might want to:
        # 1. Remove old samples beyond retention period
        # 2. Aggregate old data into larger time buckets
        # 3. Export old data to external storage

        cleanup_duration = time.time() - start_time
        self._collection_times.append(cleanup_duration)
        self._last_cleanup = time.time()

        logger.debug("Metrics cleanup completed in %.3fs", cleanup_duration)

    def get_collector_stats(self) -> Dict[str, Any]:
        """Get collector performance statistics"""
        return {
            "registered_metrics": {
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms),
            },
            "collection_performance": {
                "average_cleanup_time_ms": (
                    sum(self._collection_times) / len(self._collection_times) * 1000
                    if self._collection_times
                    else 0
                ),
                "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat(),
            },
        }


# Global singleton instance
_metrics_collector = None


def get_metrics_collector() -> PerformanceMetricsCollector:
    """Get singleton metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = PerformanceMetricsCollector()
    return _metrics_collector


def track_auth_performance(operation_type: str = "login"):
    """Decorator to automatically track authentication performance"""

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()

                if operation_type == "login":
                    collector.record_auth_login_duration(duration, status)
                elif operation_type == "session_validation":
                    collector.record_session_validation_duration(duration, status)
                elif operation_type == "context_switch":
                    collector.record_context_switch_duration(duration, "client", status)

        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()

                if operation_type == "login":
                    collector.record_auth_login_duration(duration, status)
                elif operation_type == "session_validation":
                    collector.record_session_validation_duration(duration, status)
                elif operation_type == "context_switch":
                    collector.record_context_switch_duration(duration, "client", status)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def track_cache_performance(operation: str = "get", cache_type: str = "redis"):
    """Decorator to automatically track cache performance"""

    def decorator(func: Callable) -> Callable:
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            result_type = "hit"
            try:
                result = func(*args, **kwargs)
                if result is None:
                    result_type = "miss"
                return result
            except Exception:
                status = "error"
                result_type = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()
                collector.record_cache_operation(
                    operation, duration, cache_type, status, result_type
                )

        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            result_type = "hit"
            try:
                result = await func(*args, **kwargs)
                if result is None:
                    result_type = "miss"
                return result
            except Exception:
                status = "error"
                result_type = "error"
                raise
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()
                collector.record_cache_operation(
                    operation, duration, cache_type, status, result_type
                )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
