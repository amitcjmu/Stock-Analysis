"""
Error handling utilities for standardized error responses.
Provides consistent error handling patterns and exception management.
"""

import logging
import traceback
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError

from .response_builders import ResponseBuilder
from .status_codes import StatusCode

logger = logging.getLogger(__name__)

class ErrorType(str, Enum):
    """Error type classifications."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    BUSINESS_LOGIC = "business_logic"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL_SERVER = "internal_server"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"

@dataclass
class ErrorDetails:
    """Detailed error information."""
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    constraint: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error details to dictionary."""
        result = {
            "code": self.code,
            "message": self.message
        }
        
        if self.field:
            result["field"] = self.field
        if self.value is not None:
            result["value"] = self.value
        if self.constraint:
            result["constraint"] = self.constraint
        if self.additional_info:
            result["additional_info"] = self.additional_info
        
        return result

# Custom exception classes
class BaseApplicationError(Exception):
    """Base application error."""
    
    def __init__(self, message: str, error_type: ErrorType, error_code: str, 
                 details: Optional[List[ErrorDetails]] = None):
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.details = details or []
        super().__init__(self.message)

class ValidationError(BaseApplicationError):
    """Validation error."""
    
    def __init__(self, message: str, details: Optional[List[ErrorDetails]] = None):
        super().__init__(message, ErrorType.VALIDATION, "VALIDATION_ERROR", details)

class BusinessLogicError(BaseApplicationError):
    """Business logic error."""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_LOGIC_ERROR", 
                 details: Optional[List[ErrorDetails]] = None):
        super().__init__(message, ErrorType.BUSINESS_LOGIC, error_code, details)

class AuthenticationError(BaseApplicationError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed", 
                 error_code: str = "AUTHENTICATION_ERROR"):
        super().__init__(message, ErrorType.AUTHENTICATION, error_code)

class AuthorizationError(BaseApplicationError):
    """Authorization error."""
    
    def __init__(self, message: str = "Access forbidden", 
                 error_code: str = "AUTHORIZATION_ERROR"):
        super().__init__(message, ErrorType.AUTHORIZATION, error_code)

class NotFoundError(BaseApplicationError):
    """Not found error."""
    
    def __init__(self, message: str = "Resource not found", 
                 resource_type: Optional[str] = None, 
                 resource_id: Optional[str] = None):
        details = []
        if resource_type:
            details.append(ErrorDetails("RESOURCE_TYPE", resource_type))
        if resource_id:
            details.append(ErrorDetails("RESOURCE_ID", resource_id))
        
        super().__init__(message, ErrorType.NOT_FOUND, "NOT_FOUND", details)

class ConflictError(BaseApplicationError):
    """Conflict error."""
    
    def __init__(self, message: str = "Resource conflict", 
                 conflict_type: Optional[str] = None):
        details = []
        if conflict_type:
            details.append(ErrorDetails("CONFLICT_TYPE", conflict_type))
        
        super().__init__(message, ErrorType.CONFLICT, "CONFLICT", details)

class InternalServerError(BaseApplicationError):
    """Internal server error."""
    
    def __init__(self, message: str = "Internal server error", 
                 error_id: Optional[str] = None):
        details = []
        if error_id:
            details.append(ErrorDetails("ERROR_ID", error_id))
        
        super().__init__(message, ErrorType.INTERNAL_SERVER, "INTERNAL_SERVER_ERROR", details)

