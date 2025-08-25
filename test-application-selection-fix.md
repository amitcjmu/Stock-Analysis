# Application Selection Persistence Fix - Test Plan

## What Was Fixed

The issue was that when users selected applications in ApplicationSelection and returned to AdaptiveForms, the flow data wasn't being refetched, so cached data showed "no applications selected".

## Changes Made

### 1. ApplicationSelection.tsx
- **Added cache invalidation**: After successful POST to `/collection/flows/${flowId}/applications`, we now invalidate the query cache
- **Specific fixes**:
  - Added `useQueryClient` import
  - After successful API response, invalidate `["collection-flow", flowId]` cache
  - Also invalidate `["collection-flows"]` cache for related queries
  - Added console logging for debugging

### 2. AdaptiveForms.tsx
- **Added multiple refetch mechanisms** as fallback:
  - Set `refetchOnWindowFocus: true` for the collection flow query
  - Set `staleTime: 30 * 1000` to reduce cache staleness
  - Added window focus event listener to refetch data
  - Added flowId change listener to refetch when returning from app selection

## Test Steps

### Prerequisites
- Start the application with `docker-compose up`
- Navigate to `/collection`
- Create a new collection flow (should redirect to application selection)

### Test Flow
1. **Go to ApplicationSelection**:
   - URL should be `/collection/select-applications?flowId={someId}`
   - Should see list of available applications
   - Select 5 applications
   - Click "Continue with 5 Applications"

2. **Verify POST Request**:
   - Check browser dev tools Network tab
   - Should see POST to `/api/v1/collection/flows/{flowId}/applications`
   - Should receive successful response with `success: true`

3. **Verify Cache Invalidation**:
   - Check browser console logs
   - Should see: `"✅ Cache invalidated for flow {flowId} after application selection"`

4. **Return to AdaptiveForms**:
   - Should navigate to `/collection/adaptive-forms?flowId={flowId}`
   - Should NOT show "no applications selected" message
   - Should show the adaptive form interface instead

5. **Test Window Focus (Backup)**:
   - If above fails, switch to another browser tab and back
   - Should trigger refetch and update to show selected applications

## Expected Results

- ✅ Applications persist after selection
- ✅ No "no applications selected" prompt in AdaptiveForms
- ✅ Smooth flow from ApplicationSelection → AdaptiveForms
- ✅ Cache properly invalidated and refreshed

## Debugging

If issues persist:
1. Check browser console for cache invalidation logs
2. Check Network tab for POST request to applications endpoint
3. Verify response contains selected_application_ids in collection_config
4. Check if window focus triggers refetch (backup mechanism)

## Files Modified
- `/src/pages/collection/ApplicationSelection.tsx`
- `/src/pages/collection/AdaptiveForms.tsx`
