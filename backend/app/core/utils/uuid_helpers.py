"""
UUID Helper Utilities for Type Consistency
Provides consistent UUID/string conversion across the application.
"""

import uuid
from typing import Any, Optional, Union


def ensure_uuid(value: Union[str, uuid.UUID, None]) -> Optional[uuid.UUID]:
    """
    Convert string or UUID to UUID object consistently.

    Args:
        value: String, UUID, or None value to convert

    Returns:
        UUID object or None if invalid/empty

    Examples:
        >>> ensure_uuid("11111111-1111-1111-1111-111111111111")
        UUID('11111111-1111-1111-1111-111111111111')
        >>> ensure_uuid(uuid.uuid4())
        UUID(...)
        >>> ensure_uuid(None)
        None
        >>> ensure_uuid("invalid")
        None
    """
    if value is None or value == "None":
        return None

    if isinstance(value, uuid.UUID):
        return value

    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return None

    return None


def ensure_uuid_str(value: Union[str, uuid.UUID, None]) -> Optional[str]:
    """
    Convert string or UUID to string consistently.

    Args:
        value: String, UUID, or None value to convert

    Returns:
        String representation or None if invalid/empty

    Examples:
        >>> ensure_uuid_str("11111111-1111-1111-1111-111111111111")
        "11111111-1111-1111-1111-111111111111"
        >>> ensure_uuid_str(uuid.uuid4())
        "..."
        >>> ensure_uuid_str(None)
        None
    """
    uuid_obj = ensure_uuid(value)
    return str(uuid_obj) if uuid_obj else None


def get_demo_client_id() -> uuid.UUID:
    """Get consistent demo client ID for fallbacks."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


def get_demo_engagement_id() -> uuid.UUID:
    """Get consistent demo engagement ID for fallbacks."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


def convert_uuids_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings for JSON serialization.

    This function prevents 'Object of type UUID is not JSON serializable' errors
    by recursively traversing data structures and converting UUID objects to strings.

    Args:
        obj: The object to convert (can be any type)

    Returns:
        Object with all UUIDs converted to strings

    Examples:
        >>> import uuid
        >>> test_uuid = uuid.uuid4()
        >>> convert_uuids_to_str(test_uuid)
        "..."
        >>> convert_uuids_to_str({"id": test_uuid, "name": "test"})
        {"id": "...", "name": "test"}
        >>> convert_uuids_to_str([test_uuid, "string", 123])
        ["...", "string", 123]
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return type(obj)(convert_uuids_to_str(item) for item in obj)
    return obj


class UUIDMixin:
    """
    Mixin for repositories to handle UUID fields consistently.

    Usage:
        class MyRepository(UUIDMixin, ContextAwareRepository):
            def __init__(self, db, client_account_id, engagement_id, user_id=None):
                self.client_account_id, self.engagement_id = self._parse_tenant_ids(
                    client_account_id, engagement_id
                )
                super().__init__(db, ...)
    """

    def _parse_tenant_ids(
        self,
        client_account_id: Union[str, uuid.UUID, None],
        engagement_id: Union[str, uuid.UUID, None],
    ) -> tuple[uuid.UUID, uuid.UUID]:
        """
        Parse and validate tenant IDs with fallbacks.

        Returns:
            Tuple of (client_account_id_uuid, engagement_id_uuid)
        """
        # Parse client account ID
        client_uuid = ensure_uuid(client_account_id)
        if not client_uuid:
            client_uuid = get_demo_client_id()

        # Parse engagement ID
        engagement_uuid = ensure_uuid(engagement_id)
        if not engagement_uuid:
            engagement_uuid = get_demo_engagement_id()

        return client_uuid, engagement_uuid

    def _ensure_uuid(self, value: Union[str, uuid.UUID]) -> uuid.UUID:
        """Ensure value is a UUID, raise error if invalid."""
        result = ensure_uuid(value)
        if result is None:
            raise ValueError(f"Invalid UUID format: {value}")
        return result
