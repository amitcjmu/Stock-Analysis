"""
V3 API utilities for backward compatibility, error handling, and common functions
"""

from .backward_compatibility import (
    apply_request_field_compatibility,
    apply_response_field_compatibility,
    apply_list_field_compatibility,
    get_field_mapping_info,
    field_compatibility
)

from .error_handling import (
    V3ErrorCodes,
    V3ErrorResponse,
    V3ErrorHandler,
    handle_api_error,
    log_api_error,
    with_error_handling
)

__all__ = [
    # Backward compatibility
    "apply_request_field_compatibility",
    "apply_response_field_compatibility", 
    "apply_list_field_compatibility",
    "get_field_mapping_info",
    "field_compatibility",
    
    # Error handling
    "V3ErrorCodes",
    "V3ErrorResponse",
    "V3ErrorHandler",
    "handle_api_error",
    "log_api_error",
    "with_error_handling"
]