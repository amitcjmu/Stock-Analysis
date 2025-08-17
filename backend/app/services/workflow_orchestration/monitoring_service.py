"""
Workflow Monitoring and Progress Tracking Service
Team C1 - Task C1.6

BACKWARD COMPATIBILITY MODULE - This module now imports from the modularized
monitoring_service package to maintain existing API compatibility.

The original 807-line monolithic service has been modularized into:
- monitoring_service/types.py - Enums and type definitions
- monitoring_service/models.py - Data models and dataclasses
- monitoring_service/alerts.py - Alert management and evaluation
- monitoring_service/metrics.py - Metrics collection and analysis
- monitoring_service/progress.py - Progress tracking and milestones
- monitoring_service/health.py - Health monitoring and assessment
- monitoring_service/analytics.py - Analytics and insights generation
- monitoring_service/service.py - Main orchestration service

All existing imports and usage patterns remain unchanged for backward compatibility.
"""

# Re-export all public interfaces from the modularized package
from .monitoring_service import (  # Component managers (available if needed);
    # Data models; Types and enums; Main service class
    Alert,
    AlertDefinition,
    AlertManager,
    AlertSeverity,
    AnalyticsEngine,
    HealthMonitor,
    HealthStatus,
    MetricPoint,
    MetricsCollector,
    MetricType,
    MonitoringLevel,
    MonitoringSession,
    PerformanceMetrics,
    ProgressMilestone,
    ProgressTracker,
    WorkflowMonitoringService,
    WorkflowProgress,
)

# Maintain the same __all__ list for backward compatibility
__all__ = [
    "WorkflowMonitoringService",
    "MonitoringLevel",
    "AlertSeverity",
    "MetricType",
    "HealthStatus",
    "MetricPoint",
    "ProgressMilestone",
    "WorkflowProgress",
    "PerformanceMetrics",
    "AlertDefinition",
    "Alert",
    "MonitoringSession",
    "AlertManager",
    "MetricsCollector",
    "ProgressTracker",
    "HealthMonitor",
    "AnalyticsEngine",
]

# CC: Modularization completed - original 807 LOC with 53 functions and 12 classes
# has been restructured into 8 focused modules while maintaining full backward compatibility
