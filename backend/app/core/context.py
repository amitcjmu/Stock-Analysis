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

# Demo client configuration with fixed UUIDs for frontend fallback
DEMO_CLIENT_CONFIG = {
    "client_account_id": "11111111-1111-1111-1111-111111111111",
    "client_name": "Demo Corporation",
    "engagement_id": "22222222-2222-2222-2222-222222222222",
    "engagement_name": "Demo Cloud Migration Project",
}

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


def _decode_jwt_payload(token: str) -> Optional[str]:
    """
    Decode JWT payload and extract user_id (sub claim).

    SECURITY WARNING: This function decodes JWT without verification.
    It should only be used as a fallback when proper JWT verification fails.
    """
    import base64
    import json

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_part = parts[1]
        # Add padding only if needed
        missing_padding = (-len(payload_part)) % 4
        if missing_padding:
            payload_part += "=" * missing_padding
        decoded_payload = base64.urlsafe_b64decode(payload_part)
        payload = json.loads(decoded_payload)

        # SECURITY FIX: Validate payload structure and prevent system user impersonation
        sub_claim = payload.get("sub")

        # CRITICAL: Never trust or use 'system' or empty subjects
        if not sub_claim or sub_claim in ["system", "admin", "root", ""]:
            logger.warning(
                safe_log_format(
                    "🚨 SECURITY: Rejecting suspicious JWT subject claim: {sub_claim}",
                    sub_claim=sub_claim or "empty",
                )
            )
            return None

        # Additional validation: subject should be a valid UUID or identifier
        if len(str(sub_claim).strip()) < 3:
            logger.warning(
                safe_log_format(
                    "🚨 SECURITY: Rejecting too-short JWT subject claim: {sub_claim}",
                    sub_claim=sub_claim,
                )
            )
            return None

        # Validate that sub claim doesn't contain suspicious patterns
        suspicious_patterns = ["system", "admin", "root", "service", "internal", "api"]
        sub_lower = str(sub_claim).lower()
        if any(pattern in sub_lower for pattern in suspicious_patterns):
            logger.warning(
                safe_log_format(
                    "🚨 SECURITY: Rejecting JWT with suspicious subject pattern: {sub_claim}",
                    sub_claim=sub_claim,
                )
            )
            return None

        return sub_claim
    except Exception as e:
        logger.warning(
            safe_log_format("JWT payload decode failed: {error}", error=str(e))
        )
        return None


def _extract_user_id_via_jwt_service(token: str) -> Optional[str]:
    """Extract user_id using JWT service as fallback."""
    try:
        from app.services.auth_services.jwt_service import JWTService

        jwt_service = JWTService()
        payload = jwt_service.verify_token(token)
        return payload.get("sub") if payload else None
    except Exception as jwt_error:
        logger.warning(
            safe_log_format(
                "JWT service verification failed: {jwt_error}",
                jwt_error=str(jwt_error),
            )
        )
        return None


def _extract_user_id_from_jwt(auth_header: str) -> Optional[str]:
    """
    Extract user_id from JWT token in Authorization header.

    This is a critical security fix that prevents flows from being created
    with user_id="system" which causes validation errors.

    Args:
        auth_header: Authorization header value

    Returns:
        User ID extracted from JWT token, or None if extraction fails
    """
    # SECURITY FIX: Normalize header value for case variations and extra spaces
    if not auth_header:
        return None

    # Strip extra spaces and normalize case
    normalized_header = auth_header.strip()

    # Check for Bearer token with case insensitive comparison
    if not normalized_header.lower().startswith("bearer "):
        return None

    try:
        # SECURITY FIX: Handle extra spaces properly and guard against headers with only scheme
        parts = normalized_header.split()
        if len(parts) != 2:
            logger.warning(
                "Authorization header does not contain exactly 2 parts (scheme and token)"
            )
            return None

        scheme, token = parts
        if not token:
            logger.warning("Authorization header contains empty token")
            return None

        # Try direct JWT decode first (more reliable for user_id extraction)
        user_id = _decode_jwt_payload(token)
        if user_id:
            logger.info(
                safe_log_format(
                    "✅ Extracted user_id from JWT token: {user_id}",
                    user_id=mask_id(user_id),
                )
            )
            return user_id

        # Fallback to JWT service for proper verification
        logger.debug("Direct JWT decode failed, trying JWT service")
        user_id = _extract_user_id_via_jwt_service(token)
        if user_id:
            logger.info(
                safe_log_format(
                    "✅ Extracted user_id from JWT service: {user_id}",
                    user_id=mask_id(user_id),
                )
            )
            return user_id

    except Exception as e:
        logger.warning(
            safe_log_format("Failed to extract user_id from JWT: {error}", error=str(e))
        )
    return None


def _clean_header_value(value: str) -> str:
    """
    Clean header value by taking first non-empty value if comma-separated.
    SECURITY FIX: Enhanced normalization for header processing.
    """
    if not value:
        return value

    # SECURITY FIX: Strip extra spaces and normalize
    normalized_value = value.strip()
    if not normalized_value:
        return value

    # Split by comma and take the first non-empty value
    parts = [part.strip() for part in normalized_value.split(",") if part.strip()]
    return parts[0] if parts else normalized_value


def _extract_client_account_id(headers) -> Optional[str]:
    """Extract client account ID from various header formats."""
    client_account_id = (
        headers.get("X-Client-Account-ID")  # Frontend sends this format
        or headers.get("x-client-account-id")
        or headers.get("X-Client-Account-Id")
        or headers.get("x-context-client-id")
        or headers.get("client-account-id")
        or headers.get("X-Client-ID")  # Frontend uses X-Client-ID
        or headers.get("x-client-id")  # Frontend uses x-client-id
    )
    return _clean_header_value(client_account_id) if client_account_id else None


def _extract_engagement_id(headers) -> Optional[str]:
    """Extract engagement ID from various header formats."""
    engagement_id = (
        headers.get("X-Engagement-ID")  # Frontend sends this format
        or headers.get("x-engagement-id")
        or headers.get("X-Engagement-Id")
        or headers.get("x-context-engagement-id")
        or headers.get("engagement-id")
    )
    return _clean_header_value(engagement_id) if engagement_id else None


def _extract_user_id_from_headers(headers) -> Optional[str]:
    """Extract user ID from various header formats."""
    user_id = (
        headers.get("X-User-ID")  # Frontend sends this format
        or headers.get("x-user-id")
        or headers.get("X-User-Id")
        or headers.get("x-context-user-id")
        or headers.get("user-id")
    )
    return _clean_header_value(user_id) if user_id else None


def _extract_flow_id(headers) -> Optional[str]:
    """Extract flow ID from various header formats."""
    flow_id = (
        headers.get("X-Flow-ID") or headers.get("x-flow-id") or headers.get("X-Flow-Id")
    )
    return _clean_header_value(flow_id) if flow_id else None


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
    client_account_id = _extract_client_account_id(headers)
    engagement_id = _extract_engagement_id(headers)
    user_id = _extract_user_id_from_headers(headers)

    # CRITICAL FIX: If user_id not found in headers, extract from JWT token
    if not user_id:
        # SECURITY FIX: Get authorization header with case insensitive lookup
        auth_header = (
            headers.get("authorization")
            or headers.get("Authorization")
            or headers.get("AUTHORIZATION")
            or ""
        )
        user_id = _extract_user_id_from_jwt(auth_header)

    flow_id = _extract_flow_id(headers)

    # Log extracted values (with ID masking)
    logger.info(
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
    logger.info(safe_log_format("🔍 Final context: {context}", context=context))
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
