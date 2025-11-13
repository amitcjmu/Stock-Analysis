# Deterministic IDs for JSONB Field Persistence

## Problem: Quality Issue Resolutions Not Persisting

**Symptom**: Users resolve data quality issues, but after page refresh, issue count doesn't decrease. Issues reappear as unresolved.

**Root Cause**:
1. Backend generates new random UUID for each quality issue on every analysis
2. Frontend stores resolutions by issue_id in flow.crewai_state_data JSONB field
3. On next analysis, issues get NEW UUIDs → resolutions don't match → appear unresolved

```python
# BAD: Random UUID each time
quality_issue = DataQualityIssue(
    id=str(uuid.uuid4()),  # ❌ New ID every time
    field_name="customer_name",
    issue_type="missing_values"
)
```

## Solution: Deterministic UUID5 Based on Content

```python
def _generate_deterministic_issue_id(field_name: str, issue_type: str) -> str:
    """
    Generate deterministic ID so same issue always gets same ID.
    This allows stored resolutions to persist across analysis runs.
    """
    import hashlib
    from uuid import UUID, uuid5

    # Create deterministic key from issue attributes
    issue_key = f"{field_name}:{issue_type}"

    # Use standard DNS namespace UUID
    namespace = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

    # Generate deterministic UUID5
    return str(uuid5(namespace, issue_key))

# GOOD: Same input = same UUID
quality_issue = DataQualityIssue(
    id=_generate_deterministic_issue_id(field_name, issue_type),
    field_name="customer_name",
    issue_type="missing_values"
)
```

**Result**:
- `customer_name:missing_values` → Always `abc123...` UUID
- Resolution stored in DB with issue_id `abc123...`
- Next analysis regenerates `abc123...` → resolution still applies

## SQLAlchemy JSONB Change Detection

**Problem**: Modifying nested JSONB doesn't trigger SQLAlchemy update.

```python
# BAD: SQLAlchemy doesn't detect change
flow.crewai_state_data["resolutions"]["issue_123"] = {...}
await db.commit()  # ❌ No UPDATE statement sent to PostgreSQL
```

**Solution**: Explicitly mark field as modified.

```python
from sqlalchemy.orm.attributes import flag_modified

# Update JSONB field
flow.crewai_state_data["resolutions"]["issue_123"] = resolution_data

# REQUIRED: Tell SQLAlchemy the field changed
flag_modified(flow, "crewai_state_data")

# Ensure object is tracked
db.add(flow)

# Now commit will include UPDATE
await db.commit()
await db.refresh(flow)
```

## Database Session Force Refresh

**Problem**: Reading stale cached data after another process/transaction updated it.

```python
# BAD: May return cached data
flow = await db.query(Flow).filter_by(flow_id=flow_id).first()
resolutions = flow.crewai_state_data.get("resolutions", {})
# ❌ Might be stale if another request just updated it
```

**Solution**: Force fresh read from database.

```python
# Expire all cached objects
db.expire_all()

# Now query gets fresh data from database
flow = await db.query(Flow).filter_by(flow_id=flow_id).first()
resolutions = flow.crewai_state_data.get("resolutions", {})
# ✅ Guaranteed to be latest from PostgreSQL
```

## Usage Pattern

When storing user actions in JSONB fields:

```python
async def store_resolution(issue_id: str, resolution: dict):
    # 1. Force fresh read
    db.expire_all()
    flow = await get_flow(flow_id)

    # 2. Update JSONB
    if "resolutions" not in flow.crewai_state_data:
        flow.crewai_state_data["resolutions"] = {}
    flow.crewai_state_data["resolutions"][issue_id] = resolution

    # 3. Mark as modified (REQUIRED)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(flow, "crewai_state_data")

    # 4. Track and commit
    db.add(flow)
    await db.commit()
    await db.refresh(flow)

async def load_resolutions(flow_id: str) -> dict:
    # 1. Force fresh read
    db.expire_all()
    flow = await get_flow(flow_id)

    # 2. Extract from JSONB
    return flow.crewai_state_data.get("resolutions", {})
```

## When to Use Deterministic IDs

✅ **Use when**:
- ID represents content-based identity (same content = same ID)
- Need to track state across multiple regenerations
- Deduplication based on content
- User actions target specific content

❌ **Don't use when**:
- Each occurrence should be unique (e.g., log entries)
- ID represents temporal instance (e.g., API request)
- Need true uniqueness guarantees

## Files Referenced
- `backend/app/api/v1/endpoints/data_cleansing/analysis.py:21-33` - Deterministic ID generation
- `backend/app/api/v1/endpoints/data_cleansing/operations.py:354-359` - JSONB modification
- `backend/app/api/v1/endpoints/data_cleansing/analysis.py:227` - Force refresh
