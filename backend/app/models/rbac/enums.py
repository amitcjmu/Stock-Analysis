"""
Enumerations for RBAC system.
"""

from enum import Enum as PyEnum


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
