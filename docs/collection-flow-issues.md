# Collection Flow Issues - E2E Testing Results

## Critical Issues

### 1. RBAC Not Enforced for Collection Flows (CRITICAL)
**Description**: Role-Based Access Control is not being enforced for collection flow operations. All users can create, view, and delete flows regardless of their role.

**Current Behavior**: 
- Demo user (role: user) can create and delete collection flows
- Manager user (role: engagement_manager) has same permissions as regular user
- No role-based restrictions are applied
- Both users correctly see the same collection flow for their shared context

**Expected Behavior**: 
- **User role**: View only access to collection flows
- **Analyst role**: Can create and edit collection flows
- **Manager role**: Can create, edit, and delete collection flows
- **Admin role**: Full access across all contexts

**API Endpoints Affected**: 
- `/api/v1/collection/flows` (POST) - Should check if user is analyst or above
- `/api/v1/collection/flows/{id}` (DELETE) - Should check if user is manager or above
- `/api/v1/collection/flows/{id}` (PUT) - Should check if user is analyst or above

**Fix Required**: 
- Backend: Implement RBAC checks in collection flow endpoints
- Frontend: Conditionally show/hide buttons based on user role
- Add proper error messages for unauthorized actions

### 2. Cache Invalidation After Flow Deletion (HIGH)
**Description**: After successfully deleting a collection flow, the UI continues to show the deleted flow due to React Query cache not being properly invalidated.

**Current Behavior**:
- Flow deletion API returns success
- Toast notification shows "Flow Deleted"
- UI still displays the deleted flow
- Manual refresh button uses cached data

**Expected Behavior**:
- After successful deletion, cache should be invalidated
- UI should immediately reflect the deletion
- No stale data should be shown

**Fix Required**:
- Ensure `queryClient.invalidateQueries({ queryKey: ['collection-flows', 'incomplete'] })` is called after deletion
- May need to add more specific cache keys

### 3. UI Bug - Pages Require Double Refresh on Direct Navigation (MEDIUM)
**Description**: When navigating directly to collection pages via URL, the page requires two refreshes to load properly.

**Current Behavior**:
- First load shows blank or loading state
- Requires two page refreshes to display content

**Expected Behavior**:
- Page should load correctly on first navigation

**Fix Required**:
- Investigate React component lifecycle issues
- Check for race conditions in data fetching

## Completed Fixes

### 1. ✅ Collection Flow Deletion - Missing Database Column
**Issue**: Collection flow deletion was failing with 500 error due to missing `updated_at` column in `collection_data_gaps` table.
**Fix Applied**: Created migration `011_add_updated_at_to_collection_data_gaps.py`
**Status**: RESOLVED

### 2. ✅ UI Context Management - Wrong Flow ID in Headers
**Issue**: UI was sending discovery flow ID (e9cad44b-ba3d-4474-b5bc-0ed1ade52ed3) in X-Flow-ID header even on collection pages.
**Fix Applied**: Updated AdaptiveForms.tsx and Index.tsx to use `setCurrentFlow` with collection-specific flow context
**Status**: RESOLVED

### 3. ✅ 401 Authentication Error Handling
**Issue**: Collection pages were not redirecting to login on 401 errors, causing repeated failed requests.
**Fix Applied**: Activated `useGlobalErrorHandler` hook in App.tsx that was imported but never called
**Status**: RESOLVED

## Additional Observations

### 1. No Application Data Available
- The application dropdown in Adaptive Forms shows no options
- This prevents testing the full flow creation process
- Need to ensure test data includes applications

### 2. Flow Status Confusion
- Multiple flow IDs appearing in logs but UI shows different ones
- Need clearer flow ID tracking and display

### 3. Context Headers Not Consistent
- Some API calls show "No auth token found in localStorage" warnings
- Context headers are sometimes skipped even when needed

## Recommendations

1. **Immediate Actions**:
   - Fix user context filtering in collection flow queries (CRITICAL)
   - Fix cache invalidation after deletion
   - Add integration tests for multi-user scenarios

2. **Medium Term**:
   - Improve error messages and user feedback
   - Add better logging for flow lifecycle events
   - Create comprehensive E2E test suite

3. **Long Term**:
   - Consider flow ownership model
   - Add flow sharing capabilities if needed
   - Improve flow state management architecture