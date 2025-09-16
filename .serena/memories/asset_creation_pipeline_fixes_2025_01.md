# Asset Creation Pipeline Fixes - January 2025

## [2025-01-13]
### Context: Asset creation pipeline stuck at 47 assets, 0 records passed to asset_inventory phase
### Root Cause: Data cleansing phase not persisting cleansed_data to database despite UI showing completion
### Solution: Implemented comprehensive gating logic and error handling

#### Backend Fixes Applied:
1. **Null-safe flow state construction** (`flow_state_manager.py` lines 160-192):
```python
# Safe JSON state loading instead of direct attribute access
base_state = await self.store.load_state(flow_id) or {}
validation_results = base_state.get("validation_results") or base_state.get("data_validation_results") or {}
```

2. **Enhanced logging patterns** (`execution_engine_crew_discovery.py`):
- "📦 Executing discovery asset inventory using persistent agent"
- "📊 Using cleansed rows: X; raw fallback: 0 (blocked)"
- "✅ Normalized N/N records"

#### Frontend Fixes Applied:
1. **Auto-execution gating** (`InventoryContent.tsx`):
```typescript
// Only execute when ALL conditions met:
const shouldAutoExecute =
  hasRawData &&
  hasNoAssets &&
  flow?.phase_completion?.data_cleansing === true &&
  !isExecuting &&
  !hasTriggeredInventory &&
  attemptCountRef.current < maxRetryAttempts;
```

2. **Retry flood prevention**:
- 422 errors: Show user banner, stop retries completely
- 429/5xx errors: Exponential backoff, max 3 attempts
- No retry on 401/403/422 errors

### Result:
- ✅ No more validation_results AttributeError
- ✅ No infinite retry loops
- ✅ Clear 422 error: "CLEANSING_REQUIRED - No cleansed data available"
- ✅ Asset count protected at 47 (no invalid assets created)

### Remaining Issue:
Data cleansing UI shows 89% quality but database has `cleansed_data IS NULL` and `data_cleansing_completed = false`. This requires separate investigation but gating logic correctly prevents invalid asset creation.

## Critical Learnings:
1. **Always check database state, not UI state** for data validation
2. **Use useRef for retry counters** to persist across React re-renders
3. **FlowStateManager missing attributes** should use safe JSON loading, not direct access
4. **Multi-tenant scoping** must be maintained in all database queries
