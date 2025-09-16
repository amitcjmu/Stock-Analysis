"""
Performance Metrics Collector Module

Comprehensive metrics collection system for auth performance optimization monitoring.
Provides Prometheus-compatible metrics, performance tracking, and observability for
authentication operations, cache performance, and system health.

This module maintains 100% backward compatibility with the original single-file
implementation while providing improved modularity and maintainability.

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

# Import all base types and enums
from .base import (
    MetricType,
    MetricUnit,
    MetricSample,
    HistogramBucket,
)

# Import all aggregator classes
from .aggregators import (
    Counter,
    Gauge,
    Histogram,
)

# Import the main collector class and singleton function
from .collector import (
    PerformanceMetricsCollector,
    get_metrics_collector,
)

# Import utility functions and decorators
from .utils import (
    track_auth_performance,
    track_cache_performance,
)

# Import exporters for external access if needed
from .exporters import (
    PrometheusExporter,
    PerformanceSummaryExporter,
)

# Import storage for external access if needed
from .storage import (
    MetricsStorage,
)

# Import initializers for external access if needed
from .initializers import (
    initialize_auth_metrics,
    initialize_cache_metrics,
    initialize_system_metrics,
)

# Maintain backward compatibility - export all public symbols
__all__ = [
    # Base types and enums
    "MetricType",
    "MetricUnit",
    "MetricSample",
    "HistogramBucket",
    # Aggregator classes
    "Counter",
    "Gauge",
    "Histogram",
    # Main collector
    "PerformanceMetricsCollector",
    "get_metrics_collector",
    # Utility decorators
    "track_auth_performance",
    "track_cache_performance",
    # Exporters
    "PrometheusExporter",
    "PerformanceSummaryExporter",
    # Storage
    "MetricsStorage",
    # Initializers
    "initialize_auth_metrics",
    "initialize_cache_metrics",
    "initialize_system_metrics",
]
