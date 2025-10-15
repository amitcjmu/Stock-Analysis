"""
Assessment endpoints module (modularized October 2025).

Backward-compatible aggregation of all assessment endpoint routers.
Maintains the same public API as the original master_flows_assessment.py file.
"""

from fastapi import APIRouter

from .list_status_endpoints import router as list_status_router
from .info_endpoints import router as info_router
from .lifecycle_endpoints import router as lifecycle_router

# Create main router that combines all sub-routers
router = APIRouter()

# Include all sub-routers (order matters for route precedence)
router.include_router(list_status_router)
router.include_router(info_router)
router.include_router(lifecycle_router)

# Export for backward compatibility
__all__ = ["router"]
