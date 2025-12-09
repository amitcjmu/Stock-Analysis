"""
Enhanced RBAC Service - Hierarchical role-based access control with proper data scoping.
Implements the correct role hierarchy: Platform Admin > Client Admin > Engagement Manager > Analyst > Viewer.

This module provides backward compatibility by exposing the main EnhancedRBACService class
that combines functionality from all modular components.
"""

from .access_control import RBACAccessControl
from .base import ENHANCED_RBAC_AVAILABLE, EnhancedRBACServiceBase
from .commands import RBACCommands
from .queries import RBACQueries
from .soft_delete import RBACSoftDelete
from .validators import RBACValidators


class EnhancedRBACService(
    EnhancedRBACServiceBase,
    RBACQueries,
    RBACCommands,
    RBACAccessControl,
    RBACSoftDelete,
    RBACValidators,
):
    """
    Enhanced RBAC service implementing hierarchical role-based access control.
    Provides proper data scoping, soft delete management, and platform admin oversight.

    This class combines all RBAC functionality through multiple inheritance:
    - Base: Database session and availability checking
    - Queries: Read operations for user profiles and permissions
    - Commands: Write operations for user profiles and roles
    - AccessControl: Permission checking and access validation
    - SoftDelete: Soft delete and purge operations
    - Validators: Validation and helper methods
    """

    pass


# Export the main service class for backward compatibility
__all__ = ["EnhancedRBACService", "ENHANCED_RBAC_AVAILABLE"]
