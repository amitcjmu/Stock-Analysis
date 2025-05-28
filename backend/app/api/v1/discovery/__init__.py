"""
CMDB Discovery Module
Modular organization of CMDB discovery functionality.
"""

from .models import (
    CMDBAnalysisRequest,
    CMDBProcessingRequest, 
    CMDBFeedbackRequest,
    DataQualityResult,
    AssetCoverage,
    CMDBAnalysisResponse
)

from .processor import CMDBDataProcessor
from .utils import (
    standardize_asset_type,
    get_field_value,
    get_tech_stack,
    generate_suggested_headers,
    assess_6r_readiness,
    assess_migration_complexity
)

__all__ = [
    "CMDBAnalysisRequest",
    "CMDBProcessingRequest", 
    "CMDBFeedbackRequest",
    "DataQualityResult",
    "AssetCoverage",
    "CMDBAnalysisResponse",
    "CMDBDataProcessor",
    "standardize_asset_type",
    "get_field_value",
    "get_tech_stack",
    "generate_suggested_headers",
    "assess_6r_readiness",
    "assess_migration_complexity"
] 