"""
Enhanced Asset Inventory Management API
Leverages the agentic CrewAI framework with Asset Intelligence Agent for intelligent operations.

NOTE: This file has been modularized. All functionality has been moved to the asset_inventory/ subdirectory.
This file remains for backward compatibility and re-exports all public interfaces.
"""

# Re-export everything from the modularized structure
from .asset_inventory import (
    AssetAnalysisRequest,
    AssetClassificationRequest,
    AssetFeedbackRequest,
    BulkUpdatePlanRequest,
    get_asset_data,
    router,
)

# Export the router as the main interface
__all__ = [
    "router",
    "AssetAnalysisRequest",
    "BulkUpdatePlanRequest", 
    "AssetClassificationRequest",
    "AssetFeedbackRequest",
    "get_asset_data"
]