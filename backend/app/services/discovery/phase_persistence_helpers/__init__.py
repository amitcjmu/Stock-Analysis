"""
Phase persistence helpers module.

Provides backward-compatible imports for all phase persistence functionality.
This module maintains the public API while the implementation is modularized.
"""

# Import all public APIs for backward compatibility
from .base import (
    PHASE_FLAG_MAP,
    VALID_PHASE_TRANSITIONS,
    PhaseTransitionResult,
)
from .persistence import (
    persist_error_with_classification,
    persist_field_mapping_completion,
    persist_if_changed,
    persist_phase_completion,
)
from .transitions import (
    advance_flow_phase,
    advance_phase,
)
from .utils import (
    extract_agent_insights,
    extract_next_phase,
)

# Re-export the private validation function for existing code that may use it
from .base import is_valid_transition as _is_valid_transition

__all__ = [
    # Constants
    "PHASE_FLAG_MAP",
    "VALID_PHASE_TRANSITIONS",
    # Data classes
    "PhaseTransitionResult",
    # Transition functions
    "advance_phase",
    "advance_flow_phase",
    # Persistence functions
    "persist_if_changed",
    "persist_error_with_classification",
    "persist_phase_completion",
    "persist_field_mapping_completion",
    # Utility functions
    "extract_agent_insights",
    "extract_next_phase",
    # Private functions (for existing tests)
    "_is_valid_transition",
    "is_valid_transition",  # Export the public version too
]
