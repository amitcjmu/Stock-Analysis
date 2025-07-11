"""
Response utilities module for standardized API responses.
Provides consistent response patterns, error handling, and status codes.
"""

from .response_builders import (
    ResponseBuilder,
    ApiResponse,
    ErrorResponse,
    SuccessResponse,
    DataResponse,
    PaginatedResponse,
    create_success_response,
    create_error_response,
    create_data_response,
    create_paginated_response,
    create_validation_error_response,
    create_not_found_response,
    create_unauthorized_response,
    create_forbidden_response,
    create_conflict_response,
    create_internal_error_response
)

from .error_handlers import (
    ErrorHandler,
    ErrorDetails,
    ValidationError,
    BusinessLogicError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    InternalServerError,
    handle_database_error,
    handle_validation_error,
    handle_business_logic_error,
    handle_authentication_error,
    handle_authorization_error,
    handle_not_found_error,
    handle_conflict_error,
    handle_internal_error,
    format_error_response
)

from .status_codes import (
    StatusCode,
    SUCCESS_CODES,
    ERROR_CODES,
    get_status_message,
    is_success_code,
    is_error_code,
    is_client_error,
    is_server_error
)

from .response_formatters import (
    ResponseFormatter,
    format_datetime,
    format_currency,
    format_percentage,
    format_file_size,
    format_duration,
    sanitize_response_data,
    mask_sensitive_data,
    apply_response_filters
)

__all__ = [
    # Response Builders
    "ResponseBuilder",
    "ApiResponse",
    "ErrorResponse",
    "SuccessResponse",
    "DataResponse",
    "PaginatedResponse",
    "create_success_response",
    "create_error_response",
    "create_data_response",
    "create_paginated_response",
    "create_validation_error_response",
    "create_not_found_response",
    "create_unauthorized_response",
    "create_forbidden_response",
    "create_conflict_response",
    "create_internal_error_response",
    
    # Error Handlers
    "ErrorHandler",
    "ErrorDetails",
    "ValidationError",
    "BusinessLogicError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "InternalServerError",
    "handle_database_error",
    "handle_validation_error",
    "handle_business_logic_error",
    "handle_authentication_error",
    "handle_authorization_error",
    "handle_not_found_error",
    "handle_conflict_error",
    "handle_internal_error",
    "format_error_response",
    
    # Status Codes
    "StatusCode",
    "SUCCESS_CODES",
    "ERROR_CODES",
    "get_status_message",
    "is_success_code",
    "is_error_code",
    "is_client_error",
    "is_server_error",
    
    # Response Formatters
    "ResponseFormatter",
    "format_datetime",
    "format_currency",
    "format_percentage",
    "format_file_size",
    "format_duration",
    "sanitize_response_data",
    "mask_sensitive_data",
    "apply_response_filters"
]