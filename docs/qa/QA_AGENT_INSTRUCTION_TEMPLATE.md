# QA Agent Instruction Template

**Purpose**: Standardized instruction format for invoking qa-playwright-tester agent with proper architectural context

**Target Audience**: Claude Code operators, automation scripts, CI/CD pipelines

**Last Updated**: 2025-11-15

---

## Quick Start

### Basic Invocation Pattern

```
Task tool with subagent_type: "qa-playwright-tester"

Prompt: "
IMPORTANT: Before starting, read these foundational documents:
1. /docs/qa/FLOW_ARCHITECTURE_GUIDE.md - Understand flow sequences
2. /docs/qa/TEST_SCENARIO_LIBRARY.md - Use pre-defined scenarios

Execute test scenario: [SCENARIO_ID]

Context:
- Flow Type: [Discovery/Collection/Assessment]
- Environment: [Docker localhost:8081]
- Expected Duration: [X minutes]

After test execution, provide detailed results including:
- All steps executed (with timestamps)
- Expected vs. actual behavior at each step
- Screenshots of any unexpected UI states
- Browser console errors (if any)
- Database verification (if applicable)
- Overall test verdict (PASS/FAIL/BLOCKED)
"
```

---

## Instruction Templates by Flow Type

### Template 1: Discovery Flow Testing

```
Task tool with subagent_type: "qa-playwright-tester"

Prompt: "
REQUIRED READING (MANDATORY - DO NOT SKIP):
1. /docs/qa/FLOW_ARCHITECTURE_GUIDE.md - Read 'Discovery Flow' section (lines 28-165)
2. /docs/qa/TEST_SCENARIO_LIBRARY.md - Read scenario DISC-HAPPY-001

TEST OBJECTIVE:
Execute a complete Discovery Flow test following the documented sequence.

SCENARIO: DISC-HAPPY-001 (Complete Discovery Flow with CSV Import)

EXECUTION PROTOCOL:
1. Navigate to http://localhost:8081/discovery-flows
2. Create a new discovery flow with name 'QA Test Discovery - [current timestamp]'
3. Follow phase sequence EXACTLY as documented:
   - Phase 1: INITIALIZATION (create flow)
   - Phase 2: DATA_IMPORT (upload CSV, WAIT for completion)
   - Phase 3: FIELD_MAPPING (review mappings, approve)
   - Phase 4: DATA_CLEANSING (automated - DO NOT INTERACT)
   - Phase 5: ASSET_CREATION (automated - DO NOT INTERACT)
   - Phase 6: COMPLETION (verify status)

CRITICAL RULES:
- DO NOT click buttons before phase completion indicators appear
- WAIT for progress bars to reach 100% before proceeding
- DO NOT interact during automated phases (data_cleansing, asset_creation)
- Verify each phase transition occurs correctly

EXPECTED TIMELINE:
- INITIALIZATION: < 10 seconds
- DATA_IMPORT: 5-30 seconds
- FIELD_MAPPING: 2-10 seconds
- DATA_CLEANSING: 10-60 seconds (automated wait)
- ASSET_CREATION: 15-90 seconds (automated wait)
- COMPLETION: < 5 seconds
Total: 3-5 minutes

SUCCESS CRITERIA:
✅ Flow status = 'Completed'
✅ All phases completed in sequence
✅ Assets created (count matches CSV rows)
✅ 'View Assets' button enabled
✅ No errors in browser console

FAILURE INDICATORS:
❌ Phase stuck without progress
❌ Error messages displayed
❌ Asset count mismatch
❌ Browser console errors
❌ 404 errors on navigation

REPORTING REQUIREMENTS:
Provide a detailed test report with:
1. Test execution summary (PASS/FAIL)
2. Phase-by-phase results with timestamps
3. Screenshots of key UI states:
   - Flow creation confirmation
   - CSV upload completion
   - Field mapping approval
   - Asset creation completion
   - Final completion status
4. Browser console log (all errors/warnings)
5. Database verification:
   - Query: SELECT flow_id, current_phase, status FROM migration.discovery_flows WHERE flow_id = '[flow_id]'
   - Expected: current_phase='completion', status='completed'
6. Root cause analysis for any failures
7. Recommendation: Pass to main branch OR block for bug fix

TEST DATA:
Use file: backend/tests/fixtures/sample_cmdb_data.csv (127 rows)
"
```

