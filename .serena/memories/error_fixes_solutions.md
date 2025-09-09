# Error Fixes and Solutions

## Field Mapping Execution Failures (Sep 2025)
**Error**: "All field mapping execution strategies failed" - prevents field mappings from being generated and displayed in UI
**Root Cause**: Multiple system failures in field mapping pipeline
**Solution**: 7-step systematic fix pattern:

1. **Store Detected Columns in State**:
```python
# In data_import_validation/executor.py
file_analysis = results.get("file_analysis", {})
if file_analysis and "field_analysis" in file_analysis:
    detected_columns = list(file_analysis["field_analysis"].keys())
    if detected_columns:
        self.state.metadata["detected_columns"] = detected_columns
```

2. **Fix Status Recognition**: Change "completed" to "success" in mapping_strategies.py
3. **Add Data Import ID Fallback**: Use flow_id as data_import_id for direct raw data flows
4. **Fix Phase Transitions**: Ensure proper progression from data_import to field_mapping
5. **Add Data Extraction Fallbacks**: Handle missing data structures gracefully
6. **Correct Database Model Fields**: Fix field name mismatches
7. **Ensure Database Persistence**: Create DataImport records for direct flows

**Files Affected**: 7 files across field mapping pipeline
**Validation**: Check UI displays field counts, database records created

## Async-to-Sync Bridge Errors (Jan 2025)
**Error**: `RuntimeError: no running event loop` or `RuntimeError: no AnyIO portal found`
**Cause**: Using `anyio.from_thread.run()` without a blocking portal
**Solution**: Always use blocking portal pattern:
```python
# WRONG - Will fail without portal
from anyio import from_thread
return from_thread.run(async_function, *args)

# CORRECT - Creates portal for reliable bridging
from anyio import from_thread
with from_thread.start_blocking_portal() as portal:
    return portal.call(async_function, *args, **kwargs)
```
**Files Fixed**: base_tool.py, status_tool.py, asset_creation_tool.py

## Cross-Tenant Security Violations (Sep 2025)
**Error**: Database queries without tenant scoping allowing cross-tenant data access
**Solution**: Always use `and_()` clauses with both client_account_id and engagement_id:
```python
from sqlalchemy import select, and_

# WRONG - No tenant scoping
query = select(DataImport).where(DataImport.id == data_import_id)

# CORRECT - Proper tenant scoping
query = select(DataImport).where(
    and_(
        DataImport.id == data_import_id,
        DataImport.client_account_id == client_account_id,
        DataImport.engagement_id == engagement_id,
    )
)
```

## Migration Robustness Issues (Sep 2025)
**Error**: Alembic migrations fail on mixed schemas with different PK columns ('id' vs 'flow_id')
**Solution**: Dynamic column detection pattern:
```python
def _detect_flow_id_column(bind, table_schema: str, table_name: str) -> str:
    col_check = bind.execute(
        text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            AND column_name IN ('flow_id', 'id')
        """),
        {"schema": table_schema, "table": table_name},
    ).fetchall()

    found = [r[0] for r in col_check]
    return "flow_id" if "flow_id" in found else "id"
```

## CI Cache Configuration Errors (Sep 2025)
**Error**: `Cache folder path is retrieved for pip but doesn't exist on disk`
**Cause**: GitHub Actions cache configured for pip without pip install commands
**Solution**: Remove cache configuration when not installing dependencies:
```yaml
# WRONG - Cache without installs
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'

# CORRECT - No cache for syntax-only checks
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
```

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

## Collection Flow Critical Failures (Sep 2025)

### Empty Database Tables
**Error**: `collection_flow_applications` and `collection_gap_analysis` tables empty
**Root Cause**: Application selection only updates JSON config, not normalized tables
**Solution**: Use deduplication service with Asset names:
```python
# Load Asset objects to get names
assets = await db.execute(
    select(Application).where(Application.application_id.in_(application_ids))
)
for asset in assets.scalars():
    await dedup_service.deduplicate_application(
        application_name=asset.name,  # Use name, not ID
        collection_flow_id=collection_flow.id
    )
```

### Orphaned Flows on MFO Failure
**Error**: Collection flow created but orphaned when Master Flow Orchestrator fails
**Solution**: Single transaction with proper rollback:
```python
async with db.begin():  # Let context manager handle commit/rollback
    collection_flow = CollectionFlow(...)
    db.add(collection_flow)
    await db.flush()  # Get ID without commit

    master_flow_id = await orchestrator.create_flow(...)
    if not master_flow_id:
        raise ValueError("MFO creation failed")  # Auto-rollback

    collection_flow.master_flow_id = master_flow_id
    # Context manager commits on success
```

### Non-Persistent Agent Pattern
**Error**: Agents created per-execution violating ADR-015
**Solution**: Use TenantScopedAgentPool for persistent agents:
```python
# WRONG - Per-execution
class GapAnalysisAgent(BaseDiscoveryCrew):
    pass

# CORRECT - Persistent singleton per tenant
agent = await TenantScopedAgentPool.get_collection_gap_agent(
    context.client_account_id,
    context.engagement_id
)
```

### WebSocket Architecture Violation
**Error**: WebSocket code incompatible with Vercel/Railway deployment
**Solution**: Complete removal, replace with HTTP polling:
```typescript
// Remove ALL WebSocket references
// Use HTTP polling instead
const pollInterval = setInterval(async () => {
    const state = await fetch(`/api/v1/collection/flows/${flowId}/state`);
}, 2000);
```

### Gap Analysis Model Mismatch
**Error**: Serializer doesn't match CollectionGapAnalysis structure
**Clarification**: Model has summary fields, not per-gap fields
**Solution**: New serializer matching actual structure:
```python
class CollectionGapAnalysisSummaryResponse(BaseModel):
    completeness_percentage: float
    critical_gaps: List[Dict[str, Any]]  # JSONB list
    recommended_actions: Dict[str, Any]
    attributes_analyzed: int
```
