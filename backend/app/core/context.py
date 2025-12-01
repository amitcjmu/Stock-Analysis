"""
Context management for multi-tenant request handling.
Provides utilities for extracting and injecting client/engagement/flow context.
"""

import logging
import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from app.core.security.secure_logging import (
    safe_log_format,
    sanitize_headers_for_logging,
    mask_id,
)
from app.core.jwt_extraction import extract_user_id_from_jwt
from app.core.header_extraction import (
    DEMO_CLIENT_CONFIG,
    extract_client_account_id,
    extract_engagement_id,
    extract_user_id_from_headers,
    extract_flow_id,
)

logger = logging.getLogger(__name__)

# Context variable for request context
_request_context: ContextVar[Optional["RequestContext"]] = ContextVar(
    "request_context", default=None
)

# Legacy context variables for backward compatibility
_client_account_id: ContextVar[Optional[str]] = ContextVar(
    "client_account_id", default=None
)
_engagement_id: ContextVar[Optional[str]] = ContextVar("engagement_id", default=None)
_user_id: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
_flow_id: ContextVar[Optional[str]] = ContextVar("flow_id", default=None)

try:
    from app.models.client_account import ClientAccount, Engagement, User

    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError as e:
    logger.warning(safe_log_format("Client account models not available: {e}", e=e))
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = Engagement = User = None


@dataclass
class RequestContext:
    """Enhanced request context with audit fields"""

    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    user_id: Optional[str] = None
    flow_id: Optional[str] = None
    request_id: Optional[str] = None

    # Audit fields
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_version: Optional[str] = None

    # Feature flags
    feature_flags: Optional[Dict[str, bool]] = None

    def __post_init__(self):
        if self.feature_flags is None:
            self.feature_flags = {}
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if context has permission for resource/action"""
        # TODO: Implement permission checking
        return True

    def __repr__(self):
        return (
            f"RequestContext(client={self.client_account_id}, "
            f"engagement={self.engagement_id}, user={self.user_id}, flow={self.flow_id})"
        )


def extract_context_from_request(request: Request) -> RequestContext:
    """
    Extract context from request headers. Supports X-Client-Account-Id,
    X-Engagement-Id, X-User-Id, X-Flow-Id and their variations.
    """
    headers = request.headers
    logger.debug(
        safe_log_format(
            "🔍 Headers received: {sanitized_headers}",
            sanitized_headers=sanitize_headers_for_logging(dict(headers)),
        )
    )

    # Extract context values from headers
    client_account_id = extract_client_account_id(headers)
    engagement_id = extract_engagement_id(headers)
    user_id = extract_user_id_from_headers(headers)

    # CRITICAL FIX: If user_id not found in headers, extract from JWT token
    if not user_id:
        # SECURITY FIX: Get authorization header with case insensitive lookup
        auth_header = (
            headers.get("authorization")
            or headers.get("Authorization")
            or headers.get("AUTHORIZATION")
            or ""
        )
        user_id = extract_user_id_from_jwt(auth_header)

    flow_id = extract_flow_id(headers)

    # Log extracted values (with ID masking) - use DEBUG to reduce log noise
    logger.debug(
        safe_log_format(
            "🔍 Extracted - Client: {client_account_id}, "
            "Engagement: {engagement_id}, User: {user_id}, Flow: {flow_id}",
            client_account_id=mask_id(client_account_id),
            engagement_id=mask_id(engagement_id),
            user_id=mask_id(user_id),
            flow_id=mask_id(flow_id),
        )
    )

    context = RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        flow_id=flow_id,
    )
    logger.debug(safe_log_format("🔍 Final context: {context}", context=context))
    return context


def get_request_context(request: Request) -> RequestContext:
    """
    Extract and return request context from a FastAPI request.
    Also serves as FastAPI dependency function.
    """
    context = extract_context_from_request(request)
    set_request_context(context)
    return context


# Alias for backward compatibility
get_request_context_dependency = get_request_context


def set_request_context(context: RequestContext) -> None:
    """Set the current request context"""
    _request_context.set(context)
    # Also set legacy context variables for backward compatibility
    _client_account_id.set(context.client_account_id)
    _engagement_id.set(context.engagement_id)
    _user_id.set(context.user_id)
    _flow_id.set(context.flow_id)
    logger.debug(
        safe_log_format(
            "Set context for client {context_client_account_id}",
            context_client_account_id=context.client_account_id,
        )
    )


# Legacy alias for backward compatibility
set_context = set_request_context


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context"""
    context = _request_context.get()
    if context:
        return context

    # Fallback to legacy context variables for backward compatibility
    client_id = _client_account_id.get()
    engagement_id = _engagement_id.get()
    user_id = _user_id.get()
    flow_id = _flow_id.get()

    if any([client_id, engagement_id, user_id, flow_id]):
        return RequestContext(
            client_account_id=client_id,
            engagement_id=engagement_id,
            user_id=user_id,
            flow_id=flow_id,
        )

    return None


