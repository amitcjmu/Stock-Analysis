# React Query Error Propagation Best Practice

**Problem**: Try-catch blocks that return empty arrays hide API errors from React Query, preventing proper error state handling.

**Incorrect Pattern** ❌
```typescript
const { data: flows = [], isLoading } = useQuery<AssessmentFlow[]>({
  queryKey: ['assessment-flows'],
  queryFn: async () => {
    try {
      const response = await apiCall('/master-flows/list', {
        method: 'GET',
        headers
      });
      return Array.isArray(response) ? response : [];
    } catch (error) {
      console.error('Failed to fetch:', error);
      return [];  // ❌ Hides error from React Query!
    }
  }
});
```

**Problems**:
- React Query never knows an error occurred
- `isError` state never triggers
- Error boundaries don't catch failures
- UI shows empty state instead of error message

**Correct Pattern** ✅
```typescript
const { data: flows = [], isLoading, isError, error } = useQuery<AssessmentFlow[]>({
  queryKey: ['assessment-flows'],
  queryFn: async () => {
    const response = await apiCall('/master-flows/list', {
      method: 'GET',
      headers
    });
    return Array.isArray(response) ? response : [];
    // ✅ Let errors bubble up to React Query
  }
});

// React Query automatically:
// - Sets isError = true on failure
// - Provides error object
// - Triggers error boundaries
// - Handles retries per config
```

**UI Error Handling**:
```typescript
if (isError) {
  return <ErrorMessage message={error?.message} />;
}

if (isLoading) {
  return <Spinner />;
}

return <FlowList flows={flows} />;
```

## When to Use

- All React Query `queryFn` implementations
- Any async data fetching with TanStack Query
- API calls that need proper error states

## Why This Matters

- Proper error boundaries and retry logic
- User sees meaningful error messages
- Debugging: Errors visible in React DevTools
- Monitoring: Error tracking tools capture failures

**Fixed in**: PR #587 (Qodo Bot suggestion #3)
**File**: `src/pages/assessment/AssessmentFlowOverview.tsx:127-138`
