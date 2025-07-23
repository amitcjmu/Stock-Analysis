"""
Context API Package

Modularized context management endpoints split into:
- api/: Route handlers for different context types
- services/: Business logic for context operations
- models/: Pydantic schemas and response models
"""

# Re-export router for backward compatibility
from .api import router
from .api.user_routes import get_user_context

__all__ = ["router", "get_user_context"]
