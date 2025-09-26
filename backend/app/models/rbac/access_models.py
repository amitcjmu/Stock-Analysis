"""
Client and engagement access models for RBAC system.
"""

from .base import (
    Base,
    Column,
    PostgresUUID,
    String,
    Boolean,
    DateTime,
    JSON,
    Integer,
    ForeignKey,
    relationship,
    func,
    uuid,
)


class ClientAccess(Base):
    """
    Links a user profile to a client account, defining their access level and
    specific permissions within that client's context. This table is a key part
    of the multi-tenant security model.
    """

    __tablename__ = "client_access"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the client access record.",
    )
    user_profile_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the user's profile.",
    )
    client_account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the client account being accessed.",
    )

    # Access level for this client
    access_level = Column(
        String(20),
        nullable=False,
        comment="The general access level for the user within this client (e.g., 'admin', 'read_only').",
    )

    # Specific permissions for this client
    permissions = Column(
        JSON,
        default=lambda: {
            "can_view_data": True,
            "can_import_data": False,
            "can_export_data": False,
            "can_manage_engagements": False,
            "can_configure_client_settings": False,
            "can_manage_client_users": False,
        },
        comment="A JSON blob for fine-grained permission overrides specific to this client.",
    )

    # Access restrictions
    restricted_environments = Column(
        JSON,
        default=lambda: [],
        comment="A list of environments (e.g., 'production') within this client the user CANNOT access.",
    )
    restricted_data_types = Column(
        JSON,
        default=lambda: [],
        comment="A list of data types (e.g., 'financial') within this client the user CANNOT access.",
    )

    # Access lifecycle
    granted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when access was granted.",
    )
    granted_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="The user ID of the admin who granted this access.",
    )
    expires_at = Column(
        DateTime(timezone=True),
        comment="An optional expiration date for time-bound access.",
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="A flag to enable or disable this access record without deleting it.",
    )

    # Usage tracking
    last_accessed_at = Column(
        DateTime(timezone=True),
        comment="Timestamp of the last time the user accessed resources in this client.",
    )
    access_count = Column(
        Integer,
        default=0,
        comment="A counter for how many times the user has accessed this client's resources.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the access record was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of the last update to the access record.",
    )

    # Relationships
    user_profile = relationship("UserProfile", back_populates="client_access")
    client_account = relationship("ClientAccount")
    granted_by_user = relationship("User")

    def __repr__(self):
        return (
            f"<ClientAccess(id={self.id}, user_id={self.user_profile_id}, "
            f"client_id={self.client_account_id}, access_level='{self.access_level}')>"
        )

    def record_access(self):
        """Record that user accessed this client."""
        self.last_accessed_at = func.now()
        self.access_count += 1

    @property
    def is_expired(self) -> bool:
        """Check if access has expired."""
        if not self.expires_at:
            return False
        return self.expires_at < func.now()


class EngagementAccess(Base):
    """
    Provides the most granular level of access control, linking a user profile
    to a specific engagement within a client account.
    """

    __tablename__ = "engagement_access"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the engagement access record.",
    )
    user_profile_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the user's profile.",
    )
    engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to the engagement being accessed.",
    )

    # Access level for this engagement
    access_level = Column(
        String(20),
        nullable=False,
        comment="The general access level for the user within this engagement.",
    )

    # Engagement-specific role
    engagement_role = Column(
        String(100),
        comment="A descriptive role for the user in this engagement (e.g., 'Project Manager', 'Lead Analyst').",
    )

    # Specific permissions for this engagement
    permissions = Column(
        JSON,
        default=lambda: {
            "can_view_data": True,
            "can_import_data": False,
            "can_export_data": False,
            "can_manage_sessions": False,
            "can_configure_agents": False,
            "can_approve_migration_decisions": False,
            "can_access_sensitive_data": False,
        },
        comment="A JSON blob for fine-grained permission overrides specific to this engagement.",
    )

    # Session-level restrictions
    restricted_sessions = Column(
        JSON,
        default=lambda: [],
        comment="A list of specific session IDs within this engagement that the user is barred from accessing.",
    )
    allowed_session_types = Column(
        JSON,
        default=lambda: ["data_import", "validation_run"],
        comment="A whitelist of session types the user is allowed to interact with.",
    )

    # Access lifecycle
    granted_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when engagement access was granted.",
    )
    granted_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="The user ID of the admin who granted this access.",
    )
    expires_at = Column(
        DateTime(timezone=True),
        comment="An optional expiration date for time-bound access.",
    )
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="A flag to enable or disable this access record without deleting it.",
    )

    # Usage tracking
    last_accessed_at = Column(
        DateTime(timezone=True),
        comment="Timestamp of the last time the user accessed this engagement.",
    )
    access_count = Column(
        Integer,
        default=0,
        comment="A counter for how many times the user has accessed this engagement.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the access record was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of the last update to the access record.",
    )

    # Relationships
    user_profile = relationship("UserProfile", back_populates="engagement_access")
    engagement = relationship("Engagement")
    granted_by_user = relationship("User")

    def __repr__(self):
        return (
            f"<EngagementAccess(id={self.id}, user_id={self.user_profile_id}, "
            f"engagement_id={self.engagement_id}, role='{self.engagement_role}')>"
        )

    def record_access(self):
        """Record that user accessed this engagement."""
        self.last_accessed_at = func.now()
        self.access_count += 1

    @property
    def is_expired(self) -> bool:
        """Check if access has expired."""
        if not self.expires_at:
            return False
        return self.expires_at < func.now()
