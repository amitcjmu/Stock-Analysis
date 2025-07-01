"""
Backward compatibility utilities for V3 API
Handles field name mapping for both request and response data
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# Field mappings: new_field_name -> old_field_name
FIELD_MAPPINGS = {
    # DataImport field renames (new -> old)
    'filename': 'source_filename',
    'file_size': 'file_size_bytes', 
    'mime_type': 'file_type',
    
    # Asset field renames (new -> old)
    'asset_name': 'name',
    'asset_type': 'type',
    'cpu_cores': 'cpu_count',
    'memory_gb': 'memory_mb',  # Note: also needs value conversion
    'storage_gb': 'storage_mb',  # Note: also needs value conversion
    
    # DiscoveryFlow field renames (new -> old)
    'status': 'flow_status',
    'current_phase': 'phase',
    'created_by_user_id': 'user_id',
    
    # Remove deprecated fields in responses
    'is_mock': None,  # Remove from responses
    'legacy_field': None  # Remove from responses
}

# Reverse mappings: old_field_name -> new_field_name
REVERSE_FIELD_MAPPINGS = {}
for new_field, old_field in FIELD_MAPPINGS.items():
    if old_field is not None:  # Skip removed fields
        REVERSE_FIELD_MAPPINGS[old_field] = new_field


def apply_request_field_compatibility(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert old field names in requests to new field names
    Used for incoming API requests to handle legacy field names
    """
    if not isinstance(data, dict):
        return data
    
    result = data.copy()
    
    # Convert old field names to new ones
    for old_field, new_field in REVERSE_FIELD_MAPPINGS.items():
        if old_field in result:
            value = result.pop(old_field)
            
            # Handle unit conversions for memory/storage fields
            if old_field in ['memory_mb', 'storage_mb'] and new_field in ['memory_gb', 'storage_gb']:
                if isinstance(value, (int, float)) and value > 0:
                    value = value / 1024  # Convert MB to GB
            
            result[new_field] = value
            logger.debug(f"Mapped request field {old_field} -> {new_field}")
    
    # Remove deprecated fields
    deprecated_fields = ['is_mock', 'legacy_field']
    for field in deprecated_fields:
        if field in result:
            result.pop(field)
            logger.debug(f"Removed deprecated field: {field}")
    
    return result


def apply_response_field_compatibility(
    data: Dict[str, Any], 
    include_legacy_fields: bool = True
) -> Dict[str, Any]:
    """
    Add old field names to responses for backward compatibility
    Used for outgoing API responses to include legacy field names
    """
    if not isinstance(data, dict):
        return data
    
    result = data.copy()
    
    if include_legacy_fields:
        # Add old field names as aliases
        for new_field, old_field in FIELD_MAPPINGS.items():
            if old_field is not None and new_field in result:
                value = result[new_field]
                
                # Handle unit conversions for memory/storage fields
                if new_field in ['memory_gb', 'storage_gb'] and old_field in ['memory_mb', 'storage_mb']:
                    if isinstance(value, (int, float)) and value > 0:
                        value = value * 1024  # Convert GB to MB
                
                result[old_field] = value
                logger.debug(f"Added legacy field {new_field} -> {old_field}")
    
    return result


def apply_list_field_compatibility(
    items: List[Dict[str, Any]], 
    include_legacy_fields: bool = True,
    is_request: bool = False
) -> List[Dict[str, Any]]:
    """
    Apply field compatibility to a list of items
    """
    if not items:
        return items
    
    result = []
    for item in items:
        if is_request:
            converted_item = apply_request_field_compatibility(item)
        else:
            converted_item = apply_response_field_compatibility(item, include_legacy_fields)
        result.append(converted_item)
    
    return result


def get_field_mapping_info() -> Dict[str, Any]:
    """
    Get information about current field mappings for documentation
    """
    return {
        "field_mappings": FIELD_MAPPINGS,
        "reverse_mappings": REVERSE_FIELD_MAPPINGS,
        "deprecated_fields": [field for field, mapping in FIELD_MAPPINGS.items() if mapping is None],
        "unit_conversions": {
            "memory_mb -> memory_gb": "Divide by 1024",
            "storage_mb -> storage_gb": "Divide by 1024",
            "memory_gb -> memory_mb": "Multiply by 1024", 
            "storage_gb -> storage_mb": "Multiply by 1024"
        }
    }


class FieldCompatibilityMiddleware:
    """
    Middleware to automatically apply field compatibility to API requests/responses
    """
    
    def __init__(self, include_legacy_fields: bool = True):
        self.include_legacy_fields = include_legacy_fields
    
    def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request data"""
        return apply_request_field_compatibility(data)
    
    def process_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process outgoing response data"""
        return apply_response_field_compatibility(data, self.include_legacy_fields)
    
    def process_list_response(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process list responses"""
        return apply_list_field_compatibility(items, self.include_legacy_fields, is_request=False)


# Global middleware instance
field_compatibility = FieldCompatibilityMiddleware()