class ErrorHandler:
    """
    Centralized error handler for consistent error processing.
    """
    
    @staticmethod
    def handle_exception(exc: Exception, request: Optional[Request] = None) -> JSONResponse:
        """
        Handle any exception and return appropriate JSON response.
        
        Args:
            exc: Exception to handle
            request: Optional request object for context
            
        Returns:
            JSONResponse with error details
        """
        # Log the error
        error_id = ErrorHandler._generate_error_id()
        logger.error(f"Error ID {error_id}: {type(exc).__name__}: {str(exc)}")
        
        # Handle specific exception types
        if isinstance(exc, BaseApplicationError):
            return ErrorHandler._handle_application_error(exc, error_id)
        elif isinstance(exc, HTTPException):
            return ErrorHandler._handle_http_exception(exc, error_id)
        elif isinstance(exc, PydanticValidationError):
            return ErrorHandler._handle_pydantic_validation_error(exc, error_id)
        elif isinstance(exc, SQLAlchemyError):
            return ErrorHandler._handle_database_error(exc, error_id)
        else:
            return ErrorHandler._handle_unknown_error(exc, error_id)
    
    @staticmethod
    def _handle_application_error(exc: BaseApplicationError, error_id: str) -> JSONResponse:
        """Handle application-specific errors."""
        status_code = ErrorHandler._get_status_code_for_error_type(exc.error_type)
        
        errors = [detail.to_dict() for detail in exc.details] if exc.details else None
        
        return ResponseBuilder.error(
            message=exc.message,
            errors=errors,
            error_code=exc.error_code,
            error_type=exc.error_type.value,
            meta={"error_id": error_id},
            status_code=status_code
        )
    
    @staticmethod
    def _handle_http_exception(exc: HTTPException, error_id: str) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        error_type = ErrorHandler._get_error_type_for_status_code(exc.status_code)
        
        return ResponseBuilder.error(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            error_type=error_type.value,
            meta={"error_id": error_id},
            status_code=exc.status_code
        )
    
    @staticmethod
    def _handle_pydantic_validation_error(exc: PydanticValidationError, error_id: str) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            errors.append(ErrorDetails(
                code=error["type"],
                message=error["msg"],
                field=field_path,
                value=error.get("input")
            ).to_dict())
        
        return ResponseBuilder.error(
            message="Validation failed",
            errors=errors,
            error_code="VALIDATION_ERROR",
            error_type=ErrorType.VALIDATION.value,
            meta={"error_id": error_id},
            status_code=422
        )
    
    @staticmethod
    def _handle_database_error(exc: SQLAlchemyError, error_id: str) -> JSONResponse:
        """Handle database errors."""
        logger.error(f"Database error {error_id}: {str(exc)}")
        
        if isinstance(exc, IntegrityError):
            return ResponseBuilder.error(
                message="Data integrity constraint violation",
                error_code="INTEGRITY_ERROR",
                error_type=ErrorType.DATABASE.value,
                meta={"error_id": error_id},
                status_code=409
            )
        elif isinstance(exc, NoResultFound):
            return ResponseBuilder.error(
                message="Required data not found",
                error_code="NO_RESULT_FOUND",
                error_type=ErrorType.NOT_FOUND.value,
                meta={"error_id": error_id},
                status_code=404
            )
        else:
            return ResponseBuilder.error(
                message="Database operation failed",
                error_code="DATABASE_ERROR",
                error_type=ErrorType.DATABASE.value,
                meta={"error_id": error_id},
                status_code=500
            )
    
    @staticmethod
    def _handle_unknown_error(exc: Exception, error_id: str) -> JSONResponse:
        """Handle unknown errors."""
        logger.error(f"Unknown error {error_id}: {type(exc).__name__}: {str(exc)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return ResponseBuilder.error(
            message="An unexpected error occurred",
            error_code="UNKNOWN_ERROR",
            error_type=ErrorType.INTERNAL_SERVER.value,
            meta={"error_id": error_id},
            status_code=500
        )
    
    @staticmethod
    def _get_status_code_for_error_type(error_type: ErrorType) -> int:
        """Get HTTP status code for error type."""
        mapping = {
            ErrorType.VALIDATION: 422,
            ErrorType.AUTHENTICATION: 401,
            ErrorType.AUTHORIZATION: 403,
            ErrorType.NOT_FOUND: 404,
            ErrorType.CONFLICT: 409,
            ErrorType.BUSINESS_LOGIC: 422,
            ErrorType.DATABASE: 500,
            ErrorType.EXTERNAL_SERVICE: 502,
            ErrorType.INTERNAL_SERVER: 500,
            ErrorType.RATE_LIMIT: 429,
            ErrorType.TIMEOUT: 408
        }
        return mapping.get(error_type, 500)
    
    @staticmethod
    def _get_error_type_for_status_code(status_code: int) -> ErrorType:
        """Get error type for HTTP status code."""
        mapping = {
            400: ErrorType.VALIDATION,
            401: ErrorType.AUTHENTICATION,
            403: ErrorType.AUTHORIZATION,
            404: ErrorType.NOT_FOUND,
            409: ErrorType.CONFLICT,
            422: ErrorType.VALIDATION,
            429: ErrorType.RATE_LIMIT,
            500: ErrorType.INTERNAL_SERVER,
            502: ErrorType.EXTERNAL_SERVICE,
            503: ErrorType.EXTERNAL_SERVICE,
            504: ErrorType.TIMEOUT
        }
        return mapping.get(status_code, ErrorType.INTERNAL_SERVER)
    
    @staticmethod
    def _generate_error_id() -> str:
        """Generate unique error ID for tracking."""
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")

