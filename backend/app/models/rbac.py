"""
Role-Based Access Control (RBAC) models for multi-tenant access management.
"""

try:
    from sqlalchemy import (
        JSON,
        UUID,
        Boolean,
        Column,
        DateTime,
        Enum,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = (
        String
    ) = Text = Boolean = DateTime = UUID = JSON = ForeignKey = Enum = Integer = object

    def relationship(*args, **kwargs):
        return None

    class func:
        @staticmethod
        def now():
            return None


import uuid
from enum import Enum as PyEnum

try:
    from app.core.database import Base
except ImportError:
    Base = object


class UserStatus(str, PyEnum):
    """User status in the system."""

    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class AccessLevel(str, PyEnum):
    """Access levels for users."""

    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class RoleType(str, PyEnum):
    """Types of roles in the system."""

    PLATFORM_ADMIN = "platform_admin"
    CLIENT_ADMIN = "client_admin"
    ENGAGEMENT_MANAGER = "engagement_manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserProfile(Base):
    """
    Extends the core User model with a detailed profile for RBAC, an approval workflow,
    and enhanced security tracking. This table separates sensitive profile and status
    information from the core user authentication record.
    """

    __tablename__ = "user_profiles"

    # Primary Key (references users.id)
    user_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Foreign key to the users table, serving as the primary key for this profile.",
    )

    # User status and approval workflow
    status = Column(
        String(20),
        default=UserStatus.PENDING_APPROVAL,
        nullable=False,
        index=True,
        comment="The current status of the user's profile (e.g., pending, active, suspended).",
    )
    approval_requested_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the user first requested access.",
    )
    approved_at = Column(
        DateTime(timezone=True),
        comment="Timestamp when an admin approved the user's access.",
    )
    approved_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user ID of the admin who approved the access request.",
    )

    # Registration details
    registration_reason = Column(
        Text,
        comment="The reason provided by the user for requesting access to the platform.",
    )
    organization = Column(
        String(255), comment="The organization or company the user belongs to."
    )
    role_description = Column(
        String(255), comment="The user's job title or role within their organization."
    )
    requested_access_level = Column(
        String(20),
        default=AccessLevel.READ_ONLY,
        comment="The initial access level requested by the user during registration.",
    )

    # Contact and verification
    phone_number = Column(
        String(20), comment="The user's contact phone number. This is PII."
    )
    manager_email = Column(
        String(255),
        comment="The email address of the user's manager, for verification purposes. This is PII.",
    )
    linkedin_profile = Column(
        String(255),
        comment="A link to the user's LinkedIn profile for identity verification.",
    )

    # Access tracking
    last_login_at = Column(
        DateTime(timezone=True),
        comment="Timestamp of the user's last successful login.",
    )
    login_count = Column(
        Integer,
        default=0,
        comment="A counter for the total number of successful logins.",
    )
    failed_login_attempts = Column(
        Integer,
        default=0,
        comment="A counter for consecutive failed login attempts since the last success.",
    )
    last_failed_login = Column(
        DateTime(timezone=True), comment="Timestamp of the last failed login attempt."
    )

    # Notification preferences
    notification_preferences = Column(
        JSON,
        default=lambda: {
            "email_notifications": True,
            "system_alerts": True,
            "learning_updates": False,
            "weekly_reports": True,
        },
        comment="User-configurable settings for receiving platform notifications.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the profile was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of the last update to the profile.",
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    client_access = relationship(
        "ClientAccess", back_populates="user_profile", cascade="all, delete-orphan"
    )
    engagement_access = relationship(
        "EngagementAccess", back_populates="user_profile", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, status='{self.status}', access_level='{self.requested_access_level}')>"

    @property
    def is_approved(self) -> bool:
        """Check if user is approved and active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_pending(self) -> bool:
        """Check if user is pending approval."""
        return self.status == UserStatus.PENDING_APPROVAL

    def approve(self, approved_by_user_id: str):
        """Approve user access."""
        self.status = UserStatus.ACTIVE
        self.approved_at = func.now()
        self.approved_by = approved_by_user_id

    def suspend(self):
        """Suspend user access."""
        self.status = UserStatus.SUSPENDED

    def deactivate(self, deactivated_by: str, reason: str = None):
        """Deactivate user access."""
        from datetime import datetime

        self.status = UserStatus.DEACTIVATED
        self.updated_at = datetime.utcnow()

    def activate(self, activated_by: str, reason: str = None):
        """Activate user access."""
        from datetime import datetime

        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def record_login(self):
        """Record successful login."""
        self.last_login_at = func.now()
        self.login_count += 1
        self.failed_login_attempts = 0

    def record_failed_login(self):
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        self.last_failed_login = func.now()


class UserRole(Base):
    """
    Defines a specific role that can be assigned to a user, granting a set of permissions.
    Roles can be scoped globally, to a client, or to a specific engagement, allowing for
    flexible and granular access control.
    """

    __tablename__ = "user_roles"

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the user role assignment.",
    )
    user_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key linking to the user who is assigned this role.",
    )

    # Role definition
    role_type = Column(
        String(50),
        nullable=False,
        comment="The type of the role, from the RoleType enum (e.g., 'platform_admin', 'analyst').",
    )
    role_name = Column(
        String(100),
        nullable=False,
        comment="A human-readable name for this specific role instance.",
    )
    description = Column(
        Text,
        comment="A detailed description of the role's purpose and responsibilities.",
    )

    # Scope and permissions
    permissions = Column(
        JSON,
        default=lambda: {
            "can_create_clients": False,
            "can_manage_engagements": False,
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True,
            "can_manage_users": False,
            "can_configure_agents": False,
            "can_access_admin_console": False,
        },
        comment="A JSON blob defining the specific permissions granted by this role.",
    )

    # Context scope (global, client-specific, engagement-specific)
    scope_type = Column(
        String(20),
        default="global",
        comment="The scope at which this role applies (e.g., 'global', 'client', 'engagement').",
    )
    scope_client_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("client_accounts.id"),
        nullable=True,
        comment="If scope is 'client', this links to the relevant client account.",
    )
    scope_engagement_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("engagements.id"),
        nullable=True,
        comment="If scope is 'engagement', this links to the relevant engagement.",
    )

    # Role lifecycle
    is_active = Column(
        Boolean,
        default=True,
        index=True,
        comment="A flag to enable or disable the role assignment without deleting it.",
    )
    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the role was assigned to the user.",
    )
    assigned_by = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        comment="The user ID of the admin who assigned this role.",
    )
    expires_at = Column(
        DateTime(timezone=True),
        comment="An optional expiration date for time-bound role assignments.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when this role assignment was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of the last update to this role assignment.",
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    scope_client = relationship("ClientAccount")
    scope_engagement = relationship("Engagement")

    def __repr__(self):
        return f"<UserRole(id={self.id}, user_id={self.user_id}, role_type='{self.role_type}', scope='{self.scope_type}')>"

    @property
    def is_global_admin(self) -> bool:
        """Check if this is a global admin role."""
        return self.role_type == RoleType.PLATFORM_ADMIN and self.scope_type == "global"

    @property
    def is_client_admin(self) -> bool:
        """Check if this is a client admin role."""
        return self.role_type == RoleType.CLIENT_ADMIN and self.scope_type == "client"


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
        return f"<ClientAccess(id={self.id}, user_id={self.user_profile_id}, client_id={self.client_account_id}, access_level='{self.access_level}')>"

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
        return f"<EngagementAccess(id={self.id}, user_id={self.user_profile_id}, engagement_id={self.engagement_id}, role='{self.engagement_role}')>"

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
        return f"<AccessAuditLog(id={self.id}, user_id={self.user_id}, action='{self.action_type}', result='{self.result}')>"

    @classmethod
    def log_access(cls, user_id: str, action_type: str, result: str, **kwargs):
        """Create an audit log entry."""
        return cls(user_id=user_id, action_type=action_type, result=result, **kwargs)
