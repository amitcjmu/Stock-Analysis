"""
Data Import Module - Modular architecture for data import endpoints.
Enhanced with multi-tenant context awareness and automatic session management.
"""

from fastapi import APIRouter

# Import all module routers
from .core_import import router as core_router
# ARCHIVED: field_mapping_legacy.py moved to archive/legacy
# TODO: Replace with modern field mapping implementation
# from .field_mapping_legacy import mapping_router
# from .quality_analysis import router as quality_router  # Disabled - DataQualityIssue model removed
from .critical_attributes import router as critical_router
from .learning_integration import router as learning_router
from .asset_processing import router as processing_router
# ARCHIVED: data_validation router depends on archived validation service
# from .data_validation import router as validation_router

# Create main router that combines all modules
router = APIRouter()

# Include all module routers with appropriate tags
router.include_router(core_router, tags=["Data Import Core"])
# ARCHIVED: mapping_router from field_mapping_legacy
# router.include_router(mapping_router, tags=["Field Mapping"])
# router.include_router(quality_router, tags=["Quality Analysis"])  # Disabled - DataQualityIssue model removed
router.include_router(critical_router, tags=["Critical Attributes"])
router.include_router(learning_router, tags=["AI Learning"])
router.include_router(processing_router, tags=["Asset Processing"])
# ARCHIVED: validation_router depends on archived services
# router.include_router(validation_router, tags=["Data Validation"])

__all__ = [
    "router",
    "core_router",
    # "mapping_router",  # ARCHIVED: field_mapping_legacy moved to archive
    # "quality_router",  # Disabled - DataQualityIssue model removed
    "critical_router",
    "learning_router", 
    "processing_router"
    # "validation_router"  # ARCHIVED
] 