"""
Data Import Utilities - Shared helper functions and utilities.
Common functions used across all data import modules.
"""

import math
import re
from typing import Any, Dict

from app.models.data_import import DataImport


def import_to_dict(data_import: DataImport) -> dict:
    """Convert DataImport model to dictionary."""
    return {
        "id": str(data_import.id),
        "import_name": data_import.import_name,
        "import_type": data_import.import_type,
        "source_filename": data_import.filename,  # Use 'filename' attribute from model
        "status": data_import.status,
        "total_records": data_import.total_records,
        "processed_records": data_import.processed_records,
        "failed_records": data_import.failed_records,
        "created_at": (
            data_import.created_at.isoformat() if data_import.created_at else None
        ),
        "completed_at": (
            data_import.completed_at.isoformat() if data_import.completed_at else None
        ),
    }


def expand_abbreviation(value: str) -> str:
    """Expand common abbreviations."""
    expansions = {
        "DB": "Database",
        "SRV": "Server",
        "APP": "Application",
        "WEB": "Web Server",
        "API": "API Service",
    }
    return expansions.get(value.upper(), value)


def get_suggested_value(field: str, raw_data: Dict[str, Any]) -> str:
    """Generate AI-suggested values for missing fields."""
    suggestions = {
        "hostname": f"server-{raw_data.get('ID', '001')}",
        "ip_address": "192.168.1.100",
        "operating_system": "Windows Server 2019",
        "asset_type": "Server",
        "environment": "Production",
    }
    return suggestions.get(field, "Unknown")


def is_valid_ip(ip: str) -> bool:
    """Basic IP address validation."""
    try:
        parts = ip.split(".")
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except Exception:
        return False


# Deprecated heuristic functions removed - replaced by CrewAI Field Mapping Crew
# check_content_pattern_match() and apply_matching_rules() have been replaced
# by AI-driven field mapping analysis using CrewAI agents


def matches_data_type(value: str, expected_type: str) -> bool:
    """Check if value matches expected data type."""
    try:
        if expected_type == "integer":
            int(value)
            return True
        elif expected_type == "float":
            float(value)
            return True
        elif expected_type == "ip_address":
            parts = value.split(".")
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        elif expected_type == "string":
            return isinstance(value, str) and len(value) > 0
    except (ValueError, TypeError, AttributeError):
        # Expected validation failure for invalid data types
        return False
    return False


def is_in_range(value: str, value_range: dict) -> bool:
    """Check if value is within expected range."""
    try:
        if "min" in value_range and "max" in value_range:
            num_val = float(value)
            return value_range["min"] <= num_val <= value_range["max"]
    except (ValueError, TypeError, KeyError):
        # Expected validation failure for invalid numeric values or missing range keys
        return False
    return False


# Deprecated heuristic functions removed - replaced by CrewAI Field Mapping Crew
# is_potential_new_field() and infer_field_type() have been replaced
# by AI-driven field analysis using CrewAI agents with semantic understanding


def generate_format_regex(sample_values: list) -> str:
    """Generate a regex pattern from sample values for future matching."""
    if not sample_values:
        return ""

    # Simple pattern generation - in production this would be more sophisticated
    first_value = str(sample_values[0]) if sample_values[0] else ""

    # IP pattern
    if re.match(r"\d+\.\d+\.\d+\.\d+", first_value):
        return r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

    # Server ID pattern
    if re.match(r"[A-Z]{2,4}\d+", first_value.upper()):
        return r"[A-Z]{2,4}\d+"

    # Generic alphanumeric
    if first_value.isalnum():
        return r"[A-Za-z0-9]+"

    return ""


def generate_matching_rules(source_field: str, sample_values: list) -> dict:
    """Generate basic matching rules - enhanced field analysis now handled by CrewAI."""
    # Simplified rule generation - full analysis delegated to CrewAI Field Mapping Crew
    rules = {
        "field_name_patterns": [source_field.lower()],
        "content_validation": {},
        "priority_score": 1.0,
        "ai_analysis_recommended": True,  # Flag to indicate CrewAI should handle this
    }

    return rules


def safe_json_serialize(data):
    """Safely serialize data handling NaN/Infinity values."""
    import json

    def convert_numeric(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None  # or "null" or appropriate default
        return obj

    return json.dumps(data, default=convert_numeric)
