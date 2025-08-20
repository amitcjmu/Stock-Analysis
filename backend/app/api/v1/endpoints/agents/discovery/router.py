"""
Router for discovery agent endpoints.

This module combines all discovery agent-related endpoints into a single router.
"""

from fastapi import APIRouter

from .handlers.agent_ui_integration import router as agent_ui_router
from .handlers.analysis import router as analysis_router
from .handlers.dependencies import router as dependencies_router
from .handlers.learning import router as learning_router

# Import handlers
from .handlers.status import router as status_router

# Create the router
router = APIRouter()

# Include the sub-routers
# Status endpoints are included directly (no prefix) so /agents/agent-status works
router.include_router(status_router)
router.include_router(analysis_router, prefix="/analysis")
router.include_router(learning_router, prefix="/learning")
router.include_router(dependencies_router, prefix="/dependencies")
router.include_router(agent_ui_router)  # No prefix for direct agent-status access

__all__ = ["router"]
