"""
Asset Inventory module exports.
Re-exports all routers and models for backward compatibility.
"""

from fastapi import APIRouter

# Import all sub-routers
from .intelligence import router as intelligence_router
from .audit import router as audit_router
from .crud import router as crud_router
from .pagination import router as pagination_router
from .analysis import router as analysis_router

# Import models for re-export
from .models import (
    AssetAnalysisRequest,
    BulkUpdatePlanRequest,
    AssetClassificationRequest,
    AssetFeedbackRequest
)

# Import utils for re-export
from .utils import get_asset_data

# Create main router that combines all sub-routers
router = APIRouter(tags=["Asset Inventory"])

# Include all sub-routers
router.include_router(intelligence_router)
router.include_router(audit_router)
router.include_router(crud_router)
router.include_router(pagination_router)
router.include_router(analysis_router)

# Export everything that was previously exported from the main file
__all__ = [
    "router",
    "AssetAnalysisRequest",
    "BulkUpdatePlanRequest",
    "AssetClassificationRequest",
    "AssetFeedbackRequest",
    "get_asset_data"
]