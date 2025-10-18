# Qodo Bot Race Condition and Memory Leak Fix Patterns

## Insight 1: Python Async Lock Race Conditions
**Problem**: Manual dictionary check-then-create pattern for locks is not thread-safe
**Root Cause**: Between `if flow_id not in _locks` and `_locks[flow_id] = Lock()`, another thread can execute
**Solution**: Use `defaultdict(asyncio.Lock)` for atomic lock creation
**Code**:
```python
from collections import defaultdict
import asyncio

# ❌ WRONG - Race condition:
_enrichment_locks: Dict[str, asyncio.Lock] = {}

async def process(flow_id: str):
    if flow_id not in _enrichment_locks:
        _enrichment_locks[flow_id] = asyncio.Lock()  # ⚠️ Race condition here
    lock = _enrichment_locks[flow_id]

# ✅ CORRECT - Thread-safe with defaultdict:
_enrichment_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

async def process(flow_id: str):
    lock = _enrichment_locks[flow_id]  # Atomic creation if not exists
    async with lock:
        # ... protected code
```
**Files**: `backend/app/services/enrichment/auto_enrichment_pipeline.py:329`
**Usage**: Any Python async code using per-resource locks

## Insight 2: PostgreSQL Atomic JSONB Updates
**Problem**: Read-modify-write pattern creates race condition in concurrent updates
**Root Cause**: Between SELECT and UPDATE, another transaction can modify the JSONB field
**Solution**: Use PostgreSQL's `||` operator for atomic JSONB merge at database level
**Code**:
```python
# ❌ WRONG - Race condition with read-modify-write:
result = await db.execute(
    select(AssessmentFlow.user_inputs).where(AssessmentFlow.id == flow_id)
)
current_inputs = result.scalar() or {}
current_inputs[phase] = user_input  # Python-level merge
await db.execute(
    update(AssessmentFlow)
    .where(AssessmentFlow.id == flow_id)
    .values(user_inputs=current_inputs)  # ⚠️ Can lose concurrent updates
)

# ✅ CORRECT - Atomic merge with PostgreSQL || operator:
await db.execute(
    update(AssessmentFlow)
    .where(AssessmentFlow.id == flow_id)
    .values(
        # Atomic JSONB merge at database level
        user_inputs=AssessmentFlow.user_inputs.op("||")({phase: user_input})
    )
)
```
**Files**: `backend/app/repositories/assessment_flow_repository/commands/flow_commands/updates.py:67`
**Usage**: All PostgreSQL JSONB field updates with concurrent access

## Insight 3: React useEffect Timeout Cleanup
**Problem**: setTimeout in mutation callbacks causes memory leaks on component unmount
**Root Cause**: Closure prevents garbage collection if component unmounts before timeout fires
**Solution**: Move setTimeout to useEffect with cleanup function
**Code**:
```typescript
// ❌ WRONG - Memory leak risk:
const mutation = useMutation({
  onSuccess: (data) => {
    if (data.errors.length === 0) {
      setTimeout(() => {
        onComplete();  // ⚠️ State update on unmounted component
      }, 2000);
    }
  }
});

// ✅ CORRECT - useEffect with cleanup:
useEffect(() => {
  if (mutation.isSuccess && mutation.data?.errors.length === 0) {
    const timeoutId = setTimeout(() => {
      onComplete();
    }, 2000);

    // Cleanup function prevents memory leak
    return () => {
      clearTimeout(timeoutId);
    };
  }
}, [mutation.isSuccess, mutation.data?.errors.length, onComplete]);
```
**Files**: `src/components/assessment/BulkAssetMappingDialog.tsx:128-139`
**Usage**: Any React component with delayed actions after async operations

