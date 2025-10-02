"""
DEPRECATED: Legacy field mapping helpers with hardcoded heuristics.

This module contains hardcoded field mapping patterns that violate ADR-015
(persistent agents). All field mapping intelligence should now come from
agents via the canonical FieldMappingService in app.services.field_mapping_service.

These functions are kept for backward compatibility but will be removed in a future version.
New code should use FieldMappingService instead.

Migration path:
- intelligent_field_mapping() -> FieldMappingService.analyze_columns()
- calculate_mapping_confidence() -> Handled by agent analysis
- Hardcoded patterns -> Agent-driven decisions

See: backend/app/services/field_mapping_service/
ADR: docs/adr/015-persistent-multi-tenant-agent-architecture.md
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Mark module as deprecated
logger.warning(
    "DEPRECATION WARNING: mapping_helpers.py contains hardcoded heuristics. "
    "Use FieldMappingService from app.services.field_mapping_service instead."
)


def intelligent_field_mapping(source_field: str) -> str:
    """
    DEPRECATED: Use FieldMappingService.analyze_columns() instead.

    This function uses hardcoded patterns which violate ADR-015.
    Maintained only for backward compatibility.
    """
    logger.warning(
        f"DEPRECATED: intelligent_field_mapping() called for '{source_field}'. "
        f"Use FieldMappingService.analyze_columns() instead."
    )
    # Return None to indicate no mapping - caller should use FieldMappingService
    return None


def calculate_mapping_confidence(source_field: str, target_field: str) -> float:
    """
    DEPRECATED: Confidence is now calculated by agents.

    This function uses hardcoded rules which violate ADR-015.
    Maintained only for backward compatibility.
    """
    logger.warning(
        f"DEPRECATED: calculate_mapping_confidence() called for '{source_field}' -> '{target_field}'. "
        f"Confidence scores now come from agent analysis."
    )
    # Return low confidence to indicate caller should use agent-driven analysis
    return 0.1


# Utility functions that don't contain business logic are kept
def normalize_field_name(field_name: str) -> str:
    """Normalize field name for comparison (pure utility, no business logic)."""
    if not field_name:
        return ""
    return field_name.lower().strip().replace(" ", "_").replace("-", "_")


def extract_field_metadata(field_name: str) -> Dict[str, Any]:
    """
    Extract basic metadata from field name (pure utility).

    Returns:
        Dict with keys: normalized_name, has_units, possible_type
    """
    normalized = normalize_field_name(field_name)

    # Detect units
    has_gb = "gb" in normalized or "_gb" in normalized
    has_mb = "mb" in normalized or "_mb" in normalized
    has_percent = "percent" in normalized or "%" in field_name

    # Basic type hints
    possible_type = "string"  # default
    if has_gb or has_mb:
        possible_type = "numeric"
    elif has_percent:
        possible_type = "percentage"
    elif any(kw in normalized for kw in ["date", "time", "timestamp"]):
        possible_type = "datetime"
    elif any(kw in normalized for kw in ["count", "num", "total", "quantity"]):
        possible_type = "numeric"

    return {
        "normalized_name": normalized,
        "has_units": has_gb or has_mb or has_percent,
        "possible_type": possible_type,
    }


def get_field_patterns() -> Dict[str, List[str]]:
    """
    DEPRECATED: Field patterns should come from agents, not hardcoded dictionaries.

    Returns empty dict to indicate patterns should be retrieved from agents.
    """
    logger.warning(
        "DEPRECATED: get_field_patterns() returns empty dict. "
        "Use FieldMappingService for pattern-based mapping."
    )
    return {}


def get_critical_fields_for_migration() -> List[str]:
    """
    Get list of critical fields for migration (from canonical source).

    This delegates to the canonical FieldMappingService base mappings.
    """
    from app.services.field_mapping_service import BASE_MAPPINGS

    # Return only the keys (target field names) as critical fields
    return list(BASE_MAPPINGS.keys())


def count_critical_fields_mapped(mapped_fields: List[str]) -> int:
    """Count how many critical fields have been mapped."""
    critical_fields = get_critical_fields_for_migration()
    mapped_normalized = {normalize_field_name(f) for f in mapped_fields}

    count = 0
    for critical_field in critical_fields:
        if normalize_field_name(critical_field) in mapped_normalized:
            count += 1

    return count
