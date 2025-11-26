"""
Plan API endpoints - modularized for maintainability.

This module aggregates all plan-related routers into a single router
for registration with the main API.

Modules:
- resources.py: Resource planning endpoints
- roadmap.py: Roadmap and timeline endpoints
- target.py: Target environment planning endpoints
- waveplanning.py: Wave planning and overview endpoints
- export.py: Export planning data endpoints
"""

from fastapi import APIRouter

# Import all sub-routers
from .resources import router as resources_router
from .roadmap import router as roadmap_router
from .target import router as target_router
from .waveplanning import router as waveplanning_router
from .export import router as export_router

# Create main router that combines all sub-routers
router = APIRouter()

# Include all sub-routers (no prefix needed as they define their own routes)
router.include_router(resources_router)
router.include_router(roadmap_router)
router.include_router(target_router)
router.include_router(waveplanning_router)
router.include_router(export_router)

# Re-export the main router for backward compatibility
__all__ = ["router"]
