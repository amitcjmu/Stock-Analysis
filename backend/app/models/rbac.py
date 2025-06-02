"""
Role-Based Access Control (RBAC) models for multi-tenant access management.
"""

try:
    from sqlalchemy import Column, String, Text, Boolean, DateTime, UUID, JSON, ForeignKey, Enum, Integer
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = String = Text = Boolean = DateTime = UUID = JSON = ForeignKey = Enum = Integer = object
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
    Extended user profile with RBAC and approval workflow.
    Extends the basic User model with approval and access control.
    """
    
    __tablename__ = "user_profiles"
    
    # Primary Key (references users.id)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    # User status and approval workflow
    status = Column(String(20), default=UserStatus.PENDING_APPROVAL, nullable=False, index=True)
    approval_requested_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Registration details
    registration_reason = Column(Text)  # Why they need access
    organization = Column(String(255))  # Their organization/company
    role_description = Column(String(255))  # Their role in their organization
    requested_access_level = Column(String(20), default=AccessLevel.READ_ONLY)
    
    # Contact and verification
    phone_number = Column(String(20))
    manager_email = Column(String(255))  # For verification
    linkedin_profile = Column(String(255))
    
    # Access tracking
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True))
    
    # Notification preferences
    notification_preferences = Column(JSON, default=lambda: {
        "email_notifications": True,
        "system_alerts": True,
        "learning_updates": False,
        "weekly_reports": True
    })
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    client_access = relationship("ClientAccess", back_populates="user_profile", cascade="all, delete-orphan")
    engagement_access = relationship("EngagementAccess", back_populates="user_profile", cascade="all, delete-orphan")
    
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
    User roles for different types of access.
    A user can have multiple roles across different contexts.
    """
    
    __tablename__ = "user_roles"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Role definition
    role_type = Column(String(50), nullable=False)  # RoleType enum
    role_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Scope and permissions
    permissions = Column(JSON, default=lambda: {
        "can_create_clients": False,
        "can_manage_engagements": False,
        "can_import_data": True,
        "can_export_data": True,
        "can_view_analytics": True,
        "can_manage_users": False,
        "can_configure_agents": False,
        "can_access_admin_console": False
    })
    
    # Context scope (global, client-specific, engagement-specific)
    scope_type = Column(String(20), default="global")  # global, client, engagement
    scope_client_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    scope_engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Role lifecycle
    is_active = Column(Boolean, default=True, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
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
    Client-level access control for users.
    Defines which clients a user can access and with what permissions.
    """
    
    __tablename__ = "client_access"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_profile_id = Column(PostgresUUID(as_uuid=True), ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False, index=True)
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Access level for this client
    access_level = Column(String(20), nullable=False)  # AccessLevel enum
    
    # Specific permissions for this client
    permissions = Column(JSON, default=lambda: {
        "can_view_data": True,
        "can_import_data": False,
        "can_export_data": False,
        "can_manage_engagements": False,
        "can_configure_client_settings": False,
        "can_manage_client_users": False
    })
    
    # Access restrictions
    restricted_environments = Column(JSON, default=lambda: [])  # Environments user cannot access
    restricted_data_types = Column(JSON, default=lambda: [])  # Data types user cannot access
    
    # Access lifecycle
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage tracking
    last_accessed_at = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
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
    Engagement-level access control for users.
    More granular access control within specific engagements.
    """
    
    __tablename__ = "engagement_access"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_profile_id = Column(PostgresUUID(as_uuid=True), ForeignKey('user_profiles.user_id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Access level for this engagement
    access_level = Column(String(20), nullable=False)  # AccessLevel enum
    
    # Engagement-specific role
    engagement_role = Column(String(100))  # "Project Manager", "Lead Analyst", "Stakeholder", etc.
    
    # Specific permissions for this engagement
    permissions = Column(JSON, default=lambda: {
        "can_view_data": True,
        "can_import_data": False,
        "can_export_data": False,
        "can_manage_sessions": False,
        "can_configure_agents": False,
        "can_approve_migration_decisions": False,
        "can_access_sensitive_data": False
    })
    
    # Session-level restrictions
    restricted_sessions = Column(JSON, default=lambda: [])  # Session IDs user cannot access
    allowed_session_types = Column(JSON, default=lambda: ["data_import", "validation_run"])
    
    # Access lifecycle
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime(timezone=True))  # Optional expiration
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage tracking
    last_accessed_at = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
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
    Audit log for tracking access attempts and administrative actions.
    """
    
    __tablename__ = "access_audit_log"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Who and what
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # login, access_granted, access_denied, etc.
    resource_type = Column(String(50))  # client, engagement, session, admin_console
    resource_id = Column(String(255))  # ID of the resource accessed
    
    # Context
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('data_import_sessions.id'), nullable=True)
    
    # Result and details
    result = Column(String(20), nullable=False)  # success, denied, error
    reason = Column(Text)  # Why access was granted/denied
    ip_address = Column(String(45))  # IPv4/IPv6 address
    user_agent = Column(Text)
    
    # Additional context
    details = Column(JSON, default=lambda: {})
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    session = relationship("DataImportSession")
    
    def __repr__(self):
        return f"<AccessAuditLog(id={self.id}, user_id={self.user_id}, action='{self.action_type}', result='{self.result}')>"
    
    @classmethod
    def log_access(cls, user_id: str, action_type: str, result: str, **kwargs):
        """Create an audit log entry."""
        return cls(
            user_id=user_id,
            action_type=action_type,
            result=result,
            **kwargs
        ) 