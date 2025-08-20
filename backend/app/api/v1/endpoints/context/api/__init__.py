"""
Context API Routes

Combines all context-related routes into a single router.
"""

from fastapi import APIRouter

from .admin_routes import router as admin_router

# Import individual routers
from .client_routes import router as client_router
from .demo_routes import router as demo_router
from .engagement_routes import router as engagement_router
from .user_routes import router as user_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(client_router)
router.include_router(engagement_router)
router.include_router(user_router)
router.include_router(admin_router)
router.include_router(demo_router)

__all__ = ["router"]
