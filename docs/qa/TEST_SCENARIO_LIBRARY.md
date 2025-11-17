# Test Scenario Library for QA Playwright Agent

**Purpose**: Pre-defined test scenarios for systematic QA testing of Migration Orchestrator flows

**Target Audience**: qa-playwright-tester agent, QA engineers, CI/CD automation

**Last Updated**: 2025-11-15

---

## How to Use This Library

### For QA Playwright Agent

When invoking the qa-playwright-tester agent, reference specific scenarios:

```bash
Task tool with subagent_type: "qa-playwright-tester"
Prompt: "Execute scenario DISC-HAPPY-001 from TEST_SCENARIO_LIBRARY.md"
```

### Scenario Structure

Each scenario contains:
- **ID**: Unique identifier (e.g., DISC-HAPPY-001)
- **Flow**: Which flow this tests (Discovery/Collection/Assessment)
- **Type**: Happy path, error condition, or edge case
- **Prerequisites**: Required setup before test
- **Steps**: Exact actions to perform
- **Expected Results**: What should happen at each step
- **Completion Criteria**: How to know the test passed
- **Common Failures**: Known issues to watch for

---

## Discovery Flow Scenarios

### DISC-HAPPY-001: Complete Discovery Flow with CSV Import

**Flow**: Discovery Flow
**Type**: Happy Path
**Duration**: 3-5 minutes
**Prerequisites**:
- Docker environment running (localhost:8081)
- No existing discovery flows for test tenant
- Sample CSV file: `backend/tests/fixtures/sample_cmdb_data.csv`

**Test Steps**:

1. **Navigate to Discovery Flows**
   - Action: Click "Discovery Flows" in left navigation
   - Expected: `/discovery-flows` page loads
   - Expected: "Create Discovery Flow" button visible

2. **Create Flow**
   - Action: Click "Create Discovery Flow"
   - Expected: Modal opens with form
   - Action: Enter flow name "QA Test Discovery - [timestamp]"
   - Action: Select automation tier "Tier 2"
   - Action: Click "Create Flow"
   - Expected: Redirects to `/discovery-flows/{flow_id}`
   - Expected: Phase shows "data_import"

3. **Upload CSV**
   - Action: Select file `sample_cmdb_data.csv`
   - Action: Click "Upload"
   - Expected: Progress bar appears
   - Wait: Until progress reaches 100% (max 30 seconds)
   - Expected: Message "Import completed successfully"
   - Expected: Asset count displayed (e.g., "127 rows imported")
   - Expected: Phase changes to "field_mapping"

4. **Approve Field Mappings**
   - Expected: Mapping grid visible with source → target fields
   - Expected: Most fields auto-mapped (AI confidence > 0.7)
   - Action: Review mappings (should have no red badges)
   - Action: Click "Approve Mappings"
   - Wait: 2-10 seconds for confirmation
   - Expected: Message "Field mappings approved"
   - Expected: Phase changes to "data_cleansing"

5. **Wait for Data Cleansing** (Automated)
   - Expected: Progress indicator "Cleansing data..."
   - Wait: 10-60 seconds (DO NOT INTERACT)
   - Expected: Progress reaches 100%
   - Expected: Message "Data cleansing complete"
   - Expected: Statistics displayed (e.g., "X records cleansed")
   - Expected: Phase changes to "asset_creation"

6. **Wait for Asset Creation** (Automated)
   - Expected: Progress indicator "Creating assets..."
   - Wait: 15-90 seconds (DO NOT INTERACT)
   - Expected: Progress reaches 100%
   - Expected: Message "Assets created successfully"
   - Expected: Asset count (e.g., "127 assets created")
   - Expected: "View Assets" button appears
   - Expected: Phase changes to "completion"

7. **Verify Completion**
   - Expected: Status badge shows "Completed" (green)
   - Expected: "Start Collection Flow" button enabled
   - Action: Click "View Assets"
   - Expected: Redirects to `/assets` page
   - Expected: Assets visible in inventory grid
   - Expected: Asset count matches imported rows

