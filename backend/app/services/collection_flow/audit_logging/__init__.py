"""
Audit Logging and Monitoring Services for Collection Flow

This module provides comprehensive audit logging and monitoring capabilities
for the Collection Flow system, tracking all activities, changes, and events.

This is a modularized version that maintains 100% backward compatibility
with the original audit_logging.py file.
"""

# Import all public classes and functions from submodules
from .base import AuditEvent, AuditEventType, AuditSeverity, MonitoringMetrics
from .formatters import AuditLogFormatter
from .handlers import AlertHandler, MonitoringService
from .logger import AuditLoggingService
from .storage import AuditLogStorage
from .utils import (
    assess_flow_health,
    calculate_average_confidence_score,
    calculate_average_duration,
    calculate_average_quality_score,
    calculate_error_rate,
    calculate_event_rate,
    calculate_phase_durations,
    count_flows,
    count_flows_by_status,
)

# Maintain backward compatibility - export everything that was previously available
__all__ = [
    # Main service classes (original public API)
    "AuditLoggingService",
    "MonitoringService",
    # Enums and data classes (original public API)
    "AuditEventType",
    "AuditSeverity",
    "AuditEvent",
    "MonitoringMetrics",
    # Additional classes now available
    "AuditLogStorage",
    "AuditLogFormatter",
    "AlertHandler",
    # Utility functions now available
    "count_flows",
    "count_flows_by_status",
    "calculate_average_duration",
    "calculate_average_quality_score",
    "calculate_average_confidence_score",
    "calculate_event_rate",
    "calculate_error_rate",
    "calculate_phase_durations",
    "assess_flow_health",
]