---

### Template 2: Collection Flow Testing (with Validation Gates)

```
Task tool with subagent_type: "qa-playwright-tester"

Prompt: "
REQUIRED READING (MANDATORY - DO NOT SKIP):
1. /docs/qa/FLOW_ARCHITECTURE_GUIDE.md - Read 'Collection Flow' section (lines 167-366)
2. /docs/qa/TEST_SCENARIO_LIBRARY.md - Read scenario COLL-HAPPY-001
3. **CRITICAL**: Read 'Common False Positives' section in FLOW_ARCHITECTURE_GUIDE.md

TEST OBJECTIVE:
Execute a complete Collection Flow test with special attention to THREE CRITICAL VALIDATION GATES (Bug #1056-A/B/C fixes).

SCENARIO: COLL-HAPPY-001 (Complete Collection Flow with Questionnaire Responses)

PREREQUISITES:
✅ Discovery flow completed (scenario DISC-HAPPY-001)
✅ Assets created with data gaps

EXECUTION PROTOCOL:
1. Navigate to http://localhost:8081/collection-flows
2. Create collection flow linked to completed discovery flow
3. Follow phase sequence EXACTLY as documented:
   - Phase 1: INITIALIZATION (create flow)
   - Phase 2: ASSET_SELECTION (select 3-5 assets, click Continue)
   - Phase 3: AUTO_ENRICHMENT (automated - wait 30-120s)
   - Phase 4: GAP_ANALYSIS (automated - wait 20-60s)
   - Phase 5: QUESTIONNAIRE_GENERATION (automated AI - wait 10-60s)
   - Phase 6: MANUAL_COLLECTION ⚠️ CRITICAL GATE #1
   - Phase 7: DATA_VALIDATION ⚠️ CRITICAL GATE #2
   - Phase 8: FINALIZATION ⚠️ CRITICAL GATE #3

⚠️ CRITICAL VALIDATION GATE #1 - MANUAL_COLLECTION:
This is Bug #1056-A fix working correctly:
- MUST fill questionnaire responses before completion
- If you try to complete WITHOUT responses:
  - Expected behavior: Status = 'awaiting_user_responses'
  - This is NOT A BUG - it's the completion gate working correctly
  - DO NOT report this as a bug
- To pass gate: Fill at least 3 questionnaire sections and submit responses

⚠️ CRITICAL VALIDATION GATE #2 - DATA_VALIDATION:
This is Bug #1056-B fix working correctly:
- MUST close all critical gaps (priority >= 80)
- If critical gaps remain after validation:
  - Expected behavior: Status = 'paused', reason = 'critical_gaps_remaining'
  - This is NOT A BUG - it's the validation gate working correctly
  - DO NOT report this as a bug
- To pass gate: Ensure questionnaire responses closed critical gaps

⚠️ CRITICAL VALIDATION GATE #3 - FINALIZATION:
This is Bug #1056-C fix working correctly:
- ALL three checks must pass:
  1. ✅ Questionnaires generated → responses collected
  2. ✅ Critical gaps (priority >= 80) closed
  3. ✅ Assessment readiness criteria met
- If any check fails:
  - Expected behavior: Status = 'incomplete_data_collection' or 'critical_gaps_remaining'
  - This is NOT A BUG - it's the completion gate working correctly
  - DO NOT report this as a bug

EXPECTED TIMELINE:
- INITIALIZATION: < 10 seconds
- ASSET_SELECTION: User input
- AUTO_ENRICHMENT: 30-120 seconds (automated wait)
- GAP_ANALYSIS: 20-60 seconds (automated wait)
- QUESTIONNAIRE_GENERATION: 10-60 seconds (AI generation - THIS IS NORMAL)
- MANUAL_COLLECTION: User input (fill questionnaires)
- DATA_VALIDATION: 5-30 seconds (automated wait)
- FINALIZATION: 5-15 seconds (automated wait)
Total: 5-10 minutes

SUCCESS CRITERIA:
✅ Flow status = 'COMPLETED'
✅ All phases completed in sequence
✅ Questionnaires generated (count > 0)
✅ Questionnaire responses submitted (count > 0)
✅ Critical gaps closed
✅ All finalization checks passed
✅ 'Start Assessment Flow' button enabled

FAILURE INDICATORS (Real Bugs):
❌ Phase stuck with no progress for > max expected time
❌ 404 errors on valid URLs
❌ Database constraint violations
❌ Browser console errors (excluding expected validation messages)
❌ Flow completes WITHOUT questionnaire responses (Bug #1056-A regression)
❌ Flow completes WITH critical gaps (Bug #1056-B regression)

NOT BUGS (Expected Validation Behavior):
✅ 'awaiting_user_responses' status without questionnaire responses - WORKING AS DESIGNED
✅ 'paused' status with critical gaps remaining - WORKING AS DESIGNED
✅ 'incomplete_data_collection' error in finalization - WORKING AS DESIGNED
✅ Questionnaire generation taking 30+ seconds - AI TAKES TIME, NORMAL

REPORTING REQUIREMENTS:
Provide a detailed test report with:
1. Test execution summary (PASS/FAIL)
2. Phase-by-phase results with timestamps
3. **Validation Gate Results** (CRITICAL):
   - Gate #1 (manual_collection): Did flow correctly block completion without responses?
   - Gate #2 (data_validation): Did flow correctly pause for critical gaps?
   - Gate #3 (finalization): Did all three checks pass?
4. Screenshots of:
   - Asset selection
   - Questionnaire generation completion
   - Filled questionnaire sections
   - Data validation results
   - Final completion status with all checks passed
5. Browser console log
6. Database verification:
   - Query 1: SELECT COUNT(*) FROM migration.adaptive_questionnaires WHERE collection_flow_id = '[flow_id]'
   - Expected: Count > 0
   - Query 2: SELECT COUNT(*) FROM migration.questionnaire_responses WHERE questionnaire_id IN (SELECT id FROM migration.adaptive_questionnaires WHERE collection_flow_id = '[flow_id]')
   - Expected: Count > 0 (responses submitted)
   - Query 3: SELECT COUNT(*) FROM migration.collection_data_gaps WHERE collection_flow_id = '[flow_id]' AND priority >= 80 AND resolution_status = 'pending'
   - Expected: Count = 0 (no critical gaps pending)
7. Root cause analysis for any REAL failures (distinguish from validation gates)
8. Recommendation with clear distinction between bugs and working validation

TEST DATA:
Prerequisites: Completed discovery flow with assets
"
```

