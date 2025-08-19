"""
Legacy context functions for backward compatibility.
Extracted from context.py to reduce file size and complexity.
"""

from typing import Optional

# Import context variables from main module
from app.core.context import (
    _client_account_id,
    _engagement_id,
    _user_id,
    _flow_id,
)


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
