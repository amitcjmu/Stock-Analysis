"""
Main router for agent-related API endpoints.

This module combines all agent-related sub-routers into a single router
that can be included in the main FastAPI application.
"""
from fastapi import APIRouter

# Import sub-routers
from .discovery.router import router as discovery_router

# Create main router
router = APIRouter(prefix="/agents", tags=["agents"])

# Include sub-routers
router.include_router(discovery_router, prefix="/discovery")

__all__ = ["router"]
