"""
Monitoring Operations Module

Contains performance monitoring and audit operations.
"""

from typing import Any, Dict, List, Optional

from app.services.flow_contracts import FlowAuditLogger, AuditCategory, AuditLevel
from app.services.flow_orchestration import FlowErrorHandler

from .mock_monitor import MockFlowPerformanceMonitor


class MonitoringOperations:
    """Handles performance monitoring and audit operations"""

    def __init__(
        self,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        error_handler: FlowErrorHandler,
    ):
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        self.error_handler = error_handler

    def get_performance_summary(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for a flow or system overview"""
        if flow_id:
            return self.performance_monitor.get_flow_performance_summary(flow_id)
        else:
            return self.performance_monitor.get_system_performance_overview()

    def get_audit_events(
        self,
        flow_id: str,
        category: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get audit events for a flow"""
        audit_category = None
        audit_level = None

        if category:
            try:
                audit_category = AuditCategory(category)
            except ValueError:
                pass

        if level:
            try:
                audit_level = AuditLevel(level)
            except ValueError:
                pass

        return self.audit_logger.get_audit_events(
            flow_id, audit_category, audit_level, limit
        )

    def get_compliance_report(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get compliance report for a flow or all flows"""
        return self.audit_logger.get_compliance_report(flow_id)

    def clear_flow_data(self, flow_id: str):
        """Clear all tracking data for a flow"""
        self.performance_monitor.clear_flow_metrics(flow_id)
        self.audit_logger.clear_audit_events(flow_id)
        self.error_handler.clear_error_history(flow_id)
