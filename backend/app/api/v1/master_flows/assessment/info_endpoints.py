"""
Assessment information endpoints.

MODULARIZED (November 2025): This file now re-exports from info_endpoints/ directory.

Original 544-line file split into:
- info_endpoints/queries.py: GET endpoints (applications, readiness, progress)
- info_endpoints/commands.py: PUT endpoints (complexity metrics)
- info_endpoints/schemas.py: Pydantic models

All imports remain backward compatible.
"""

from .info_endpoints import router

__all__ = ["router"]