**Completion Criteria**:
- ✅ Flow status = "Completed"
- ✅ All phases completed in sequence
- ✅ Assets created and visible in inventory
- ✅ No errors in browser console
- ✅ Total time < 5 minutes

**Common Failures**:
- ❌ CSV upload timeout (check file size, network)
- ❌ Field mapping stuck (AI service issue)
- ❌ Asset creation fails (database constraint violation)
- ❌ Phase doesn't auto-advance (state service issue)

---

### DISC-ERROR-001: Invalid CSV Upload

**Flow**: Discovery Flow
**Type**: Error Condition
**Duration**: 1 minute
**Prerequisites**:
- Discovery flow created and in "data_import" phase
- Invalid CSV file: `backend/tests/fixtures/invalid_csv_missing_headers.csv`

**Test Steps**:

1. **Upload Invalid CSV**
   - Action: Select file `invalid_csv_missing_headers.csv`
   - Action: Click "Upload"
   - Expected: Upload starts then fails
   - Expected: Error message appears
   - Expected: Message contains "Missing required headers" or similar
   - Expected: Phase remains "data_import"

2. **Verify Error Recovery**
   - Expected: Upload area still visible
   - Expected: Can retry with valid CSV
   - Expected: No partial data created in database

**Completion Criteria**:
- ✅ Error message displayed clearly
- ✅ Upload area remains interactive
- ✅ No data corruption

**Common Failures**:
- ❌ Generic error message (should be specific)
- ❌ Upload area disabled (should allow retry)
- ❌ Partial data persisted (should rollback)

---

### DISC-EDGE-001: Duplicate Discovery Flow Name

**Flow**: Discovery Flow
**Type**: Edge Case
**Duration**: 2 minutes
**Prerequisites**:
- One existing discovery flow named "Production Discovery"

**Test Steps**:

1. **Create Flow with Duplicate Name**
   - Action: Click "Create Discovery Flow"
   - Action: Enter flow name "Production Discovery" (exact match)
   - Action: Select automation tier "Tier 2"
   - Action: Click "Create Flow"
   - Expected: Either validation error OR flow created with suffix (e.g., "Production Discovery (2)")

2. **Verify Behavior**
   - Check: If error shown, modal remains open for correction
   - Check: If created, unique identifier added to name
   - Check: Both flows visible in list with distinct IDs

**Completion Criteria**:
- ✅ No database constraint violation
- ✅ User can distinguish between flows
- ✅ Clear error or auto-rename behavior

---

## Collection Flow Scenarios

### COLL-HAPPY-001: Complete Collection Flow with Questionnaire Responses

**Flow**: Collection Flow
**Type**: Happy Path
**Duration**: 5-10 minutes
**Prerequisites**:
- ✅ Discovery flow completed (DISC-HAPPY-001)
- ✅ At least 5 assets created with data gaps
- ✅ No existing collection flows for test tenant

**Test Steps**:

1. **Navigate to Collection Flows**
   - Action: Click "Collection Flows" in navigation
   - Expected: `/collection-flows` page loads
   - Expected: "Create Collection Flow" button visible

2. **Create Collection Flow**
   - Action: Click "Create Collection Flow"
   - Expected: Modal opens
   - Expected: Dropdown shows completed discovery flows
   - Action: Select discovery flow from DISC-HAPPY-001
   - Action: Enter flow name "QA Test Collection - [timestamp]"
   - Action: Click "Create Flow"
   - Expected: Redirects to `/collection-flows/{flow_id}`
   - Expected: Phase shows "asset_selection"

3. **Select Assets** (Phase: asset_selection)
   - Expected: Asset grid displays all discovered assets
   - Action: Check boxes for 3-5 assets with incomplete data
   - Expected: Selection count updates (e.g., "5 assets selected")
   - Action: Click "Continue"
   - Expected: Phase changes to "auto_enrichment"

4. **Wait for Auto-Enrichment** (Automated)
   - Expected: Progress "Enriching asset data..."
   - Wait: 30-120 seconds (DO NOT INTERACT)
   - Expected: Statistics update (e.g., "X fields enriched")
   - Expected: Phase changes to "gap_analysis"

