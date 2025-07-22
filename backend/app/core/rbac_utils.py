"""
RBAC utility functions for role-based access control
"""
from typing import Optional

from fastapi import HTTPException, status

from app.models import User
from app.models.rbac import RoleType


def check_user_role(user: User, allowed_roles: list[str]) -> bool:
    """
    Check if user has one of the allowed roles
    
    Args:
        user: User object with role information
        allowed_roles: List of allowed role types
        
    Returns:
        True if user has allowed role, False otherwise
    """
    # Get user role from UserRole or UserProfile relationship
    user_roles = []
    
    # Check if user has roles relationship
    if hasattr(user, 'roles') and user.roles:
        user_roles.extend([role.role_type for role in user.roles])
    
    # Check if user has profile with role_level
    if hasattr(user, 'profile') and user.profile:
        if hasattr(user.profile, 'role_level'):
            user_roles.append(user.profile.role_level)
    
    # Also check legacy role field if exists
    if hasattr(user, 'role') and user.role:
        user_roles.append(user.role)
    
    # Check if any user role is in allowed roles
    return any(role in allowed_roles for role in user_roles)


def require_role(user: User, allowed_roles: list[str], action: str = "perform this action") -> None:
    """
    Require user to have one of the allowed roles, raise 403 if not
    
    Args:
        user: User object with role information
        allowed_roles: List of allowed role types
        action: Description of the action for error message
        
    Raises:
        HTTPException: 403 if user doesn't have required role
    """
    if not check_user_role(user, allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. You need one of these roles to {action}: {', '.join(allowed_roles)}"
        )


# Role constants for collection flow operations
COLLECTION_CREATE_ROLES = [
    RoleType.PLATFORM_ADMIN.value,
    RoleType.CLIENT_ADMIN.value, 
    RoleType.ENGAGEMENT_MANAGER.value,
    RoleType.ANALYST.value,
    "admin",  # Legacy role
    "engagement_manager",  # Legacy role
    "analyst"  # Legacy role
]

COLLECTION_EDIT_ROLES = COLLECTION_CREATE_ROLES  # Same as create

COLLECTION_DELETE_ROLES = [
    RoleType.PLATFORM_ADMIN.value,
    RoleType.CLIENT_ADMIN.value,
    RoleType.ENGAGEMENT_MANAGER.value,
    "admin",  # Legacy role
    "engagement_manager"  # Legacy role
]

COLLECTION_VIEW_ROLES = [
    RoleType.PLATFORM_ADMIN.value,
    RoleType.CLIENT_ADMIN.value,
    RoleType.ENGAGEMENT_MANAGER.value,
    RoleType.ANALYST.value,
    RoleType.VIEWER.value,
    "admin",  # Legacy role
    "engagement_manager",  # Legacy role
    "analyst",  # Legacy role
    "user",  # Legacy role
    "viewer"  # Legacy role
]