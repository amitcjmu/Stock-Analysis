"""
Type inference utilities for field mapping.
"""

import re
from datetime import datetime
from typing import Any, Dict, List


def infer_field_type(values: List[Any]) -> str:
    """Infer the data type from a list of values."""
    if not values:
        return "unknown"

    # Filter out None values
    non_null_values = [v for v in values if v is not None]
    if not non_null_values:
        return "null"

    # Check for boolean
    if all(isinstance(v, bool) for v in non_null_values):
        return "boolean"

    # Check for integer
    if all(isinstance(v, int) and not isinstance(v, bool) for v in non_null_values):
        return "integer"

    # Check for float/numeric
    if all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in non_null_values
    ):
        return "numeric"

    # Check for string representations of numbers
    if all(isinstance(v, str) for v in non_null_values):
        if all(is_integer_string(v) for v in non_null_values):
            return "integer_string"
        elif all(is_numeric_string(v) for v in non_null_values):
            return "numeric_string"
        elif all(is_date_string(v) for v in non_null_values):
            return "date_string"
        elif all(is_email(v) for v in non_null_values):
            return "email"
        elif all(is_ip_address(v) for v in non_null_values):
            return "ip_address"
        elif all(is_hostname(v) for v in non_null_values):
            return "hostname"
        else:
            return "string"

    # Check for datetime
    if all(isinstance(v, datetime) for v in non_null_values):
        return "datetime"

    # Mixed types
    return "mixed"


def is_integer_string(value: str) -> bool:
    """Check if string represents an integer."""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def is_numeric_string(value: str) -> bool:
    """Check if string represents a number."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_date_string(value: str) -> bool:
    """Check if string represents a date."""
    date_patterns = [
        r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
        r"\d{2}-\d{2}-\d{4}",  # MM-DD-YYYY
        r"\d{4}/\d{2}/\d{2}",  # YYYY/MM/DD
    ]

    for pattern in date_patterns:
        if re.match(pattern, value.strip()):
            return True
    return False


def is_email(value: str) -> bool:
    """Check if string is an email address."""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, value.strip()))


def is_ip_address(value: str) -> bool:
    """Check if string is an IP address."""
    ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(ip_pattern, value.strip()))


def is_hostname(value: str) -> bool:
    """Check if string looks like a hostname."""
    hostname_pattern = (
        r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
        r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    )
    return bool(re.match(hostname_pattern, value.strip())) and len(value.strip()) > 3


def validate_data_type_compatibility(
    source_type: str, target_type: str
) -> Dict[str, Any]:
    """Validate if source data type can be converted to target type."""

    # Define conversion compatibility matrix
    compatibility_matrix = {
        "string": {
            "string": {"compatible": True, "transformation": None},
            "integer": {"compatible": True, "transformation": "int()"},
            "numeric": {"compatible": True, "transformation": "float()"},
            "boolean": {"compatible": True, "transformation": "bool()"},
        },
        "integer": {
            "string": {"compatible": True, "transformation": "str()"},
            "integer": {"compatible": True, "transformation": None},
            "numeric": {"compatible": True, "transformation": "float()"},
            "boolean": {"compatible": True, "transformation": "bool()"},
        },
        "numeric": {
            "string": {"compatible": True, "transformation": "str()"},
            "integer": {"compatible": True, "transformation": "int()"},
            "numeric": {"compatible": True, "transformation": None},
            "boolean": {"compatible": False, "transformation": None},
        },
        "integer_string": {
            "string": {"compatible": True, "transformation": None},
            "integer": {"compatible": True, "transformation": "int()"},
            "numeric": {"compatible": True, "transformation": "float()"},
        },
        "numeric_string": {
            "string": {"compatible": True, "transformation": None},
            "integer": {"compatible": True, "transformation": "int(float())"},
            "numeric": {"compatible": True, "transformation": "float()"},
        },
        "boolean": {
            "string": {"compatible": True, "transformation": "str()"},
            "integer": {"compatible": True, "transformation": "int()"},
            "boolean": {"compatible": True, "transformation": None},
        },
        "date_string": {
            "string": {"compatible": True, "transformation": None},
            "datetime": {"compatible": True, "transformation": "parse_date()"},
        },
        "email": {"string": {"compatible": True, "transformation": None}},
        "ip_address": {"string": {"compatible": True, "transformation": None}},
        "hostname": {"string": {"compatible": True, "transformation": None}},
    }

    source_conversions = compatibility_matrix.get(source_type, {})
    conversion_info = source_conversions.get(
        target_type, {"compatible": False, "transformation": None}
    )

    return {
        "compatible": conversion_info["compatible"],
        "transformation_needed": conversion_info["transformation"] is not None,
        "suggested_transformation": conversion_info["transformation"],
        "confidence": 0.9 if conversion_info["compatible"] else 0.1,
    }


def suggest_target_field_by_type(inferred_type: str) -> List[str]:
    """Suggest target fields based on inferred data type."""

    type_to_fields = {
        "string": ["name", "asset_name", "hostname", "description"],
        "integer": ["cpu_cores", "migration_priority"],
        "numeric": ["memory_gb", "storage_gb"],
        "integer_string": ["asset_id", "cpu_cores"],
        "numeric_string": ["memory_gb", "storage_gb"],
        "email": ["business_owner", "technical_owner"],
        "ip_address": ["ip_address"],
        "hostname": ["hostname", "fqdn"],
        "date_string": ["created_at", "updated_at"],
        "boolean": ["is_critical", "is_virtual"],
    }

    return type_to_fields.get(inferred_type, ["name"])


def analyze_field_patterns(field_name: str, sample_values: List[Any]) -> Dict[str, Any]:
    """Analyze field patterns to provide better mapping suggestions."""

    analysis = {
        "field_name": field_name,
        "inferred_type": infer_field_type(sample_values),
        "sample_count": len(sample_values),
        "null_count": len([v for v in sample_values if v is None]),
        "unique_count": len(set(sample_values)) if sample_values else 0,
        "patterns": [],
    }

    # Analyze field name patterns
    field_lower = field_name.lower()

    if "id" in field_lower:
        analysis["patterns"].append("identifier")
    if "name" in field_lower:
        analysis["patterns"].append("name_field")
    if "ip" in field_lower or "addr" in field_lower:
        analysis["patterns"].append("network_address")
    if "cpu" in field_lower or "core" in field_lower:
        analysis["patterns"].append("hardware_spec")
    if "memory" in field_lower or "ram" in field_lower:
        analysis["patterns"].append("memory_spec")
    if "storage" in field_lower or "disk" in field_lower:
        analysis["patterns"].append("storage_spec")
    if "os" in field_lower or "operating" in field_lower:
        analysis["patterns"].append("operating_system")
    if "env" in field_lower or "environment" in field_lower:
        analysis["patterns"].append("environment")

    # Add suggested target fields based on analysis
    analysis["suggested_targets"] = suggest_target_field_by_type(
        analysis["inferred_type"]
    )

    return analysis
