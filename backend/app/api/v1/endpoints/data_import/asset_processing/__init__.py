"""
Asset Processing Module - Asset creation and processing workflows.
Handles raw data to asset conversion, CrewAI integration, and agentic processing.

This module has been modularized for maintainability while preserving backward compatibility.
All existing imports continue to work as before.
"""

# Import router from handlers to preserve backward compatibility
from .handlers import router

# Import processors and utilities for internal use
from .processors import (
    fallback_raw_to_assets_processing,
    process_single_raw_record_agentic,
)
from .utils import determine_asset_type_agentic, get_safe_context

# Export all public APIs to maintain backward compatibility
__all__ = [
    "router",
    "process_single_raw_record_agentic",
    "determine_asset_type_agentic",
    "fallback_raw_to_assets_processing",
    "get_safe_context",
]
