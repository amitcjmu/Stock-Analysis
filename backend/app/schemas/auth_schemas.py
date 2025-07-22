"""
Authentication and RBAC Schemas
Pydantic schemas for user registration, approval, and access control.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

# =========================
# Enums for Type Safety
# =========================

class UserStatusEnum(str, Enum):
    """User status in the system."""
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"

class AccessLevelEnum(str, Enum):
    """Access levels for users."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class RoleTypeEnum(str, Enum):
    """Types of roles in the system."""
    PLATFORM_ADMIN = "platform_admin"
    CLIENT_ADMIN = "client_admin"
    ENGAGEMENT_MANAGER = "engagement_manager"
    ANALYST = "analyst"
    VIEWER = "viewer"

# =========================
# Token Schemas
# =========================

class Token(BaseModel):
    """Schema for the access token."""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Schema for the JWT payload."""
    sub: Optional[str] = None # Subject (user_id)

# =========================
# User Registration Schemas
# =========================

class LoginRequest(BaseModel):
    """Schema for user login request."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class LoginResponse(BaseModel):
    """Schema for user login response."""
    status: str
    message: str
    user: Optional[Dict[str, Any]] = None
    token: Optional[Token] = None

class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info: ValidationInfo) -> str:
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordChangeResponse(BaseModel):
    """Schema for password change response."""
    status: str
    message: str

