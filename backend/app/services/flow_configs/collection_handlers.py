"""
Collection Flow Handlers
ADCS: Handlers for Collection flow lifecycle and phase transitions

This file has been modularized for better maintainability. All functionality
has been moved to the collection_handlers/ module while maintaining backward compatibility.

Generated with CC for backend collection handler modularization.
"""

# Explicitly import all the main handler functions to maintain the original interface
from .collection_handlers import (
    # Lifecycle handlers
    collection_initialization,
    collection_finalization,
    collection_error_handler,
    collection_rollback_handler,
    collection_checkpoint_handler,
    # Phase-specific handlers
    platform_inventory_creation,
    adapter_preparation,
    collection_data_normalization,
    gap_analysis_preparation,
    gap_prioritization,
    questionnaire_generation,
    response_processing,
    synthesis_preparation,
    # Background operations
    start_crewai_collection_flow_background,
    # Asset operations
    apply_resolved_gaps_to_assets,
    # Helper functions (keeping private naming)
    CollectionHandlerBase as _CollectionHandlerBase,
    normalize_platform_data as _normalize_platform_data,
    get_question_template as _get_question_template,
    build_field_updates_from_rows as _build_field_updates_from_rows,
    clear_collected_data as _clear_collected_data,
    clear_gaps as _clear_gaps,
    clear_questionnaire_responses as _clear_questionnaire_responses,
    get_adapter_by_name as _get_adapter_by_name,
    initialize_adapter_registry as _initialize_adapter_registry,
)


# Re-export helper functions with original names for backward compatibility
def _get_collection_flow_by_master_id(db, master_flow_id):
    """Get collection flow by master flow ID - backward compatibility wrapper"""
    handler = _CollectionHandlerBase()
    return handler._get_collection_flow_by_master_id(db, master_flow_id)


# Re-export all the __all__ from the modular structure
__all__ = [
    # Lifecycle handlers
    "collection_initialization",
    "collection_finalization",
    "collection_error_handler",
    "collection_rollback_handler",
    "collection_checkpoint_handler",
    # Phase-specific handlers
    "platform_inventory_creation",
    "adapter_preparation",
    "collection_data_normalization",
    "gap_analysis_preparation",
    "gap_prioritization",
    "questionnaire_generation",
    "response_processing",
    "synthesis_preparation",
    # Background operations
    "start_crewai_collection_flow_background",
    # Asset operations
    "apply_resolved_gaps_to_assets",
]