# Convenience functions for specific error types
def handle_database_error(exc: SQLAlchemyError, context: Optional[str] = None) -> JSONResponse:
    """Handle database errors with context."""
    error_id = ErrorHandler._generate_error_id()
    logger.error(f"Database error {error_id} in {context}: {str(exc)}")
    return ErrorHandler._handle_database_error(exc, error_id)

def handle_validation_error(message: str, details: Optional[List[ErrorDetails]] = None) -> JSONResponse:
    """Handle validation errors."""
    exc = ValidationError(message, details)
    return ErrorHandler.handle_exception(exc)

def handle_business_logic_error(message: str, error_code: str = "BUSINESS_LOGIC_ERROR") -> JSONResponse:
    """Handle business logic errors."""
    exc = BusinessLogicError(message, error_code)
    return ErrorHandler.handle_exception(exc)

def handle_authentication_error(message: str = "Authentication failed") -> JSONResponse:
    """Handle authentication errors."""
    exc = AuthenticationError(message)
    return ErrorHandler.handle_exception(exc)

def handle_authorization_error(message: str = "Access forbidden") -> JSONResponse:
    """Handle authorization errors."""
    exc = AuthorizationError(message)
    return ErrorHandler.handle_exception(exc)

def handle_not_found_error(message: str = "Resource not found", 
                          resource_type: Optional[str] = None,
                          resource_id: Optional[str] = None) -> JSONResponse:
    """Handle not found errors."""
    exc = NotFoundError(message, resource_type, resource_id)
    return ErrorHandler.handle_exception(exc)

def handle_conflict_error(message: str = "Resource conflict", 
                         conflict_type: Optional[str] = None) -> JSONResponse:
    """Handle conflict errors."""
    exc = ConflictError(message, conflict_type)
    return ErrorHandler.handle_exception(exc)

def handle_internal_error(message: str = "Internal server error") -> JSONResponse:
    """Handle internal server errors."""
    exc = InternalServerError(message)
    return ErrorHandler.handle_exception(exc)

def format_error_response(
    message: str,
    error_type: ErrorType,
    error_code: str,
    details: Optional[List[ErrorDetails]] = None,
    status_code: Optional[int] = None
) -> JSONResponse:
    """Format a custom error response."""
    if status_code is None:
        status_code = ErrorHandler._get_status_code_for_error_type(error_type)
    
    errors = [detail.to_dict() for detail in details] if details else None
    error_id = ErrorHandler._generate_error_id()
    
    return ResponseBuilder.error(
        message=message,
        errors=errors,
        error_code=error_code,
        error_type=error_type.value,
        meta={"error_id": error_id},
        status_code=status_code
    )