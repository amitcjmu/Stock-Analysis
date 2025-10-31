"""
User profile and role models for RBAC system.
"""

from .base import (
    Base,
    Column,
    PostgresUUID,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    Integer,
    ForeignKey,
    relationship,
    func,
    uuid,
)
from .enums import UserStatus, AccessLevel, RoleType


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
        return (
            f"<UserProfile(user_id={self.user_id}, status='{self.status}', "
            f"access_level='{self.requested_access_level}')>"
        )

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
    user = relationship(
        "User", foreign_keys=[user_id], back_populates="roles"
    )  # CC: Add back_populates for RBAC
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    scope_client = relationship("ClientAccount")
    scope_engagement = relationship("Engagement")

    def __repr__(self):
        return (
            f"<UserRole(id={self.id}, user_id={self.user_id}, role_type='{self.role_type}', "
            f"scope='{self.scope_type}')>"
        )

    @property
    def is_global_admin(self) -> bool:
        """Check if this is a global admin role."""
        return self.role_type == RoleType.PLATFORM_ADMIN and self.scope_type == "global"

    @property
    def is_client_admin(self) -> bool:
        """Check if this is a client admin role."""
        return self.role_type == RoleType.CLIENT_ADMIN and self.scope_type == "client"
