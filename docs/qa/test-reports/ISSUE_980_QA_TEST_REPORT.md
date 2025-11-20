# Issue #980 QA Test Report: Assessment → Collection → Assessment Workflow

**Test Date**: November 9, 2025
**Test Session**: 19:45 - 19:58 UTC
**Tester**: qa-playwright-tester agent
**Test Objective**: Verify that explicit `db.flush()` fixes allow questionnaire responses to persist correctly and asset readiness updates after submission

---

## Executive Summary

### Test Result: ⚠️ PARTIAL PASS with Critical Finding

**What Works (Priority 0 Flush Fixes)**:
- ✅ Response records successfully persist to database (27 total responses confirmed)
- ✅ Backend flush operation working correctly ("Flushed 12 response records")
- ✅ Database commit successful ("COMMIT SUCCESSFUL for collection_flow_id")
- ✅ Readiness calculation executing and computing 40% completeness

**Critical Issue Discovered**:
- ❌ Assessment Flow UI continues to display 0% readiness despite backend calculating 40% completeness
- ❌ Asset `sixr_ready` field remains NULL in database after questionnaire submission
- ❌ Readiness summary API returning 0% when it should reflect 40% completeness

---

## Test Execution Details

### Test Environment
- **Frontend**: http://localhost:8081
- **Backend**: Docker container `migration_backend`
- **Database**: Docker container `migration_postgres`
- **Assessment Flow ID**: 8bdaa388-75a7-4059-81f6-d29af2037538
- **Collection Flow ID**: 32bcc9e4-cfe3-4dbe-b592-f59470163702
- **Asset ID**: 778f9a98-1ed9-4acd-8804-bdcec659ac00
- **Asset Name**: Analytics Engine

---

## Phase 1: Initial Assessment (0% Readiness)

**Objective**: Verify asset shows "Not Ready" with 0% readiness

**Actions**:
1. Navigated to Assessment Flow overview at `/assess/overview`
2. Selected assessment flow 8bdaa388-75a7-4059-81f6-d29af2037538
3. Verified "Analytics Engine" application group displays 0% readiness
4. Captured screenshot: `phase1_initial_assessment_0_percent.png`

**Results**: ✅ PASS
- UI correctly showed: "Analytics Engine 1 assets 0% ready (0/1 assets)"
- Readiness summary: "Not Ready Assets: 1 (100% of total)"
- Assessment Blockers warning displayed: "1 assets need data collection before assessment"

---

## Phase 2: Data Collection (Questionnaire Submission)

**Objective**: Navigate to Collection Flow and submit complete questionnaire

**Actions**:
1. Clicked "Collect Missing Data" button
2. System created Collection Flow linked to Assessment Flow
3. Filled ALL 12 questionnaire fields with test data:
   - Application Tier: 3-tier
   - Authentication Method: OAuth2
   - Business Criticality: High
   - Cloud Readiness: Ready
   - Compliance Framework: PCI-DSS
   - Data Sensitivity: Sensitive
   - Database Type: PostgreSQL
   - Deployment Frequency: Weekly
   - DR Requirements: 4 hour RTO
   - Monitoring Tools: Datadog
   - Peak Load: 10000 concurrent users
   - Supported Versions: 2.1.0
4. Progress tracked: 9/12 (75%) → 11/12 (92%) → 12/12 (100%)
5. Clicked "Submit Complete" button

**Screenshots**:
- `phase2_collection_questionnaire_loaded.png` - Initial questionnaire at 75%
- `phase2_before_final_submission.png` - Questionnaire at 92%
- `phase2_100_percent_ready_for_submission.png` - All 12/12 fields completed

**Results**: ✅ PASS
- All 12 questions answered successfully
- UI progress indicator updated correctly to 100%
- Submit button became enabled
- No frontend errors in browser console

---

## Phase 3: Database Persistence Verification

**Objective**: Verify flush fixes allow response records to persist

### Backend Log Analysis

**Flush Operation Log (19:54:41)**:
```
INFO - ✅ Flushed 12 response records to database: IDs=['a2bb2674-fb63-440d-bd3b-b2dca3f14815', '4bb766a5-6d02-45ae-8493-e691d44ecf28', '6786303b-0533-49a9-a2a0-71313d9f1dae', '70d10c34-a46d-4cb8-b706-a1471cceef31', 'cd9f86c1-2224-4546-908f-5de6ab95d085', 'fbb4a92b-4250-40de-a29a-6c72e7f9eda6', 'c0bab738-43e0-4751-9a8c-fc0b144ecdb8', 'b4698122-fe0a-462c-bcad-1b0a4871a0b6', '2d5d99df-2e9c-4af9-8c67-900492c4e783', '7a489410-9ece-4c54-bd75-e7313c488461', '6ce45941-2698-4e7f-9741-dcc0007b7a94', '9c8419df-a303-40c3-abd6-cb6dabfbb8cc'], collection_flow_id=5b31fbc1-ec55-4664-adf8-e5c26d0c0282
```

