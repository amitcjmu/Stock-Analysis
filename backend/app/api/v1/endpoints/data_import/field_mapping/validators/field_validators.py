"""
Field-level validators for mapping operations.
"""

import re
from typing import Any, List, Dict, Optional


class FieldValidator:
    """Validator for individual field operations."""
    
    def __init__(self):
        self.valid_field_name_pattern = re.compile(r'^[a-zA-Z0-9_\-\.\s]+$')
        self.identifier_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
    
    def validate_field_name(self, field_name: str) -> Dict[str, Any]:
        """Validate field name format."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not field_name:
            result["valid"] = False
            result["errors"].append("Field name cannot be empty")
            return result
        
        if len(field_name) > 100:
            result["valid"] = False
            result["errors"].append("Field name too long (max 100 characters)")
        
        if not self.valid_field_name_pattern.match(field_name):
            result["valid"] = False
            result["errors"].append("Field name contains invalid characters")
        
        if field_name.startswith(' ') or field_name.endswith(' '):
            result["warnings"].append("Field name has leading/trailing spaces")
        
        return result
    
    def validate_target_field(self, target_field: str, valid_targets: List[str]) -> Dict[str, Any]:
        """Validate target field against allowed values."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not target_field:
            result["valid"] = False
            result["errors"].append("Target field cannot be empty")
            return result
        
        if target_field not in valid_targets:
            if target_field.startswith('custom_'):
                result["warnings"].append(f"Using custom target field: {target_field}")
            else:
                result["valid"] = False
                result["errors"].append(f"Invalid target field: {target_field}")
        
        return result
    
    def validate_sample_values(self, values: List[Any]) -> Dict[str, Any]:
        """Validate sample values for consistency."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        if not values:
            result["warnings"].append("No sample values provided")
            return result
        
        # Calculate statistics
        non_null_values = [v for v in values if v is not None]
        unique_values = set(non_null_values)
        
        result["statistics"] = {
            "total_count": len(values),
            "non_null_count": len(non_null_values),
            "null_count": len(values) - len(non_null_values),
            "unique_count": len(unique_values),
            "null_percentage": (len(values) - len(non_null_values)) / len(values) * 100
        }
        
        # Warnings for data quality
        if result["statistics"]["null_percentage"] > 50:
            result["warnings"].append("High percentage of null values (>50%)")
        
        if len(unique_values) == 1:
            result["warnings"].append("All non-null values are identical")
        
        if len(unique_values) == len(non_null_values) and len(non_null_values) > 10:
            result["warnings"].append("All values are unique - might be an identifier field")
        
        return result
    
    def validate_data_consistency(self, values: List[Any]) -> Dict[str, Any]:
        """Validate data consistency and type uniformity."""
        result = {
            "consistent": True,
            "issues": [],
            "type_analysis": {}
        }
        
        if not values:
            return result
        
        # Analyze types
        type_counts = {}
        for value in values:
            if value is not None:
                value_type = type(value).__name__
                type_counts[value_type] = type_counts.get(value_type, 0) + 1
        
        result["type_analysis"] = type_counts
        
        # Check for mixed types
        if len(type_counts) > 1:
            result["consistent"] = False
            result["issues"].append(f"Mixed data types found: {list(type_counts.keys())}")
        
        # Check for string format consistency if all strings
        if len(type_counts) == 1 and 'str' in type_counts:
            string_values = [str(v) for v in values if v is not None]
            if not self._check_string_format_consistency(string_values):
                result["issues"].append("Inconsistent string formats detected")
        
        return result
    
    def _check_string_format_consistency(self, string_values: List[str]) -> bool:
        """Check if string values have consistent formatting."""
        if len(string_values) < 2:
            return True
        
        # Check for consistent patterns
        patterns = {
            "has_spaces": any(' ' in v for v in string_values),
            "has_underscores": any('_' in v for v in string_values),
            "has_hyphens": any('-' in v for v in string_values),
            "is_upper": any(v.isupper() for v in string_values),
            "is_lower": any(v.islower() for v in string_values),
            "is_mixed_case": any(v != v.upper() and v != v.lower() for v in string_values)
        }
        
        # If there's high variation in formatting, it's inconsistent
        pattern_count = sum(1 for v in patterns.values() if v)
        return pattern_count <= 2  # Allow some variation
    
    def suggest_validation_rule(self, field_name: str, sample_values: List[Any]) -> Optional[str]:
        """Suggest validation rule based on field analysis."""
        if not sample_values:
            return None
        
        field_lower = field_name.lower()
        non_null_values = [v for v in sample_values if v is not None]
        
        if not non_null_values:
            return "not null"
        
        # Suggest rules based on field name patterns
        if "email" in field_lower:
            return "format: email"
        elif "ip" in field_lower:
            return "format: ip_address"
        elif "phone" in field_lower:
            return "format: phone_number"
        elif "id" in field_lower:
            return "not empty"
        elif "name" in field_lower:
            return "length > 1"
        elif "url" in field_lower or "link" in field_lower:
            return "format: url"
        
        # Suggest rules based on data patterns
        if all(isinstance(v, str) and len(v) > 0 for v in non_null_values):
            min_length = min(len(str(v)) for v in non_null_values)
            max_length = max(len(str(v)) for v in non_null_values)
            
            if min_length == max_length:
                return f"length = {min_length}"
            else:
                return f"length between {min_length} and {max_length}"
        
        return None