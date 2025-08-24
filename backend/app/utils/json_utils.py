"""
JSON serialization utilities with UUID support.

This module provides utilities to handle JSON serialization of UUID objects,
addressing the common 'Object of type UUID is not JSON serializable' error.
"""

import json
from typing import Any
from uuid import UUID


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle UUID objects by converting them to strings.

    This encoder fixes the 'Object of type UUID is not JSON serializable' error
    by automatically converting UUID instances to their string representation.

    Usage:
        json.dumps(data_with_uuids, cls=UUIDEncoder)

    Or use the convenience functions below:
        safe_json_dumps(data_with_uuids)
        safe_json_dump(data_with_uuids, file_handle)
    """

    def default(self, obj: Any) -> Any:
        """Convert UUID objects to strings for JSON serialization.

        Args:
            obj: Object to serialize

        Returns:
            String representation of UUID or delegates to parent encoder

        Raises:
            TypeError: If object is not JSON serializable and not a UUID
        """
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize objects to JSON, handling UUIDs automatically.

    This is a drop-in replacement for json.dumps that automatically handles
    UUID objects by converting them to strings.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments passed to json.dumps

    Returns:
        JSON string representation of the object

    Example:
        data = {"id": uuid4(), "name": "test"}
        json_str = safe_json_dumps(data)  # Works without error
    """
    # Set UUIDEncoder as default cls if not already specified
    if "cls" not in kwargs:
        kwargs["cls"] = UUIDEncoder

    return json.dumps(obj, **kwargs)


def safe_json_dump(obj: Any, fp, **kwargs) -> None:
    """Safely write objects to JSON file, handling UUIDs automatically.

    This is a drop-in replacement for json.dump that automatically handles
    UUID objects by converting them to strings.

    Args:
        obj: Object to serialize
        fp: File-like object to write to
        **kwargs: Additional arguments passed to json.dump

    Example:
        data = {"id": uuid4(), "name": "test"}
        with open("data.json", "w") as f:
            safe_json_dump(data, f)  # Works without error
    """
    if "cls" not in kwargs:
        kwargs["cls"] = UUIDEncoder

    return json.dump(obj, fp, **kwargs)


def ensure_json_serializable(obj: Any) -> Any:
    """Recursively convert UUID objects to strings in data structures.

    This function traverses dictionaries, lists, and other common data structures
    to convert any UUID instances to strings, making the entire structure
    JSON serializable.

    Args:
        obj: Object to process

    Returns:
        Copy of the object with UUIDs converted to strings

    Example:
        data = {"id": uuid4(), "items": [uuid4(), "string", 123]}
        clean_data = ensure_json_serializable(data)
        json.dumps(clean_data)  # Works without custom encoder
    """
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, set):
        return {ensure_json_serializable(item) for item in obj}
    else:
        return obj
