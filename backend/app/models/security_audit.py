"""
Security Audit Model - Tracks all security-sensitive events
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func

from app.core.database import Base


class SecurityAuditLog(Base):
    """
    Comprehensive security audit logging for all privilege changes and sensitive operations.
    """

    __tablename__ = "security_audit_logs"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event Information
    event_type = Column(String(100), nullable=False, index=True)
    event_category = Column(
        String(50), nullable=False, index=True
    )  # ROLE_CHANGE, LOGIN, ADMIN_ACCESS, etc.
    severity = Column(
        String(20), nullable=False, default="INFO"
    )  # INFO, WARNING, CRITICAL

    # Actor Information
    actor_user_id = Column(String(36), nullable=False, index=True)
    actor_email = Column(String(255), nullable=True)
    actor_role = Column(String(50), nullable=True)

    # Target Information (for operations affecting other users)
    target_user_id = Column(String(36), nullable=True, index=True)
    target_email = Column(String(255), nullable=True)

    # Request Information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_path = Column(String(500), nullable=True)
    request_method = Column(String(10), nullable=True)

    # Event Details
    description = Column(Text, nullable=False)
    details = Column(JSONB, nullable=True)  # Structured event details

    # Security Flags
    is_suspicious = Column(Boolean, default=False, index=True)
    requires_review = Column(Boolean, default=False, index=True)
    is_blocked = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(36), nullable=True)

    def __repr__(self):
        return f"<SecurityAuditLog(event_type='{self.event_type}', actor='{self.actor_user_id}', severity='{self.severity}')>"

    @classmethod
    def create_role_change_event(
        cls,
        actor_user_id: str,
        target_user_id: str,
        old_role: str,
        new_role: str,
        **kwargs,
    ):
        """Create a role change audit event."""
        return cls(
            event_type="ROLE_CHANGE",
            event_category=(
                "PRIVILEGE_ESCALATION"
                if cls._is_escalation(old_role, new_role)
                else "ROLE_MODIFICATION"
            ),
            severity="CRITICAL" if new_role == "platform_admin" else "WARNING",
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            description=f"Role changed from '{old_role}' to '{new_role}'",
            details={
                "old_role": old_role,
                "new_role": new_role,
                "is_escalation": cls._is_escalation(old_role, new_role),
                **kwargs,
            },
            requires_review=new_role == "platform_admin",
        )

    @classmethod
    def create_admin_access_event(cls, user_id: str, endpoint: str, **kwargs):
        """Create an admin access audit event."""
        return cls(
            event_type="ADMIN_ACCESS",
            event_category="ADMIN_OPERATION",
            severity="INFO",
            actor_user_id=user_id,
            description=f"Admin endpoint accessed: {endpoint}",
            details={"endpoint": endpoint, **kwargs},
        )

    @classmethod
    def create_security_violation_event(
        cls, user_id: str, violation_type: str, **kwargs
    ):
        """Create a security violation audit event."""
        return cls(
            event_type="SECURITY_VIOLATION",
            event_category="UNAUTHORIZED_ACCESS",
            severity="CRITICAL",
            actor_user_id=user_id,
            description=f"Security violation: {violation_type}",
            details={"violation_type": violation_type, **kwargs},
            is_suspicious=True,
            requires_review=True,
        )

    @staticmethod
    def _is_escalation(old_role: str, new_role: str) -> bool:
        """Determine if role change is a privilege escalation."""
        role_hierarchy = {
            "viewer": 1,
            "analyst": 2,
            "engagement_manager": 3,
            "client_admin": 4,
            "platform_admin": 5,
        }

        old_level = role_hierarchy.get(old_role, 0)
        new_level = role_hierarchy.get(new_role, 0)

        return new_level > old_level


class RoleChangeApproval(Base):
    """
    Role change approval workflow - requires approval for privilege escalations
    """

    __tablename__ = "role_change_approvals"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request Information
    requested_by = Column(String(36), nullable=False, index=True)
    target_user_id = Column(String(36), nullable=False, index=True)
    current_role = Column(String(50), nullable=False)
    requested_role = Column(String(50), nullable=False)
    justification = Column(Text, nullable=True)

    # Approval Information
    status = Column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING, APPROVED, REJECTED
    approved_by = Column(String(36), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Timestamps
    requested_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<RoleChangeApproval(target='{self.target_user_id}', role='{self.requested_role}', status='{self.status}')>"
