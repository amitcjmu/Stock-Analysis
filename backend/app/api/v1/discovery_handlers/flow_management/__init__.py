"""
Flow Management Package

Modularized flow management handlers split into:
- handlers/: Individual operation handlers (create, status, update, delete)
- validators/: Flow and phase validation logic
- services/: Core business logic for flow operations
- utils/: Helper functions and utilities
"""

# Re-export main handler for backward compatibility
from .handlers.flow_handler import FlowManagementHandler

__all__ = ['FlowManagementHandler']