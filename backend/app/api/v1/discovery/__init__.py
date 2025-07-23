"""
CMDB Discovery Module
Modular organization of CMDB discovery functionality.
"""

# Import routers for modular endpoints
from .app_server_mappings import router as app_server_mappings_router
from .chat_interface import router as chat_interface_router
from .models import (AssetCoverage, CMDBAnalysisRequest, CMDBAnalysisResponse,
                     CMDBFeedbackRequest, CMDBProcessingRequest,
                     DataQualityResult, PageFeedbackRequest)
from .persistence import (add_processed_asset, backup_processed_assets,
                          clear_processed_assets, get_processed_assets,
                          initialize_persistence, load_from_file, save_to_file,
                          update_asset_by_id)
from .serialization import (clean_for_json_serialization,
                            ensure_json_serializable)
from .utils import (assess_6r_readiness, assess_migration_complexity,
                    generate_suggested_headers, get_field_value,
                    get_tech_stack, standardize_asset_type)

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
    "chat_interface_router",
]
