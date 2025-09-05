"""
Utility functions for Unified Discovery Flow State.
JSON encoder and UUID handling utilities.
"""

import json
import uuid
from datetime import datetime
from typing import Any


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID objects"""

    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_uuid_to_str(value: Any) -> str:
    """Safely convert UUID or string to string"""
    if isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, str):
        return value
    elif value is None:
        return ""
    else:
        return str(value)