---

### Template 3: Assessment Flow Testing

```
Task tool with subagent_type: "qa-playwright-tester"

Prompt: "
REQUIRED READING (MANDATORY - DO NOT SKIP):
1. /docs/qa/FLOW_ARCHITECTURE_GUIDE.md - Read 'Assessment Flow' section (lines 368-460)
2. /docs/qa/TEST_SCENARIO_LIBRARY.md - Read scenario ASSESS-HAPPY-001

TEST OBJECTIVE:
Execute a complete Assessment Flow test to verify 6R recommendation generation.

SCENARIO: ASSESS-HAPPY-001 (Complete Assessment Flow)

PREREQUISITES:
✅ Collection flow completed (scenario COLL-HAPPY-001)
✅ Assets with sufficient data quality

EXECUTION PROTOCOL:
1. Navigate to http://localhost:8081/assessment-flow
2. Create assessment flow linked to completed collection flow
3. Follow phase sequence EXACTLY as documented:
   - Phase 1: INITIALIZATION (create flow, select applications)
   - Phase 2: ARCHITECTURE_MINIMUMS (set standards)
   - Phase 3: TECH_DEBT_ANALYSIS (automated AI - wait 60-180s)
   - Phase 4: COMPONENT_SIXR_STRATEGIES (review recommendations)
   - Phase 5: APP_ON_PAGE_GENERATION (automated - wait 30-90s)
   - Phase 6: FINALIZATION (verify completion)

CRITICAL RULES:
- AI phases take LONGER than Discovery/Collection (60-180s for tech debt)
- This is NORMAL - AI analysis requires time
- DO NOT report long wait times as bugs if within expected range

EXPECTED TIMELINE:
- INITIALIZATION: < 10 seconds
- ARCHITECTURE_MINIMUMS: User input
- TECH_DEBT_ANALYSIS: 60-180 seconds (AI analysis - WAIT PATIENTLY)
- COMPONENT_SIXR_STRATEGIES: 10-30 seconds (auto-review)
- APP_ON_PAGE_GENERATION: 30-90 seconds (report generation)
- FINALIZATION: < 5 seconds
Total: 6-12 minutes

SUCCESS CRITERIA:
✅ Flow status = 'Completed'
✅ All phases completed in sequence
✅ 6R recommendations generated for all components
✅ Each component has strategy badge (Rehost/Refactor/Retain/etc.)
✅ AI reasoning displayed for recommendations
✅ Reports generated successfully
✅ 'View Assessments' and 'Export Results' buttons enabled

FAILURE INDICATORS:
❌ Tech debt analysis timeout (> 300 seconds)
❌ Missing 6R recommendations
❌ Report generation fails
❌ 404 errors on navigation
❌ Browser console errors

REPORTING REQUIREMENTS:
Provide a detailed test report with:
1. Test execution summary (PASS/FAIL)
2. Phase timing analysis:
   - Were AI phases within expected ranges?
   - Any phases exceed max acceptable time?
3. Screenshots of:
   - Architecture standards selection
   - Tech debt analysis results
   - 6R recommendations grid
   - Generated reports
   - Final completion status
4. 6R Recommendation validation:
   - List all components assessed
   - List 6R strategy for each
   - Verify AI reasoning provided
5. Browser console log
6. Database verification:
   - Query: SELECT asset_id, six_r_strategy FROM migration.assets WHERE id IN (SELECT asset_id FROM migration.assessment_applications WHERE assessment_flow_id = '[flow_id]')
   - Expected: All assets have six_r_strategy populated
7. Root cause analysis for any failures
8. Recommendation

TEST DATA:
Prerequisites: Completed collection flow with assessed applications
"
```

