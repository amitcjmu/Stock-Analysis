"""
Legacy context functions for backward compatibility.
Extracted from context.py to reduce file size and complexity.
"""

# Re-export the legacy functions from main module to maintain backward compatibility
# This avoids circular imports and provides a single source of truth
from app.core.context import (  # noqa: F401
    get_client_account_id,
    get_engagement_id,
    get_user_id,
    get_flow_id,
)

# All functions are now re-exported from context.py
# This module exists purely for backward compatibility

__all__ = [
    "get_client_account_id",
    "get_engagement_id",
    "get_user_id",
    "get_flow_id",
]
