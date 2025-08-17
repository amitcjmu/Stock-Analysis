"""
Collection Flow Handlers
ADCS: Modularized collection flow handlers with backward compatibility

This module provides all collection flow handlers through a modular structure
while maintaining complete backward compatibility with the original interface.

The handlers are organized into logical modules:
- lifecycle_handlers: Flow lifecycle management (init, finalize, error, rollback, checkpoint)
- data_handlers: Data processing and normalization
- platform_handlers: Platform detection and adapter management
- questionnaire_handlers: Questionnaire generation and response processing
- asset_handlers: Asset write-back operations
- background_handlers: Async/background processing
- base: Common utilities and base classes
- exceptions: Handler-specific exceptions
"""

# Import all handler functions for backward compatibility
from .lifecycle_handlers import (
    collection_initialization,
    collection_finalization,
)

from .error_handlers import (
    collection_error_handler,
    collection_rollback_handler,
    collection_checkpoint_handler,
)

from .data_handlers import (
    collection_data_normalization,
    gap_analysis_preparation,
    gap_prioritization,
    synthesis_preparation,
)

from .asset_handlers import (
    apply_resolved_gaps_to_assets,
    _resolve_target_asset_ids,
)

from .platform_handlers import (
    platform_inventory_creation,
    adapter_preparation,
)

from .questionnaire_handlers import (
    questionnaire_generation,
    response_processing,
)

from .background_handlers import (
    start_crewai_collection_flow_background,
    _start_crewai_collection_flow_background,
)

from .base import (
    CollectionHandlerBase,
    normalize_platform_data,
    get_question_template,
    build_field_updates_from_rows,
    clear_collected_data,
    clear_gaps,
    clear_questionnaire_responses,
    get_adapter_by_name,
    initialize_adapter_registry,
)

from .exceptions import (
    CollectionFlowError,
    CollectionFlowNotFoundError,
    CollectionInitializationError,
    CollectionFinalizationError,
    PlatformDetectionError,
    AdapterPreparationError,
    DataNormalizationError,
    GapAnalysisError,
    QuestionnaireGenerationError,
    ResponseProcessingError,
    DataSynthesisError,
    CrewAIExecutionError,
    WriteBackError,
    TenantContextError,
    RollbackError,
    CheckpointError,
    ValidationError,
    AdapterError,
    ConfigurationError,
    DataQualityError,
    DataCollectionError,
)

# Backward compatibility aliases for private functions that were in the original module
_get_collection_flow_by_master_id = (
    CollectionHandlerBase()._get_collection_flow_by_master_id
)
_initialize_adapter_registry = initialize_adapter_registry
_get_adapter_by_name = get_adapter_by_name
_normalize_platform_data = normalize_platform_data
_clear_collected_data = clear_collected_data
_clear_gaps = clear_gaps
_clear_questionnaire_responses = clear_questionnaire_responses
_get_question_template = get_question_template
_build_field_updates_from_rows = build_field_updates_from_rows
_apply_resolved_gaps_to_assets = apply_resolved_gaps_to_assets

# Export all handlers exactly as they were in the original module
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
    # Background processing
    "start_crewai_collection_flow_background",
    "_start_crewai_collection_flow_background",
    # Asset operations
    "apply_resolved_gaps_to_assets",
    "_apply_resolved_gaps_to_assets",
    "_resolve_target_asset_ids",
    # Utility functions (exposed for testing/debugging)
    "normalize_platform_data",
    "get_question_template",
    "build_field_updates_from_rows",
    "clear_collected_data",
    "clear_gaps",
    "clear_questionnaire_responses",
    "get_adapter_by_name",
    "initialize_adapter_registry",
    # Private function aliases (backward compatibility)
    "_get_collection_flow_by_master_id",
    "_initialize_adapter_registry",
    "_get_adapter_by_name",
    "_normalize_platform_data",
    "_clear_collected_data",
    "_clear_gaps",
    "_clear_questionnaire_responses",
    "_get_question_template",
    "_build_field_updates_from_rows",
    # Base classes
    "CollectionHandlerBase",
    # Exceptions
    "CollectionFlowError",
    "CollectionFlowNotFoundError",
    "CollectionInitializationError",
    "CollectionFinalizationError",
    "PlatformDetectionError",
    "AdapterPreparationError",
    "DataNormalizationError",
    "GapAnalysisError",
    "QuestionnaireGenerationError",
    "ResponseProcessingError",
    "DataSynthesisError",
    "CrewAIExecutionError",
    "WriteBackError",
    "TenantContextError",
    "RollbackError",
    "CheckpointError",
    "ValidationError",
    "AdapterError",
    "ConfigurationError",
    "DataQualityError",
    "DataCollectionError",
]
