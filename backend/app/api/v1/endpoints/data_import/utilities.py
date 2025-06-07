"""
Data Import Utilities - Shared helper functions and utilities.
Common functions used across all data import modules.
"""

import re
import math
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.data_import import DataImport

def import_to_dict(data_import: DataImport) -> dict:
    """Convert DataImport model to dictionary."""
    return {
        "id": str(data_import.id),
        "import_name": data_import.import_name,
        "import_type": data_import.import_type,
        "source_filename": data_import.source_filename,
        "status": data_import.status,
        "total_records": data_import.total_records,
        "processed_records": data_import.processed_records,
        "failed_records": data_import.failed_records,
        "created_at": data_import.created_at.isoformat() if data_import.created_at else None,
        "completed_at": data_import.completed_at.isoformat() if data_import.completed_at else None
    }

def expand_abbreviation(value: str) -> str:
    """Expand common abbreviations."""
    expansions = {
        'DB': 'Database',
        'SRV': 'Server', 
        'APP': 'Application',
        'WEB': 'Web Server',
        'API': 'API Service'
    }
    return expansions.get(value.upper(), value)

def get_suggested_value(field: str, raw_data: Dict[str, Any]) -> str:
    """Generate AI-suggested values for missing fields."""
    suggestions = {
        'hostname': f"server-{raw_data.get('ID', '001')}",
        'ip_address': '192.168.1.100',
        'operating_system': 'Windows Server 2019',
        'asset_type': 'Server',
        'environment': 'Production'
    }
    return suggestions.get(field, 'Unknown')

def is_valid_ip(ip: str) -> bool:
    """Basic IP address validation."""
    try:
        parts = ip.split('.')
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except:
        return False

def check_content_pattern_match(values: list, content_pattern: dict) -> float:
    """Check if values match the learned content pattern."""
    if not content_pattern or not values:
        return 0.0
    
    matches = 0
    total = len(values)
    
    for value in values:
        if not value or value in ['<empty>', '', 'Unknown']:
            continue
            
        # Check data type pattern
        expected_type = content_pattern.get("data_type")
        if expected_type and matches_data_type(value, expected_type):
            matches += 1
            
        # Check format pattern
        format_pattern = content_pattern.get("format_regex")
        if format_pattern and re.search(format_pattern, str(value), re.IGNORECASE):
            matches += 1
            
        # Check value range
        value_range = content_pattern.get("value_range")
        if value_range and is_in_range(value, value_range):
            matches += 1
    
    return matches / max(total, 1)

def apply_matching_rules(source_field: str, sample_value: str, all_values: list, matching_rules: dict) -> float:
    """Apply learned matching rules to calculate confidence."""
    # This would contain AI-learned rules specific to this pattern
    # For now, return basic matching
    return 0.1

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
            parts = value.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        elif expected_type == "string":
            return isinstance(value, str) and len(value) > 0
    except:
        pass
    return False

def is_in_range(value: str, value_range: dict) -> bool:
    """Check if value is within expected range."""
    try:
        if "min" in value_range and "max" in value_range:
            num_val = float(value)
            return value_range["min"] <= num_val <= value_range["max"]
    except:
        pass
    return False

def is_potential_new_field(source_field: str, sample_value: str, available_fields: list) -> bool:
    """Check if this looks like a field that should be added to the schema."""
    existing_names = {field["name"] for field in available_fields}
    
    # Don't suggest new field if it's very similar to existing ones
    normalized_source = source_field.lower().replace(' ', '_').replace('(', '').replace(')', '')
    
    for existing in existing_names:
        if normalized_source in existing or existing in normalized_source:
            return False
    
    # Suggest new field if it has meaningful data
    if sample_value and sample_value not in ['<empty>', '', 'Unknown', 'NULL']:
        return True
    
    return False

def infer_field_type(values: list) -> str:
    """Infer the appropriate field type from sample values."""
    if not values:
        return "string"
    
    # Check if all values are integers
    try:
        for value in values[:5]:
            if value and value not in ['<empty>', '', 'Unknown']:
                int(value)
        return "integer"
    except:
        pass
    
    # Check if all values are floats
    try:
        for value in values[:5]:
            if value and value not in ['<empty>', '', 'Unknown']:
                float(value)
        return "number"
    except:
        pass
    
    # Check if values look like dates
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{2}/\d{2}/\d{4}',
        r'\d{2}-\d{2}-\d{4}'
    ]
    
    for value in values[:3]:
        if value and any(re.search(pattern, str(value)) for pattern in date_patterns):
            return "date"
    
    return "string"

def generate_format_regex(sample_values: list) -> str:
    """Generate a regex pattern from sample values for future matching."""
    if not sample_values:
        return ""
    
    # Simple pattern generation - in production this would be more sophisticated
    first_value = str(sample_values[0]) if sample_values[0] else ""
    
    # IP pattern
    if re.match(r'\d+\.\d+\.\d+\.\d+', first_value):
        return r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    
    # Server ID pattern
    if re.match(r'[A-Z]{2,4}\d+', first_value.upper()):
        return r'[A-Z]{2,4}\d+'
    
    # Generic alphanumeric
    if first_value.isalnum():
        return r'[A-Za-z0-9]+'
    
    return ""

def generate_matching_rules(source_field: str, sample_values: list) -> dict:
    """Generate matching rules for future AI use."""
    rules = {
        "field_name_patterns": [source_field.lower()],
        "content_validation": {},
        "priority_score": 1.0
    }
    
    # Add content-based rules
    if sample_values:
        rules["content_validation"] = {
            "expected_type": infer_field_type(sample_values),
            "sample_formats": [str(v)[:20] for v in sample_values[:3] if v]
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