## Insight 4: React Polling Timeout Cleanup
**Problem**: setInterval with setTimeout doesn't clear timeout on success
**Root Cause**: Timeout fires even after interval is cleared, causing memory leak
**Solution**: Store timeout ID and clear it when polling completes successfully
**Code**:
```typescript
// ❌ WRONG - Timeout not cleared on success:
const pollInterval = setInterval(async () => {
  const status = await fetchStatus();
  if (status.complete) {
    clearInterval(pollInterval);
    // ⚠️ Timeout still fires, causing memory leak
  }
}, 3000);

setTimeout(() => {
  clearInterval(pollInterval);
}, 300000);

// ✅ CORRECT - Clear both interval and timeout:
const pollInterval = setInterval(async () => {
  const status = await fetchStatus();
  if (status.complete) {
    clearInterval(pollInterval);
    clearTimeout(timeoutId);  // Prevent memory leak
    setIsProcessing(false);
  }
}, 3000);

const timeoutId = setTimeout(() => {
  clearInterval(pollInterval);
  setIsProcessing(false);
}, 300000);
```
**Files**: `src/pages/assessment/[flowId]/architecture.tsx:190`
**Usage**: React polling with timeout fallback

## Insight 5: N+1 Query Optimization
**Problem**: Loop executing one SELECT query per iteration
**Root Cause**: Querying database inside loop instead of batch fetching
**Solution**: Pre-fetch all records with `WHERE id IN (...)` into dictionary
**Code**:
```python
# ❌ WRONG - N+1 queries (100 assets = 100 queries):
async with db.begin():
    for mapping in request.mappings:
        # Query executed EVERY iteration
        result = await db.execute(
            select(Asset).where(
                Asset.id == mapping.asset_id,
                Asset.client_account_id == client_account_id
            )
        )
        asset = result.scalar_one_or_none()

# ✅ CORRECT - Single query with IN clause:
# Pre-fetch all assets (100 assets = 1 query)
asset_ids = [UUID(m.asset_id) for m in request.mappings]
result = await db.execute(
    select(Asset).where(
        Asset.id.in_(asset_ids),
        Asset.client_account_id == client_account_id
    )
)
valid_assets = {str(asset.id): asset for asset in result.scalars().all()}

async with db.begin():
    for mapping in request.mappings:
        asset = valid_assets.get(mapping.asset_id)  # Dictionary lookup
```
**Files**: `backend/app/api/v1/canonical_applications/bulk_mapping.py:200-208`
**Usage**: Any loop querying database by ID

## Insight 6: Rate Limiter Logic Optimization
**Problem**: `while` loop causes redundant re-checks after wait completes
**Root Cause**: After sleeping for calculated wait time and cleaning timestamps, condition is guaranteed to be false
**Solution**: Use `if` instead of `while` since single wait is sufficient
**Code**:
```python
# ❌ INEFFICIENT - while loop with redundant checks:
while len(self.timestamps) >= self.max_operations:
    oldest_ts = self.timestamps[0]
    wait_time = self.time_window_seconds - (current_time - oldest_ts)
    if wait_time > 0:
        await asyncio.sleep(wait_time + 0.1)
    current_time = time.time()
    self.timestamps = [ts for ts in self.timestamps
                       if current_time - ts < self.time_window_seconds]
    # ⚠️ Loops back to check condition again (unnecessary)

# ✅ EFFICIENT - if statement (single wait):
if len(self.timestamps) >= self.max_operations:
    oldest_ts = self.timestamps[0]
    wait_time = self.time_window_seconds - (current_time - oldest_ts)
    if wait_time > 0:
        await asyncio.sleep(wait_time + 0.1)
        # Refresh and clean after wait
        current_time = time.time()
        self.timestamps = [ts for ts in self.timestamps
                           if current_time - ts < self.time_window_seconds]
# Proceed - condition guaranteed to be false after wait
```
**Files**: `backend/app/services/enrichment/batch_processor.py:95`
**Usage**: Token bucket rate limiters with calculated wait times

## Cross-Cutting Patterns

**Atomic Operations Principle**: Prefer database/language-level atomic operations over application-level read-modify-write patterns.

**React Cleanup Principle**: ALWAYS provide cleanup functions in useEffect when creating async operations (timeouts, intervals, subscriptions).

**Query Optimization Principle**: When querying in loops, check if batch fetching is possible (especially with SQLAlchemy's `.in_()`).

**Async Lock Principle**: Use language-provided atomic data structures (`defaultdict`, `ConcurrentHashMap`) instead of manual synchronization.