---

### Template 4: Validation Gate Testing (Bug #1056 Verification)

```
Task tool with subagent_type: "qa-playwright-tester"

Prompt: "
REQUIRED READING (MANDATORY - DO NOT SKIP):
1. /docs/qa/FLOW_ARCHITECTURE_GUIDE.md - Read 'Collection Flow' section, especially lines 281-365
2. /docs/qa/TEST_SCENARIO_LIBRARY.md - Read scenarios COLL-GATE-001, COLL-GATE-002, COLL-GATE-003
3. **CRITICAL**: Read PR #1058 description in GitHub issue comments

TEST OBJECTIVE:
Verify that Collection Flow completion gates (Bug #1056-A/B/C fixes from PR #1058) are working correctly.

⚠️ THIS IS A REGRESSION TEST - DO NOT REPORT VALIDATION GATES AS BUGS

TEST SCENARIOS:
1. COLL-GATE-001: Manual Collection Gate (Bug #1056-A)
2. COLL-GATE-002: Data Validation Gate (Bug #1056-B)
3. COLL-GATE-003: Finalization Gate (Bug #1056-C)

SCENARIO 1: Manual Collection Gate (Bug #1056-A)
OBJECTIVE: Verify flow CANNOT complete without questionnaire responses

Steps:
1. Create collection flow to manual_collection phase
2. Questionnaires generated
3. **DO NOT** fill any questionnaire responses
4. Attempt to complete collection flow
5. EXPECTED: Status = 'awaiting_user_responses', error message displayed
6. EXPECTED: Phase does NOT advance to data_validation
7. **VERDICT**: If flow blocks completion → PASS (Bug #1056-A working)
8. **VERDICT**: If flow completes with 0 responses → FAIL (REGRESSION BUG)

SCENARIO 2: Data Validation Gate (Bug #1056-B)
OBJECTIVE: Verify flow PAUSES when critical gaps remain

Steps:
1. Create collection flow to data_validation phase
2. Fill questionnaires with MINIMAL responses (not enough to close critical gaps)
3. Wait for data validation to complete
4. EXPECTED: Status = 'paused', reason = 'critical_gaps_remaining'
5. EXPECTED: Critical gap details displayed (field names, priorities)
6. EXPECTED: Phase does NOT advance to finalization
7. **VERDICT**: If flow pauses for critical gaps → PASS (Bug #1056-B working)
8. **VERDICT**: If flow completes with critical gaps → FAIL (REGRESSION BUG)

SCENARIO 3: Finalization Gate (Bug #1056-C)
OBJECTIVE: Verify all three completion checks are enforced

Steps:
1. Create collection flow to finalization phase
2. Ensure:
   - Questionnaires generated AND responses collected
   - Critical gaps closed
3. Wait for finalization to complete
4. EXPECTED: Three checks displayed with green checkmarks:
   - ✅ Questionnaires generated → responses collected
   - ✅ Critical gaps (priority >= 80) closed
   - ✅ Assessment readiness criteria met
5. EXPECTED: Status = 'COMPLETED'
6. **VERDICT**: If all checks pass and flow completes → PASS (Bug #1056-C working)
7. **VERDICT**: If flow completes without all checks → FAIL (REGRESSION BUG)

REPORTING REQUIREMENTS:
Provide a test report with:
1. Overall regression test verdict (PASS/FAIL)
2. Individual scenario results:
   - COLL-GATE-001: PASS/FAIL
   - COLL-GATE-002: PASS/FAIL
   - COLL-GATE-003: PASS/FAIL
3. For each scenario:
   - Expected behavior (from PR #1058)
   - Actual behavior observed
   - Screenshots of validation messages
   - Database state verification
4. **CRITICAL DISTINCTION**:
   - Clearly label whether failures are REGRESSIONS (Bug #1056 broken) or NEW BUGS (different issue)
5. If ALL scenarios PASS:
   - Confirm: 'Collection Flow completion gates (Bug #1056-A/B/C) working as designed per PR #1058'
6. If ANY scenario FAILS:
   - Mark as CRITICAL regression
   - Recommend immediate investigation
   - Reference PR #1058 in bug report

SUCCESS CRITERIA:
✅ All three validation gates function correctly
✅ Flows blocked when completion criteria not met
✅ Clear error messages displayed
✅ User knows what action is required

FAILURE CRITERIA (REGRESSION):
❌ Flow completes without responses (Bug #1056-A regression)
❌ Flow completes with critical gaps (Bug #1056-B regression)
❌ Flow completes without all checks passing (Bug #1056-C regression)
"
```

