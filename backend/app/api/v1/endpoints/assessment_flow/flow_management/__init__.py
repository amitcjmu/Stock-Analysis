"""
Assessment flow management module.
Modularized endpoints for flow creation, status, updates, and navigation.

This module maintains 100% backward compatibility with original imports.
The router is created by aggregating individual endpoint modules:
- create.py: Flow initialization endpoints
- queries.py: Flow status and retrieval endpoints
- update.py: Flow resume and phase navigation endpoints

All endpoints use MFO integration (ADR-006) for unified state management.
"""

from fastapi import APIRouter

# Import routers from modularized components
from .create import router as create_router
from .queries import router as queries_router
from .update import router as update_router

# Create aggregated router that combines all endpoints
router = APIRouter()

# Include all modularized routers
router.include_router(create_router)
router.include_router(queries_router)
router.include_router(update_router)

__all__ = ["router"]
