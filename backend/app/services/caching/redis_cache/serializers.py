"""
JSON Serialization utilities for Redis cache.

Handles serialization and deserialization of complex Python types
like datetime, UUID, and binary data for Redis storage.
"""

import base64

# JSON operations are handled by other modules
import uuid
from datetime import datetime, date, time
from typing import Any


def datetime_json_serializer(obj: Any) -> dict[str, Any]:
    """Custom JSON serializer for datetime objects and specific supported types

    Raises TypeError for unsupported types to prevent lossy serialization.
    Only handles explicitly supported types to maintain data integrity.
    """
    if isinstance(obj, datetime):
        return {"_type": "datetime", "_data": obj.isoformat()}
    elif isinstance(obj, date):
        return {"_type": "date", "_data": obj.isoformat()}
    elif isinstance(obj, time):
        return {"_type": "time", "_data": obj.isoformat()}
    elif isinstance(obj, uuid.UUID):
        return {"_type": "uuid", "_data": str(obj)}
    elif isinstance(obj, (bytes, bytearray, memoryview)):
        # Handle binary types properly - base64 encode to avoid double-encoding
        if isinstance(obj, (bytearray, memoryview)):
            obj = bytes(obj)  # Convert to bytes first
        return {"_type": "binary", "_data": base64.b64encode(obj).decode("ascii")}
    else:
        # Raise TypeError for unsupported types to prevent lossy serialization
        raise TypeError(
            f"Object of type '{type(obj).__name__}' is not JSON serializable. "
            f"Supported types: datetime, date, time, UUID, bytes, bytearray, memoryview. "
            f"To serialize this type, handle it explicitly in the calling code."
        )


def datetime_json_deserializer(data: Any) -> Any:
    """Custom JSON deserializer to recursively reconstruct typed objects from serialized format

    Handles datetime, date, time, UUID, and binary types, and recursively processes
    nested dictionaries and lists to restore all typed objects.
    """

    def _deserialize_recursive(obj: Any) -> Any:
        """Recursively deserialize nested structures"""
        if isinstance(obj, dict):
            obj_type = obj.get("_type")
            if obj_type and "_data" in obj:
                # Handle typed objects
                if obj_type == "datetime":
                    return datetime.fromisoformat(obj["_data"])
                elif obj_type == "date":
                    return date.fromisoformat(obj["_data"])
                elif obj_type == "time":
                    return time.fromisoformat(obj["_data"])
                elif obj_type == "uuid":
                    return uuid.UUID(obj["_data"])
                elif obj_type == "binary":
                    return base64.b64decode(obj["_data"])
            else:
                # Recursively process dictionary values
                return {
                    key: _deserialize_recursive(value) for key, value in obj.items()
                }
        elif isinstance(obj, list):
            # Recursively process list items
            return [_deserialize_recursive(item) for item in obj]

        return obj

    return _deserialize_recursive(data)
