"""
Master Flows Module
Backward compatibility exports for the modularized master flows API
"""

from fastapi import APIRouter

# Import routers from sub-modules
from .master_flows_analytics import router as analytics_router
from .master_flows_assessment import router as assessment_router
from .master_flows_crud import router as crud_router

# Create main router that combines all sub-routers for backward compatibility
router = APIRouter()
router.include_router(analytics_router)
router.include_router(assessment_router)
router.include_router(crud_router)

# Export everything for backward compatibility
__all__ = [
    "router",  # Main export for backward compatibility
    "analytics_router",
    "assessment_router",
    "crud_router",
]
