# Collection to Assessment Flow E2E Testing

## Overview

This directory contains comprehensive E2E testing for the collection-to-assessment flow, validating all Week 1 Foundation fixes.

## Files Created

### 1. Navigation Sequence Documentation
**Location:** `/docs/testing/E2E_COLLECTION_TO_ASSESSMENT_FLOW.md`

**Purpose:** Comprehensive step-by-step guide for testing the collection-to-assessment flow

**Contents:**
- Detailed navigation instructions for each phase
- Expected states and validation points
- Selector patterns and interaction methods
- Data validation checkpoints
- Error scenarios and debugging tips
- Performance benchmarks
- Success criteria

**Use Cases:**
- Reference for manual testing
- Blueprint for creating new E2E tests
- Onboarding documentation for QA engineers
- Debugging guide for failed tests

### 2. Playwright E2E Test Suite
**Location:** `/tests/e2e/collection-to-assessment-flow.spec.ts`

**Purpose:** Automated E2E tests for the complete collection-to-assessment workflow

**Test Cases:**
1. **Main Flow Test:** Complete end-to-end flow from login to agent execution
2. **UUID Resolution Test:** Focused test for Fix #5 (asset name display)
3. **Asset Preservation Test:** Validates asset_id tracking through submission

**Validates:**
- ✅ Fix #1: asyncio.wrap_future() in assessment executors
- ✅ Fix #2: Flexible tool parameters for data validation
- ✅ Fix #3: Transaction rollback for missing servers table
- ✅ Fix #4: Phase results transaction recovery
- ✅ Fix #5: UUID-to-name resolution in questionnaires

## Running the Tests

### Prerequisites

1. **Docker Containers Running:**
   ```bash
   cd config/docker
   docker-compose up -d
   ```

2. **Services Available:**
   - Frontend: http://localhost:8081
   - Backend: http://localhost:8000
   - Database: PostgreSQL on :5433

3. **Demo Data Seeded:**
   - Demo user: demo@example.com / demo123
   - At least one application in canonical_applications table

### Run All Collection-Assessment Tests

```bash
# From project root
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts
```

### Run Specific Test

```bash
# Run only the main flow test
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --grep "should complete collection flow"

# Run only the UUID resolution test
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --grep "should display asset name"

# Run only the asset preservation test
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --grep "should preserve asset_id"
```

### Run with UI Mode (Recommended for Debugging)

```bash
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --ui
```

### Run in Headed Mode (See Browser)

```bash
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --headed
```

### Run with Debugging

```bash
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --debug
```

## Test Flow Breakdown

### Phase 1: Login (Lines 82-97)
- Navigate to login page
- Fill credentials
- Verify successful authentication

### Phase 2: Navigate to Collection (Lines 102-112)
- Click Collection menu
- Click Adaptive Forms
- Verify page loaded

### Phase 3: Asset Selection (Lines 117-145)
- Wait for asset selector
- Select first valid asset (not "app-new")
- Store asset name for validation

### Phase 4: Gap Analysis (Lines 150-181)
- Click Generate Questionnaires
- Wait for gap analysis
- Accept all gaps
- Continue to questionnaire

### Phase 5: UUID Resolution Validation (Lines 186-205)
**CRITICAL TEST - Validates Fix #5**
- Verify asset name displayed (NOT "app-new")
- Verify no UUID in page content
- Confirm UUID-to-name resolution working

### Phase 6: Form Filling (Lines 210-242)
- Fill 7 form fields with test data
- Wait for data confidence update
- Track number of fields filled

### Phase 7: Form Submission (Lines 247-254)
- Submit form
- Wait for processing
- Verify success

### Phase 8: Assessment Transition (Lines 259-284)
- Verify URL changed to /assessment/
- Extract assessment flow ID
- Confirm automatic transition

### Phase 9: Agent Execution (Lines 289-301)
- Click "Continue to Application Review"
- Verify "Check Status" button appears
- Click "Check Status"

### Phase 10: Phase Progression (Lines 306-324)
**CRITICAL TEST - Validates Fixes #1, #3, #4**
- Verify status shows "IN PROGRESS"
- Verify phase progression occurred
- Confirm agents processing

### Final Validation (Lines 329-353)
- Check for asyncio errors (should be none)
- Check for 401/422 errors (should be none)
- Verify all fixes working

## Expected Test Output

### Successful Run
```
✅ Login successful
📍 PHASE 1: Navigating to Adaptive Forms
✅ Adaptive Forms page loaded
📍 PHASE 2: Selecting Asset
✅ Selected asset: Analytics Engine
📍 PHASE 3: Generating Questionnaires
✅ Gap analysis generated
✅ Selected all gaps via checkbox
✅ Navigated to questionnaire
📍 PHASE 4: Verifying UUID-to-Name Resolution (Fix #5)
✅ FIX #5 VALIDATED: Asset name "Analytics Engine" displayed correctly
   - Shows asset name: true
   - No "app-new": true
   - No UUID display: true
📍 PHASE 5: Filling Form Fields
✅ Filled 7 form fields
📍 PHASE 6: Submitting Form
✅ Form submitted successfully
📍 PHASE 7: Verifying Assessment Flow Transition
✅ Transitioned to assessment flow
✅ Assessment Flow ID: 1f0ff53c-333e-40db-b3d7-10101c86b56c
📍 PHASE 8: Triggering Assessment Agents
✅ Clicked "Continue to Application Review"
📍 PHASE 9: Checking Agent Status
✅ "Check Status" button appeared
✅ Clicked "Check Status"
📍 PHASE 10: Verifying Phase Progression
✅ FIX #1, #3, #4 VALIDATED: Phase progression working
   Status: IN PROGRESS (33%)

✅ ALL VALIDATIONS PASSED:
   - Fix #5: UUID-to-name resolution working
   - Fix #1: No asyncio.wrap_future() errors
   - Fix #3, #4: No transaction rollback errors
   - Collection → Assessment transition successful
   - Agent processing initiated successfully
```

