"""
Router for discovery agent endpoints.

This module combines all discovery agent-related endpoints into a single router.
"""
from fastapi import APIRouter

# Import handlers
from .handlers.status import router as status_router
from .handlers.analysis import router as analysis_router
from .handlers.learning import router as learning_router
from .handlers.dependencies import router as dependencies_router

# Create the router
router = APIRouter(prefix="", tags=["discovery"])

# Include the sub-routers
router.include_router(status_router, prefix="/status")
router.include_router(analysis_router, prefix="/analysis")
router.include_router(learning_router, prefix="/learning")
router.include_router(dependencies_router, prefix="/dependencies")

__all__ = ["router"]
