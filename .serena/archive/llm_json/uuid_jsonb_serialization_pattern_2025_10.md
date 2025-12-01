# UUID to JSONB Serialization Pattern (October 2025)

## Problem
PostgreSQL JSONB columns cannot directly store Python UUID objects. Attempting to insert causes:
```
TypeError: Object of type UUID is not JSON serializable
```

## Root Cause
When creating database records with JSONB columns that contain nested data structures, Python UUID objects must be converted to strings before JSON serialization.

## Solution Pattern

### Recursive UUID Serialization Helper
```python
from typing import Dict, Any
from uuid import UUID

def serialize_uuids_for_jsonb(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert all UUID objects to strings for JSONB storage compatibility.

    PostgreSQL JSONB columns cannot directly store Python UUID objects.
    This function recursively converts all UUID instances to strings.

    Args:
        data: Dictionary potentially containing UUID objects

    Returns:
        Dictionary with all UUIDs converted to strings
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_uuids_for_jsonb(value)
        elif isinstance(value, list):
            result[key] = [
                (
                    serialize_uuids_for_jsonb(item)
                    if isinstance(item, dict)
                    else str(item) if isinstance(item, UUID) else item
                )
                for item in value
            ]
        else:
            result[key] = value
    return result
```

## Usage Example: Asset Conflict Resolution

**File**: `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py`

```python
from app.models.asset_conflict_resolution import AssetConflictResolution

# Serialize before storing in JSONB column
for conflict in conflicts_data:
    serialized_new_asset_data = serialize_uuids_for_jsonb(
        conflict["new_asset_data"]
    )

    conflict_record = AssetConflictResolution(
        client_account_id=UUID(client_account_id),  # Regular UUID column - OK
        engagement_id=UUID(engagement_id),           # Regular UUID column - OK
        discovery_flow_id=child_flow_id,             # Regular UUID column - OK
        master_flow_id=UUID(master_flow_id),         # Regular UUID column - OK
        existing_asset_snapshot=conflict["existing_asset_data"],  # Already serialized
        new_asset_data=serialized_new_asset_data,    # ✅ NOW SERIALIZED
        resolution_status="pending",
    )
    db_session.add(conflict_record)
```

## When to Apply

Apply this pattern when:
1. Storing dictionaries in JSONB columns that may contain UUID objects
2. The data comes from SQLAlchemy models with UUID fields
3. Data includes tenant scoping fields (client_account_id, engagement_id)
4. Nested data structures with mixed types

## Common Scenarios

### Scenario 1: Conflict Records
```python
# Asset data from database includes UUID fields
asset_data = {
    "name": "server01",
    "client_account_id": UUID("..."),  # Will fail in JSONB!
    "engagement_id": UUID("..."),      # Will fail in JSONB!
}

# Serialize before storing
serialized = serialize_uuids_for_jsonb(asset_data)
record.snapshot = serialized  # ✅ Works
```

### Scenario 2: Audit Logs
```python
# Log entry with UUID references
log_entry = {
    "user_id": UUID("..."),
    "resource_id": UUID("..."),
    "changes": {"field": "value"}
}

serialized = serialize_uuids_for_jsonb(log_entry)
audit_log.metadata = serialized  # ✅ Works
```

## NOT Needed For

1. **Regular UUID columns** - SQLAlchemy handles these automatically
2. **String columns** - Already serialized
3. **Reading from JSONB** - UUIDs come back as strings, conversion only needed when writing

## Related Patterns

- **sqlalchemy-integrity-error-rollback-pattern**: Handle database errors after serialization attempts
- **unified_asset_deduplication_architecture_oct2025**: Context for conflict detection that generates the data

## Files Using This Pattern

1. `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py:25-55` - Helper function
2. `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py:244-246` - Usage in conflict creation

## Discovery Context

- Found during asset conflict resolution feature implementation (October 2025)
- QA testing discovered TypeError during Phase 3 (conflict modal display)
- Backend logs showed: "Object of type UUID is not JSON serializable"
- Transaction rolled back, preventing conflict records from being saved
- Fix applied: commit ffa996f0d

## Prevention

To avoid this issue:
1. Always serialize dictionaries with UUID objects before JSONB storage
2. Check if data comes from SQLAlchemy models (likely has UUIDs)
3. Test with actual database inserts, not just mocks
4. Use QA agents to catch serialization errors during integration testing
