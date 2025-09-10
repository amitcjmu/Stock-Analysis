"""
Master Flows Module
Backward compatibility exports for the modularized master flows API
"""

# Import routers from sub-modules
from .master_flows_analytics import router as analytics_router
from .master_flows_assessment import router as assessment_router
from .master_flows_crud import router as crud_router

# Export sub-routers for selective inclusion if needed
__all__ = [
    "analytics_router",
    "assessment_router", 
    "crud_router",
]