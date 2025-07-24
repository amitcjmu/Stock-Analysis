#!/usr/bin/env python3
"""Direct test of the _ensure_json_serializable method"""

import json
import uuid
from datetime import datetime
from typing import Any


# Copy the method from execution_engine.py
def _ensure_json_serializable(obj: Any) -> Any:
    """
    Recursively ensure all objects in a structure are JSON serializable.
    Handles UUIDs, datetimes, sets, and custom objects.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {key: _ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_ensure_json_serializable(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        # Handle custom objects by converting to dict
        return _ensure_json_serializable(obj.__dict__)
    else:
        return obj


def test_uuid_serialization():
    print("Testing UUID serialization method directly...")

    # Test data with UUIDs
    test_data = {
        "flow_id": str(uuid.uuid4()),
        "user_id": uuid.uuid4(),  # Deliberately leave as UUID object
        "engagement_id": uuid.uuid4(),  # Deliberately leave as UUID object
        "timestamp": datetime.utcnow(),
        "metadata": {
            "nested_uuid": uuid.uuid4(),
            "list_with_uuid": [uuid.uuid4(), uuid.uuid4()],
            "normal_data": "test",
        },
    }

    try:
        # Test the serialization method
        serialized = _ensure_json_serializable(test_data)

        print("✅ Serialization successful!")
        print(f"Original data type: user_id = {type(test_data['user_id'])}")
        print(f"Serialized data type: user_id = {type(serialized['user_id'])}")
        print(f"Nested UUID serialized: {serialized['metadata']['nested_uuid']}")

        # Try to JSON encode it
        json_str = json.dumps(serialized)
        print("✅ JSON encoding successful!")
        print(f"JSON length: {len(json_str)} characters")

        # Verify we can parse it back
        json.loads(json_str)
        print("✅ JSON parsing successful!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_uuid_serialization()