---

## Test Reporting Format

### Standard Test Report Structure

```
# QA Test Report: [SCENARIO_ID]

## Executive Summary
- **Test Date**: [YYYY-MM-DD HH:MM]
- **Scenario**: [SCENARIO_ID] - [Scenario Name]
- **Flow Type**: [Discovery/Collection/Assessment]
- **Overall Result**: [PASS/FAIL/BLOCKED]
- **Execution Time**: [X minutes Y seconds]

## Test Environment
- **Frontend URL**: http://localhost:8081
- **Backend URL**: http://localhost:8000
- **Database**: PostgreSQL (port 5433)
- **Browser**: [Chrome/Firefox/Safari] [Version]
- **Docker Compose**: [Running/Stopped]

## Prerequisites Status
- [ ] Docker environment running
- [ ] Test data available
- [ ] Prerequisite flows completed (if applicable)
- [ ] Browser console cleared

## Test Execution Details

### Phase-by-Phase Results

#### Phase 1: [PHASE_NAME]
- **Start Time**: [HH:MM:SS]
- **End Time**: [HH:MM:SS]
- **Duration**: [X seconds]
- **Expected Behavior**: [From scenario documentation]
- **Actual Behavior**: [What actually happened]
- **Status**: [PASS/FAIL]
- **Screenshot**: [Filename or embedded image]
- **Notes**: [Any observations]

#### Phase 2: [PHASE_NAME]
[Repeat for each phase]

## Validation Gate Results (Collection Flow Only)

### Gate #1: Manual Collection (Bug #1056-A)
- **Test**: Attempt completion without responses
- **Expected**: Status = 'awaiting_user_responses'
- **Actual**: [What happened]
- **Result**: [PASS - Gate working / FAIL - Regression bug]

### Gate #2: Data Validation (Bug #1056-B)
- **Test**: Validation with critical gaps remaining
- **Expected**: Status = 'paused', reason = 'critical_gaps_remaining'
- **Actual**: [What happened]
- **Result**: [PASS - Gate working / FAIL - Regression bug]

### Gate #3: Finalization (Bug #1056-C)
- **Test**: All three completion checks
- **Expected**: All checks pass, status = 'COMPLETED'
- **Actual**: [What happened]
- **Result**: [PASS - Gate working / FAIL - Regression bug]

## Success Criteria Checklist
- [ ] All phases completed in sequence
- [ ] No unexpected errors
- [ ] Expected UI states displayed
- [ ] Database state correct
- [ ] Browser console clean (or expected warnings only)
- [ ] Flow completed within expected time

## Issues Encountered

### Issue 1: [Title]
- **Severity**: [Critical/High/Medium/Low]
- **Phase**: [Which phase]
- **Expected**: [What should happen]
- **Actual**: [What actually happened]
- **Screenshot**: [Filename]
- **Browser Console Log**: [Relevant errors]
- **Database Query Results**: [If applicable]
- **Is This a Bug?**: [YES/NO - with reasoning]
- **Recommended Action**: [File bug / Working as designed / Investigate further]

## Database Verification

```sql
-- Query 1: Flow Status Check
SELECT flow_id, current_phase, status
FROM migration.[flow_table]
WHERE flow_id = '[flow_id]';

