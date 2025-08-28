# Data Integrity and Counting Patterns

## Record Count Verification

### Problem: Zero Records Despite Data Present
**Symptoms**: UI shows 0 records but data exists in database
**Root Cause**: Relying on cached/stored count fields instead of actual data

**Solution Pattern**:
```python
from sqlalchemy import select, func
from app.models.data_import import RawImportRecord
from app.core.database import AsyncSessionLocal

async def get_actual_record_count(data_import_id):
    """Always query actual count from source table"""
    async with AsyncSessionLocal() as db:
        count_query = select(func.count(RawImportRecord.id)).where(
            RawImportRecord.data_import_id == data_import_id
        )
        count_result = await db.execute(count_query)
        actual_count = count_result.scalar() or 0

        # Fallback to stored count only if query fails
        total_records = actual_count if actual_count > 0 else (data_import.total_records or 0)

        logger.info(
            f"📊 Data import {data_import_id}: actual_count={actual_count}, "
            f"total_records field={data_import.total_records}, using={total_records}"
        )
        return total_records
```

### Key Principles:
1. **Always verify counts** from source tables
2. **Log discrepancies** between stored and actual counts
3. **Use independent sessions** for count queries to avoid transaction issues
4. **Fallback gracefully** when queries fail

## Field Mapping Data Integrity

### Problem: Incorrect Fields Shown in Mapping
**Symptoms**: UI shows fields that don't exist in uploaded data
**Root Cause**: CSV parsing creating wrapper metadata structure

**Detection Pattern**:
```python
# Log sample record to verify structure
logger.info(f"🔍 DEBUG: Sample record keys: {list(sample_record.keys())}")
logger.info(f"🔍 DEBUG: Sample record type: {type(sample_record)}")

# Verify field types before mapping
for field_name in sample_record.keys():
    logger.info(f"🔍 DEBUG: Processing field_name: {field_name} (type: {type(field_name)})")
```

## Data Import Validation

### Pre-Import Validation:
```python
def validate_import_data(file_data):
    """Validate data structure before storage"""
    if not file_data:
        raise ValueError("No data to import")

    # Check for wrapper structures
    if isinstance(file_data, dict) and 'data' in file_data:
        actual_data = file_data['data']
        logger.warning("Unwrapping nested data structure")
    else:
        actual_data = file_data

    # Validate record structure
    if actual_data and len(actual_data) > 0:
        sample = actual_data[0]
        if not isinstance(sample, dict):
            raise ValueError(f"Invalid record type: {type(sample)}")

    return actual_data
```

## Master-Child Table Synchronization

### Problem: Discovery Flow Missing Despite Master Flow Existing
**Solution**: Check and create missing child records

```python
async def ensure_discovery_flow_exists(flow_id, master_flow):
    """Ensure discovery flow record exists for master flow"""
    discovery_flow = await get_discovery_flow(flow_id)

    if not discovery_flow and master_flow:
        logger.info("🔧 Master flow found but discovery flow missing, creating record")
        discovery_flow = DiscoveryFlow(
            flow_id=master_flow.flow_id,
            master_flow_id=master_flow.flow_id,
            client_account_id=master_flow.client_account_id,
            engagement_id=master_flow.engagement_id,
            status=master_flow.flow_status,
            # ... other fields
        )
        db.add(discovery_flow)
        await db.commit()

    return discovery_flow
```

## Async Context Data Access

### Problem: Lazy-loaded Relationships in Async Context
**Solution**: Explicitly query needed data

```python
# BAD: May fail in async context
total_records = data_import.raw_records.count()  # Lazy-loaded relationship

# GOOD: Explicit query
from sqlalchemy import select, func
count_query = select(func.count(RawImportRecord.id)).where(
    RawImportRecord.data_import_id == data_import.id
)
result = await db.execute(count_query)
total_records = result.scalar() or 0
```

## Data Cleansing Analysis Pattern

### Ensure Data Availability:
```python
async def get_data_for_cleansing(flow_id, db):
    """Get data with multiple fallback strategies"""

    # Strategy 1: Via discovery flow's data_import_id
    flow = await get_discovery_flow(flow_id)
    if flow and flow.data_import_id:
        data_import = await get_data_import(flow.data_import_id)

    # Strategy 2: Via master flow ID lookup
    if not data_import:
        master_flow = await get_master_flow(flow_id)
        if master_flow:
            data_import = await get_data_import_by_master_flow(master_flow.id)

    # Strategy 3: Via flow metadata
    if not data_import:
        metadata = await get_flow_metadata(flow_id)
        if metadata and 'import_id' in metadata:
            data_import = await get_data_import(metadata['import_id'])

    return data_import
```

## Common Data Integrity Issues

1. **Empty total_records field**: Always query actual count
2. **Mismatched IDs**: Use UUID type consistently
3. **Missing child records**: Implement creation on detection
4. **Stale cached counts**: Implement cache invalidation
5. **Wrapped data structures**: Unwrap before processing
6. **Type mismatches**: Validate and convert types explicitly

## Debug Logging Best Practices

```python
# Log data structures for debugging
logger.info(f"🔍 Data structure: type={type(data)}, keys={data.keys() if hasattr(data, 'keys') else 'N/A'}")
logger.info(f"📊 Counts: stored={stored_count}, actual={actual_count}, using={final_count}")
logger.info(f"🔧 Creating missing record: type={record_type}, id={record_id}")
```
