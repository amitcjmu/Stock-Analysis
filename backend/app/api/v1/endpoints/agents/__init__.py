"""
Agent API endpoints package.

This package contains all agent-related API endpoints organized into submodules.
"""

from fastapi import APIRouter

from .discovery.router import router as discovery_router

# Create the main router without a prefix since it's already included in api.py
router = APIRouter()

# Include sub-routers with appropriate prefixes
# NOTE: status_router is included under discovery_router, not at root level
# Frontend uses /agents/discovery/status, not /agents/status
router.include_router(discovery_router, prefix="/discovery")

# Export the router
__all__ = ["router"]