class UserRegistrationRequest(BaseModel):
    """Schema for user registration request."""
    email: str = Field(..., description="User's business email address", pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    full_name: str = Field(..., min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=2, max_length=50, description="Optional username for the user")
    organization: str = Field(..., min_length=2, max_length=255)
    role_description: str = Field(..., min_length=5, max_length=255)
    registration_reason: str = Field(..., min_length=10, max_length=1000)
    requested_access_level: AccessLevelEnum = AccessLevelEnum.READ_ONLY
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    manager_email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    linkedin_profile: Optional[str] = Field(None, max_length=255)
    notification_preferences: Optional[Dict[str, bool]] = {
        "email_notifications": True,
        "system_alerts": True,
        "learning_updates": False,
        "weekly_reports": True
    }
    
    # Admin user creation fields
    password: Optional[str] = Field(None, min_length=8, description="Password for admin-created users")
    access_level: Optional[AccessLevelEnum] = None
    role_name: Optional[str] = Field(None, max_length=100, description="Role name for admin-created users")
    is_active: Optional[bool] = Field(None, description="Whether user should be immediately active")
    notes: Optional[str] = Field(None, max_length=1000, description="Admin notes about the user")
    default_client_id: Optional[str] = Field(None, description="Default client account for the user")
    default_engagement_id: Optional[str] = Field(None, description="Default engagement for the user")
    
    @field_validator('registration_reason')
    @classmethod
    def validate_registration_reason(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Registration reason must be at least 10 characters')
        return v.strip()
    
    @field_validator('organization')
    @classmethod
    def validate_organization(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError('Organization name must be at least 2 characters')
        return v.strip()

class UserRegistrationResponse(BaseModel):
    """Schema for user registration response."""
    status: str
    message: str
    user_profile_id: Optional[str] = None
    approval_status: Optional[str] = None

# =========================
# User Approval Schemas
# =========================

class ClientAccessRequest(BaseModel):
    """Schema for client access during approval."""
    client_id: str
    access_level: AccessLevelEnum = AccessLevelEnum.READ_ONLY
    permissions: Optional[Dict[str, bool]] = None
    restricted_environments: Optional[List[str]] = []
    restricted_data_types: Optional[List[str]] = []
    expires_at: Optional[datetime] = None

class UserApprovalRequest(BaseModel):
    """Schema for approving a user."""
    user_id: str
    access_level: AccessLevelEnum = AccessLevelEnum.READ_ONLY
    role_name: str = Field(default="Analyst", max_length=100)
    client_access: List[ClientAccessRequest] = []
    approval_notes: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('client_access')
    @classmethod
    def validate_client_access(cls, v: List[ClientAccessRequest]) -> List[ClientAccessRequest]:
        if not v:
            raise ValueError('At least one client access must be specified')
        return v

class UserApprovalResponse(BaseModel):
    """Schema for user approval response."""
    status: str
    message: str
    user_id: str
    access_level: str
    client_access_count: int

class UserRejectionRequest(BaseModel):
    """Schema for rejecting a user."""
    user_id: str
    rejection_reason: str = Field(..., min_length=10, max_length=1000)
    
    @field_validator('rejection_reason')
    @classmethod
    def validate_rejection_reason(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Rejection reason must be at least 10 characters')
        return v.strip()

class UserRejectionResponse(BaseModel):
    """Schema for user rejection response."""
    status: str
    message: str
    user_id: str
    reason: str

# =========================
# Pending Approvals Schemas
# =========================

class PendingUserProfile(BaseModel):
    """Schema for pending user profile."""
    user_id: str
    organization: str
    role_description: str
    registration_reason: str
    requested_access_level: str
    manager_email: Optional[str] = None
    phone_number: Optional[str] = None
    requested_at: Optional[str] = None

class PendingApprovalsResponse(BaseModel):
    """Schema for pending approvals response."""
    status: str
    pending_approvals: List[PendingUserProfile]
    total_pending: int

# =========================
# Access Control Schemas
# =========================

class AccessValidationRequest(BaseModel):
    """Schema for access validation request."""
    user_id: str
    resource_type: str = Field(..., pattern=r'^(client|engagement|admin_console|data|session)$')
    resource_id: Optional[str] = None
    action: str = Field(default="read", pattern=r'^(read|write|delete|admin|manage)$')

class AccessValidationResponse(BaseModel):
    """Schema for access validation response."""
    has_access: bool
    reason: str

class ClientAccessGrant(BaseModel):
    """Schema for granting client access."""
    user_id: str
    client_id: str
    access_level: AccessLevelEnum = AccessLevelEnum.READ_ONLY
    permissions: Optional[Dict[str, bool]] = None
    restricted_environments: Optional[List[str]] = []
    restricted_data_types: Optional[List[str]] = []
    expires_at: Optional[datetime] = None

class ClientAccessGrantResponse(BaseModel):
    """Schema for client access grant response."""
    status: str
    message: str
    user_id: str
    client_id: str
    access_level: str

# =========================
# User Profile Schemas
# =========================

class UserProfileInfo(BaseModel):
    """Schema for user profile information."""
    user_id: str
    status: UserStatusEnum
    organization: str
    role_description: str
    requested_access_level: AccessLevelEnum
    phone_number: Optional[str] = None
    manager_email: Optional[str] = None
    notification_preferences: Dict[str, bool]
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

# Alias for backward compatibility or simpler imports
User = UserProfileInfo

class UserRoleInfo(BaseModel):
    """Schema for user role information."""
    id: str
    role_type: RoleTypeEnum
    role_name: str
    description: Optional[str] = None
    permissions: Dict[str, bool]
    scope_type: str = "global"
    scope_client_id: Optional[str] = None
    scope_engagement_id: Optional[str] = None
    is_active: bool = True
    assigned_at: datetime
    expires_at: Optional[datetime] = None

class ClientAccessInfo(BaseModel):
    """Schema for client access information."""
    id: str
    client_account_id: str
    access_level: AccessLevelEnum
    permissions: Dict[str, bool]
    restricted_environments: List[str] = []
    restricted_data_types: List[str] = []
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0

# =========================
# Logging and Monitoring Schemas
# =========================

class AccessLogEntry(BaseModel):
    """Schema for access log entry."""
    id: str
    user_id: str
    action_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: str
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    session_id: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: datetime

class AccessLogResponse(BaseModel):
    """Schema for access log response."""
    status: str
    logs: List[AccessLogEntry]
    total_logs: int
    page: int = 1
    page_size: int = 50

# =========================
# Dashboard and Analytics Schemas
# =========================

class AdminDashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""
    total_users: int
    pending_approvals: int
    active_users: int
    suspended_users: int
    total_clients: int
    total_engagements: int
    total_sessions_today: int
    recent_registrations: List[PendingUserProfile]
    recent_access_logs: List[AccessLogEntry]

class SystemHealthStatus(BaseModel):
    """Schema for system health status."""
    rbac_system: str = "healthy"
    database_connection: str = "healthy"
    authentication_service: str = "healthy"
    audit_logging: str = "healthy"
    user_approval_workflow: str = "healthy"
    last_check: datetime

# =========================
# Generic/Utility Schemas
# =========================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    """Schema for success responses."""
    status: str = "success"
    message: str
    data: Optional[Dict[str, Any]] = None

# =========================
# Pagination and Filtering Schemas
# =========================

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)

class SortParams(BaseModel):
    """Schema for sorting parameters."""
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", pattern=r'^(asc|desc)$')

class FilterParams(BaseModel):
    """Schema for filtering parameters."""
    status: Optional[UserStatusEnum] = None
    access_level: Optional[AccessLevelEnum] = None
    organization: Optional[str] = None
    role_type: Optional[RoleTypeEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class UserProfileUpdateRequest(BaseModel):
    """Schema for updating user profile information."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    organization: Optional[str] = Field(None, min_length=2, max_length=255)
    role_description: Optional[str] = Field(None, min_length=5, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    manager_email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    linkedin_profile: Optional[str] = Field(None, max_length=255)
    notification_preferences: Optional[Dict[str, bool]] = None 