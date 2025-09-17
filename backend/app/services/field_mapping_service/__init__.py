"""
Field Mapping Service for Service Registry Architecture

This service provides field mapping capabilities for the discovery flow,
following the Service Registry pattern with proper session management
and multi-tenant context propagation.

This module maintains backward compatibility by exporting all original classes
and functions from the modularized structure.
"""

# Import from modularized structure
from .base import MappingAnalysis, MappingRule, BASE_MAPPINGS, REQUIRED_FIELDS
from .service import FieldMappingService
from .mappers import FieldMappingAnalyzer
from .validators import FieldMappingValidator
from .utils import (
    calculate_field_similarity,
    normalize_field_name,
    extract_field_components,
    find_fuzzy_matches,
    get_asset_type_priority_fields,
    suggest_field_corrections,
    analyze_field_patterns,
    validate_field_name_format,
    get_field_type_hints,
)

# Export everything that was available in the original file
__all__ = [
    # Core classes
    "FieldMappingService",
    "FieldMappingAnalyzer",
    "FieldMappingValidator",
    # Data classes
    "MappingAnalysis",
    "MappingRule",
    # Constants
    "BASE_MAPPINGS",
    "REQUIRED_FIELDS",
    # Utility functions
    "calculate_field_similarity",
    "normalize_field_name",
    "extract_field_components",
    "find_fuzzy_matches",
    "get_asset_type_priority_fields",
    "suggest_field_corrections",
    "analyze_field_patterns",
    "validate_field_name_format",
    "get_field_type_hints",
]