**Commit Operation Log (19:54:41)**:
```
INFO - ✅ COMMIT SUCCESSFUL for collection_flow_id=5b31fbc1-ec55-4664-adf8-e5c26d0c0282 - 12 responses persisted
```

**Readiness Update Log (19:54:41)**:
```
INFO - ✅ Updated readiness for asset 778f9a98-1ed9-4acd-8804-bdcec659ac00: ready=False, completeness=0.40
```

### Database Query Verification

**Query Executed**:
```sql
SELECT COUNT(*) as response_count
FROM migration.collection_questionnaire_responses
WHERE collection_flow_id = '5b31fbc1-ec55-4664-adf8-e5c26d0c0282';
```

**Result**: 27 rows (12 newly submitted + 15 from previous submissions)

**Results**: ✅ PASS
- All 12 response records successfully persisted to database
- Database commit completed without errors
- Readiness calculation executed: **completeness=0.40 (40%)**
- Priority 0 fixes (0.1, 0.2, 0.3) working correctly

---

## Phase 4: Return to Assessment Flow (UI Verification)

**Objective**: Verify readiness percentage updated from 0% to 40% in UI

**Actions**:
1. Navigated back to Assessment Flow overview
2. Verified "Analytics Engine" application group readiness
3. Checked readiness summary cards
4. Captured final screenshot: `phase4_final_assessment_verification.png`

**Results**: ❌ FAIL - Critical UI Issue Discovered

**Expected**:
- Analytics Engine shows 40% ready (based on backend calculation)
- "Avg Completeness" card shows 40%
- Asset moves from "Not Ready" (0%) to "In Progress" (40%)

**Actual**:
- Analytics Engine still shows **0% ready (0/1 assets)**
- "Avg Completeness" card shows **0%**
- "Not Ready Assets" still shows **1 (100% of total)**
- Readiness summary API returns: `"rate=0.00%"` despite backend computing 40%

### Backend Logs Show Contradiction

**Questionnaire Submission (19:54:41)**:
```
INFO - ✅ Updated readiness for asset 778f9a98-1ed9-4acd-8804-bdcec659ac00: ready=False, completeness=0.40
```

**Readiness Summary API Calls (19:55-19:57)**:
```
INFO - Readiness summary complete: flow_id=8bdaa388-75a7-4059-81f6-d29af2037538, total=1, ready=0, rate=0.00%
```

**Gap Analysis Executes Correctly**:
```
INFO - Starting gap analysis for asset 778f9a98-1ed9-4acd-8804-bdcec659ac00
INFO - Gap analysis complete for asset 778f9a98-1ed9-4acd-8804-bdcec659ac00
```

### Database State Verification

**Asset Table Query**:
```sql
SELECT id, name, sixr_ready, status
FROM migration.assets
WHERE id = '778f9a98-1ed9-4acd-8804-bdcec659ac00';
```

**Result**:
```
id: 778f9a98-1ed9-4acd-8804-bdcec659ac00
name: Analytics Engine
sixr_ready: NULL  ⚠️ PROBLEM: Should be a percentage or boolean
status: discovered
```

---

## Critical Finding Analysis

### Problem: Disconnect Between Calculation and Display

**Evidence**:
1. Backend log at 19:54:41 shows: `completeness=0.40` (40%)
2. Asset table shows: `sixr_ready = NULL`
3. Readiness summary API returns: `rate=0.00%`
4. UI displays: `0% ready`

**Root Cause Hypothesis**:

There are TWO separate code paths for readiness calculation:

1. **Questionnaire Submission Path** (Working ✅):
   - Location: `app/api/v1/endpoints/collection_crud_update_commands/questionnaire_helpers.py`
   - Executes gap analysis and logs `completeness=0.40`
   - **Problem**: Appears to compute but NOT persist to Asset table

2. **Assessment Flow Readiness Summary Path** (Not Finding Data ❌):
   - Location: `app/services/assessment/asset_readiness_service.py`
   - Executes gap analysis on every API call
   - Checks Asset table `sixr_ready` field
   - Finds `sixr_ready = NULL` → returns 0%

