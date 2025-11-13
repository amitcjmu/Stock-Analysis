"""
Compliance and Security Rules

Methods for checking compliance rules and security monitoring.
"""

from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger

from .models import AuditCategory, AuditEvent, AuditLevel

logger = get_logger(__name__)


class ComplianceRules:
    """Compliance checking rules"""

    @staticmethod
    async def check_data_retention_compliance(event: AuditEvent) -> Dict[str, Any]:
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

    @staticmethod
    async def check_access_control_compliance(event: AuditEvent) -> Dict[str, Any]:
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

    @staticmethod
    async def check_audit_completeness_compliance(event: AuditEvent) -> Dict[str, Any]:
        """Check audit completeness compliance"""
        # Check if required fields are present
        required_fields = ["flow_id", "operation", "client_account_id"]
        missing_fields = []

        # user_id is required for user-initiated operations but optional for system operations
        system_operations = [
            "resume",
            "pause",
            "health_check",
            "status_sync",
            "cleanup",
            "monitoring",
        ]
        user_id_required = not any(
            sys_op in event.operation.lower() for sys_op in system_operations
        )

        if user_id_required:
            required_fields.append("user_id")

        for field in required_fields:
            if not getattr(event, field, None):
                missing_fields.append(field)

        return {
            "compliant": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "message": f"Audit completeness check: {len(missing_fields)} missing fields"
            + (
                f" (user_id optional for system operation: {event.operation})"
                if not user_id_required
                else ""
            ),
        }

    @staticmethod
    async def check_flow_approval_compliance(event: AuditEvent) -> Dict[str, Any]:
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


class SecurityRules:
    """Security monitoring rules"""

    @staticmethod
    async def check_unauthorized_access(event: AuditEvent) -> Dict[str, Any]:
        """Check for unauthorized access attempts"""
        # Check for failed authentication or authorization
        if not event.success and event.operation in ["login", "access", "authenticate"]:
            return {
                "alert": True,
                "severity": "high",
                "message": f"Unauthorized access attempt detected: {event.operation}",
            }

        return {"alert": False, "message": "No unauthorized access detected"}

    @staticmethod
    async def check_suspicious_activity(event: AuditEvent) -> Dict[str, Any]:
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

    @staticmethod
    async def check_privilege_escalation(event: AuditEvent) -> Dict[str, Any]:
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

    @staticmethod
    async def check_data_exfiltration(event: AuditEvent) -> Dict[str, Any]:
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


class ComplianceAndSecurityHandler:
    """Handler for compliance violations and security alerts"""

    @staticmethod
    async def handle_compliance_violation(
        event: AuditEvent,
        rule_name: str,
        compliance_result: Dict[str, Any],
        audit_events: dict,
        log_to_system: callable,
    ) -> AuditEvent:
        """
        Handle compliance violations

        Args:
            event: Original audit event
            rule_name: Name of the compliance rule that was violated
            compliance_result: Result from the compliance check
            audit_events: Dictionary to store the violation event
            log_to_system: Function to log the event to system logger

        Returns:
            Violation audit event
        """
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
        log_to_system(violation_event)

        # Store violation event
        if event.flow_id not in audit_events:
            audit_events[event.flow_id] = []
        audit_events[event.flow_id].append(violation_event)

        return violation_event

    @staticmethod
    async def handle_security_alert(
        event: AuditEvent,
        rule_name: str,
        security_result: Dict[str, Any],
        audit_events: dict,
        log_to_system: callable,
    ) -> AuditEvent:
        """
        Handle security alerts

        Args:
            event: Original audit event
            rule_name: Name of the security rule that triggered
            security_result: Result from the security check
            audit_events: Dictionary to store the alert event
            log_to_system: Function to log the event to system logger

        Returns:
            Alert audit event
        """
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
        log_to_system(alert_event)

        # Store alert event
        if event.flow_id not in audit_events:
            audit_events[event.flow_id] = []
        audit_events[event.flow_id].append(alert_event)

        return alert_event
