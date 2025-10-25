"""
Collection Flow Query Operations
Read-only database operations for collection flows including status, flow details,
gaps, and readiness assessments.

This module maintains backward compatibility by re-exporting all functions
from the modularized submodules.
"""

# Status operations
from .status import (
    get_collection_status,
    get_collection_flow,
)

# Analysis operations
from .analysis import (
    get_collection_gaps,
    get_collection_readiness,
    _get_readiness_recommendations,
)

# List operations
from .lists import (
    get_incomplete_flows,
    get_actively_incomplete_flows,
    get_all_flows,
)

# Re-export questionnaire functions for backward compatibility
from app.api.v1.endpoints.collection_crud_questionnaires import (
    get_adaptive_questionnaires,
)

__all__ = [
    # From questionnaires (re-exported)
    "get_adaptive_questionnaires",
    # From status
    "get_collection_status",
    "get_collection_flow",
    # From analysis
    "get_collection_gaps",
    "get_collection_readiness",
    "_get_readiness_recommendations",
    # From lists
    "get_incomplete_flows",
    "get_actively_incomplete_flows",
    "get_all_flows",
]
