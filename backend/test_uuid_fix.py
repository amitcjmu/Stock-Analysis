#!/usr/bin/env python3
"""Test script to verify UUID serialization fix in execution_engine.py"""

import asyncio
import uuid
from datetime import datetime


async def test_uuid_serialization():
    print("Testing UUID serialization fix...")
    
    # Test data with UUIDs
    test_data = {
        "flow_id": str(uuid.uuid4()),
        "user_id": uuid.uuid4(),  # Deliberately leave as UUID object
        "engagement_id": uuid.uuid4(),  # Deliberately leave as UUID object
        "timestamp": datetime.utcnow(),
        "metadata": {
            "nested_uuid": uuid.uuid4(),
            "list_with_uuid": [uuid.uuid4(), uuid.uuid4()],
            "normal_data": "test"
        }
    }
    
    # Import the execution engine
    try:
        from app.services.flow_orchestration.execution_engine import FlowExecutionEngine
        
        # Create a dummy engine instance
        engine = FlowExecutionEngine(None, None)
        
        # Test the serialization method
        serialized = engine._ensure_json_serializable(test_data)
        
        print("✅ Serialization successful!")
        print(f"Original data type: user_id = {type(test_data['user_id'])}")
        print(f"Serialized data type: user_id = {type(serialized['user_id'])}")
        print(f"Nested UUID serialized: {serialized['metadata']['nested_uuid']}")
        
        # Try to JSON encode it
        import json
        json_str = json.dumps(serialized)
        print("✅ JSON encoding successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_uuid_serialization())