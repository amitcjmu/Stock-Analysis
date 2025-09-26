"""
Audit and logging models for RBAC system.
"""

from .base import (
    Base,
    Column,
    PostgresUUID,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    relationship,
    func,
    uuid,
)


class AccessAuditLog(Base):
    """
    Logs significant security and access-related events for auditing and monitoring.
    This provides a persistent, immutable record of actions taken by users and the system.
    """

    __tablename__ = "access_audit_log"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the audit log entry.",
    )

    # Who and what
    user_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="The user who performed the action or was the subject of the event.",
    )
    action_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="The type of action being logged (e.g., 'login', 'access_granted', 'resource_deleted').",
    )
    resource_type = Column(
        String(50),
        comment="The type of resource that was affected (e.g., 'client', 'engagement', 'user_profile').",
    )
    resource_id = Column(
        String(255), comment="The ID of the specific resource that was affected."
    )

    # Context
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id"),
        nullable=True,
        comment="The client account context in which the action occurred.",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id"),
        nullable=True,
        comment="The engagement context in which the action occurred.",
    )

    # Result and details
    result = Column(
        String(20),
        nullable=False,
        comment="The outcome of the action (e.g., 'success', 'denied', 'error').",
    )
    reason = Column(
        Text,
        comment="A human-readable reason for the outcome (e.g., 'insufficient_permissions').",
    )
    ip_address = Column(String(45), comment="The source IP address of the request.")
    user_agent = Column(
        Text, comment="The user agent string of the client that made the request."
    )

    # Additional context
    details = Column(
        JSON,
        default=lambda: {},
        comment="A JSON blob for storing any other relevant details about the event.",
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        comment="The timestamp when the event occurred.",
    )

    # Relationships
    user = relationship("User")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    def __repr__(self):
        return (
            f"<AccessAuditLog(id={self.id}, user_id={self.user_id}, action='{self.action_type}', "
            f"result='{self.result}')>"
        )

    @classmethod
    def log_access(cls, user_id: str, action_type: str, result: str, **kwargs):
        """Create an audit log entry."""
        return cls(user_id=user_id, action_type=action_type, result=result, **kwargs)
