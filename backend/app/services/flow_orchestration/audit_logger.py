"""
Flow Audit Logger

Handles audit logging, compliance tracking, flow operation logging, and security event monitoring.
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditLevel(Enum):
    """Audit logging levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit event categories"""

    FLOW_LIFECYCLE = "flow_lifecycle"
    FLOW_EXECUTION = "flow_execution"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    PERFORMANCE_EVENT = "performance_event"
    ERROR_EVENT = "error_event"
    AGENT_DECISION = "agent_decision"  # Agent decision audit events


@dataclass
class AuditEvent:
    """Audit event data structure"""

    event_id: str
    timestamp: datetime
    category: AuditCategory
    level: AuditLevel
    flow_id: str
    operation: str
    user_id: Optional[str] = None
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


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

        logger.info("✅ Flow Audit Logger initialized")

    def _initialize_compliance_rules(self):
        """Initialize compliance checking rules"""
        self.compliance_rules = {
            "data_retention": self._check_data_retention_compliance,
            "access_control": self._check_access_control_compliance,
            "audit_completeness": self._check_audit_completeness_compliance,
            "flow_approval": self._check_flow_approval_compliance,
        }

    def _initialize_security_rules(self):
        """Initialize security monitoring rules"""
        self.security_rules = {
            "unauthorized_access": self._check_unauthorized_access,
            "suspicious_activity": self._check_suspicious_activity,
            "privilege_escalation": self._check_privilege_escalation,
            "data_exfiltration": self._check_data_exfiltration,
        }

    def _initialize_audit_filters(self):
        """Initialize audit filtering rules"""
        self.audit_filters = {
            "sensitive_data": self._filter_sensitive_data,
            "pii_data": self._filter_pii_data,
            "credentials": self._filter_credentials,
        }

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

            # Create audit event
            audit_event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                category=category,
                level=level,
                flow_id=flow_id,
                operation=operation,
                user_id=context.user_id if context else None,
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
            filtered_event = self._apply_audit_filters(audit_event)

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
            logger.error(f"❌ Failed to log audit event: {e}")
            return ""

    def _apply_audit_filters(self, event: AuditEvent) -> AuditEvent:
        """Apply audit filters to remove sensitive data"""
        filtered_event = event

        for filter_name, filter_func in self.audit_filters.items():
            try:
                filtered_event = filter_func(filtered_event)
            except Exception as e:
                logger.warning(f"⚠️ Audit filter {filter_name} failed: {e}")

        return filtered_event

    def _log_to_system(self, event: AuditEvent):
        """Log audit event to system logger"""
        log_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "category": event.category.value,
            "level": event.level.value,
            "flow_id": str(event.flow_id) if event.flow_id else None,
            "operation": event.operation,
            "user_id": str(event.user_id) if event.user_id else None,
            "client_account_id": (
                str(event.client_account_id) if event.client_account_id else None
            ),
            "engagement_id": str(event.engagement_id) if event.engagement_id else None,
            "success": event.success,
            "error_message": event.error_message,
            "details": self._convert_to_serializable(event.details),
            "metadata": self._convert_to_serializable(event.metadata),
        }

        # Log based on audit level
        if event.level == AuditLevel.CRITICAL:
            logger.critical(f"📝 AUDIT: {json.dumps(log_data, default=str)}")
        elif event.level == AuditLevel.ERROR:
            logger.error(f"📝 AUDIT: {json.dumps(log_data, default=str)}")
        elif event.level == AuditLevel.WARNING:
            logger.warning(f"📝 AUDIT: {json.dumps(log_data, default=str)}")
        elif event.level == AuditLevel.DEBUG:
            logger.debug(f"📝 AUDIT: {json.dumps(log_data, default=str)}")
        else:
            logger.info(f"📝 AUDIT: {json.dumps(log_data, default=str)}")

    async def _check_compliance_rules(self, event: AuditEvent):
        """Check compliance rules against audit event"""
        for rule_name, rule_func in self.compliance_rules.items():
            try:
                compliance_result = await rule_func(event)
                if not compliance_result.get("compliant", True):
                    await self._handle_compliance_violation(
                        event, rule_name, compliance_result
                    )
            except Exception as e:
                logger.warning(f"⚠️ Compliance rule {rule_name} failed: {e}")

    async def _check_security_rules(self, event: AuditEvent):
        """Check security rules against audit event"""
        for rule_name, rule_func in self.security_rules.items():
            try:
                security_result = await rule_func(event)
                if security_result.get("alert", False):
                    await self._handle_security_alert(event, rule_name, security_result)
            except Exception as e:
                logger.warning(f"⚠️ Security rule {rule_name} failed: {e}")

    async def _handle_compliance_violation(
        self, event: AuditEvent, rule_name: str, compliance_result: Dict[str, Any]
    ):
        """Handle compliance violations"""
        violation_event = AuditEvent(
            event_id=f"compliance_{event.event_id}",
            timestamp=datetime.utcnow(),
            category=AuditCategory.COMPLIANCE_EVENT,
            level=AuditLevel.WARNING,
            flow_id=event.flow_id,
            operation="compliance_violation",
            user_id=event.user_id,
            client_account_id=event.client_account_id,
            engagement_id=event.engagement_id,
            success=False,
            error_message=f"Compliance violation: {rule_name}",
            details={
                "rule_name": rule_name,
                "violation_details": compliance_result,
                "original_event": event.event_id,
            },
        )

        # Log compliance violation
        self._log_to_system(violation_event)

        # Store violation event
        if event.flow_id not in self.audit_events:
            self.audit_events[event.flow_id] = []
        self.audit_events[event.flow_id].append(violation_event)

    async def _handle_security_alert(
        self, event: AuditEvent, rule_name: str, security_result: Dict[str, Any]
    ):
        """Handle security alerts"""
        alert_event = AuditEvent(
            event_id=f"security_{event.event_id}",
            timestamp=datetime.utcnow(),
            category=AuditCategory.SECURITY_EVENT,
            level=AuditLevel.CRITICAL,
            flow_id=event.flow_id,
            operation="security_alert",
            user_id=event.user_id,
            client_account_id=event.client_account_id,
            engagement_id=event.engagement_id,
            success=False,
            error_message=f"Security alert: {rule_name}",
            details={
                "rule_name": rule_name,
                "alert_details": security_result,
                "original_event": event.event_id,
            },
        )

        # Log security alert
        self._log_to_system(alert_event)

        # Store alert event
        if event.flow_id not in self.audit_events:
            self.audit_events[event.flow_id] = []
        self.audit_events[event.flow_id].append(alert_event)

    # Built-in audit filters
    def _filter_sensitive_data(self, event: AuditEvent) -> AuditEvent:
        """Filter sensitive data from audit events"""
        sensitive_keys = ["password", "secret", "token", "key", "credential"]

        if event.details:
            for key in list(event.details.keys()):
                if any(
                    sensitive_key in key.lower() for sensitive_key in sensitive_keys
                ):
                    event.details[key] = "***FILTERED***"

        if event.metadata:
            for key in list(event.metadata.keys()):
                if any(
                    sensitive_key in key.lower() for sensitive_key in sensitive_keys
                ):
                    event.metadata[key] = "***FILTERED***"

        return event

    def _filter_pii_data(self, event: AuditEvent) -> AuditEvent:
        """Filter PII data from audit events"""
        pii_keys = ["ssn", "social_security", "email", "phone", "address", "name"]

        if event.details:
            for key in list(event.details.keys()):
                if any(pii_key in key.lower() for pii_key in pii_keys):
                    event.details[key] = "***PII_FILTERED***"

        return event

    def _filter_credentials(self, event: AuditEvent) -> AuditEvent:
        """Filter credential data from audit events"""
        if event.details and "configuration" in event.details:
            config = event.details["configuration"]
            if isinstance(config, dict):
                for key in list(config.keys()):
                    if any(
                        cred_key in key.lower()
                        for cred_key in ["api_key", "secret", "password", "token"]
                    ):
                        config[key] = "***CREDENTIAL_FILTERED***"

        return event

    # Built-in compliance rules
    async def _check_data_retention_compliance(
        self, event: AuditEvent
    ) -> Dict[str, Any]:
        """Check data retention compliance"""
        # Check if event is older than retention period
        retention_days = 90  # Default retention period
        age_days = (datetime.utcnow() - event.timestamp).days

        return {
            "compliant": age_days <= retention_days,
            "retention_days": retention_days,
            "age_days": age_days,
            "message": f"Event age ({age_days} days) within retention period ({retention_days} days)",
        }

    async def _check_access_control_compliance(
        self, event: AuditEvent
    ) -> Dict[str, Any]:
        """Check access control compliance"""
        # Check if user has proper authorization for operation
        sensitive_operations = ["delete", "modify", "export", "admin"]

        if event.operation in sensitive_operations:
            # In a real implementation, this would check user permissions
            has_permission = event.user_id is not None  # Simplified check

            return {
                "compliant": has_permission,
                "operation": event.operation,
                "user_id": event.user_id,
                "message": f"Access control check for operation: {event.operation}",
            }

        return {"compliant": True, "message": "No access control check required"}

    async def _check_audit_completeness_compliance(
        self, event: AuditEvent
    ) -> Dict[str, Any]:
        """Check audit completeness compliance"""
        # Check if required fields are present
        required_fields = ["flow_id", "operation", "user_id", "client_account_id"]
        missing_fields = []

        for field in required_fields:
            if not getattr(event, field, None):
                missing_fields.append(field)

        return {
            "compliant": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "message": f"Audit completeness check: {len(missing_fields)} missing fields",
        }

    async def _check_flow_approval_compliance(
        self, event: AuditEvent
    ) -> Dict[str, Any]:
        """Check flow approval compliance"""
        # Check if flow operations require approval
        approval_required_operations = ["delete", "export", "modify_sensitive"]

        if event.operation in approval_required_operations:
            # Check if approval is recorded in event details
            approval_recorded = event.details and event.details.get(
                "approval_recorded", False
            )

            return {
                "compliant": approval_recorded,
                "operation": event.operation,
                "approval_recorded": approval_recorded,
                "message": f"Flow approval compliance check for operation: {event.operation}",
            }

        return {"compliant": True, "message": "No approval required"}

    # Built-in security rules
    async def _check_unauthorized_access(self, event: AuditEvent) -> Dict[str, Any]:
        """Check for unauthorized access attempts"""
        # Check for failed authentication or authorization
        if not event.success and event.operation in ["login", "access", "authenticate"]:
            return {
                "alert": True,
                "severity": "high",
                "message": f"Unauthorized access attempt detected: {event.operation}",
            }

        return {"alert": False, "message": "No unauthorized access detected"}

    async def _check_suspicious_activity(self, event: AuditEvent) -> Dict[str, Any]:
        """Check for suspicious activity patterns"""
        # Check for unusual patterns (simplified)
        suspicious_patterns = [
            "multiple_failed_attempts",
            "unusual_time_access",
            "bulk_operations",
            "privilege_change",
        ]

        if event.details and any(
            pattern in str(event.details) for pattern in suspicious_patterns
        ):
            return {
                "alert": True,
                "severity": "medium",
                "message": "Suspicious activity pattern detected",
            }

        return {"alert": False, "message": "No suspicious activity detected"}

    async def _check_privilege_escalation(self, event: AuditEvent) -> Dict[str, Any]:
        """Check for privilege escalation attempts"""
        # Check for privilege escalation patterns
        escalation_operations = ["grant_permission", "change_role", "admin_access"]

        if event.operation in escalation_operations:
            return {
                "alert": True,
                "severity": "high",
                "message": f"Privilege escalation detected: {event.operation}",
            }

        return {"alert": False, "message": "No privilege escalation detected"}

    async def _check_data_exfiltration(self, event: AuditEvent) -> Dict[str, Any]:
        """Check for data exfiltration attempts"""
        # Check for data export or bulk access patterns
        exfiltration_operations = ["export", "bulk_download", "data_copy"]

        if event.operation in exfiltration_operations:
            return {
                "alert": True,
                "severity": "critical",
                "message": f"Potential data exfiltration detected: {event.operation}",
            }

        return {"alert": False, "message": "No data exfiltration detected"}

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
        return [self._event_to_dict(event) for event in events]

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
            logger.info(f"🧹 Cleared audit events for flow {flow_id}")
        else:
            self.audit_events.clear()
            logger.info("🧹 Cleared all audit events")

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
            return json.dumps(
                [self._event_to_dict(event) for event in events], indent=2, default=str
            )
        elif format.lower() == "csv":
            # Simple CSV export (would need proper CSV library for production)
            csv_lines = [
                "timestamp,category,level,flow_id,operation,user_id,success,error_message"
            ]
            for event in events:
                csv_lines.append(
                    f"{event.timestamp},{event.category.value},{event.level.value},"
                    f"{event.flow_id},{event.operation},{event.user_id},{event.success},{event.error_message or ''}"
                )
            return "\n".join(csv_lines)
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
        logger.info(f"📋 Registered compliance rule: {rule_name}")

    def register_security_rule(self, rule_name: str, rule_function: callable):
        """
        Register a custom security rule

        Args:
            rule_name: Name of the rule
            rule_function: Function that checks security
        """
        self.security_rules[rule_name] = rule_function
        logger.info(f"🔒 Registered security rule: {rule_name}")

    def register_audit_filter(self, filter_name: str, filter_function: callable):
        """
        Register a custom audit filter

        Args:
            filter_name: Name of the filter
            filter_function: Function that filters audit events
        """
        self.audit_filters[filter_name] = filter_function
        logger.info(f"🔍 Registered audit filter: {filter_name}")

    def _convert_to_serializable(self, obj: Any) -> Any:
        """Recursively convert UUIDs and other non-serializable objects to strings."""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif hasattr(obj, "__dict__"):
            return self._convert_to_serializable(obj.__dict__)
        else:
            return obj

    def _event_to_dict(self, event: AuditEvent) -> Dict[str, Any]:
        """Convert AuditEvent to dictionary with proper serialization."""
        event_dict = asdict(event)
        # Convert any nested UUIDs or non-serializable objects
        return self._convert_to_serializable(event_dict)
