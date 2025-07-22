"""
Response builder utilities for standardized API responses.
Provides consistent response patterns and structure.
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ApiResponse:
    """Base API response structure."""
    status: ResponseStatus
    message: str
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, Any]]] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        result = asdict(self)
        # Remove None values to keep response clean
        return {k: v for k, v in result.items() if v is not None}

@dataclass
class SuccessResponse(ApiResponse):
    """Success response structure."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "Operation completed successfully"

@dataclass
class ErrorResponse(ApiResponse):
    """Error response structure."""
    status: ResponseStatus = ResponseStatus.ERROR
    message: str = "An error occurred"
    error_code: Optional[str] = None
    error_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        result = super().to_dict()
        if self.error_code:
            result['error_code'] = self.error_code
        if self.error_type:
            result['error_type'] = self.error_type
        return result

@dataclass
class DataResponse(SuccessResponse):
    """Data response structure."""
    data: Any = None
    count: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert data response to dictionary."""
        result = super().to_dict()
        if self.count is not None:
            result['count'] = self.count
        return result

@dataclass
class PaginatedResponse(DataResponse):
    """Paginated response structure."""
    pagination: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert paginated response to dictionary."""
        result = super().to_dict()
        if self.pagination:
            result['pagination'] = self.pagination
        return result

