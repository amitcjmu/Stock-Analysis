"""
Metrics initialization logic for performance metrics collection.

This module contains the initialization methods for setting up default
metrics for authentication, cache, and system monitoring. Separated from
the main collector to keep modules under 400 lines.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .collector import PerformanceMetricsCollector


def initialize_auth_metrics(collector: "PerformanceMetricsCollector") -> None:
    """Initialize authentication-related metrics"""

    # Authentication response time histograms
    collector.register_histogram(
        "auth_login_duration_seconds",
        "Time taken for user login operations",
        labels=["status", "auth_method"],
    )

    collector.register_histogram(
        "auth_session_validation_duration_seconds",
        "Time taken for session validation",
        labels=["status", "cache_hit"],
    )

    collector.register_histogram(
        "auth_context_switch_duration_seconds",
        "Time taken for client/engagement context switching",
        labels=["context_type", "status"],
    )

    collector.register_histogram(
        "auth_token_refresh_duration_seconds",
        "Time taken for token refresh operations",
        labels=["status"],
    )

    # Authentication operation counters
    collector.register_counter(
        "auth_login_attempts_total",
        "Total number of login attempts",
        labels=["status", "auth_method"],
    )

    collector.register_counter(
        "auth_login_failures_total",
        "Total number of failed login attempts",
        labels=["reason", "auth_method"],
    )

    collector.register_counter(
        "auth_session_validations_total",
        "Total number of session validations",
        labels=["status", "cache_hit"],
    )

    collector.register_counter(
        "auth_context_switches_total",
        "Total number of context switches",
        labels=["context_type", "status"],
    )

    # Authentication state gauges
    collector.register_gauge(
        "auth_active_sessions", "Number of currently active user sessions"
    )

    collector.register_gauge(
        "auth_concurrent_logins", "Number of concurrent login operations"
    )

    collector.register_gauge(
        "auth_session_avg_duration_seconds", "Average session duration in seconds"
    )


def initialize_cache_metrics(collector: "PerformanceMetricsCollector") -> None:
    """Initialize cache performance metrics"""

    # Cache operation histograms
    collector.register_histogram(
        "cache_operation_duration_seconds",
        "Time taken for cache operations",
        labels=["operation", "cache_type", "status"],
    )

    # Cache operation counters
    collector.register_counter(
        "cache_operations_total",
        "Total cache operations",
        labels=["operation", "cache_type", "result"],
    )

    collector.register_counter(
        "cache_hits_total", "Total cache hits", labels=["cache_type", "key_pattern"]
    )

    collector.register_counter(
        "cache_misses_total",
        "Total cache misses",
        labels=["cache_type", "key_pattern"],
    )

    collector.register_counter(
        "cache_errors_total",
        "Total cache errors",
        labels=["cache_type", "operation", "error_type"],
    )

    # Cache state gauges
    collector.register_gauge(
        "cache_hit_ratio", "Cache hit ratio by cache layer", labels=["cache_type"]
    )

    collector.register_gauge(
        "cache_size_bytes", "Current cache size in bytes", labels=["cache_type"]
    )

    collector.register_gauge(
        "cache_utilization_percent",
        "Cache utilization percentage",
        labels=["cache_type"],
    )

    collector.register_gauge(
        "cache_evictions_total",
        "Total cache evictions",
        labels=["cache_type", "reason"],
    )


def initialize_system_metrics(collector: "PerformanceMetricsCollector") -> None:
    """Initialize system resource metrics"""

    # System resource gauges
    collector.register_gauge(
        "system_memory_usage_bytes", "System memory usage in bytes", labels=["type"]
    )

    collector.register_gauge("system_cpu_usage_percent", "System CPU usage percentage")

    collector.register_gauge(
        "system_active_connections",
        "Number of active system connections",
        labels=["type"],
    )

    collector.register_gauge(
        "system_queue_size", "Size of system queues", labels=["queue_type"]
    )

    # Performance threshold gauges
    collector.register_gauge(
        "performance_threshold_breaches_total",
        "Number of performance threshold breaches",
        labels=["metric_type", "threshold_type"],
    )