def get_required_context() -> RequestContext:
    """Get context or raise if not available"""
    context = get_current_context()
    if not context:
        raise RuntimeError("No request context available")
    return context


async def get_current_context_dependency() -> RequestContext:
    """
    FastAPI dependency function for getting current request context.
    This function can be used with Depends() to inject context into endpoints.

    Returns:
        Current RequestContext that was set by the middleware

    Usage:
        @app.get("/api/data")
        async def get_data(context: RequestContext = Depends(get_current_context_dependency)):
            # Use context.client_account_id, etc.
    """
    context = get_current_context()
    if not context:
        raise HTTPException(
            status_code=500,
            detail=(
                "No request context available. This usually means the context "
                "middleware is not properly configured."
            ),
        )
    return context


def clear_request_context() -> None:
    """Clear the current request context"""
    _request_context.set(None)
    # Also clear legacy variables
    _client_account_id.set(None)
    _engagement_id.set(None)
    _user_id.set(None)
    _flow_id.set(None)


# Backward compatibility imports and wrapper functions
# These functions delegate to the refactored modules but maintain the original interface


def validate_context(
    context: RequestContext,
    require_client: bool = True,
    require_engagement: bool = False,
) -> None:
    """
    Validate that required context is present.
    Wrapper for backward compatibility.
    """
    from app.core.context_utils import validate_context as _validate

    _validate(context, require_client, require_engagement)


def is_demo_client(client_account_id: Optional[str] = None) -> bool:
    """
    Check if the given client account ID matches our demo client.
    Wrapper for backward compatibility that doesn't require demo_client_config parameter.

    Args:
        client_account_id: Client account ID to check, or None to use current context

    Returns:
        True if this is the demo client
    """
    if client_account_id is None:
        # Get client account ID directly from context var to avoid circular import
        client_account_id = _client_account_id.get()

    from app.core.context_utils import is_demo_client as _is_demo_client

    return _is_demo_client(client_account_id, DEMO_CLIENT_CONFIG)


def create_context_headers(context: RequestContext) -> Dict[str, str]:
    """
    Create HTTP headers from request context.
    Wrapper for backward compatibility.
    """
    from app.core.context_utils import create_context_headers as _create_headers

    return _create_headers(context)


async def resolve_demo_client_ids(db_session) -> None:
    """
    Resolve and update demo client configuration from database.
    Wrapper for backward compatibility.
    """
    from app.core.context_utils import resolve_demo_client_ids as _resolve_ids

    await _resolve_ids(db_session, DEMO_CLIENT_CONFIG)


# Legacy getter functions for backward compatibility
# These are defined here to avoid circular imports with context_legacy.py


def get_client_account_id() -> Optional[str]:
    """Get current client account ID."""
    return _client_account_id.get()


def get_engagement_id() -> Optional[str]:
    """Get current engagement ID."""
    return _engagement_id.get()


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return _user_id.get()


def get_flow_id() -> Optional[str]:
    """Get current flow ID."""
    return _flow_id.get()


def require_flow_id() -> str:
    """
    Get current flow ID, raising an error if not set.

    Bug #1161 Fix: Provides clear error messages when flow_id is None,
    helping identify context initialization issues during testing.

    Raises:
        ValueError: If flow_id is not set in current context
    """
    flow_id = _flow_id.get()
    if not flow_id:
        # Log context details to aid debugging
        logger.warning(
            "require_flow_id() called but flow_id not set in context. "
            f"client_account_id={_client_account_id.get()}, "
            f"engagement_id={_engagement_id.get()}, "
            f"user_id={_user_id.get()}"
        )
        raise ValueError(
            "flow_id is required but not set in current context. "
            "Ensure X-Flow-Id header is provided or context is properly initialized."
        )
    return flow_id


def get_flow_id_or_default(default: str = "unknown") -> str:
    """
    Get current flow ID with a fallback default value.

    Bug #1161 Fix: Provides safe access to flow_id with a default,
    preventing None-related errors in string operations.

    Args:
        default: Value to return if flow_id is not set

    Returns:
        The flow_id if set, otherwise the default value
    """
    return _flow_id.get() or default