5. **Wait for Gap Analysis** (Automated)
   - Expected: Progress "Analyzing data gaps..."
   - Wait: 20-60 seconds (DO NOT INTERACT)
   - Expected: Gap count displayed (e.g., "47 gaps identified")
   - Expected: Priority distribution shown (Critical/High/Medium/Low)
   - Expected: Phase changes to "questionnaire_generation"

6. **Wait for Questionnaire Generation** (Automated - AI)
   - Expected: Progress "Generating questionnaires..."
   - Wait: 10-60 seconds (AI takes time - THIS IS NORMAL)
   - Expected: Message "X questionnaires generated"
   - Expected: Questionnaires visible in UI
   - Expected: Phase changes to "manual_collection"

7. **Fill Questionnaires** (Phase: manual_collection - CRITICAL GATE)
   - Expected: Questionnaires grouped by asset/category
   - Expected: Progress shows "0/X questionnaires completed"
   - Action: Expand first questionnaire section
   - Action: Fill in 2-3 form fields with test data
   - Action: Click "Save" on section
   - Expected: Progress updates "1/X questionnaires completed"
   - Action: Repeat for at least 2 more sections
   - Expected: Progress shows "3/X questionnaires completed"
   - Action: Click "Submit Responses"
   - Wait: 5-10 seconds
   - Expected: Message "Responses submitted successfully"
   - Expected: Phase changes to "data_validation"

8. **Wait for Data Validation** (Automated - CRITICAL GATE)
   - Expected: Progress "Validating collected data..."
   - Wait: 5-30 seconds
   - Expected: Gap closure statistics displayed
   - Expected: Before/after gap count comparison
   - **Decision Point**:
     - If all critical gaps closed → Phase changes to "finalization"
     - If critical gaps remain → Status shows "paused", message "Critical gaps remaining"
   - **For Happy Path**: Assume critical gaps closed

9. **Wait for Finalization** (Automated - CRITICAL GATE)
   - Expected: Progress "Finalizing collection..."
   - Expected: Readiness checks displayed (all must pass):
     - ✅ Questionnaires generated → responses collected
     - ✅ Critical gaps (priority >= 80) closed
     - ✅ Assessment readiness criteria met
   - Wait: 5-15 seconds
   - Expected: All checks show green checkmarks
   - Expected: Status changes to "COMPLETED"
   - Expected: "Start Assessment Flow" button enabled

10. **Verify Completion**
    - Expected: Status badge "Completed" (green)
    - Expected: Summary shows flow statistics
    - Action: Click "Start Assessment Flow"
    - Expected: Redirects to assessment creation

**Completion Criteria**:
- ✅ Flow status = "COMPLETED"
- ✅ All phases completed in sequence
- ✅ Questionnaires generated and responses collected
- ✅ Critical gaps closed
- ✅ Assessment flow creation enabled
- ✅ No errors in browser console
- ✅ Total time < 10 minutes

