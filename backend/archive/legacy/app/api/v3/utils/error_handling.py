"""
Centralized error handling for V3 APIs
Provides consistent error responses and logging
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback
import uuid

logger = logging.getLogger(__name__)

# Standard error codes for V3 APIs
class V3ErrorCodes:
    # Client errors (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    
    # Server errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    TIMEOUT = "TIMEOUT"


class V3ErrorResponse:
    """Standardized error response structure for V3 APIs"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        status_code: int = 500
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.status_code = status_code
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
                "timestamp": self.timestamp
            }
        }
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )


class V3ErrorHandler:
    """Centralized error handling for V3 APIs"""
    
    @staticmethod
    def handle_validation_error(error: ValidationError, request_id: Optional[str] = None) -> V3ErrorResponse:
        """Handle Pydantic validation errors"""
        details = {
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"]
                }
                for err in error.errors()
            ]
        }
        
        return V3ErrorResponse(
            error_code=V3ErrorCodes.VALIDATION_FAILED,
            message="Request validation failed",
            details=details,
            request_id=request_id,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    def handle_database_error(error: SQLAlchemyError, request_id: Optional[str] = None) -> V3ErrorResponse:
        """Handle SQLAlchemy database errors"""
        if isinstance(error, IntegrityError):
            # Handle foreign key, unique constraint violations
            return V3ErrorResponse(
                error_code=V3ErrorCodes.CONFLICT,
                message="Database constraint violation",
                details={"database_error": str(error.orig) if hasattr(error, 'orig') else str(error)},
                request_id=request_id,
                status_code=status.HTTP_409_CONFLICT
            )
        
        # Generic database error
        logger.error(f"Database error: {error}", exc_info=True)
        return V3ErrorResponse(
            error_code=V3ErrorCodes.DATABASE_ERROR,
            message="Database operation failed",
            details={"error_type": type(error).__name__},
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def handle_not_found_error(resource_type: str, resource_id: str, request_id: Optional[str] = None) -> V3ErrorResponse:
        """Handle resource not found errors"""
        return V3ErrorResponse(
            error_code=V3ErrorCodes.RESOURCE_NOT_FOUND,
            message=f"{resource_type} not found",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            },
            request_id=request_id,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def handle_service_error(
        service_name: str, 
        error: Exception, 
        request_id: Optional[str] = None
    ) -> V3ErrorResponse:
        """Handle service layer errors"""
        logger.error(f"Service error in {service_name}: {error}", exc_info=True)
        
        # Check if it's a known error type
        if isinstance(error, ValueError):
            return V3ErrorResponse(
                error_code=V3ErrorCodes.INVALID_REQUEST,
                message=f"Invalid request to {service_name}",
                details={"service": service_name, "error": str(error)},
                request_id=request_id,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if isinstance(error, PermissionError):
            return V3ErrorResponse(
                error_code=V3ErrorCodes.FORBIDDEN,
                message=f"Access denied to {service_name}",
                details={"service": service_name},
                request_id=request_id,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Generic service error
        return V3ErrorResponse(
            error_code=V3ErrorCodes.INTERNAL_ERROR,
            message=f"Service {service_name} encountered an error",
            details={
                "service": service_name,
                "error_type": type(error).__name__
            },
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def handle_external_service_error(
        service_name: str, 
        error: Exception, 
        request_id: Optional[str] = None
    ) -> V3ErrorResponse:
        """Handle external service errors (CrewAI, etc.)"""
        logger.warning(f"External service error in {service_name}: {error}")
        
        return V3ErrorResponse(
            error_code=V3ErrorCodes.EXTERNAL_SERVICE_ERROR,
            message=f"External service {service_name} is unavailable",
            details={
                "service": service_name,
                "error": str(error)
            },
            request_id=request_id,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    @staticmethod
    def handle_generic_error(error: Exception, request_id: Optional[str] = None) -> V3ErrorResponse:
        """Handle any unhandled errors"""
        logger.error(f"Unhandled error: {error}", exc_info=True)
        
        return V3ErrorResponse(
            error_code=V3ErrorCodes.INTERNAL_ERROR,
            message="An unexpected error occurred",
            details={
                "error_type": type(error).__name__,
                "trace_id": request_id
            },
            request_id=request_id,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handle_api_error(error: Exception, request_id: Optional[str] = None) -> HTTPException:
    """
    Main error handler function for V3 APIs
    Returns appropriate HTTPException based on error type
    """
    handler = V3ErrorHandler()
    
    # Handle specific error types
    if isinstance(error, ValidationError):
        error_response = handler.handle_validation_error(error, request_id)
    elif isinstance(error, SQLAlchemyError):
        error_response = handler.handle_database_error(error, request_id)
    elif isinstance(error, HTTPException):
        # Re-raise existing HTTP exceptions
        raise error
    else:
        error_response = handler.handle_generic_error(error, request_id)
    
    return error_response.to_http_exception()


def log_api_error(
    endpoint: str,
    error: Exception,
    request_id: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None
):
    """
    Log API errors with consistent format and context
    """
    context = {
        "endpoint": endpoint,
        "request_id": request_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        **(additional_context or {})
    }
    
    # Log with appropriate level based on error type
    if isinstance(error, (ValidationError, ValueError)):
        logger.warning(f"Client error in {endpoint}: {error}", extra=context)
    else:
        logger.error(f"Server error in {endpoint}: {error}", extra=context, exc_info=True)


# Decorator for consistent error handling
def with_error_handling(endpoint_name: str):
    """Decorator to add consistent error handling to API endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4())
            try:
                return await func(*args, **kwargs)
            except Exception as error:
                log_api_error(endpoint_name, error, request_id)
                raise handle_api_error(error, request_id)
        return wrapper
    return decorator