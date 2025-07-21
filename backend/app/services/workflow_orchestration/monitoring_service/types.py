"""
Monitoring Service Types and Enums
Team C1 - Task C1.6

Common types and enumerations used throughout the workflow monitoring system.
"""

from enum import Enum


class MonitoringLevel(Enum):
    """Monitoring detail levels"""
    BASIC = "basic"              # Basic status and health
    STANDARD = "standard"        # Standard metrics and progress
    DETAILED = "detailed"        # Detailed phase and component metrics
    COMPREHENSIVE = "comprehensive"  # Full diagnostic and performance data


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics tracked"""
    PERFORMANCE = "performance"
    QUALITY = "quality"
    RESOURCE = "resource"
    BUSINESS = "business"
    OPERATIONAL = "operational"


class HealthStatus(Enum):
    """Health status indicators"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"