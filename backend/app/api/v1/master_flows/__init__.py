"""
Master Flows Module
Backward compatibility exports for the modularized master flows API
"""

from fastapi import APIRouter

from app.api.v1.api_tags import APITags

# Import routers from sub-modules
from .master_flows_analytics import router as analytics_router
from .master_flows_assessment import router as assessment_router
from .master_flows_crud import router as crud_router
from .planning import router as planning_router

# Create main router that combines all sub-routers for backward compatibility
router = APIRouter()
router.include_router(analytics_router)
router.include_router(assessment_router)
router.include_router(crud_router)
router.include_router(planning_router, prefix="/planning", tags=[APITags.PLANNING_FLOW])

# Export everything for backward compatibility
__all__ = [
    "router",  # Main export for backward compatibility
    "analytics_router",
    "assessment_router",
    "crud_router",
    "planning_router",
]
