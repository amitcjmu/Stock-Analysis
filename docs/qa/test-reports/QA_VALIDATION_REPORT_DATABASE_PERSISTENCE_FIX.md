# QA Validation Report: Database Persistence Fix Testing

## Test Date: 2025-11-18 00:31 UTC
## Tester: QA Playwright Agent
## Feature: Assessment Flow - Refresh Readiness Database Persistence

---

## Executive Summary

**TEST STATUS: ❌ BLOCKED - Unable to Complete Testing**

The database persistence fix could not be tested due to a **critical blocker**: The "New Assessment" modal fails to load canonical applications due to a 404 error on the `/api/v1/canonical-applications` endpoint. This prevents access to the "Refresh Readiness" functionality that was intended to be tested.

---

## Test Environment

- **Frontend URL**: http://localhost:8081
- **Backend URL**: http://localhost:8000
- **Database**: PostgreSQL 16 (migration_postgres container)
- **Client Account**: 11111111-1111-1111-1111-111111111111 (Democorp)
- **Engagement**: Current context shows "Cloud Migration 2024"

---

## Critical Blocker Identified

### Issue #1: 404 Error on Canonical Applications Endpoint

**Severity**: 🔴 **CRITICAL** - Blocks all testing

**Description**:
When opening the "New Assessment" modal, the frontend attempts to fetch canonical applications but receives a 404 error, preventing the modal from loading any data.

**Evidence**:

1. **Frontend Error (Browser Console)**:
   ```
   ❌ API Error [i8v89j] 404 (113.10ms): API Error 404: Not Found
   Failed to fetch canonical applications: ApiError: API Error 404: Not Found
   ```

2. **Backend Logs**:
   ```
   2025-11-18 00:31:40,446 - WARNING - ⚠️ GET http://backend:8000/api/v1/canonical-applications?search=&page=1&page_size=100&include_unmapped_assets=true | Status: 404 | Time: 0.083s
   ```

3. **Modal State**:
   - Tab counts show: Ready (0), Needs Mapping (0), Needs Collection (0)
   - Error message: "Failed to load applications. Please try again."
   - "Refresh Readiness" button is visible but operates on empty data

**Root Cause Analysis**:

- **Frontend calls**: `/api/v1/canonical-applications` (line 109 in `StartAssessmentModal.tsx`)
- **Service expects**: `/api/v1/collection/canonical-applications` (line 21 in `canonical-applications.ts`)
- **Backend endpoint**: Appears to not exist or is not properly registered in the router

**File References**:
- `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/components/assessment/StartAssessmentModal.tsx:109`
- `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/services/api/canonical-applications.ts:21`

**Impact**:
- Users cannot see any applications in the "New Assessment" modal
- Cannot test the "Refresh Readiness" functionality
- Cannot verify database persistence fix
- Assessment flow creation is blocked

---

## Test Scenario (Attempted)

### Planned Test Steps

1. ✅ Navigate to http://localhost:8081 and log in
2. ✅ Open "New Assessment" modal
3. ❌ Note INITIAL tab counts ← **BLOCKED HERE**
4. ❌ Click "Refresh Readiness" button
5. ❌ Verify toast shows "X assets persisted" where X > 0
6. ❌ Note POST-REFRESH tab counts
7. ❌ Close modal and reopen
8. ❌ Verify tab counts persist

### Actual Results

1. ✅ Successfully navigated to assessment overview page
2. ✅ Clicked "New Assessment" button - modal opened
3. ❌ **Modal failed to load applications**:
   - Error: "Failed to load applications. Please try again."
   - Tab counts: Ready (0), Needs Mapping (0), Needs Collection (0)
   - Toast notification: "No Applications - No applications to refresh readiness for."
4. ❌ Cannot proceed with testing

---

## Database Investigation

### Assets in Database

**Total Assets**: 376 assets in the database
- Applications: 222
- Servers: 83
- Other: 33
- Database: 19
- Network: 15

**Data Distribution**:
```sql
client_account_id: 11111111-1111-1111-1111-111111111111
engagement_id: 22222222-2222-2222-2222-222222222222
asset_count: 50 applications
```

**Issue**: There's a **context mismatch**:
- Database has applications under engagement: `22222222-2222-2222-2222-222222222222`
- UI may be using a different engagement ID (needs verification)
- This could explain why no applications are being found

---

## Screenshots Captured

