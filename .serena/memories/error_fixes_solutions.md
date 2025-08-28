# Error Fixes and Solutions

## Circular Import Errors
**Error**: `ImportError: cannot import name '_client_account_id' from partially initialized module`
**Solution**: Break circular dependency by defining functions in the module that owns the context variables, then re-export elsewhere

## Pre-commit File Length Violations
**Error**: `FILE LENGTH VIOLATIONS: exceeds 400 line limit`
**Solution**: Modularize into focused modules:
1. Extract utilities to `*_utils.py`
2. Extract converters to `*_converters.py`
3. Extract fallback logic to `*_fallback.py`
4. Keep main file as compatibility wrapper

## Test Data Contamination
**Error**: Frontend crashes when Device_* fields detected
**Solution**: Server-controlled filtering with environment variable:
```typescript
const ENABLE_TEST_DATA_FILTERING = process.env.NEXT_PUBLIC_ENABLE_TEST_DATA_FILTERING !== 'false';
const shouldFilterTestData = (data: any) => {
  if (data?.metadata?.filter_test_fields === true) return true;
  if (STRICT_TEST_DATA_BLOCK === true) return true;
  return ENABLE_TEST_DATA_FILTERING;
};
```

## Database Transaction Missing Commits
**Error**: Records added but not persisted to database
**Solution**: Add explicit flush/commit after operations:
```python
for record in records:
    self.db.add(raw_record)
    records_stored += 1
if records_stored:
    await self.db.flush()  # Ensure persistence
```

## CrewAI Availability False Positive
**Error**: CREWAI_FLOW_AVAILABLE always True despite missing imports
**Solution**: Test with concrete imports:
```python
try:
    from crewai import Flow
    from crewai.llm import LLM
    _ = Flow.__name__  # Test accessibility
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    CREWAI_FLOW_AVAILABLE = False
```

## UUID/Parameter Mismatch Errors
**Error**: `TypeError: got an unexpected keyword argument` or 404 errors on valid IDs
**Common Causes**:
1. Frontend sends `flow_id` but backend expects database `id`
2. String UUID compared directly with UUID type
3. Parameter name mismatches between frontend/backend

**Solutions**:
```python
# Always convert to UUID type before comparison
from uuid import UUID
result = await db.execute(
    select(CollectionFlow).where(
        CollectionFlow.flow_id == UUID(flow_id),  # Convert string to UUID
        CollectionFlow.engagement_id == context.engagement_id,
    )
)

# Use correct field for queries
# Wrong: CollectionFlow.id == flow_id (id is database PK, flow_id is business key)
# Right: CollectionFlow.flow_id == UUID(flow_id)

# Validate UUID format
try:
    uuid_value = UUID(string_id)
except (ValueError, TypeError):
    raise HTTPException(status_code=400, detail="Invalid UUID format")
```

## Enum Value Comparison Errors
**Error**: SQLAlchemy queries fail with enum comparisons
**Solution**: Always use `.value` property when comparing enums with database strings:
```python
# Wrong
CollectionFlow.status.notin_([
    CollectionFlowStatus.COMPLETED,
    CollectionFlowStatus.FAILED,
])

# Right
CollectionFlow.status.notin_([
    CollectionFlowStatus.COMPLETED.value,
    CollectionFlowStatus.FAILED.value,
])
```

## Flow Continuation AttributeError (Aug 2025)
**Error**: `'CrewAIFlowStateExtensions' object has no attribute 'current_phase'`
**Solution**: Use fallback pattern for missing attributes:
```python
current_phase = "questionnaires"  # Default
if hasattr(master_flow, 'get_current_phase'):
    try:
        phase = master_flow.get_current_phase()
        if phase:
            current_phase = phase
    except Exception:
        pass  # Use default
```

## Frontend Response Extraction TypeError (Aug 2025)
**Error**: `Cannot read properties of undefined (reading 'user_guidance')`
**Cause**: Response already unwrapped, not in `{data: ...}` format
**Solution**:
```typescript
// Wrong: const data = response.data as FlowContinuationResponse
// Right: const data = response as FlowContinuationResponse
```

## Parameter Name Mismatch - Flow Type Filtering (Aug 2025)
**Error**: Upload blocking when ANY flow active, not just Discovery flows
**Cause**: Frontend sends `flow_type`, backend expects `flowType`
**Solution**: Add alias to accept snake_case:
```python
flow_type: Optional[str] = Query(
    None,
    alias="flow_type",  # Accept snake_case from frontend
    description="Filter by flow type..."
)
```
