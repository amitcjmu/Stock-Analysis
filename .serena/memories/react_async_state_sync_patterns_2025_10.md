# React Async State Synchronization Patterns

**Date**: October 2025
**Context**: Collection flow debugging - gap analysis and questionnaire generation

## Insight 1: Race Condition Fix - Refetch After Async Operations

### Problem
User can interact with UI before React state updates from async operation:
```
Timeline:
12:31:56.856 - GET /gaps returns 0 gaps (component loads)
12:31:56.959 - POST /scan-gaps starts (103ms later)
12:31:57.117 - Scan completes, 23 gaps persisted to DB
[USER CLICKS "Accept Selected"] - Before setGaps() re-renders
Result: gaps array empty, lookup fails for all 23 gaps
```

### Solution
**Always refetch from database after async operation completes**, even if operation returns data:

```typescript
// DataGapDiscovery.tsx - handleScanGaps()
const response = await collectionFlowApi.scanGaps(flowId, selectedAssetIds);

// Set gaps from response
setGaps(response.gaps);
setScanSummary(response.summary);

// CRITICAL FIX: Refetch from database to ensure state synchronization
try {
  const dbGaps = await collectionFlowApi.getGaps(flowId);
  setGaps(dbGaps);
  console.log(`✅ Refetched ${dbGaps.length} gaps from database`);
} catch (refetchError) {
  console.error("Failed to refetch gaps:", refetchError);
  // Non-fatal - already have data from response
}
```

### Why This Works
- Scan response immediately sets gaps in state
- Refetch guarantees state matches database
- Prevents race condition window between operation and user interaction
- Non-fatal error handling (already have response data as fallback)

### When to Apply
- After any POST/PUT operation that creates/updates data user will immediately interact with
- When user can trigger actions within milliseconds of operation completing
- Multi-step flows where next step depends on previous step's database state

---

## Insight 2: Polling Interval Optimization

### Problem
Slow polling shows stale data when backend operation completes quickly:
```
Timeline:
12:54:23 - Backend creates pending questionnaire (0 questions)
12:54:24 - Frontend fetches (gets pending with 0 fields)
12:54:55 - Agent completes, generates 14 questions, status = "ready"
         - Frontend still shows stale "pending" questionnaire

Polling: 30 seconds
Generation: 31 seconds
Result: User sees stale data for 30+ seconds after completion
```

### Solution
**Match polling frequency to operation duration**:

```typescript
// useQuestionnairePolling.ts
// Before: const POLLING_INTERVAL_MS = 30000; // 30 seconds
const POLLING_INTERVAL_MS = 5000; // 5 seconds

// Rule of thumb: Poll at 1/6th of expected operation duration
// For 30-40s operations → 5s polling
// For 5-10s operations → 1s polling
```

### Formula
```
Polling Interval ≤ (Expected Operation Time / 6)
```

This ensures 5-6 poll attempts during operation, catching completion quickly.

### Trade-offs
- More API calls during operation (every 5s vs 30s)
- Only lasts until operation completes (~30s window)
- Much better UX - no stale data
- Worth it for user-facing real-time operations

---

## General Pattern: Async Operation Synchronization

```typescript
async function handleAsyncOperation() {
  setIsLoading(true);

  try {
    // 1. Perform async operation
    const response = await api.performOperation(params);

    // 2. Immediately update state from response
    setState(response.data);

    // 3. CRITICAL: Refetch from source of truth
    const freshData = await api.getData(id);
    setState(freshData);

    // 4. Show success feedback
    toast({ title: "Success" });
  } catch (error) {
    // Handle errors
  } finally {
    setIsLoading(false);
  }
}
```

**Key Principle**: Double-set pattern prevents race conditions while maintaining responsiveness.

---

## Debugging Timeline Analysis

**Pattern used to diagnose race condition**:
1. Extract timestamp sequence from backend logs
2. Identify async operation start/complete times
3. Compare with user action timestamps
4. Calculate time windows where race can occur

**Example**:
```
GET request:  12:31:56.856
POST starts:  12:31:56.959 (+103ms)
POST completes: 12:31:57.117 (+261ms from GET)
Race window: 261ms where user can interact with stale state
```

This pattern works for any async flow debugging.