1. **01-initial-modal-state.png**: Shows "New Assessment" modal with:
   - 404 error in console
   - Empty tab counts (0/0/0)
   - Error message: "Failed to load applications"
   - "No ready applications found" message

---

## Recommendations

### Immediate Actions Required

1. **Fix the 404 Endpoint Error** (Priority: CRITICAL)
   - **Option A**: Update `StartAssessmentModal.tsx` to use the correct endpoint `/api/v1/collection/canonical-applications`
   - **Option B**: Create missing endpoint `/api/v1/canonical-applications` in backend router
   - **Option C**: Verify router registry includes canonical applications endpoint

2. **Verify Engagement Context** (Priority: HIGH)
   - Check localStorage for engagement_id being used by UI
   - Verify it matches the database engagement_id (`22222222-2222-2222-2222-222222222222`)
   - Fix context switching if needed

3. **Re-test Database Persistence After Fixes**
   - Once applications load successfully, repeat the test scenario
   - Verify toast message shows `updated_count > 0`
   - Verify backend logs show "💾 Persisted readiness updates"
   - Verify tab counts persist after modal close/reopen

### Code Fixes Needed

**File**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/components/assessment/StartAssessmentModal.tsx`

**Lines to Update**:
```typescript
// Line 109 - Change from:
`/api/v1/canonical-applications?search=${encodeURIComponent(searchQuery)}...`

// To:
`/api/v1/collection/canonical-applications?search=${encodeURIComponent(searchQuery)}...`

// Line 200 - Change from:
'/api/v1/canonical-applications/map-asset'

// To:
'/api/v1/collection/canonical-applications/map-asset'

// Line 222 - Change from:
`/api/v1/canonical-applications?search=${encodeURIComponent(searchQuery)}...`

// To:
`/api/v1/collection/canonical-applications?search=${encodeURIComponent(searchQuery)}...`

// Line 299 - Change from:
`/api/v1/canonical-applications/${app.id}/readiness-gaps`

// To:
`/api/v1/collection/canonical-applications/${app.id}/readiness-gaps`
```

**Alternatively**, use the service layer:
```typescript
import { canonicalApplicationsApi } from '@/services/api/canonical-applications';

// Replace direct apiCall with:
const response = await canonicalApplicationsApi.getAll({
  search: searchQuery,
  page: 1,
  page_size: 100,
  include_unmapped_assets: true
});
```

---

## Backend Verification Needed

The backend needs to verify that the following endpoints exist and are properly registered:

1. `GET /api/v1/collection/canonical-applications` - List applications
2. `POST /api/v1/collection/canonical-applications/map-asset` - Map asset to application
3. `GET /api/v1/collection/canonical-applications/{id}/readiness-gaps` - Get readiness gaps
4. `GET /api/v1/collection/canonical-applications/{id}/refresh-readiness` - Refresh readiness (for the fix being tested)

**Verification Command**:
```bash
docker exec migration_backend python -c "from app.api.router_registry import app; routes = [r.path for r in app.routes]; print('\n'.join([r for r in routes if 'canonical' in r]))"
```

---

## Unable to Verify

The following test objectives from the original request **could not be verified** due to the blocker:

❌ Toast shows `updated_count > 0`
❌ Backend logs show "🔍 DEBUG readiness_gaps" with `update_database=True (type=bool)`
❌ Backend logs show "💾 Persisted readiness updates for X assets"
❌ Tab counts persist after modal reopen
❌ Applications don't flip-flop between tabs
❌ `update_database=true` query parameter is correctly passed

---

## Next Steps

1. **Developer**: Fix the 404 endpoint issue
2. **Developer**: Verify engagement context is correctly set
3. **QA**: Re-run this test after fixes are deployed
4. **QA**: Verify the database persistence fix works as intended

---

## Test Artifacts

- **Screenshot**: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/.playwright-mcp/01-initial-modal-state.png`
- **Browser Console Logs**: 404 error captured
- **Backend Logs**: 404 warning logged at 2025-11-18 00:31:40,446

---

## Conclusion

The database persistence fix **cannot be validated** until the critical 404 endpoint issue is resolved. Once applications can be successfully loaded in the "New Assessment" modal, the test can be re-run to verify:

1. Readiness data is properly fetched
2. "Refresh Readiness" updates the database (not just in-memory)
3. Updated counts are reflected in the toast message
4. Persistence is maintained after modal close/reopen

**Recommendation**: Prioritize fixing the endpoint issue before proceeding with further QA testing of the assessment flow.
