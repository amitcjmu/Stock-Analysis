"""
UUID conversion utilities for assessment endpoints.

Provides defense-in-depth UUID conversion for legacy integer client_account_id values.
"""

import logging
from typing import Union, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Demo client UUID mappings (per Alembic migration pattern)
# Reference: .serena/memories/alembic-integer-to-uuid-migration-pattern.md
DEMO_INTEGER_TO_UUID_MAP = {
    1: UUID("11111111-1111-1111-1111-111111111111"),  # Demo client account
    2: UUID("22222222-2222-2222-2222-222222222222"),  # Demo engagement
}


def ensure_uuid(value: Union[int, str, UUID, None]) -> Optional[UUID]:
    """
    Convert int, str, or UUID to UUID safely.

    Handles both INTEGER and UUID formats for client_account_id/engagement_id.
    Frontend may send INTEGER values (e.g., 1, 2) which need conversion to UUID format.

    For demo/known integer values (1, 2), maps to standard demo UUIDs.
    For unknown integers, uses zero-padding conversion.

    Args:
        value: Value to convert (UUID object, string UUID, integer, or None)

    Returns:
        UUID object or None if value is None

    Raises:
        ValueError: If value cannot be converted to UUID

    Examples:
        >>> ensure_uuid(UUID("11111111-1111-1111-1111-111111111111"))
        UUID('11111111-1111-1111-1111-111111111111')
        >>> ensure_uuid("11111111-1111-1111-1111-111111111111")
        UUID('11111111-1111-1111-1111-111111111111')
        >>> ensure_uuid(1)  # Demo client
        UUID('11111111-1111-1111-1111-111111111111')
        >>> ensure_uuid("1")  # Demo client via string
        UUID('11111111-1111-1111-1111-111111111111')
        >>> ensure_uuid(2)  # Demo engagement
        UUID('22222222-2222-2222-2222-222222222222')
        >>> ensure_uuid(999)  # Unknown integer
        UUID('00000000-0000-0000-0000-0000000003e7')
    """
    if value is None:
        return None

    # Already a UUID object - return as-is
    if isinstance(value, UUID):
        return value

    # Handle string values
    if isinstance(value, str):
        # Try direct UUID conversion first (for properly formatted UUIDs)
        try:
            return UUID(value)
        except ValueError:
            # If direct conversion fails, check if it's a string representation of an integer
            try:
                int_value = int(value)
                # Use the integer conversion path (includes demo mapping)
                return _convert_int_to_uuid(int_value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Cannot convert string '{value}' to UUID - not a valid UUID or integer"
                )

    # Handle integer values directly
    if isinstance(value, int):
        return _convert_int_to_uuid(value)

    # Fallback: try to convert to string then UUID
    try:
        return UUID(str(value))
    except (ValueError, AttributeError, TypeError) as e:
        raise ValueError(
            f"Cannot convert {type(value).__name__} value '{value}' to UUID: {e}"
        )


def _convert_int_to_uuid(int_value: int) -> UUID:
    """
    Convert integer to UUID with demo value mapping.

    Args:
        int_value: Integer to convert

    Returns:
        UUID object (demo UUID if known, zero-padded UUID otherwise)
    """
    # Check if this is a known demo value
    if int_value in DEMO_INTEGER_TO_UUID_MAP:
        demo_uuid = DEMO_INTEGER_TO_UUID_MAP[int_value]
        logger.debug(f"Mapped demo integer {int_value} to UUID: {demo_uuid}")
        return demo_uuid

    # For unknown integers, use zero-padding conversion
    hex_str = f"{int_value:032x}"
    # Format as UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    formatted = f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"
    logger.debug(f"Converted integer {int_value} to zero-padded UUID: {formatted}")
    return UUID(formatted)
