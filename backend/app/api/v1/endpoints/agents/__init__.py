"""
Agent API endpoints package.

This package contains all agent-related API endpoints organized into submodules.
"""
from fastapi import APIRouter

# Create the main router
router = APIRouter(prefix="/agents", tags=["agents"])

# Import and include sub-routers
from .discovery.router import router as discovery_router

# Include sub-routers
router.include_router(discovery_router, prefix="/discovery")

# Export the router
__all__ = ["router"]
