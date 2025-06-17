"""
Agent API endpoints package.

This package contains all agent-related API endpoints organized into submodules.
"""
from fastapi import APIRouter

# Create the main router without a prefix since it's already included in api.py
router = APIRouter(tags=["agents"])

# Import and include sub-routers and handlers
from .discovery.router import router as discovery_router
from .discovery.handlers.status import router as status_router

# Include sub-routers with appropriate prefixes
router.include_router(discovery_router, prefix="/discovery")
router.include_router(status_router, prefix="")

# Export the router
__all__ = ["router"]