### Failed Run (Example)
```
❌ FAIL: tests/e2e/collection-to-assessment-flow.spec.ts
   Expected: "Analytics Engine"
   Received: "app-new"

   This indicates Fix #5 is not working - UUID-to-name resolution broken.
```

## Debugging Failed Tests

### Issue: Asset Shows "app-new"
**Problem:** Fix #5 not working - UUID resolution broken

**Check:**
1. Browser console for applications array
2. useAdaptiveFormFlow.ts - verify `applications` parameter passed
3. convertQuestionnairesToFormData() - verify applications received
4. extractAssetName() logic in formDataTransformation.ts

**Fix:**
```typescript
// In useAdaptiveFormFlow.ts
const { applications } = useApplications(); // Must be called
const adaptiveFormData = convertQuestionnairesToFormData(
  questionnaires[0],
  applicationId,
  applications // Must be passed
);
```

### Issue: Assessment Agents Fail
**Problem:** Fix #1 not working - asyncio errors

**Check:**
1. Backend logs for asyncio errors
2. Assessment executor files for asyncio.wrap_future()
3. LiteLLM configuration

**Fix:**
```python
# In risk_executor.py (and other executors)
import asyncio
future = task.execute_async(context=context_str)
result = await asyncio.wrap_future(future)  # Required!
```

### Issue: Transaction Rollback Errors
**Problem:** Fixes #3, #4 not working

**Check:**
1. Backend logs for "transaction aborted"
2. readiness_queries.py for rollback handling
3. phase_results.py for retry logic

**Fix:**
```python
# Add rollback handling
try:
    result = await self.db.execute(stmt)
except Exception as e:
    await self.db.rollback()
    # Retry with clean transaction
    result = await self.db.execute(stmt)
```

## Test Data Requirements

### Database State
- client_account_id: 1
- engagement_id: 1
- At least 1 application in canonical_applications
- Demo user credentials active

### Expected Application
- Name: "Analytics Engine" (or similar)
- UUID: Valid v4 format
- Status: Active
- Linked to client_account_id=1, engagement_id=1

## Performance Expectations

- **Total test duration:** < 60 seconds
- **Login:** < 2 seconds
- **Asset selection:** < 1 second
- **Gap analysis:** < 5 seconds
- **Form submission:** < 5 seconds
- **Assessment transition:** < 3 seconds
- **Agent initialization:** < 3 seconds

## CI/CD Integration

### Add to GitHub Actions

```yaml
- name: Run Collection-Assessment E2E Tests
  run: |
    cd /path/to/project
    npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts
```

### Add to Pre-Deployment Checks

```bash
# In deployment script
echo "Running E2E validation..."
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --reporter=json > test-results.json

if [ $? -ne 0 ]; then
  echo "❌ E2E tests failed - blocking deployment"
  exit 1
fi
```

## Extending the Tests

### Add New Test Case

```typescript
test('should handle new scenario', async ({ page }) => {
  // Use existing beforeEach for login

  // Your test logic here
});
```

### Add Validation Point

```typescript
// In main flow test
// After Phase X, add:
console.log('\n📍 NEW PHASE: Your Phase Name');

// Your validation logic
expect(someCondition).toBeTruthy();

console.log('✅ New validation passed');
```

## Maintenance

### Update Test Data
Edit `FORM_DATA` constant (lines 28-36) if form structure changes

### Update Selectors
If UI changes, update selectors in:
- Asset selection (lines 119-145)
- Gap analysis (lines 167-181)
- Form filling (lines 212-242)
- Status checking (lines 309-324)

### Update Timeouts
If network conditions change, edit `TEST_CONFIG.timeouts` (lines 15-22)

## Related Documentation

- **Navigation Guide:** `/docs/testing/E2E_COLLECTION_TO_ASSESSMENT_FLOW.md`
- **Week 1 Fixes:** `/docs/fixes/WEEK_1_FOUNDATION_FIXES.md`
- **API Patterns:** `/docs/guidelines/API_REQUEST_PATTERNS.md`
- **Playwright Docs:** https://playwright.dev/

## Support

For issues or questions:
1. Check navigation guide documentation
2. Review debugging tips in this README
3. Check browser console logs
4. Review backend logs: `docker logs migration_backend -f`

## Success Criteria

All tests PASS when:
- [ ] All 3 test cases pass without errors
- [ ] Asset names display correctly (no UUIDs)
- [ ] Forms submit with correct asset_id
- [ ] Assessment flow auto-initializes
- [ ] Agents create without asyncio errors
- [ ] Phase progression works correctly
- [ ] No 401/422 errors in console
- [ ] Total runtime < 60 seconds
