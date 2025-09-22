"""
Utility functions for governance API endpoints.

Provides helper functions for approval workflow decisions and data transformation.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def requires_approval(risk_level: str, exception_type: str) -> bool:
    """
    Determine if an exception requires approval based on risk level and type.

    Args:
        risk_level: Risk level (low, medium, high, critical)
        exception_type: Type of exception (custom_approach, skip_migration, etc.)

    Returns:
        True if approval is required, False otherwise
    """
    high_risk_levels = ["high", "critical"]
    approval_required_types = ["custom_approach", "skip_migration"]

    return risk_level in high_risk_levels or exception_type in approval_required_types


def generate_approval_notes(risk_level: str, exception_type: str) -> str:
    """
    Generate standardized notes for approval requests.

    Args:
        risk_level: Risk level of the exception
        exception_type: Type of the exception

    Returns:
        Formatted approval request notes
    """
    return (
        f"Auto-generated approval request for {risk_level} "
        f"risk {exception_type} exception"
    )


def format_timestamp(timestamp) -> str:
    """
    Format timestamp for API response.

    Args:
        timestamp: Datetime object or None

    Returns:
        ISO formatted string or empty string
    """
    if timestamp:
        return timestamp.isoformat()
    return ""


def format_optional_id(obj_id) -> Optional[str]:
    """
    Format optional ID field for API response.

    Args:
        obj_id: UUID object or None

    Returns:
        String representation or None
    """
    return str(obj_id) if obj_id else None
