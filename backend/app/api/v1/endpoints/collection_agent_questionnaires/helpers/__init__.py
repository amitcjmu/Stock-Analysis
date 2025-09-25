"""
Collection Agent Questionnaire Helpers
Utility functions for building agent context and managing generation state.

This module has been modularized to improve maintainability while preserving
backward compatibility. All public APIs remain the same.
"""

# Import all public functions to maintain backward compatibility
from .core import (
    build_agent_context,
    mark_generation_failed,
)

from .assets import (
    calculate_completeness,
)

from .gaps import (
    identify_gaps,
    identify_comprehensive_gaps,
    assess_6r_readiness_gaps,
    get_asset_type_overlay,
    get_asset_type_overlay_legacy,
)

# Context module functions are internal and imported where needed

# Maintain __all__ for explicit public API
__all__ = [
    "build_agent_context",
    "mark_generation_failed",
    "calculate_completeness",
    "identify_gaps",
    "identify_comprehensive_gaps",
    "assess_6r_readiness_gaps",
    "get_asset_type_overlay",
    "get_asset_type_overlay_legacy",
]
