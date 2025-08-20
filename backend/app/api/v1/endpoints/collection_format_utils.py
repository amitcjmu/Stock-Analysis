"""
Collection Formatting Utilities
Formatting and conversion utilities for collection flows including
display name generation, error formatting, and UUID normalization.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from app.core.security.secure_logging import safe_log_format


def format_flow_display_name(
    application_count: int = 0, timestamp: Optional[datetime] = None
) -> str:
    """Format a display name for a collection flow.

    Args:
        application_count: Number of applications in the flow
        timestamp: Optional timestamp (defaults to current time)

    Returns:
        Formatted display name
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    if application_count > 0:
        return f"Collection from Discovery - {application_count} apps"
    else:
        return f"Collection Flow - {timestamp.strftime('%Y-%m-%d %H:%M')}"


def safe_format_error(
    error: Exception, default_message: str = "An error occurred"
) -> str:
    """Safely format an error message for logging.

    Args:
        error: Exception to format
        default_message: Default message if formatting fails

    Returns:
        Formatted error message
    """
    try:
        return safe_log_format("Error: {e}", e=error)
    except Exception:
        return default_message


def normalize_uuid(value: Any) -> Optional[UUID]:
    """Normalize a value to UUID, handling strings and None.

    Args:
        value: Value to normalize (UUID, string, or None)

    Returns:
        UUID object or None if conversion fails
    """
    if value is None:
        return None

    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None
