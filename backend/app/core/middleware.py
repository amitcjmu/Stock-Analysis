"""
FastAPI middleware for automatic context injection.
Extracts multi-tenant context from request headers and makes it available via context variables.

This module re-exports components from the middleware package for backward compatibility.
"""

# Re-export from middleware package for backward compatibility
from .middleware import (
    ContextMiddleware,
    RequestLoggingMiddleware,
    get_current_context_dependency,
    create_context_aware_dependency,
)

__all__ = [
    "ContextMiddleware",
    "RequestLoggingMiddleware",
    "get_current_context_dependency",
    "create_context_aware_dependency",
]
