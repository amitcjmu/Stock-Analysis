"""
API v3 Response Schemas
Common response schemas and error handling patterns.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime
import uuid

T = TypeVar('T')


class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    request_id: str = Field(..., description="Unique request identifier for debugging")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "flow_id",
                        "code": "INVALID_UUID",
                        "message": "Invalid UUID format",
                        "context": {"provided_value": "invalid-uuid"}
                    }
                ],
                "request_id": "req_123456789",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response wrapper"""
    success: bool = Field(True, description="Operation success indicator")
    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Optional success message")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: List[T] = Field(..., description="Page items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific details"""
    error: str = Field(default="VALIDATION_ERROR", description="Validation error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "name",
                        "code": "MISSING_REQUIRED_FIELD",
                        "message": "Field is required",
                        "context": {}
                    },
                    {
                        "field": "page_size",
                        "code": "VALUE_OUT_OF_RANGE",
                        "message": "Value must be between 1 and 100",
                        "context": {"min": 1, "max": 100, "provided": 150}
                    }
                ],
                "request_id": "req_123456789",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class NotFoundErrorResponse(ErrorResponse):
    """Resource not found error response"""
    error: str = Field(default="RESOURCE_NOT_FOUND", description="Not found error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "RESOURCE_NOT_FOUND",
                "message": "Discovery flow not found",
                "details": [
                    {
                        "field": "flow_id",
                        "code": "FLOW_NOT_FOUND",
                        "message": "No flow found with the specified ID",
                        "context": {"flow_id": "12345678-1234-1234-1234-123456789012"}
                    }
                ],
                "request_id": "req_123456789",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class ConflictErrorResponse(ErrorResponse):
    """Resource conflict error response"""
    error: str = Field(default="RESOURCE_CONFLICT", description="Conflict error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "RESOURCE_CONFLICT",
                "message": "Flow is already running",
                "details": [
                    {
                        "field": "status",
                        "code": "INVALID_STATE_TRANSITION",
                        "message": "Cannot start flow that is already in progress",
                        "context": {"current_status": "in_progress", "requested_action": "start"}
                    }
                ],
                "request_id": "req_123456789",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class InternalServerErrorResponse(ErrorResponse):
    """Internal server error response"""
    error: str = Field(default="INTERNAL_SERVER_ERROR", description="Internal error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": None,
                "request_id": "req_123456789",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit exceeded error response"""
    error: str = Field(default="RATE_LIMIT_EXCEEDED", description="Rate limit error code")
    retry_after: int = Field(..., description="Seconds to wait before retry")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests",
                "details": [
                    {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "API rate limit exceeded. Please try again later.",
                        "context": {"limit": 100, "window": "1 hour", "reset_time": "2024-01-01T13:00:00Z"}
                    }
                ],
                "request_id": "req_123456789",
                "timestamp": "2024-01-01T12:00:00Z",
                "retry_after": 3600
            }
        }


class StatusResponse(BaseModel):
    """Generic status response"""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    components: Dict[str, bool] = Field(default_factory=dict, description="Component health status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "discovery-flow-v3",
                "version": "3.0.0",
                "timestamp": "2024-01-01T12:00:00Z",
                "components": {
                    "database": True,
                    "crewai": True,
                    "flow_management": True
                },
                "uptime_seconds": 3600.0
            }
        }


class MetricsResponse(BaseModel):
    """Performance metrics response"""
    active_flows: int = Field(..., description="Number of active flows")
    total_flows: int = Field(..., description="Total number of flows")
    completed_flows: int = Field(..., description="Number of completed flows")
    failed_flows: int = Field(..., description="Number of failed flows")
    avg_completion_time_seconds: Optional[float] = Field(None, description="Average completion time")
    avg_response_time_ms: Optional[float] = Field(None, description="Average API response time")
    success_rate_percentage: Optional[float] = Field(None, description="Success rate percentage")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "active_flows": 5,
                "total_flows": 150,
                "completed_flows": 130,
                "failed_flows": 15,
                "avg_completion_time_seconds": 450.0,
                "avg_response_time_ms": 120.5,
                "success_rate_percentage": 86.7,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }


class AsyncOperationResponse(BaseModel):
    """Response for asynchronous operations"""
    operation_id: str = Field(..., description="Unique operation identifier")
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Operation message")
    estimated_completion_time: Optional[datetime] = Field(None, description="Estimated completion time")
    progress_percentage: Optional[float] = Field(None, description="Progress percentage", ge=0, le=100)
    result_url: Optional[str] = Field(None, description="URL to check operation result")
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation_id": "op_123456789",
                "status": "in_progress",
                "message": "Flow execution started",
                "estimated_completion_time": "2024-01-01T12:15:00Z",
                "progress_percentage": 25.0,
                "result_url": "/api/v3/discovery-flow/operations/op_123456789"
            }
        }


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return f"req_{uuid.uuid4().hex[:12]}"


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[List[ErrorDetail]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Helper function to create error responses"""
    return ErrorResponse(
        error=error_code,
        message=message,
        details=details or [],
        request_id=request_id or generate_request_id()
    )


def create_validation_error(
    field: str,
    error_code: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ValidationErrorResponse:
    """Helper function to create validation error responses"""
    detail = ErrorDetail(
        field=field,
        code=error_code,
        message=message,
        context=context or {}
    )
    
    return ValidationErrorResponse(
        message="Request validation failed",
        details=[detail],
        request_id=request_id or generate_request_id()
    )


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> SuccessResponse:
    """Helper function to create success responses"""
    return SuccessResponse(
        data=data,
        message=message,
        request_id=request_id or generate_request_id()
    )


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int
) -> PaginatedResponse:
    """Helper function to create paginated responses"""
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1
    )