-- Result:
-- [Paste query results]

-- Query 2: [Additional verification query]
[Query and results]
```

## Browser Console Log

```
[Paste relevant console messages]
[Include errors, warnings, and any validation messages]
```

## Screenshots

1. **Flow Creation**: [Filename or embedded]
2. **Phase X Completion**: [Filename or embedded]
3. **Error State (if any)**: [Filename or embedded]
4. **Final Status**: [Filename or embedded]

## Root Cause Analysis (For Failures)

If test FAILED, provide:
1. **Immediate Cause**: What triggered the failure
2. **Root Cause**: Why the failure occurred
3. **Affected Components**: Code areas impacted
4. **Proposed Fix**: How to resolve
5. **Regression Risk**: Could this break other flows?

## Performance Metrics

- **Total Execution Time**: [X minutes]
- **Expected Time**: [Y minutes]
- **Performance Delta**: [+/- Z seconds]
- **Memory Usage**: [Peak memory in browser]
- **Network Requests**: [Count]
- **Failed Requests**: [Count]

## Recommendation

### If PASS:
✅ **APPROVE FOR MERGE**
- All phases completed successfully
- No unexpected errors
- Flow behaves as documented
- Performance within acceptable range

### If FAIL:
❌ **BLOCK MERGE**
- Critical bug identified: [Issue title]
- Recommend: [Immediate fix / Further investigation]
- **Blocker Priority**: [P0/P1/P2]
- **Assignee Suggestion**: [Developer/Team]

### If BLOCKED:
⚠️ **CANNOT COMPLETE TEST**
- Reason: [Why test couldn't complete]
- Prerequisite failure: [What failed]
- Recommend: [Fix prerequisite first]

## Test Artifacts

- Test report: [This file]
- Screenshots: [Directory path]
- Screen recording (if available): [File path]
- Browser console log: [File path]
- Database dump (if relevant): [File path]

---
**Tested By**: qa-playwright-tester agent
**Report Generated**: [YYYY-MM-DD HH:MM:SS]
**Session ID**: [Unique identifier]
```

