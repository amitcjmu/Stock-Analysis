"""
Comprehensive Performance Monitoring System for Auth Optimization

This package provides a complete performance monitoring and analytics solution
for tracking the effectiveness of authentication performance optimizations.

Key Components:
- PerformanceMetricsCollector: Prometheus-compatible metrics collection
- AuthPerformanceMonitor: Authentication flow performance tracking
- CachePerformanceMonitor: Multi-layer cache performance monitoring
- SystemHealthDashboard: Real-time system health visualization
- PerformanceAnalyticsEngine: Advanced analytics and optimization recommendations
- GrafanaDashboardConfig: Pre-configured observability dashboards

Performance Targets (from design document):
- Login page load: 200-500ms (from 2-4 seconds) - 80-90% improvement
- Authentication flow: 300-600ms (from 1.5-3 seconds) - 75-85% improvement
- Context switching: 100-300ms (from 1-2 seconds) - 85-90% improvement

Usage:
    from app.services.monitoring import (
        get_metrics_collector,
        get_auth_performance_monitor,
        get_cache_performance_monitor,
        get_system_health_dashboard,
        get_performance_analytics_engine,
        get_grafana_dashboard_config
    )

    # Track authentication performance
    auth_monitor = get_auth_performance_monitor()
    operation_id = auth_monitor.start_operation(AuthOperation.LOGIN, user_id="user123")
    # ... perform login operation ...
    auth_monitor.end_operation(operation_id, AuthStatus.SUCCESS)

    # Get comprehensive performance analytics
    analytics = get_performance_analytics_engine()
    report = await analytics.generate_performance_report()
"""

# Existing monitoring components
from .auth_performance_monitor import (
    AuthOperation,
    AuthPerformanceMonitor,
    AuthStatus,
    PerformanceThreshold,
    auth_performance_decorator,
    get_auth_performance_monitor,
    track_auth_operation,
)
from .cache_performance_monitor import (
    CacheLayer,
    CacheOperation,
    CachePerformanceMonitor,
    CacheResult,
    get_cache_performance_monitor,
    track_cache_operation_performance,
)
from .grafana_dashboard_config import (
    GrafanaDashboardConfig,
    get_grafana_dashboard_config,
)
from .performance_analytics_engine import (
    BottleneckType,
    ImpactLevel,
    PerformanceAnalyticsEngine,
    TrendDirection,
    get_performance_analytics_engine,
)

# New performance monitoring components
from .performance_metrics_collector import (
    MetricType,
    PerformanceMetricsCollector,
    get_metrics_collector,
    track_auth_performance,
    track_cache_performance,
)
from .service_health_manager import ServiceHealthManager, get_service_health_manager
from .system_health_dashboard import (
    AlertSeverity,
    HealthStatus,
    SystemHealthDashboard,
    get_system_health_dashboard,
)

__all__ = [
    # Existing components
    "ServiceHealthManager",
    "get_service_health_manager",
    # Core monitoring components
    "get_metrics_collector",
    "get_auth_performance_monitor",
    "get_cache_performance_monitor",
    "get_system_health_dashboard",
    "get_performance_analytics_engine",
    "get_grafana_dashboard_config",
    # Classes
    "PerformanceMetricsCollector",
    "AuthPerformanceMonitor",
    "CachePerformanceMonitor",
    "SystemHealthDashboard",
    "PerformanceAnalyticsEngine",
    "GrafanaDashboardConfig",
    # Enums and types
    "MetricType",
    "AuthOperation",
    "AuthStatus",
    "PerformanceThreshold",
    "CacheLayer",
    "CacheOperation",
    "CacheResult",
    "HealthStatus",
    "AlertSeverity",
    "TrendDirection",
    "BottleneckType",
    "ImpactLevel",
    # Decorators and utilities
    "track_auth_performance",
    "track_cache_performance",
    "track_auth_operation",
    "auth_performance_decorator",
    "track_cache_operation_performance",
]
