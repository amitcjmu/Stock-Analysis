"""
Maintenance Windows API module for Collection Gaps Phase 2.

This module preserves backward compatibility while providing modularized
maintenance window functionality for CRUD operations and conflict detection.
"""

# Import handlers to preserve public API
from .handlers import (
    create_maintenance_window,
    delete_maintenance_window,
    list_maintenance_windows,
    update_maintenance_window,
)

# Import router for FastAPI integration
from .handlers import router

__all__ = [
    "router",
    "create_maintenance_window",
    "delete_maintenance_window",
    "list_maintenance_windows",
    "update_maintenance_window",
]
