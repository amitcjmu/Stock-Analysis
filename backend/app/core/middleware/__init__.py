"""
FastAPI middleware package for automatic context injection and security.

This package provides middleware components for:
- Multi-tenant context extraction and injection
- Admin access control and audit logging
- Request logging and monitoring
- Context-aware dependencies
"""

from .context_middleware import ContextMiddleware
from .request_logging import RequestLoggingMiddleware
from .dependencies import (
    get_current_context_dependency,
    create_context_aware_dependency,
)

__all__ = [
    "ContextMiddleware",
    "RequestLoggingMiddleware",
    "get_current_context_dependency",
    "create_context_aware_dependency",
]
