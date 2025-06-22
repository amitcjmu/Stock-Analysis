"""
CMDB Discovery Module
Modular organization of CMDB discovery functionality.
"""

from .models import (
    CMDBAnalysisRequest,
    CMDBProcessingRequest, 
    CMDBFeedbackRequest,
    PageFeedbackRequest,
    DataQualityResult,
    AssetCoverage,
    CMDBAnalysisResponse
)

from .utils import (
    standardize_asset_type,
    get_field_value,
    get_tech_stack,
    generate_suggested_headers,
    assess_6r_readiness,
    assess_migration_complexity
)

from .persistence import (
    save_to_file,
    load_from_file,
    backup_processed_assets,
    initialize_persistence,
    get_processed_assets,
    add_processed_asset,
    clear_processed_assets,
    update_asset_by_id
)

from .serialization import (
    clean_for_json_serialization,
    ensure_json_serializable
)

# Import routers for modular endpoints
from .app_server_mappings import router as app_server_mappings_router
from .testing_endpoints import router as testing_endpoints_router
from .chat_interface import router as chat_interface_router

__all__ = [
    # Models
    "CMDBAnalysisRequest",
    "CMDBProcessingRequest", 
    "CMDBFeedbackRequest",
    "PageFeedbackRequest",
    "DataQualityResult",
    "AssetCoverage",
    "CMDBAnalysisResponse",
    
    # Core functionality
    "standardize_asset_type",
    "get_field_value",
    "get_tech_stack",
    "generate_suggested_headers",
    "assess_6r_readiness",
    "assess_migration_complexity",
    
    # Persistence
    "save_to_file",
    "load_from_file",
    "backup_processed_assets",
    "initialize_persistence",
    "get_processed_assets",
    "add_processed_asset",
    "clear_processed_assets",
    "update_asset_by_id",
    
    # Serialization
    "clean_for_json_serialization",
    "ensure_json_serializable",
    
    # Routers
    "app_server_mappings_router",
    "testing_endpoints_router",
    "chat_interface_router"
] 