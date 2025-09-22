"""
Maintenance Windows API endpoints for Collection Gaps Phase 2.

This module provides endpoints for managing maintenance windows and blackout periods,
including CRUD operations with conflict detection and scheduling validation.

This is a compatibility module that imports from the modularized maintenance_windows package.
"""

# Import all public functions to maintain backward compatibility
from .maintenance_windows import (
    create_maintenance_window,
    delete_maintenance_window,
    list_maintenance_windows,
    router,
    update_maintenance_window,
)

# Export all public symbols
__all__ = [
    "router",
    "create_maintenance_window",
    "delete_maintenance_window",
    "list_maintenance_windows",
    "update_maintenance_window",
]
