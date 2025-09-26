"""
Role-Based Access Control (RBAC) models for multi-tenant access management.

This module has been modularized for better maintainability. All classes and enums
are still available via this import path for backward compatibility.
"""

# Import all classes and enums from the modularized package
from .enums import UserStatus, AccessLevel, RoleType
from .models import (
    UserProfile,
    UserRole,
    ClientAccess,
    EngagementAccess,
    AccessAuditLog,
)

__all__ = [
    "UserStatus",
    "AccessLevel",
    "RoleType",
    "UserProfile",
    "UserRole",
    "ClientAccess",
    "EngagementAccess",
    "AccessAuditLog",
]
