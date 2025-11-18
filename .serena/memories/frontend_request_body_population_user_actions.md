# Frontend Request Body Population for User Actions

## Problem
User action buttons sending empty request bodies instead of relevant context:
```typescript
// ❌ WRONG - Empty body
body: JSON.stringify({})

// Backend receives: { apps_to_finalize: [] }
// Logs: "Marked 0 apps ready for planning"
```

## Root Cause
Frontend hook/component not extracting state data before API call.

## Solution Pattern
Extract relevant IDs/data from frontend state and populate request body.

## Implementation

### Step 1: Update API Method Signature
```typescript
// src/hooks/useAssessmentFlow/api.ts

// Before
async finalize(flowId: string): Promise<Response> {
  return apiCall(`/master-flows/${flowId}/assessment/finalize`, {
    method: "POST",
    body: JSON.stringify({}), // ❌ Empty
  });
}

// After
async finalize(flowId: string, apps_to_finalize: string[]): Promise<Response> {
  return apiCall(`/master-flows/${flowId}/assessment/finalize`, {
    method: "POST",
    body: JSON.stringify({ apps_to_finalize }), // ✅ Populated
  });
}
```

### Step 2: Extract State Data in Hook
```typescript
// src/hooks/useAssessmentFlow/useAssessmentFlow.ts

finalizeAssessment: async () => {
  if (!state.flowId) return;

  // ✅ Extract relevant data from state
  const appsToFinalize = Object.keys(state.sixrDecisions);

  // ✅ Validate before sending
  if (appsToFinalize.length === 0) {
    throw new Error("No applications have been assessed yet");
  }

  // ✅ Pass data to API
  await assessmentFlowAPI.finalize(state.flowId, appsToFinalize);

  // ✅ Refresh to pick up server changes
  await loadFlowState();
}
```

## Common Patterns

### Pattern 1: Extract from Object Keys
```typescript
// Get IDs from dictionary/map
const itemIds = Object.keys(state.itemsById);
```

### Pattern 2: Extract from Array
```typescript
// Get IDs from selected items
const selectedIds = state.selectedItems.map(item => item.id);
```

### Pattern 3: Extract from Filtered Data
```typescript
// Get IDs matching condition
const completedIds = state.items
  .filter(item => item.status === 'completed')
  .map(item => item.id);
```

## Anti-Patterns

❌ Sending empty objects:
```typescript
body: JSON.stringify({})
```

❌ Assuming backend will infer context:
```typescript
// Backend can't read your frontend state!
await api.finalize(flowId); // Missing data
```

❌ Not validating before sending:
```typescript
// Might send empty array
await api.finalize(flowId, extractedIds);
```

## Best Practices

✅ Extract state data in hook/component
✅ Validate data before API call
✅ Pass explicit parameters (don't rely on defaults)
✅ Refresh state after mutation to sync with backend
✅ Handle edge cases (no items selected, etc.)

## Related Files
- `src/hooks/useAssessmentFlow/useAssessmentFlow.ts:719-733`
- `src/hooks/useAssessmentFlow/api.ts:219-228`

## When to Use
- User confirmation buttons (finalize, approve, submit)
- Bulk actions (delete selected, export selected)
- Form submissions with selected items
- Any POST/PUT/DELETE with user-selected context
