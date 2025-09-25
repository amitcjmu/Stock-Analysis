"""
Collection Flow Questionnaire Query Operations
Questionnaire-specific CRUD operations for collection flows.

This module has been modularized to improve maintainability while preserving
backward compatibility. All public APIs remain the same.
"""

# Import all public functions to maintain backward compatibility
from .queries import (
    get_adaptive_questionnaires,
)

# Track background tasks to prevent memory leaks (shared across modules)
from .commands import _background_tasks

# Export the main public API
__all__ = [
    "get_adaptive_questionnaires",
    "_background_tasks",  # For external access if needed
]