class ResponseBuilder:
    """
    Builder class for creating standardized API responses.
    """
    
    @staticmethod
    def success(
        message: str = "Operation completed successfully",
        data: Optional[Any] = None,
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """
        Create a success response.
        
        Args:
            message: Success message
            data: Response data
            meta: Additional metadata
            status_code: HTTP status code
            
        Returns:
            JSONResponse with success structure
        """
        response = SuccessResponse(
            message=message,
            data=data,
            meta=meta
        )
        
        return JSONResponse(
            content=response.to_dict(),
            status_code=status_code
        )
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        errors: Optional[List[Dict[str, Any]]] = None,
        error_code: Optional[str] = None,
        error_type: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> JSONResponse:
        """
        Create an error response.
        
        Args:
            message: Error message
            errors: List of detailed errors
            error_code: Specific error code
            error_type: Error type classification
            meta: Additional metadata
            status_code: HTTP status code
            
        Returns:
            JSONResponse with error structure
        """
        response = ErrorResponse(
            message=message,
            errors=errors,
            error_code=error_code,
            error_type=error_type,
            meta=meta
        )
        
        return JSONResponse(
            content=response.to_dict(),
            status_code=status_code
        )
    
    @staticmethod
    def data(
        data: Any,
        message: str = "Data retrieved successfully",
        count: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """
        Create a data response.
        
        Args:
            data: Response data
            message: Success message
            count: Number of items in data
            meta: Additional metadata
            status_code: HTTP status code
            
        Returns:
            JSONResponse with data structure
        """
        response = DataResponse(
            message=message,
            data=data,
            count=count,
            meta=meta
        )
        
        return JSONResponse(
            content=response.to_dict(),
            status_code=status_code
        )
    
    @staticmethod
    def paginated(
        data: List[Any],
        pagination: Dict[str, Any],
        message: str = "Data retrieved successfully",
        count: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_200_OK
    ) -> JSONResponse:
        """
        Create a paginated response.
        
        Args:
            data: Response data
            pagination: Pagination metadata
            message: Success message
            count: Number of items in current page
            meta: Additional metadata
            status_code: HTTP status code
            
        Returns:
            JSONResponse with paginated structure
        """
        if count is None and isinstance(data, list):
            count = len(data)
        
        response = PaginatedResponse(
            message=message,
            data=data,
            count=count,
            pagination=pagination,
            meta=meta
        )
        
        return JSONResponse(
            content=response.to_dict(),
            status_code=status_code
        )
    
    @staticmethod
    def created(
        data: Any,
        message: str = "Resource created successfully",
        meta: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Create a resource created response."""
        return ResponseBuilder.data(
            data=data,
            message=message,
            meta=meta,
            status_code=status.HTTP_201_CREATED
        )
    
    @staticmethod
    def updated(
        data: Any,
        message: str = "Resource updated successfully",
        meta: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Create a resource updated response."""
        return ResponseBuilder.data(
            data=data,
            message=message,
            meta=meta,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def deleted(
        message: str = "Resource deleted successfully",
        meta: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Create a resource deleted response."""
        return ResponseBuilder.success(
            message=message,
            meta=meta,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def no_content(
        message: str = "Operation completed successfully"
    ) -> JSONResponse:
        """Create a no content response."""
        return ResponseBuilder.success(
            message=message,
            status_code=status.HTTP_204_NO_CONTENT
        )

# Convenience functions
def create_success_response(
    message: str = "Operation completed successfully",
    data: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a success response."""
    return ResponseBuilder.success(message, data, meta, status_code)

def create_error_response(
    message: str = "An error occurred",
    errors: Optional[List[Dict[str, Any]]] = None,
    error_code: Optional[str] = None,
    error_type: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """Create an error response."""
    return ResponseBuilder.error(message, errors, error_code, error_type, meta, status_code)

def create_data_response(
    data: Any,
    message: str = "Data retrieved successfully",
    count: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a data response."""
    return ResponseBuilder.data(data, message, count, meta, status_code)

def create_paginated_response(
    data: List[Any],
    pagination: Dict[str, Any],
    message: str = "Data retrieved successfully",
    count: Optional[int] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a paginated response."""
    return ResponseBuilder.paginated(data, pagination, message, count, meta, status_code)

# Common error responses
def create_validation_error_response(
    message: str = "Validation failed",
    errors: Optional[List[Dict[str, Any]]] = None
) -> JSONResponse:
    """Create a validation error response."""
    return ResponseBuilder.error(
        message=message,
        errors=errors,
        error_code="VALIDATION_ERROR",
        error_type="validation",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

def create_not_found_response(
    message: str = "Resource not found",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> JSONResponse:
    """Create a not found error response."""
    meta = {}
    if resource_type:
        meta['resource_type'] = resource_type
    if resource_id:
        meta['resource_id'] = resource_id
    
    return ResponseBuilder.error(
        message=message,
        error_code="NOT_FOUND",
        error_type="not_found",
        meta=meta if meta else None,
        status_code=status.HTTP_404_NOT_FOUND
    )

def create_unauthorized_response(
    message: str = "Authentication required"
) -> JSONResponse:
    """Create an unauthorized error response."""
    return ResponseBuilder.error(
        message=message,
        error_code="UNAUTHORIZED",
        error_type="authentication",
        status_code=status.HTTP_401_UNAUTHORIZED
    )

def create_forbidden_response(
    message: str = "Access forbidden"
) -> JSONResponse:
    """Create a forbidden error response."""
    return ResponseBuilder.error(
        message=message,
        error_code="FORBIDDEN",
        error_type="authorization",
        status_code=status.HTTP_403_FORBIDDEN
    )

def create_conflict_response(
    message: str = "Resource conflict",
    conflict_type: Optional[str] = None
) -> JSONResponse:
    """Create a conflict error response."""
    meta = {}
    if conflict_type:
        meta['conflict_type'] = conflict_type
    
    return ResponseBuilder.error(
        message=message,
        error_code="CONFLICT",
        error_type="conflict",
        meta=meta if meta else None,
        status_code=status.HTTP_409_CONFLICT
    )

def create_internal_error_response(
    message: str = "Internal server error",
    error_id: Optional[str] = None
) -> JSONResponse:
    """Create an internal server error response."""
    meta = {}
    if error_id:
        meta['error_id'] = error_id
    
    return ResponseBuilder.error(
        message=message,
        error_code="INTERNAL_ERROR",
        error_type="server_error",
        meta=meta if meta else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )