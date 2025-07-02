"""
Flow Management Handler - Modularized

This file now imports from the modularized flow_management package.
The original 1,352-line file has been split into:

- handlers/: Individual operation handlers (create, status, update, delete)
- validators/: Flow and phase validation logic
- services/: Core business logic for flow operations
- utils/: Helper functions and utilities

For backward compatibility, the FlowManagementHandler is re-exported.
"""

# Re-export the main handler from the package
from .flow_management.handlers.flow_handler import FlowManagementHandler

__all__ = ['FlowManagementHandler']