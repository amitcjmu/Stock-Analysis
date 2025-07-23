"""
API Error Handlers

Provides centralized error handling for FastAPI endpoints with:
- Consistent error response format
- User-friendly error messages
- Proper HTTP status codes
- Request tracking and logging
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseApplicationError,
    DatabaseError,
    FlowNotFoundError,
    NetworkTimeoutError,
    ResourceExhaustedError,
    TenantIsolationError,
    ValidationError,
)
from app.core.logging import get_logger, trace_id_context

logger = get_logger(__name__)


async def handle_application_error(
    request: Request, exc: BaseApplicationError
) -> JSONResponse:
    """Handle application-specific errors"""
    # Log the error with context
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "trace_id": exc.trace_id,
            "stack_trace": exc.stack_trace,
        },
    )

    # Determine HTTP status code based on error type
    status_code = _get_status_code(exc)

    # Build error response
    error_response = {
        "error": exc.to_dict(),
        "status": "error",
        "path": request.url.path,
        "method": request.method,
    }

    # Add trace ID if available
    trace_id = trace_id_context.get() or exc.trace_id
    if trace_id:
        error_response["trace_id"] = trace_id

    return JSONResponse(status_code=status_code, content=error_response)


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI validation errors"""
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"path": request.url.path, "method": request.method, "errors": errors},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "error_code": "VAL_002",
                "message": "Request validation failed",
                "details": {"validation_errors": errors},
                "recovery_suggestions": [
                    "Check the request format and required fields",
                    "Ensure all values match the expected types",
                ],
            },
            "status": "error",
            "path": request.url.path,
            "method": request.method,
            "trace_id": trace_id_context.get(),
        },
    )


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP exception on {request.url.path}: {exc.status_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )

    # Map common HTTP errors to user-friendly messages
    error_messages = {
        404: "The requested resource was not found",
        403: "You don't have permission to access this resource",
        401: "Authentication required. Please log in.",
        400: "Invalid request format",
        405: "This method is not allowed for this endpoint",
        500: "An internal server error occurred",
    }

    recovery_suggestions = {
        404: [
            "Check the URL is correct",
            "The resource may have been moved or deleted",
        ],
        403: [
            "Contact your administrator for access",
            "Check if you're logged into the correct account",
        ],
        401: ["Please log in and try again", "Your session may have expired"],
        400: ["Check your request format", "Ensure all required fields are provided"],
        405: ["Use the correct HTTP method for this endpoint"],
        500: ["Please try again later", "If the problem persists, contact support"],
    }

    user_message = error_messages.get(exc.status_code, str(exc.detail))
    suggestions = recovery_suggestions.get(exc.status_code, ["Please try again"])

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "error_code": f"HTTP_{exc.status_code}",
                "message": user_message,
                "details": {"original_message": str(exc.detail)},
                "recovery_suggestions": suggestions,
            },
            "status": "error",
            "path": request.url.path,
            "method": request.method,
            "trace_id": trace_id_context.get(),
        },
    )


async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors"""
    # Log the full error internally
    logger.error(
        f"Database error on {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_details": str(exc),
        },
        exc_info=True,
    )

    # Determine user-friendly message based on error type
    if isinstance(exc, IntegrityError):
        user_message = (
            "Data integrity error. The operation violates database constraints."
        )
        suggestions = [
            "Check for duplicate entries",
            "Ensure all required relationships exist",
            "Verify data uniqueness requirements",
        ]
        error_code = "DB_002"
    else:
        user_message = "A database error occurred. Please try again later."
        suggestions = [
            "Please try your request again in a few moments",
            "If the problem persists, contact support",
        ]
        error_code = "DB_001"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "error_code": error_code,
                "message": user_message,
                "recovery_suggestions": suggestions,
            },
            "status": "error",
            "path": request.url.path,
            "method": request.method,
            "trace_id": trace_id_context.get(),
        },
    )


async def handle_generic_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""
    # Generate trace ID if not present
    trace_id = trace_id_context.get()

    # Log the full error with traceback
    logger.critical(
        f"Unexpected error on {request.url.path}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "trace_id": trace_id,
        },
        exc_info=True,
    )

    # Generic user-friendly response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "error_code": "SYS_001",
                "message": "An unexpected error occurred. Our team has been notified.",
                "recovery_suggestions": [
                    "Please try your request again",
                    "If the issue persists, contact support with the trace ID",
                ],
                "trace_id": trace_id,
            },
            "status": "error",
            "path": request.url.path,
            "method": request.method,
        },
    )


def _get_status_code(exc: BaseApplicationError) -> int:
    """Map exception types to HTTP status codes"""
    if isinstance(exc, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, (AuthorizationError, TenantIsolationError)):
        return status.HTTP_403_FORBIDDEN
    elif isinstance(exc, FlowNotFoundError):
        return status.HTTP_404_NOT_FOUND
    elif isinstance(exc, NetworkTimeoutError):
        return status.HTTP_504_GATEWAY_TIMEOUT
    elif isinstance(exc, ResourceExhaustedError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, DatabaseError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        # Default to 500 for unknown application errors
        return status.HTTP_500_INTERNAL_SERVER_ERROR


def register_error_handlers(app):
    """Register all error handlers with the FastAPI app"""

    # Application errors
    app.add_exception_handler(BaseApplicationError, handle_application_error)

    # FastAPI validation errors
    app.add_exception_handler(RequestValidationError, handle_validation_error)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)

    # Database errors
    app.add_exception_handler(SQLAlchemyError, handle_database_error)

    # Generic errors (must be last)
    app.add_exception_handler(Exception, handle_generic_error)

    logger.info("Error handlers registered successfully")