**Common Failures**:
- ❌ Questionnaire generation timeout (AI service slow)
- ❌ Stuck in manual_collection without responses (BUG #1056-A working correctly - need responses!)
- ❌ Paused for critical gaps (BUG #1056-B working correctly - need more data!)
- ❌ Finalization blocked (Check all three gates passed)

---

### COLL-GATE-001: Manual Collection Gate (Bug #1056-A Verification)

**Flow**: Collection Flow
**Type**: Validation Gate Test
**Duration**: 3 minutes
**Prerequisites**:
- Collection flow in "manual_collection" phase
- Questionnaires generated
- ⚠️ DO NOT fill questionnaires

**Test Steps**:

1. **Attempt Completion Without Responses**
   - Expected: In "manual_collection" phase
   - Expected: Progress shows "0/X questionnaires completed"
   - Action: Look for "Complete Collection" or similar button
   - Expected: Button should be disabled OR not visible
   - Action: If button visible, click it
   - Expected: Status remains "awaiting_user_responses"
   - Expected: Error message "Cannot complete without questionnaire responses"

2. **Verify Gate Behavior**
   - Expected: Phase does NOT advance to data_validation
   - Expected: Flow status NOT "COMPLETED"
   - Expected: Questionnaires remain visible for completion

**Completion Criteria**:
- ✅ Flow correctly blocks completion without responses
- ✅ Clear error message displayed
- ✅ Phase remains manual_collection
- ✅ **This is NOT a bug** - Bug #1056-A fix working correctly

**If Test Fails**:
- ❌ Flow completes with 0 responses → REGRESSION BUG (Bug #1056-A broken)
- ❌ No error message → UX issue
- ❌ Phase advances without responses → STATE MACHINE BUG

---

### COLL-GATE-002: Data Validation Gate (Bug #1056-B Verification)

**Flow**: Collection Flow
**Type**: Validation Gate Test
**Duration**: 4 minutes
**Prerequisites**:
- Collection flow in "data_validation" phase
- Questionnaires filled with minimal responses (not enough to close critical gaps)

**Test Steps**:

1. **Trigger Validation with Critical Gaps Remaining**
   - Expected: In "data_validation" phase
   - Wait: 5-30 seconds for validation to complete
   - Expected: Status changes to "paused"
   - Expected: Message contains "critical gaps remaining" or similar
   - Expected: Gap statistics displayed:
     - Total gaps: X
     - Resolved gaps: Y
     - Critical gaps remaining: Z (where Z > 0)

2. **Verify Gate Behavior**
   - Expected: Phase does NOT advance to finalization
   - Expected: Flow status NOT "COMPLETED"
   - Expected: "User action required" message displayed
   - Expected: Suggested actions provided (e.g., "Review critical gap details")

3. **Check Critical Gap Details**
   - Expected: List of critical gaps displayed (up to 10)
   - Expected: Each gap shows:
     - Field name
     - Priority score
     - Impact on 6R
     - Gap ID

**Completion Criteria**:
- ✅ Flow correctly pauses for critical gaps
- ✅ Clear gap details provided
- ✅ User knows what data is missing
- ✅ **This is NOT a bug** - Bug #1056-B fix working correctly

**If Test Fails**:
- ❌ Flow completes with critical gaps → REGRESSION BUG (Bug #1056-B broken)
- ❌ No gap details → UX issue
- ❌ Phase advances to finalization → STATE MACHINE BUG

---

### COLL-GATE-003: Finalization Gate (Bug #1056-C Verification)

**Flow**: Collection Flow
**Type**: Validation Gate Test
**Duration**: 2 minutes
**Prerequisites**:
- Collection flow in "finalization" phase
- All critical gaps closed
- Questionnaire responses submitted

**Test Steps**:

1. **Verify Finalization Checks**
   - Expected: In "finalization" phase
   - Expected: Readiness checks displayed:
     1. ✅ Questionnaires generated → responses collected
     2. ✅ Critical gaps (priority >= 80) closed
     3. ✅ Assessment readiness criteria met
   - Wait: 5-15 seconds for checks to complete

2. **Verify Successful Completion**
   - Expected: All checks show green checkmarks
   - Expected: Status changes to "COMPLETED"
   - Expected: Message "Collection flow completed successfully"
   - Expected: "Start Assessment Flow" button enabled

**Completion Criteria**:
- ✅ All three gates validated
- ✅ Flow completes successfully
- ✅ Assessment flow creation enabled
- ✅ **This is NOT a bug** - Bug #1056-C fix working correctly

**If Test Fails**:
- ❌ Flow stuck with all checks passing → STATE MACHINE BUG
- ❌ Completes without all checks → REGRESSION BUG (Bug #1056-C broken)

---

## Assessment Flow Scenarios

### ASSESS-HAPPY-001: Complete Assessment Flow

**Flow**: Assessment Flow
**Type**: Happy Path
**Duration**: 6-12 minutes
**Prerequisites**:
- ✅ Collection flow completed (COLL-HAPPY-001)
- ✅ Assets with sufficient data quality
- ✅ No existing assessment flows for test applications

**Test Steps**:

1. **Navigate to Assessment Flows**
   - Action: Click "Assessment Flows" in navigation
   - Expected: `/assessment-flow` page loads
   - Expected: "Create Assessment Flow" button visible

2. **Create Assessment Flow**
   - Action: Click "Create Assessment Flow"
   - Expected: Modal opens
   - Expected: Dropdown shows completed collection flows
   - Action: Select collection flow from COLL-HAPPY-001
   - Expected: Application grid displays assessed applications
   - Action: Check boxes for 2-3 applications
   - Action: Enter flow name "QA Test Assessment - [timestamp]"
   - Action: Click "Create Assessment"
   - Expected: Redirects to `/assessment-flow/{flow_id}`
   - Expected: Phase shows "architecture_minimums"

3. **Set Architecture Standards** (Phase: architecture_minimums)
   - Expected: Form displays architecture requirements
   - Expected: Checkboxes for cloud platform (AWS/Azure/GCP)
   - Expected: Security standards checkboxes
   - Action: Select AWS as target platform
   - Action: Check 2-3 security requirements
   - Action: Click "Confirm Standards"
   - Expected: Phase changes to "tech_debt_analysis"

4. **Wait for Tech Debt Analysis** (Automated - AI)
   - Expected: Progress "Analyzing technical debt..."
   - Wait: 60-180 seconds (AI analysis takes time - THIS IS NORMAL)
   - Expected: Metrics displayed (debt score by component)
   - Expected: Phase changes to "component_sixr_strategies"

5. **Review 6R Recommendations** (Phase: component_sixr_strategies)
   - Expected: Grid shows components with recommended strategies
   - Expected: Each component has 6R badge (Rehost/Refactor/Retain/etc.)
   - Expected: AI reasoning displayed for each recommendation
   - Action: Review recommendations (no action required)
   - Wait: Auto-transitions after 10 seconds
   - Expected: Phase changes to "app_on_page_generation"

6. **Wait for Report Generation** (Automated)
   - Expected: Progress "Generating assessment reports..."
   - Wait: 30-90 seconds
   - Expected: Preview of "App on a Page" document visible
   - Expected: Phase changes to "finalization"

7. **Verify Completion**
   - Expected: Status badge "Completed" (green)
   - Expected: "View Assessments" button visible
   - Expected: "Export Results" button visible
   - Action: Click "View Assessments"
   - Expected: Assessment results displayed with 6R recommendations

**Completion Criteria**:
- ✅ Flow status = "Completed"
- ✅ All phases completed in sequence
- ✅ 6R recommendations generated for all components
- ✅ Reports generated successfully
- ✅ No errors in browser console
- ✅ Total time < 12 minutes

**Common Failures**:
- ❌ Tech debt analysis timeout (AI service slow)
- ❌ 6R recommendations missing (agent failure)
- ❌ Report generation fails (PDF service issue)

---

## Cross-Flow Scenarios

### FULL-HAPPY-001: Complete End-to-End User Journey

**Flow**: All Flows (Discovery → Collection → Assessment)
**Type**: Full Integration Test
**Duration**: 15-25 minutes
**Prerequisites**:
- Fresh Docker environment
- Sample CSV: `backend/tests/fixtures/sample_cmdb_data.csv`

**Test Steps**:

1. **Execute DISC-HAPPY-001** (Discovery Flow)
   - Follow all steps from DISC-HAPPY-001
   - Verify completion
   - Note: `flow_id` for next step

2. **Execute COLL-HAPPY-001** (Collection Flow)
   - Follow all steps from COLL-HAPPY-001
   - Use discovery flow from step 1
   - Verify completion
   - Note: `flow_id` for next step

3. **Execute ASSESS-HAPPY-001** (Assessment Flow)
   - Follow all steps from ASSESS-HAPPY-001
   - Use collection flow from step 2
   - Verify completion

4. **Verify End-to-End Data Flow**
   - Action: Navigate to Assets page
   - Expected: Assets show 6R strategy badges
   - Action: Navigate to Assessment results
   - Expected: All selected applications assessed
   - Action: Click "Export Results"
   - Expected: PDF/Excel download succeeds

**Completion Criteria**:
- ✅ All three flows completed
- ✅ Data flows correctly between flows
- ✅ 6R recommendations applied to assets
- ✅ Reports exportable
- ✅ No errors in any phase
- ✅ Total time < 25 minutes

---

## Error Recovery Scenarios

### ERROR-REC-001: Browser Refresh During Flow Execution

**Flow**: Any Flow
**Type**: Edge Case
**Duration**: 2 minutes
**Prerequisites**:
- Any flow in mid-execution (e.g., data_cleansing or gap_analysis)

**Test Steps**:

1. **Refresh Page During Automated Phase**
   - Expected: Flow in automated phase (e.g., data_cleansing)
   - Action: Press F5 or click browser refresh
   - Wait: 2-5 seconds for page reload
   - Expected: Page reloads to same flow detail page
   - Expected: Phase status preserved (still data_cleansing)
   - Expected: Progress indicator resumes from last state

2. **Verify State Persistence**
   - Expected: No data loss
   - Expected: Phase continues executing
   - Expected: Completion happens normally

**Completion Criteria**:
- ✅ Flow survives page refresh
- ✅ State preserved correctly
- ✅ Execution continues

**If Test Fails**:
- ❌ Flow resets to beginning → STATE PERSISTENCE BUG
- ❌ 404 error → ROUTING BUG

---

## Performance Scenarios

### PERF-001: Large Dataset Discovery Flow

**Flow**: Discovery Flow
**Type**: Performance Test
**Duration**: 10-15 minutes
**Prerequisites**:
- Large CSV file: 1000+ rows
- Performance monitoring enabled (browser dev tools)

**Test Steps**:

1. **Upload Large CSV**
   - Action: Follow DISC-HAPPY-001 steps
   - Use large CSV (1000+ assets)
   - Monitor: Network tab for upload progress
   - Monitor: Memory usage in browser

2. **Monitor Phase Timing**
   - Record: data_import duration (should be < 60s)
   - Record: field_mapping duration (should be < 30s)
   - Record: data_cleansing duration (should be < 120s)
   - Record: asset_creation duration (should be < 180s)

3. **Verify Performance Thresholds**
   - Check: Total time < 10 minutes for 1000 assets
   - Check: Browser memory < 500MB
   - Check: No 502/504 gateway timeouts

**Completion Criteria**:
- ✅ Flow completes within time limits
- ✅ No performance degradation
- ✅ Memory usage acceptable

---

## Test Data Reference

### Available Test Files

```
backend/tests/fixtures/
├── sample_cmdb_data.csv              # 127 rows, valid format
├── invalid_csv_missing_headers.csv   # Missing required headers
├── large_dataset_1000_assets.csv     # Performance testing
└── minimal_data_with_gaps.csv        # Collection flow testing
```

### Sample CSV Format

**Required Headers**: `asset_id`, `asset_name`, `asset_type`, `environment`, `owner`

**Optional Headers**: `ip_address`, `os_version`, `application_tier`, `dependencies`, `location`

---

## Test Execution Checklist

Before running any scenario:
- [ ] Docker environment running (`docker-compose up -d`)
- [ ] Frontend accessible at http://localhost:8081
- [ ] Backend accessible at http://localhost:8000
- [ ] Database accessible (port 5433)
- [ ] Browser console clear of errors
- [ ] Test data files prepared

After each scenario:
- [ ] Flow completed successfully OR expected error occurred
- [ ] No unexpected errors in browser console
- [ ] Database state verified (if applicable)
- [ ] Screenshots captured for documentation
- [ ] Test results logged

---

## Version History

- **v1.0** (2025-11-15): Initial test scenario library
  - Covers Discovery, Collection, and Assessment flows
  - Includes validation gate tests (Bug #1056-A/B/C)
  - Performance and error recovery scenarios

---

**Last Updated**: 2025-11-15
**Related Issues**: #1061 (QA agent architectural context)
**Related PRs**: #1058 (Collection Flow completion gates)
**Reference**: `/docs/qa/FLOW_ARCHITECTURE_GUIDE.md` for architectural details