---

## Common Pitfalls for QA Agent (DO NOT DO)

### ❌ DON'T: Click Randomly
**Problem**: Clicking buttons without understanding flow sequence
**Solution**: Follow documented phase progression in FLOW_ARCHITECTURE_GUIDE.md

### ❌ DON'T: Report Validation Gates as Bugs
**Problem**: Reporting "stuck in manual_collection" as a bug
**Solution**: Read Bug #1056-A/B/C fixes - validation gates are WORKING AS DESIGNED

### ❌ DON'T: Skip Waiting for Completion
**Problem**: Clicking "Continue" before phase completion indicators appear
**Solution**: Wait for progress bars to reach 100% and success messages

### ❌ DON'T: Expect Instant AI Generation
**Problem**: Reporting "questionnaire generation timeout" after 15 seconds
**Solution**: AI tasks take 10-60 seconds - this is NORMAL

### ❌ DON'T: Test Without Reading Architecture Guide
**Problem**: Not understanding why certain behaviors occur
**Solution**: ALWAYS read FLOW_ARCHITECTURE_GUIDE.md first

### ❌ DON'T: Test Out of Sequence
**Problem**: Trying to start Collection Flow without completed Discovery
**Solution**: Follow prerequisite dependencies (Discovery → Collection → Assessment)

### ❌ DON'T: Ignore Expected Response Times
**Problem**: Reporting "slow performance" within acceptable ranges
**Solution**: Check "Expected Response Times" table in FLOW_ARCHITECTURE_GUIDE.md

### ❌ DON'T: Mix Up Bugs and Features
**Problem**: Reporting "fewer questionnaires for complete data" as a bug
**Solution**: Adaptive behavior is INTELLIGENT - showing less = better data quality

---

## Integration with CI/CD

### GitHub Actions Integration (Future)

```yaml
# .github/workflows/qa-playwright.yml
name: QA Playwright Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  qa-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start Docker Environment
        run: |
          cd config/docker
          docker-compose up -d
          sleep 30  # Wait for services to start

      - name: Run Discovery Flow Test
        uses: anthropic/claude-code-action@v1
        with:
          agent-type: qa-playwright-tester
          instruction-template: /docs/qa/QA_AGENT_INSTRUCTION_TEMPLATE.md#template-1
          scenario: DISC-HAPPY-001
          report-path: ./qa-reports/discovery-flow-test.md

      - name: Run Collection Flow Test
        uses: anthropic/claude-code-action@v1
        with:
          agent-type: qa-playwright-tester
          instruction-template: /docs/qa/QA_AGENT_INSTRUCTION_TEMPLATE.md#template-2
          scenario: COLL-HAPPY-001
          report-path: ./qa-reports/collection-flow-test.md

      - name: Upload Test Reports
        uses: actions/upload-artifact@v3
        with:
          name: qa-test-reports
          path: ./qa-reports/*.md
```

---

## Version History

- **v1.0** (2025-11-15): Initial QA agent instruction template
  - Four template types (Discovery, Collection, Assessment, Validation Gates)
  - Standard test reporting format
  - Common pitfalls documentation
  - CI/CD integration pattern

---

**Last Updated**: 2025-11-15
**Related Issues**: #1061 (QA agent architectural context)
**Related PRs**: #1058 (Collection Flow completion gates)
**Related Documents**:
- `/docs/qa/FLOW_ARCHITECTURE_GUIDE.md` - Flow sequences and architecture
- `/docs/qa/TEST_SCENARIO_LIBRARY.md` - Pre-defined test scenarios
