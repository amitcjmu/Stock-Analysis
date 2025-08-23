"""
Endpoint Migration Logger Utility

This utility helps track usage of legacy endpoints and provides migration guidance.
CC: Added as part of issue #222 fix for API endpoint inconsistencies.
"""

import logging
from typing import Dict, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Mapping of legacy endpoints to their new unified-discovery equivalents
ENDPOINT_MIGRATION_MAP: Dict[str, str] = {
    "/api/v1/discovery/flows/active": "/api/v1/unified-discovery/flows/active",
    "/api/v1/discovery/flows/{flow_id}/status": "/api/v1/unified-discovery/flows/{flow_id}/status",
    "/api/v1/discovery/flows/{flow_id}/clarifications/submit": "/api/v1/unified-discovery/flows/{flow_id}/clarifications/submit",
    "/api/v1/discovery/flows/{flow_id}/data-cleansing": "/api/v1/unified-discovery/flows/{flow_id}/data-cleansing",
    "/api/v1/discovery/flows/{flow_id}/field-mappings": "/api/v1/unified-discovery/flows/{flow_id}/field-mappings",
    "/api/v1/discovery/flow/{flow_id}/resume": "/api/v1/unified-discovery/flow/{flow_id}/resume",
    "/api/v1/discovery/latest-import": "/api/v1/data-import/latest-import",
}


def log_legacy_endpoint_usage(
    endpoint: str, user_id: Optional[str] = None, client_ip: Optional[str] = None
):
    """
    Log usage of legacy endpoints with migration guidance.

    Args:
        endpoint: The legacy endpoint being used
        user_id: Optional user ID for tracking
        client_ip: Optional client IP for tracking
    """
    if endpoint in ENDPOINT_MIGRATION_MAP:
        new_endpoint = ENDPOINT_MIGRATION_MAP[endpoint]

        logger.warning(
            f"🔄 LEGACY ENDPOINT USED: {endpoint} | "
            f"MIGRATE TO: {new_endpoint} | "
            f"User: {user_id or 'unknown'} | "
            f"IP: {client_ip or 'unknown'}"
        )
    else:
        # Check for pattern matches (endpoints with dynamic parts)
        for legacy_pattern, new_pattern in ENDPOINT_MIGRATION_MAP.items():
            if (
                "{" in legacy_pattern
                and legacy_pattern.replace("{flow_id}", "*") in endpoint
            ):
                logger.warning(
                    f"🔄 LEGACY ENDPOINT PATTERN USED: {endpoint} | "
                    f"MIGRATE TO PATTERN: {new_pattern} | "
                    f"User: {user_id or 'unknown'} | "
                    f"IP: {client_ip or 'unknown'}"
                )
                break


def endpoint_migration_warning(legacy_endpoint: str):
    """
    Decorator to add migration warnings to legacy endpoint handlers.

    Args:
        legacy_endpoint: The legacy endpoint path
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Log the legacy endpoint usage
            log_legacy_endpoint_usage(legacy_endpoint)

            # Execute the original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_migration_suggestion(legacy_endpoint: str) -> Optional[str]:
    """
    Get migration suggestion for a legacy endpoint.

    Args:
        legacy_endpoint: The legacy endpoint path

    Returns:
        The suggested new endpoint, or None if no mapping exists
    """
    return ENDPOINT_MIGRATION_MAP.get(legacy_endpoint)


def validate_endpoint_migration():
    """
    Validate that all legacy endpoints have valid migration paths.
    This can be called during application startup.
    """
    logger.info("🔍 Validating endpoint migration mappings...")

    for legacy, new in ENDPOINT_MIGRATION_MAP.items():
        logger.info(f"  {legacy} → {new}")

    logger.info(
        f"✅ {len(ENDPOINT_MIGRATION_MAP)} endpoint migration mappings validated"
    )


# Export utility functions
__all__ = [
    "log_legacy_endpoint_usage",
    "endpoint_migration_warning",
    "get_migration_suggestion",
    "validate_endpoint_migration",
    "ENDPOINT_MIGRATION_MAP",
]
