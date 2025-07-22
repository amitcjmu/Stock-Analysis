"""
HTTP status codes and utilities for consistent API responses.
Provides standard status codes and helper functions.
"""

from enum import IntEnum
from typing import Dict, Optional


class StatusCode(IntEnum):
    """HTTP status codes enumeration."""
    
    # Success codes (2xx)
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    PARTIAL_CONTENT = 206
    
    # Redirection codes (3xx)
    MOVED_PERMANENTLY = 301
    FOUND = 302
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308
    
    # Client error codes (4xx)
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    IM_A_TEAPOT = 418
    UNPROCESSABLE_ENTITY = 422
    LOCKED = 423
    FAILED_DEPENDENCY = 424
    TOO_EARLY = 425
    UPGRADE_REQUIRED = 426
    PRECONDITION_REQUIRED = 428
    TOO_MANY_REQUESTS = 429
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    UNAVAILABLE_FOR_LEGAL_REASONS = 451
    
    # Server error codes (5xx)
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    VARIANT_ALSO_NEGOTIATES = 506
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511

# Status code categories
SUCCESS_CODES = {
    StatusCode.OK,
    StatusCode.CREATED,
    StatusCode.ACCEPTED,
    StatusCode.NO_CONTENT,
    StatusCode.PARTIAL_CONTENT
}

REDIRECTION_CODES = {
    StatusCode.MOVED_PERMANENTLY,
    StatusCode.FOUND,
    StatusCode.NOT_MODIFIED,
    StatusCode.TEMPORARY_REDIRECT,
    StatusCode.PERMANENT_REDIRECT
}

CLIENT_ERROR_CODES = {
    StatusCode.BAD_REQUEST,
    StatusCode.UNAUTHORIZED,
    StatusCode.PAYMENT_REQUIRED,
    StatusCode.FORBIDDEN,
    StatusCode.NOT_FOUND,
    StatusCode.METHOD_NOT_ALLOWED,
    StatusCode.NOT_ACCEPTABLE,
    StatusCode.REQUEST_TIMEOUT,
    StatusCode.CONFLICT,
    StatusCode.GONE,
    StatusCode.LENGTH_REQUIRED,
    StatusCode.PRECONDITION_FAILED,
    StatusCode.PAYLOAD_TOO_LARGE,
    StatusCode.URI_TOO_LONG,
    StatusCode.UNSUPPORTED_MEDIA_TYPE,
    StatusCode.RANGE_NOT_SATISFIABLE,
    StatusCode.EXPECTATION_FAILED,
    StatusCode.IM_A_TEAPOT,
    StatusCode.UNPROCESSABLE_ENTITY,
    StatusCode.LOCKED,
    StatusCode.FAILED_DEPENDENCY,
    StatusCode.TOO_EARLY,
    StatusCode.UPGRADE_REQUIRED,
    StatusCode.PRECONDITION_REQUIRED,
    StatusCode.TOO_MANY_REQUESTS,
    StatusCode.REQUEST_HEADER_FIELDS_TOO_LARGE,
    StatusCode.UNAVAILABLE_FOR_LEGAL_REASONS
}

SERVER_ERROR_CODES = {
    StatusCode.INTERNAL_SERVER_ERROR,
    StatusCode.NOT_IMPLEMENTED,
    StatusCode.BAD_GATEWAY,
    StatusCode.SERVICE_UNAVAILABLE,
    StatusCode.GATEWAY_TIMEOUT,
    StatusCode.HTTP_VERSION_NOT_SUPPORTED,
    StatusCode.VARIANT_ALSO_NEGOTIATES,
    StatusCode.INSUFFICIENT_STORAGE,
    StatusCode.LOOP_DETECTED,
    StatusCode.NOT_EXTENDED,
    StatusCode.NETWORK_AUTHENTICATION_REQUIRED
}

ERROR_CODES = CLIENT_ERROR_CODES | SERVER_ERROR_CODES

# Status code messages
STATUS_MESSAGES: Dict[int, str] = {
    # Success codes
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    206: "Partial Content",
    
    # Redirection codes
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    
    # Client error codes
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    
    # Server error codes
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required"
}

def get_status_message(status_code: int) -> Optional[str]:
    """
    Get the standard message for a status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Status message or None if not found
    """
    return STATUS_MESSAGES.get(status_code)

def is_success_code(status_code: int) -> bool:
    """
    Check if status code is a success code (2xx).
    
    Args:
        status_code: HTTP status code
        
    Returns:
        True if success code, False otherwise
    """
    return status_code in SUCCESS_CODES

def is_error_code(status_code: int) -> bool:
    """
    Check if status code is an error code (4xx or 5xx).
    
    Args:
        status_code: HTTP status code
        
    Returns:
        True if error code, False otherwise
    """
    return status_code in ERROR_CODES

def is_client_error(status_code: int) -> bool:
    """
    Check if status code is a client error (4xx).
    
    Args:
        status_code: HTTP status code
        
    Returns:
        True if client error, False otherwise
    """
    return status_code in CLIENT_ERROR_CODES

def is_server_error(status_code: int) -> bool:
    """
    Check if status code is a server error (5xx).
    
    Args:
        status_code: HTTP status code
        
    Returns:
        True if server error, False otherwise
    """
    return status_code in SERVER_ERROR_CODES

def is_redirection(status_code: int) -> bool:
    """
    Check if status code is a redirection (3xx).
    
    Args:
        status_code: HTTP status code
        
    Returns:
        True if redirection, False otherwise
    """
    return status_code in REDIRECTION_CODES

def get_status_category(status_code: int) -> str:
    """
    Get the category of a status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Status category string
    """
    if is_success_code(status_code):
        return "success"
    elif is_redirection(status_code):
        return "redirection"
    elif is_client_error(status_code):
        return "client_error"
    elif is_server_error(status_code):
        return "server_error"
    else:
        return "unknown"

def get_status_info(status_code: int) -> Dict[str, str]:
    """
    Get comprehensive information about a status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Dictionary with status information
    """
    return {
        "code": str(status_code),
        "message": get_status_message(status_code) or "Unknown",
        "category": get_status_category(status_code),
        "is_success": is_success_code(status_code),
        "is_error": is_error_code(status_code),
        "is_client_error": is_client_error(status_code),
        "is_server_error": is_server_error(status_code),
        "is_redirection": is_redirection(status_code)
    }

# Common status code constants for convenience
HTTP_200_OK = StatusCode.OK
HTTP_201_CREATED = StatusCode.CREATED
HTTP_204_NO_CONTENT = StatusCode.NO_CONTENT
HTTP_400_BAD_REQUEST = StatusCode.BAD_REQUEST
HTTP_401_UNAUTHORIZED = StatusCode.UNAUTHORIZED
HTTP_403_FORBIDDEN = StatusCode.FORBIDDEN
HTTP_404_NOT_FOUND = StatusCode.NOT_FOUND
HTTP_409_CONFLICT = StatusCode.CONFLICT
HTTP_422_UNPROCESSABLE_ENTITY = StatusCode.UNPROCESSABLE_ENTITY
HTTP_429_TOO_MANY_REQUESTS = StatusCode.TOO_MANY_REQUESTS
HTTP_500_INTERNAL_SERVER_ERROR = StatusCode.INTERNAL_SERVER_ERROR
HTTP_502_BAD_GATEWAY = StatusCode.BAD_GATEWAY
HTTP_503_SERVICE_UNAVAILABLE = StatusCode.SERVICE_UNAVAILABLE