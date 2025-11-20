"""
Flow Audit Logger - Base Implementation

Main FlowAuditLogger class for comprehensive audit logging with compliance and security tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from app.core.logging import get_logger

from ..compliance import (
    ComplianceAndSecurityHandler,
    ComplianceRules,
    SecurityRules,
)
from ..filters import AuditFilters
from ..models import AuditCategory, AuditEvent, AuditLevel
from .user_extraction import extract_user_id_with_fallbacks
from .utils import (
    event_to_dict,
    export_events_to_csv,
    export_events_to_json,
    log_event_to_system,
)

logger = get_logger(__name__)


class FlowAuditLogger:
    """
    Comprehensive audit logging system for flow operations with compliance and security tracking.
    """

    def __init__(self):
        """Initialize the Flow Audit Logger"""
        self.audit_events: Dict[str, List[AuditEvent]] = {}
        self.compliance_rules: Dict[str, callable] = {}
        self.security_rules: Dict[str, callable] = {}
        self.audit_filters: Dict[str, callable] = {}

        # Initialize built-in rules
        self._initialize_compliance_rules()
        self._initialize_security_rules()
        self._initialize_audit_filters()

        logger.info("Flow Audit Logger initialized")

    def _initialize_compliance_rules(self):
        """Initialize compliance checking rules"""
        self.compliance_rules = {
            "data_retention": ComplianceRules.check_data_retention_compliance,
            "access_control": ComplianceRules.check_access_control_compliance,
            "audit_completeness": ComplianceRules.check_audit_completeness_compliance,
            "flow_approval": ComplianceRules.check_flow_approval_compliance,
        }

    def _initialize_security_rules(self):
        """Initialize security monitoring rules"""
        self.security_rules = {
            "unauthorized_access": SecurityRules.check_unauthorized_access,
            "suspicious_activity": SecurityRules.check_suspicious_activity,
            "privilege_escalation": SecurityRules.check_privilege_escalation,
            "data_exfiltration": SecurityRules.check_data_exfiltration,
        }

    def _initialize_audit_filters(self):
        """Initialize audit filtering rules"""
        self.audit_filters = {
            "sensitive_data": AuditFilters.filter_sensitive_data,
            "pii_data": AuditFilters.filter_pii_data,
            "credentials": AuditFilters.filter_credentials,
        }

    def _extract_user_id_with_fallbacks(
        self, context: Optional[RequestContext], operation: str
    ) -> Optional[str]:
        """
        Extract user_id with multiple fallback strategies (delegates to user_extraction module).

        Args:
            context: Request context (may be None or have user_id=None)
            operation: Operation being performed (determines if system operation)

        Returns:
            User ID string, or None if all extraction methods fail
        """
        return extract_user_id_with_fallbacks(context, operation)

    async def log_audit_event(
        self,
        flow_id: str,
        operation: str,
        category: AuditCategory,
        level: AuditLevel = AuditLevel.INFO,
        context: Optional[RequestContext] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an audit event

        Args:
            flow_id: Flow identifier
            operation: Operation being performed
            category: Audit event category
            level: Audit level
            context: Request context
            success: Whether the operation succeeded
            error_message: Error message if operation failed
            details: Additional details about the event
            metadata: Additional metadata

        Returns:
            Audit event ID
        """
        try:
            # Generate unique event ID
            event_id = (
                f"audit_{flow_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            )

            # AUDIT FIX: Extract user_id with multiple fallback strategies
            user_id = self._extract_user_id_with_fallbacks(context, operation)

            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                category=category,
                level=level,
                flow_id=flow_id,
                operation=operation,
                user_id=user_id,
                client_account_id=str(context.client_account_id) if context else None,
                engagement_id=str(context.engagement_id) if context else None,
                success=success,
                error_message=error_message,
                details=details or {},
                metadata=metadata or {},
                ip_address=getattr(context, "ip_address", None) if context else None,
                user_agent=getattr(context, "user_agent", None) if context else None,
            )

            # Apply audit filters
            filtered_event = AuditFilters.apply_all_filters(
                audit_event, self.audit_filters
            )

            # Store audit event
            if flow_id not in self.audit_events:
                self.audit_events[flow_id] = []

            self.audit_events[flow_id].append(filtered_event)

            # Keep only last 100 events per flow
            if len(self.audit_events[flow_id]) > 100:
                self.audit_events[flow_id] = self.audit_events[flow_id][-100:]

            # Log to system logger
            self._log_to_system(filtered_event)

            # Check compliance rules
            await self._check_compliance_rules(filtered_event)

            # Check security rules
            await self._check_security_rules(filtered_event)

            return event_id

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return ""

    def _log_to_system(self, event: AuditEvent):
        """Log audit event to system logger (delegates to utils module)"""
        log_event_to_system(event)

    async def _check_compliance_rules(self, event: AuditEvent):
        """Check compliance rules against audit event"""
        for rule_name, rule_func in self.compliance_rules.items():
            try:
                compliance_result = await rule_func(event)
                if not compliance_result.get("compliant", True):
                    await ComplianceAndSecurityHandler.handle_compliance_violation(
                        event,
                        rule_name,
                        compliance_result,
                        self.audit_events,
                        self._log_to_system,
                    )
            except Exception as e:
                logger.warning(f"Compliance rule {rule_name} failed: {e}")

    async def _check_security_rules(self, event: AuditEvent):
        """Check security rules against audit event"""
        for rule_name, rule_func in self.security_rules.items():
            try:
                security_result = await rule_func(event)
                if security_result.get("alert", False):
                    await ComplianceAndSecurityHandler.handle_security_alert(
                        event,
                        rule_name,
                        security_result,
                        self.audit_events,
                        self._log_to_system,
                    )
            except Exception as e:
                logger.warning(f"Security rule {rule_name} failed: {e}")

    def get_audit_events(
        self,
        flow_id: str,
        category: Optional[AuditCategory] = None,
        level: Optional[AuditLevel] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get audit events for a flow

        Args:
            flow_id: Flow identifier
            category: Optional category filter
            level: Optional level filter
            limit: Maximum number of events to return

        Returns:
            List of audit events
        """
        events = self.audit_events.get(flow_id, [])

        # Apply filters
        if category:
            events = [e for e in events if e.category == category]

        if level:
            events = [e for e in events if e.level == level]

        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply limit
        events = events[:limit]

        # Convert to dict format
        return [event_to_dict(event) for event in events]

    def get_compliance_report(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get compliance report for a flow or all flows

        Args:
            flow_id: Optional flow identifier

        Returns:
            Compliance report
        """
        if flow_id:
            events = self.audit_events.get(flow_id, [])
        else:
            events = []
            for flow_events in self.audit_events.values():
                events.extend(flow_events)

        # Count compliance events
        compliance_events = [
            e for e in events if e.category == AuditCategory.COMPLIANCE_EVENT
        ]
        violation_count = len([e for e in compliance_events if not e.success])

        # Count security events
        security_events = [
            e for e in events if e.category == AuditCategory.SECURITY_EVENT
        ]
        alert_count = len(
            [e for e in security_events if e.level == AuditLevel.CRITICAL]
        )

        return {
            "flow_id": flow_id,
            "total_events": len(events),
            "compliance_events": len(compliance_events),
            "compliance_violations": violation_count,
            "security_events": len(security_events),
            "security_alerts": alert_count,
            "compliance_score": (
                (1 - violation_count / len(events)) * 100 if events else 100
            ),
            "security_score": (1 - alert_count / len(events)) * 100 if events else 100,
        }

    def clear_audit_events(self, flow_id: Optional[str] = None):
        """
        Clear audit events for a flow or all flows

        Args:
            flow_id: Optional flow identifier
        """
        if flow_id:
            self.audit_events.pop(flow_id, None)
            logger.info(f"Cleared audit events for flow {flow_id}")
        else:
            self.audit_events.clear()
            logger.info("Cleared all audit events")

    def export_audit_log(
        self, flow_id: Optional[str] = None, format: str = "json"
    ) -> str:
        """
        Export audit log in specified format

        Args:
            flow_id: Optional flow identifier
            format: Export format (json, csv)

        Returns:
            Exported audit log data
        """
        if flow_id:
            events = self.audit_events.get(flow_id, [])
        else:
            events = []
            for flow_events in self.audit_events.values():
                events.extend(flow_events)

        if format.lower() == "json":
            return export_events_to_json(events)
        elif format.lower() == "csv":
            return export_events_to_csv(events)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def register_compliance_rule(self, rule_name: str, rule_function: callable):
        """
        Register a custom compliance rule

        Args:
            rule_name: Name of the rule
            rule_function: Function that checks compliance
        """
        self.compliance_rules[rule_name] = rule_function
        logger.info(f"Registered compliance rule: {rule_name}")

    def register_security_rule(self, rule_name: str, rule_function: callable):
        """
        Register a custom security rule

        Args:
            rule_name: Name of the rule
            rule_function: Function that checks security
        """
        self.security_rules[rule_name] = rule_function
        logger.info(f"Registered security rule: {rule_name}")

    def register_audit_filter(self, filter_name: str, filter_function: callable):
        """
        Register a custom audit filter

        Args:
            filter_name: Name of the filter
            filter_function: Function that filters audit events
        """
        self.audit_filters[filter_name] = filter_function
        logger.info(f"Registered audit filter: {filter_name}")
