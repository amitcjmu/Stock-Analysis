"""Field mapping utilities."""

from .mapping_helpers import (
    calculate_mapping_confidence,
    count_critical_fields_mapped,
    extract_field_metadata,
    get_critical_fields_for_migration,
    get_field_patterns,
    intelligent_field_mapping,
    normalize_field_name,
)
from .type_inference import (
    analyze_field_patterns,
    infer_field_type,
    is_date_string,
    is_email,
    is_hostname,
    is_integer_string,
    is_ip_address,
    is_numeric_string,
    suggest_target_field_by_type,
    validate_data_type_compatibility,
)

__all__ = [
    "intelligent_field_mapping",
    "calculate_mapping_confidence",
    "get_field_patterns",
    "get_critical_fields_for_migration",
    "count_critical_fields_mapped",
    "normalize_field_name",
    "extract_field_metadata",
    "infer_field_type",
    "validate_data_type_compatibility",
    "is_integer_string",
    "is_numeric_string",
    "is_date_string",
    "is_email",
    "is_ip_address",
    "is_hostname",
    "suggest_target_field_by_type",
    "analyze_field_patterns",
]
