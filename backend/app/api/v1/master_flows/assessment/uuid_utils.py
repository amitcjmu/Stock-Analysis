"""
UUID conversion utilities for assessment endpoints.

Provides defense-in-depth UUID conversion for legacy integer client_account_id values.
"""

import logging
from typing import Union
from uuid import UUID

logger = logging.getLogger(__name__)


def ensure_uuid(value: Union[int, str, UUID]) -> UUID:
    """
    Convert int, str, or UUID to UUID safely.

    NOTE: As of October 2025, context middleware now handles legacy integer
    client_account_id conversion (app/core/context.py). This function provides
    defense-in-depth for edge cases and handles UUID/string conversion.

    Args:
        value: Value to convert (UUID object, string UUID, or legacy int ID)

    Returns:
        UUID object

    Raises:
        ValueError: If value cannot be converted to UUID
    """
    if isinstance(value, UUID):
        return value
    elif isinstance(value, str):
        return UUID(value)
    elif isinstance(value, int):
        # Defense-in-depth: Map legacy integer client_account_id to UUID
        # Primary fix is in context middleware (app/core/context.py)
        if value == 1:
            return UUID("11111111-1111-1111-1111-111111111111")
        else:
            raise ValueError(
                f"Cannot convert integer {value} to UUID - unknown mapping"
            )
    else:
        # Try to convert whatever it is
        try:
            return UUID(str(value))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Cannot convert {type(value)} value {value} to UUID: {e}")