**The Missing Link**:
The questionnaire submission successfully calculates 40% completeness but does NOT update the `sixr_ready` field in the Asset table. When the Assessment Flow queries readiness, it finds NULL and defaults to 0%.

---

## Recommendations

### Priority 1 (Critical) - Fix Readiness Persistence

**Issue**: Readiness calculation executes correctly but doesn't persist to Asset table

**Files to Investigate**:
- `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection_crud_update_commands/questionnaire_helpers.py`
- `/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/services/assessment/asset_readiness_service.py`

**Expected Fix**:
After questionnaire submission and readiness calculation:
```python
# Current (logs but doesn't persist):
logger.info(f"✅ Updated readiness for asset {asset_id}: ready={ready}, completeness={completeness}")

# Should be:
asset.sixr_ready = f"{int(completeness * 100)}%"  # or boolean based on threshold
db.flush()  # Use explicit flush per Issue #980 fixes
db.commit()
```

**Acceptance Criteria**:
- After questionnaire submission, Asset table `sixr_ready` field should update to "40%" or appropriate value
- Assessment Flow UI should reflect updated readiness percentage
- Readiness summary API should return correct rate

### Priority 2 - Define Readiness Threshold

**Question**: When does an asset become "ready" vs "in progress"?

**Current Behavior**:
- Backend shows: `ready=False, completeness=0.40`
- Suggests threshold may be >50% or requires specific critical fields

**Recommendation**:
- Document the readiness threshold logic
- If 40% completeness is "In Progress", UI should show that status
- If 40% is insufficient for "ready", display as "In Progress" not "Not Ready"

### Priority 3 - Add Integration Test

**Test Case**: Full Assessment → Collection → Assessment Round Trip
```typescript
test('questionnaire submission updates assessment readiness', async () => {
  // 1. Create assessment flow with 0% readiness
  // 2. Navigate to collection flow and submit questionnaire
  // 3. Verify backend logs show completeness calculation
  // 4. Query Asset table - verify sixr_ready updated
  // 5. Return to assessment flow - verify UI shows updated percentage
  // 6. Verify readiness summary API returns correct rate
});
```

---

## Test Evidence (Screenshots)

All screenshots saved to: `/Users/chocka/CursorProjects/migrate-ui-orchestrator/.playwright-mcp/`

1. **phase1_initial_assessment_0_percent.png**
   - Shows initial Assessment Flow with 0% readiness
   - "Analytics Engine 1 assets 0% ready (0/1 assets)"
   - Assessment Blockers warning displayed

2. **phase2_collection_questionnaire_loaded.png**
   - Collection Flow questionnaire at 75% completion (9/12 fields)
   - Shows first 9 questions answered

3. **phase2_before_final_submission.png**
   - Questionnaire at 92% completion (11/12 fields)
   - Final question being answered

4. **phase2_100_percent_ready_for_submission.png**
   - All 12/12 fields completed (100%)
   - "Submit Complete" button enabled
   - Ready for submission

5. **phase4_final_assessment_verification.png**
   - Assessment Flow after questionnaire submission
   - Still showing 0% readiness despite backend calculating 40%
   - Demonstrates the UI display issue

---

## Summary of Success Criteria

| Criteria | Status | Evidence |
|----------|--------|----------|
| Flush Fix Working | ✅ PASS | Backend logs show "Flushed 12 response records" |
| Database Persistence | ✅ PASS | Query confirms 27 response records exist |
| Fix 0.1, 0.2, 0.3 Working | ✅ PASS | Commit successful, no flush errors |
| Readiness Updates | ⚠️ PARTIAL | Backend calculates 40%, but UI shows 0% |

**Overall Test Result**: ⚠️ PARTIAL PASS

**Issue #980 Fixes Are Working**: The explicit `db.flush()` operations successfully persist questionnaire responses to the database.

**Secondary Issue Discovered**: Readiness calculation executes correctly (40% completeness) but the result is not persisted to the Asset table's `sixr_ready` field, causing the Assessment Flow UI to display 0% instead of 40%.

---

## Conclusion

The Priority 0 flush fixes for Issue #980 are **WORKING CORRECTLY**. Questionnaire responses now persist to the database without errors. However, testing revealed a secondary integration issue where the calculated readiness percentage (40%) is not being written back to the Asset table, resulting in the UI displaying 0% instead of the correct value.

**Recommended Next Action**: Create a new issue to track the readiness persistence problem, as it is distinct from the flush operation fixes that were the focus of Issue #980.

---

**Test Artifacts Location**:
- Screenshots: `/.playwright-mcp/phase*.png`
- Backend logs: Docker container `migration_backend`
- Database queries: PostgreSQL container `migration_postgres`
