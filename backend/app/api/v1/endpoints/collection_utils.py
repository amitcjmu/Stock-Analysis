"""
Collection Flow Utilities - Main Module
Facade module that re-exports all collection utilities from modularized components.
Provides backward compatibility while maintaining clean separation of concerns.
"""

# Import all functions from modularized components
from app.api.v1.endpoints.collection_time_utils import (
    ensure_timezone_aware,
    calculate_time_since_creation,
    estimate_completion_time,
)

from app.api.v1.endpoints.collection_status_utils import (
    is_flow_stuck_in_initialization,
    determine_next_phase_status,
    calculate_progress_percentage,
)

from app.api.v1.endpoints.collection_mfo_utils import (
    create_mfo_flow,
    execute_mfo_phase,
    resume_mfo_flow,
    delete_mfo_flow,
    initialize_mfo_flow_execution,
    sync_collection_child_flow_state,
)

from app.api.v1.endpoints.collection_validation_utils import (
    validate_data_flow,
    log_collection_failure,
)

from app.api.v1.endpoints.collection_format_utils import (
    format_flow_display_name,
    safe_format_error,
    normalize_uuid,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Time utilities
    "ensure_timezone_aware",
    "calculate_time_since_creation",
    "estimate_completion_time",
    # Status utilities
    "is_flow_stuck_in_initialization",
    "determine_next_phase_status",
    "calculate_progress_percentage",
    # MFO utilities
    "create_mfo_flow",
    "execute_mfo_phase",
    "resume_mfo_flow",
    "delete_mfo_flow",
    "initialize_mfo_flow_execution",
    "sync_collection_child_flow_state",
    # Validation utilities
    "validate_data_flow",
    "log_collection_failure",
    # Format utilities
    "format_flow_display_name",
    "safe_format_error",
    "normalize_uuid",
]
