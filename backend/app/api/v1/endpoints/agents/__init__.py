"""
Agent API endpoints package.

This package contains all agent-related API endpoints organized into submodules.
"""

from fastapi import APIRouter

from .discovery.handlers.status import router as status_router
from .discovery.router import router as discovery_router

# Create the main router without a prefix since it's already included in api.py
router = APIRouter()

# Include sub-routers with appropriate prefixes
router.include_router(discovery_router, prefix="/discovery")
router.include_router(status_router, prefix="")

# Export the router
__all__ = ["router"]
