"""
Header extraction utilities for multi-tenant context.

Provides functions for extracting client_account_id, engagement_id, user_id, and flow_id
from various header formats.

IMPORTANT: HTTP headers are case-insensitive per RFC 7230. However, to ensure maximum
compatibility, this module checks multiple casing variations explicitly:
- X-Client-Account-ID (frontend convention - uppercase 'ID')
- X-Client-Account-Id (backend recommendation - lowercase 'd')
- x-client-account-id (all lowercase)
- Alternative formats (X-Client-ID, client-account-id, etc.)

All variations are functionally equivalent due to Starlette's case-insensitive Headers class.
The multiple checks are defensive programming to ensure compatibility across different
HTTP clients and proxies.

For full specification, see: /docs/api/MULTI_TENANT_HEADERS.md
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Demo client configuration with fixed UUIDs for frontend fallback
DEMO_CLIENT_CONFIG = {
    "client_account_id": "11111111-1111-1111-1111-111111111111",
    "client_name": "Demo Corporation",
    "engagement_id": "22222222-2222-2222-2222-222222222222",
    "engagement_name": "Demo Cloud Migration Project",
}


def clean_header_value(value: str) -> str:
    """
    Clean header value by taking first non-empty value if comma-separated.
    SECURITY FIX: Enhanced normalization for header processing.

    Args:
        value: Header value to clean

    Returns:
        Cleaned header value
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


def extract_client_account_id(headers) -> Optional[str]:
    """
    Extract client account ID from various header formats.

    Args:
        headers: Request headers

    Returns:
        Client account ID or None
    """
    client_account_id = (
        headers.get("X-Client-Account-ID")  # Frontend sends this format
        or headers.get("x-client-account-id")
        or headers.get("X-Client-Account-Id")
        or headers.get("x-context-client-id")
        or headers.get("client-account-id")
        or headers.get("X-Client-ID")  # Frontend uses X-Client-ID
        or headers.get("x-client-id")  # Frontend uses x-client-id
    )

    if not client_account_id:
        return None

    return clean_header_value(client_account_id)


def extract_engagement_id(headers) -> Optional[str]:
    """
    Extract engagement ID from various header formats.

    Args:
        headers: Request headers

    Returns:
        Engagement ID or None
    """
    engagement_id = (
        headers.get("X-Engagement-ID")  # Frontend sends this format
        or headers.get("x-engagement-id")
        or headers.get("X-Engagement-Id")
        or headers.get("x-context-engagement-id")
        or headers.get("engagement-id")
    )

    return clean_header_value(engagement_id) if engagement_id else None


def extract_user_id_from_headers(headers) -> Optional[str]:
    """
    Extract user ID from various header formats.

    Args:
        headers: Request headers

    Returns:
        User ID or None
    """
    user_id = (
        headers.get("X-User-ID")  # Frontend sends this format
        or headers.get("x-user-id")
        or headers.get("X-User-Id")
        or headers.get("x-context-user-id")
        or headers.get("user-id")
    )
    return clean_header_value(user_id) if user_id else None


def extract_flow_id(headers) -> Optional[str]:
    """
    Extract flow ID from various header formats.

    Args:
        headers: Request headers

    Returns:
        Flow ID or None
    """
    flow_id = (
        headers.get("X-Flow-ID") or headers.get("x-flow-id") or headers.get("X-Flow-Id")
    )
    return clean_header_value(flow_id) if flow_id else None
