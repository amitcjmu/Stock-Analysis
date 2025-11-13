"""
Flow Orchestration Module

This module provides modular flow orchestration components for the Master Flow Orchestrator.

IMPORTANT: FlowAuditLogger and FlowStatusManager have been moved to flow_contracts package
to break circular dependencies. They are re-exported here for backward compatibility.
"""

# Import from flow_contracts to break circular dependency
from app.services.flow_contracts import (
    AuditCategory,
    AuditEvent,
    AuditLevel,
    FlowAuditLogger,
    FlowStatusManager,
)

# from .performance_monitor import FlowPerformanceMonitor  # DISABLED - psutil dependency
from .error_handler import FlowErrorHandler
from .execution_engine import FlowExecutionEngine
from .lifecycle_manager import FlowLifecycleManager

__all__ = [
    "FlowLifecycleManager",
    "FlowExecutionEngine",
    "FlowErrorHandler",
    # "FlowPerformanceMonitor",  # DISABLED - psutil dependency
    "FlowAuditLogger",  # Re-exported from flow_contracts
    "FlowStatusManager",  # Re-exported from flow_contracts
    "AuditCategory",  # Re-exported from flow_contracts
    "AuditEvent",  # Re-exported from flow_contracts
    "AuditLevel",  # Re-exported from flow_contracts
]
