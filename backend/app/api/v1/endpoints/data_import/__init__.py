"""
Data Import Module - Modular architecture for data import endpoints.
Enhanced with multi-tenant context awareness and automatic session management.
"""

from fastapi import APIRouter

# Import all module routers
from .core_import import router as core_router
# from .quality_analysis import router as quality_router  # Disabled - DataQualityIssue model removed
from .critical_attributes import router as critical_router
from .learning_integration import router as learning_router
from .asset_processing import router as processing_router

# Create main router that combines all modules
router = APIRouter()

# Include all module routers with appropriate tags
router.include_router(core_router, tags=["Data Import Core"])
# router.include_router(quality_router, tags=["Quality Analysis"])  # Disabled - DataQualityIssue model removed
router.include_router(critical_router, tags=["Critical Attributes"])
router.include_router(learning_router, tags=["AI Learning"])
router.include_router(processing_router, tags=["Asset Processing"])

__all__ = [
    "router",
    "core_router",
    # "quality_router",  # Disabled - DataQualityIssue model removed
    "critical_router",
    "learning_router", 
    "processing_router"
] 