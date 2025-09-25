"""
Collection Flow Serializers
Data transformation and serialization functions for collection flows including
model-to-response conversion, configuration builders, and metadata creation.

This module maintains backward compatibility by re-exporting all functions
from the modularized submodules.
"""

# Core serialization functions
from .core import (
    serialize_collection_flow,
    build_collection_flow_response,
    build_collection_config_from_discovery,
    build_collection_metrics_for_discovery_transition,
    build_gap_analysis_response,
    build_questionnaire_response,
)

# Response builder functions
from .responses import (
    build_collection_status_response,
    build_no_active_flow_response,
    build_execution_response,
    build_questionnaire_submission_response,
    build_readiness_response,
    build_continue_flow_response,
    build_delete_flow_response,
    build_cleanup_response,
    build_batch_delete_response,
)

# Utility functions
from .utils import (
    build_cleanup_flow_details,
    normalize_tenant_ids,
    build_application_snapshot,
    extract_application_ids_from_assets,
)

__all__ = [
    # Core functions
    "serialize_collection_flow",
    "build_collection_flow_response",
    "build_collection_config_from_discovery",
    "build_collection_metrics_for_discovery_transition",
    "build_gap_analysis_response",
    "build_questionnaire_response",
    # Response builders
    "build_collection_status_response",
    "build_no_active_flow_response",
    "build_execution_response",
    "build_questionnaire_submission_response",
    "build_readiness_response",
    "build_continue_flow_response",
    "build_delete_flow_response",
    "build_cleanup_response",
    "build_batch_delete_response",
    # Utils
    "build_cleanup_flow_details",
    "normalize_tenant_ids",
    "build_application_snapshot",
    "extract_application_ids_from_assets",
]
