"""
User Management Handler for RBAC operations - Backward Compatibility Module.

This module provides backward compatibility while the handler has been
modularized into separate operation modules for better maintainability.

All existing imports will continue to work unchanged:
from app.services.rbac_handlers.user_management_handler import UserManagementHandler
"""

# Import the modular implementation
from .user_management.user_management_handler import UserManagementHandler

# Preserve backward compatibility - all existing imports continue to work
__all__ = ["UserManagementHandler"]
