"""
Enhanced Role-Based Access Control (RBAC) models for hierarchical multi-tenant access management.
This redesign implements the proper role hierarchy: Platform Admin > Client Admin > Engagement Manager > Analyst > Viewer.
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
from typing import List, Dict, Any, Optional

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


class RoleLevel(str, PyEnum):
    """Role hierarchy levels."""
    PLATFORM_ADMIN = "platform_admin"      # Access to all data + platform management
    CLIENT_ADMIN = "client_admin"           # Access to specific client data + admin functions
    ENGAGEMENT_MANAGER = "engagement_manager"  # Access to specific engagement + management functions
    ANALYST = "analyst"                     # Read/write access within assigned scope
    VIEWER = "viewer"                       # Read-only access within assigned scope
    ANONYMOUS = "anonymous"                 # Demo data only


class DataScope(str, PyEnum):
    """Data access scopes."""
    PLATFORM = "platform"           # All data across all clients
    CLIENT = "client"               # All data for specific client
    ENGAGEMENT = "engagement"       # Data for specific engagement
    DEMO_ONLY = "demo_only"         # Only mock/demo data


class DeletedItemType(str, PyEnum):
    """Types of items that can be soft deleted."""
    CLIENT_ACCOUNT = "client_account"
    ENGAGEMENT = "engagement" 
    DATA_IMPORT_SESSION = "data_import_session"
    ASSET = "asset"
    USER_PROFILE = "user_profile"


class EnhancedUserProfile(Base):
    """
    Enhanced user profile with clear role hierarchy and data scoping.
    Replaces the existing UserProfile with simplified role management.
    """
    
    __tablename__ = "enhanced_user_profiles"
    
    # Primary Key
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    
    # Basic Profile Information
    status = Column(String(20), default=UserStatus.PENDING_APPROVAL, nullable=False, index=True)
    
    # Role and Access Scope
    role_level = Column(String(30), default=RoleLevel.VIEWER, nullable=False, index=True)
    data_scope = Column(String(20), default=DataScope.DEMO_ONLY, nullable=False, index=True)
    
    # Scope Context (null for platform admins, specific IDs for others)
    scope_client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    scope_engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Registration and Approval
    registration_reason = Column(Text)
    organization = Column(String(255))
    role_description = Column(String(255))
    phone_number = Column(String(20))
    manager_email = Column(String(255))
    
    # Approval Workflow
    approval_requested_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Access Tracking
    last_login_at = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    delete_reason = Column(Text)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    scope_client = relationship("ClientAccount")
    scope_engagement = relationship("Engagement")
    
    def __repr__(self):
        return f"<EnhancedUserProfile(user_id={self.user_id}, role='{self.role_level}', scope='{self.data_scope}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if user is approved, active, and not deleted."""
        return (self.status == UserStatus.ACTIVE and 
                not self.is_deleted)
    
    @property
    def is_platform_admin(self) -> bool:
        """Check if user has platform admin privileges."""
        return self.role_level == RoleLevel.PLATFORM_ADMIN
    
    @property
    def is_client_admin(self) -> bool:
        """Check if user has client admin privileges."""
        return self.role_level == RoleLevel.CLIENT_ADMIN
    
    @property
    def is_engagement_manager(self) -> bool:
        """Check if user has engagement manager privileges."""
        return self.role_level == RoleLevel.ENGAGEMENT_MANAGER
    
    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role_level in [RoleLevel.PLATFORM_ADMIN, RoleLevel.CLIENT_ADMIN, RoleLevel.ENGAGEMENT_MANAGER]
    
    @property
    def can_delete_data(self) -> bool:
        """Check if user can perform soft delete operations."""
        return self.role_level in [RoleLevel.PLATFORM_ADMIN, RoleLevel.CLIENT_ADMIN, RoleLevel.ENGAGEMENT_MANAGER]
    
    @property
    def can_purge_data(self) -> bool:
        """Check if user can permanently delete data."""
        return self.role_level == RoleLevel.PLATFORM_ADMIN
    
    def get_accessible_client_ids(self) -> List[str]:
        """Get list of client account IDs this user can access."""
        if self.role_level == RoleLevel.PLATFORM_ADMIN:
            return []  # Empty list means all clients
        elif self.data_scope == DataScope.CLIENT and self.scope_client_account_id:
            return [str(self.scope_client_account_id)]
        elif self.data_scope == DataScope.ENGAGEMENT and self.scope_client_account_id:
            return [str(self.scope_client_account_id)]
        else:
            return []  # No client access
    
    def get_accessible_engagement_ids(self) -> List[str]:
        """Get list of engagement IDs this user can access."""
        if self.role_level == RoleLevel.PLATFORM_ADMIN:
            return []  # Empty list means all engagements
        elif self.data_scope == DataScope.ENGAGEMENT and self.scope_engagement_id:
            return [str(self.scope_engagement_id)]
        else:
            return []  # No specific engagement access
    
    def can_access_client(self, client_account_id: str) -> bool:
        """Check if user can access specific client data."""
        if self.role_level == RoleLevel.PLATFORM_ADMIN:
            return True
        
        accessible_clients = self.get_accessible_client_ids()
        return not accessible_clients or client_account_id in accessible_clients
    
    def can_access_engagement(self, engagement_id: str, client_account_id: str = None) -> bool:
        """Check if user can access specific engagement data."""
        if self.role_level == RoleLevel.PLATFORM_ADMIN:
            return True
        
        # Check client access first
        if client_account_id and not self.can_access_client(client_account_id):
            return False
        
        # Check engagement access
        if self.data_scope == DataScope.ENGAGEMENT:
            return str(self.scope_engagement_id) == engagement_id
        elif self.data_scope == DataScope.CLIENT:
            return True  # Can access all engagements in accessible clients
        
        return False
    
    def soft_delete(self, deleted_by_user_id: str, reason: str = None):
        """Perform soft delete of user profile."""
        self.is_deleted = True
        self.deleted_at = func.now()
        self.deleted_by = deleted_by_user_id
        self.delete_reason = reason
        self.status = UserStatus.DEACTIVATED
    
    def restore(self):
        """Restore soft deleted user profile."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.delete_reason = None
        self.status = UserStatus.ACTIVE


class RolePermissions(Base):
    """
    Detailed permissions for each role level.
    Defines what actions each role can perform.
    """
    
    __tablename__ = "role_permissions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_level = Column(String(30), nullable=False, index=True)
    
    # Platform Management Permissions
    can_manage_platform_settings = Column(Boolean, default=False)
    can_manage_all_clients = Column(Boolean, default=False)
    can_manage_all_users = Column(Boolean, default=False)
    can_purge_deleted_data = Column(Boolean, default=False)
    can_view_system_logs = Column(Boolean, default=False)
    
    # Client Management Permissions
    can_create_clients = Column(Boolean, default=False)
    can_modify_client_settings = Column(Boolean, default=False)
    can_manage_client_users = Column(Boolean, default=False)
    can_delete_client_data = Column(Boolean, default=False)
    
    # Engagement Management Permissions
    can_create_engagements = Column(Boolean, default=False)
    can_modify_engagement_settings = Column(Boolean, default=False)
    can_manage_engagement_users = Column(Boolean, default=False)
    can_delete_engagement_data = Column(Boolean, default=False)
    
    # Data Permissions
    can_import_data = Column(Boolean, default=False)
    can_export_data = Column(Boolean, default=False)
    can_view_analytics = Column(Boolean, default=False)
    can_modify_data = Column(Boolean, default=False)
    
    # Agent Permissions
    can_configure_agents = Column(Boolean, default=False)
    can_view_agent_insights = Column(Boolean, default=False)
    can_approve_agent_decisions = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RolePermissions(role_level='{self.role_level}')>"


class SoftDeletedItems(Base):
    """
    Registry of soft-deleted items awaiting platform admin approval for permanent deletion.
    """
    
    __tablename__ = "soft_deleted_items"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Item Details
    item_type = Column(String(30), nullable=False, index=True)  # DeletedItemType enum
    item_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    item_name = Column(String(255))  # For display purposes
    
    # Context
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Deletion Details
    deleted_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    deleted_at = Column(DateTime(timezone=True), server_default=func.now())
    delete_reason = Column(Text)
    
    # Platform Admin Review
    reviewed_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True))
    review_decision = Column(String(20))  # 'approved', 'rejected', 'pending'
    review_notes = Column(Text)
    
    # Purge Details
    purged_at = Column(DateTime(timezone=True))
    purged_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Status
    status = Column(String(20), default='pending_review', index=True)  # pending_review, approved_for_purge, rejected, purged
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    purged_by_user = relationship("User", foreign_keys=[purged_by])
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    
    def __repr__(self):
        return f"<SoftDeletedItems(item_type='{self.item_type}', item_id={self.item_id}, status='{self.status}')>"
    
    def approve_for_purge(self, reviewed_by_user_id: str, notes: str = None):
        """Approve item for permanent deletion."""
        self.reviewed_by = reviewed_by_user_id
        self.reviewed_at = func.now()
        self.review_decision = 'approved'
        self.review_notes = notes
        self.status = 'approved_for_purge'
    
    def reject_purge(self, reviewed_by_user_id: str, notes: str = None):
        """Reject permanent deletion request."""
        self.reviewed_by = reviewed_by_user_id
        self.reviewed_at = func.now()
        self.review_decision = 'rejected'
        self.review_notes = notes
        self.status = 'rejected'
    
    def mark_purged(self, purged_by_user_id: str):
        """Mark item as permanently deleted."""
        self.purged_by = purged_by_user_id
        self.purged_at = func.now()
        self.status = 'purged'


class AccessAuditLog(Base):
    """
    Enhanced audit log for tracking all access attempts and administrative actions.
    """
    
    __tablename__ = "enhanced_access_audit_log"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who and what
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    
    # Context
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Result and details
    result = Column(String(20), nullable=False)  # success, denied, error
    reason = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Additional context
    details = Column(JSON, default=lambda: {})
    
    # Role and permissions at time of action
    user_role_level = Column(String(30))
    user_data_scope = Column(String(20))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    
    def __repr__(self):
        return f"<AccessAuditLog(user_id={self.user_id}, action='{self.action_type}', result='{self.result}')>"
    
    @classmethod
    def log_access(cls, user_id: str, action_type: str, result: str, **kwargs):
        """Create an audit log entry."""
        return cls(
            user_id=user_id,
            action_type=action_type,
            result=result,
            **kwargs
        )


# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    RoleLevel.PLATFORM_ADMIN: {
        'can_manage_platform_settings': True,
        'can_manage_all_clients': True,
        'can_manage_all_users': True,
        'can_purge_deleted_data': True,
        'can_view_system_logs': True,
        'can_create_clients': True,
        'can_modify_client_settings': True,
        'can_manage_client_users': True,
        'can_delete_client_data': True,
        'can_create_engagements': True,
        'can_modify_engagement_settings': True,
        'can_manage_engagement_users': True,
        'can_delete_engagement_data': True,
        'can_import_data': True,
        'can_export_data': True,
        'can_view_analytics': True,
        'can_modify_data': True,
        'can_configure_agents': True,
        'can_view_agent_insights': True,
        'can_approve_agent_decisions': True,
    },
    RoleLevel.CLIENT_ADMIN: {
        'can_manage_platform_settings': False,
        'can_manage_all_clients': False,
        'can_manage_all_users': False,
        'can_purge_deleted_data': False,
        'can_view_system_logs': False,
        'can_create_clients': False,
        'can_modify_client_settings': True,
        'can_manage_client_users': True,
        'can_delete_client_data': True,
        'can_create_engagements': True,
        'can_modify_engagement_settings': True,
        'can_manage_engagement_users': True,
        'can_delete_engagement_data': True,
        'can_import_data': True,
        'can_export_data': True,
        'can_view_analytics': True,
        'can_modify_data': True,
        'can_configure_agents': True,
        'can_view_agent_insights': True,
        'can_approve_agent_decisions': True,
    },
    RoleLevel.ENGAGEMENT_MANAGER: {
        'can_manage_platform_settings': False,
        'can_manage_all_clients': False,
        'can_manage_all_users': False,
        'can_purge_deleted_data': False,
        'can_view_system_logs': False,
        'can_create_clients': False,
        'can_modify_client_settings': False,
        'can_manage_client_users': False,
        'can_delete_client_data': False,
        'can_create_engagements': False,
        'can_modify_engagement_settings': True,
        'can_manage_engagement_users': True,
        'can_delete_engagement_data': True,
        'can_import_data': True,
        'can_export_data': True,
        'can_view_analytics': True,
        'can_modify_data': True,
        'can_configure_agents': False,
        'can_view_agent_insights': True,
        'can_approve_agent_decisions': True,
    },
    RoleLevel.ANALYST: {
        'can_manage_platform_settings': False,
        'can_manage_all_clients': False,
        'can_manage_all_users': False,
        'can_purge_deleted_data': False,
        'can_view_system_logs': False,
        'can_create_clients': False,
        'can_modify_client_settings': False,
        'can_manage_client_users': False,
        'can_delete_client_data': False,
        'can_create_engagements': False,
        'can_modify_engagement_settings': False,
        'can_manage_engagement_users': False,
        'can_delete_engagement_data': False,
        'can_import_data': True,
        'can_export_data': True,
        'can_view_analytics': True,
        'can_modify_data': True,
        'can_configure_agents': False,
        'can_view_agent_insights': True,
        'can_approve_agent_decisions': False,
    },
    RoleLevel.VIEWER: {
        'can_manage_platform_settings': False,
        'can_manage_all_clients': False,
        'can_manage_all_users': False,
        'can_purge_deleted_data': False,
        'can_view_system_logs': False,
        'can_create_clients': False,
        'can_modify_client_settings': False,
        'can_manage_client_users': False,
        'can_delete_client_data': False,
        'can_create_engagements': False,
        'can_modify_engagement_settings': False,
        'can_manage_engagement_users': False,
        'can_delete_engagement_data': False,
        'can_import_data': False,
        'can_export_data': True,
        'can_view_analytics': True,
        'can_modify_data': False,
        'can_configure_agents': False,
        'can_view_agent_insights': True,
        'can_approve_agent_decisions': False,
    },
    RoleLevel.ANONYMOUS: {
        'can_manage_platform_settings': False,
        'can_manage_all_clients': False,
        'can_manage_all_users': False,
        'can_purge_deleted_data': False,
        'can_view_system_logs': False,
        'can_create_clients': False,
        'can_modify_client_settings': False,
        'can_manage_client_users': False,
        'can_delete_client_data': False,
        'can_create_engagements': False,
        'can_modify_engagement_settings': False,
        'can_manage_engagement_users': False,
        'can_delete_engagement_data': False,
        'can_import_data': False,
        'can_export_data': False,
        'can_view_analytics': True,
        'can_modify_data': False,
        'can_configure_agents': False,
        'can_view_agent_insights': False,
        'can_approve_agent_decisions': False,
    }
} 