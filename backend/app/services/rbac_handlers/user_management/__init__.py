"""
User Management Handler Module - Modularized RBAC operations.

This module provides a backward-compatible API while splitting the large
UserManagementHandler into smaller, focused modules.
"""

# Import all components to maintain backward compatibility
from .registration_operations import RegistrationOperations
from .approval_operations import ApprovalOperations
from .user_state_operations import UserStateOperations
from .profile_operations import ProfileOperations
from .user_management_handler import UserManagementHandler

# Preserve public API - existing imports will continue to work
__all__ = [
    "UserManagementHandler",
    "RegistrationOperations",
    "ApprovalOperations",
    "UserStateOperations",
    "ProfileOperations",
]
