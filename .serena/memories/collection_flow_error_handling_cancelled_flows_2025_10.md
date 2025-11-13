# Collection Flow Error Handling - Cancelled/Failed Flows (October 2025)

## Problem: Cancelled Flows Showing Partial Data

**Issue #799**: Users accessing cancelled/failed/completed collection flows via URL received confusing partial UI:
- Backend returned 200 OK for cancelled flows
- Frontend displayed gaps but no "Continue to Questionnaire" button
- No clear error message indicating flow was unavailable
- User confusion: "Why are gaps showing but I can't continue?"

**Root Cause**: `get_collection_flow()` endpoint lacked status filtering, returning ANY flow regardless of state.

## Solution: Treat Cancelled Flows Like Deleted Flows

### Backend Fix (collection_crud_queries/status.py)

```python
# ❌ BEFORE - Returns any flow including cancelled
result = await db.execute(
    select(CollectionFlow).where(
        (CollectionFlow.flow_id == flow_uuid) | (CollectionFlow.id == flow_uuid),
        CollectionFlow.engagement_id == context.engagement_id,
    )
)

# ✅ AFTER - Excludes inactive flows
result = await db.execute(
    select(CollectionFlow).where(
        (CollectionFlow.flow_id == flow_uuid) | (CollectionFlow.id == flow_uuid),
        CollectionFlow.engagement_id == context.engagement_id,
        CollectionFlow.status.notin_([
            CollectionFlowStatus.CANCELLED.value,
            CollectionFlowStatus.FAILED.value,
            CollectionFlowStatus.COMPLETED.value,
        ]),
    )
)
```

### Key Insights

1. **Status filtering must match get_collection_status()** - The status endpoint already filtered correctly, but get_collection_flow() didn't
2. **Cancelled = Deleted from user perspective** - Both should return 404, not partial data
3. **Database has gaps even for cancelled flows** - Gap detection ran before cancellation, so data exists but shouldn't be accessible

### Dual UUID Column Support

The same fix also handles flows with TWO UUID columns:
- `id` (primary key): Internal database ID
- `flow_id` (business identifier): User-facing flow ID used in URLs

```python
# Check BOTH columns with OR clause
(CollectionFlow.flow_id == flow_uuid) | (CollectionFlow.id == flow_uuid)
```

## Frontend Error Handling (GapAnalysis.tsx)

Enhanced error display with specific HTTP status codes:

```typescript
if (err instanceof Error) {
  const msg = err.message.toLowerCase();
  if (msg.includes('404') || msg.includes('not found')) {
    errorMessage = `Collection flow not found (ID: ${flowId}). The flow may have been deleted or the URL is invalid.`;
  } else if (msg.includes('403') || msg.includes('unauthorized')) {
    errorMessage = 'You do not have permission to access this collection flow.';
  } else if (msg.includes('500') || msg.includes('server error')) {
    errorMessage = 'Server error while loading flow. Please try again or contact support.';
  }
}
```

## API Client Error Detection (flows.ts)

```typescript
async getFlow(flowId: string): Promise<CollectionFlowResponse> {
  try {
    return await apiCall(`${this.baseUrl}/flows/${flowId}`, { method: "GET" });
  } catch (error: unknown) {
    if (error && typeof error === 'object') {
      const apiError = error as ApiError;

      if (apiError.status === 404) {
        throw new Error(`404: Collection flow not found (ID: ${flowId})`);
      }
      if (apiError.status === 403) {
        throw new Error('403: You do not have permission to access this collection flow');
      }
      if (apiError.status === 500) {
        throw new Error('500: Server error while loading flow');
      }
    }
    throw error;
  }
}
```

## Testing Approach

1. **Find cancelled flow**: `SELECT flow_id FROM collection_flows WHERE status = 'cancelled' LIMIT 1;`
2. **Navigate to gap analysis**: `http://localhost:8081/collection/gap-analysis/{flow_id}`
3. **Expect**: 404 error page with clear message
4. **NOT**: Partial UI with gaps displayed

## Related Pattern: get_collection_status()

Reference implementation that already filtered correctly:

```python
.where(
    CollectionFlow.client_account_id == context.client_account_id,
    CollectionFlow.engagement_id == context.engagement_id,
    CollectionFlow.status.notin_([
        CollectionFlowStatus.COMPLETED.value,
        CollectionFlowStatus.CANCELLED.value,
        CollectionFlowStatus.FAILED.value,
    ])
)
```

**Lesson**: When implementing similar endpoints, check existing patterns for proper filtering logic.

## GitHub Issue

Issue #799: "Poor Error Handling for Non-Existent Collection Flow IDs"
- Initial report focused on truly non-existent flows
- Investigation revealed broader issue with cancelled flows
- Final fix addresses both scenarios with unified approach

## Commits

1. `7c1cb7ff9` - Initial UUID lookup and error handling
2. `eff671eef` - Added status filter + config.py modularization
