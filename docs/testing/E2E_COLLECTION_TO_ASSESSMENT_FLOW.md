# E2E Collection to Assessment Flow - Navigation Sequence

## Overview
This document provides a complete navigation sequence for testing the collection flow through to assessment flow execution. Use this as a reference for creating Playwright E2E tests or manual testing validation.

## Test Objectives
1. Verify collection flow initialization and asset selection
2. Validate gap analysis generation and acceptance
3. Test questionnaire generation and form submission
4. Verify automatic transition from collection to assessment
5. Confirm assessment agents can access collected data
6. Validate phase progression in assessment flow

## Prerequisites
- Docker containers running (frontend on :8081, backend on :8000, DB on :5433)
- Database seeded with demo data (client_account_id=1, engagement_id=1)
- At least one application in canonical_applications table

## Test Data
```javascript
const TEST_CREDENTIALS = {
  username: "demo@example.com",
  password: "demo123"
};

const TEST_CONTEXT = {
  client_account_id: 1,
  engagement_id: 1,
  organization: "Democorp",
  engagement_name: "Cloud Migration 2024"
};
```

---

## Step-by-Step Navigation Sequence

### Phase 1: Login and Context Selection

#### Step 1.1: Navigate to Application
```javascript
await page.goto('http://localhost:8081');
await page.waitForLoadState('networkidle');
```

**Expected State:**
- URL: `http://localhost:8081/login` (auto-redirect if not authenticated)
- Page Title: "AI powered Migration Orchestrator"

#### Step 1.2: Perform Login
```javascript
// Fill login form
await page.fill('input[type="email"]', TEST_CREDENTIALS.username);
await page.fill('input[type="password"]', TEST_CREDENTIALS.password);

// Submit login
await page.click('button[type="submit"]');
await page.waitForLoadState('networkidle');
```

**Expected State:**
- URL: `http://localhost:8081/` (dashboard)
- User profile visible in header
- Organization and engagement context displayed

**Validation Points:**
- [ ] Login successful without errors
- [ ] User profile shows "Demo User"
- [ ] Organization shows "Democorp"
- [ ] Engagement shows "Cloud Migration 2024"

---

### Phase 2: Collection Flow Initialization

#### Step 2.1: Navigate to Adaptive Forms
```javascript
// Click Collection in sidebar
await page.click('text=Collection');
await page.waitForTimeout(500); // Allow submenu to expand

// Click Adaptive Forms
await page.click('text=Adaptive Forms');
await page.waitForLoadState('networkidle');
```

**Expected State:**
- URL: `http://localhost:8081/collection/adaptive-forms`
- Page displays "Adaptive Data Collection Forms"
- Collection flow auto-initializes

**Validation Points:**
- [ ] Page loads without errors
- [ ] Flow ID is generated (UUID format)
- [ ] Console log: "✅ Collection flow initialized with ID: [UUID]"
- [ ] Status shows "Asset Selection" phase

#### Step 2.2: Extract Flow ID
```javascript
// Extract flow ID from URL or page state
const flowIdMatch = await page.url().match(/flow_id=([a-f0-9-]+)/);
const flowId = flowIdMatch ? flowIdMatch[1] : null;

// Alternatively, extract from console logs
const logs = [];
page.on('console', msg => logs.push(msg.text()));
const flowIdLog = logs.find(log => log.includes('Collection flow initialized'));
```

**Expected State:**
- Flow ID is a valid UUID v4 format
- Flow ID persists in URL query parameters

---

### Phase 3: Asset Selection

#### Step 3.1: Wait for Applications to Load
```javascript
await page.waitForSelector('[data-testid="asset-selector"]', { timeout: 10000 });
```

**Expected State:**
- Asset selector dropdown is visible
- Dropdown contains application options (not UUIDs)

#### Step 3.2: Select an Asset
```javascript
// Click asset selector dropdown
await page.click('[data-testid="asset-selector"]');
await page.waitForTimeout(300);

// Get first application option (avoid "app-new" or placeholders)
const assetOptions = await page.$$('[role="option"]');
let selectedAsset = null;

for (const option of assetOptions) {
  const text = await option.textContent();
  if (text && !text.includes('app-new') && !text.includes('Select')) {
    await option.click();
    selectedAsset = {
      name: text.trim(),
      element: option
    };
    break;
  }
}

await page.waitForTimeout(500);
```

**Expected State:**
- Asset selected (e.g., "Analytics Engine")
- Asset UUID extracted from DOM (data-asset-id attribute)
- Page status shows asset selection complete

**Validation Points:**
- [ ] Asset name is human-readable (not UUID)
- [ ] Asset UUID is stored in page state
- [ ] Console log: "✅ Asset selected: [Name] (UUID: [UUID])"

#### Step 3.3: Extract Asset ID
```javascript
// Extract asset_id from DOM
const assetId = await page.evaluate(() => {
  const selector = document.querySelector('[data-asset-id]');
  return selector ? selector.getAttribute('data-asset-id') : null;
});

// Store for later validation
const TEST_ASSET = {
  id: assetId,
  name: selectedAsset.name
};
```

---

### Phase 4: Gap Analysis

#### Step 4.1: Generate Questionnaires
```javascript
// Click "Generate Questionnaires" button
await page.click('button:has-text("Generate Questionnaires")');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000); // Allow gap analysis to process
```

**Expected State:**
- Gap analysis grid appears
- Multiple gaps are displayed (e.g., 15 gaps)
- Each gap has: title, description, recommendation

**Validation Points:**
- [ ] Gap count > 0
- [ ] Gaps are specific to selected asset
- [ ] Console log: "✅ Gap analysis completed: X gaps identified"

#### Step 4.2: Accept All Gaps
```javascript
// Wait for gap analysis grid
await page.waitForSelector('[data-testid="gap-analysis-grid"]');

// Click "Select All" checkbox (if available)
const selectAllCheckbox = await page.$('[data-testid="select-all-gaps"]');
if (selectAllCheckbox) {
  await selectAllCheckbox.click();
} else {
  // Manually check all gap checkboxes
  const gapCheckboxes = await page.$$('[data-testid^="gap-checkbox-"]');
  for (const checkbox of gapCheckboxes) {
    await checkbox.click();
    await page.waitForTimeout(100);
  }
}

await page.waitForTimeout(500);
```

**Expected State:**
- All gap checkboxes are checked
- "Continue to Questionnaire" button is enabled

**Validation Points:**
- [ ] All gaps selected
- [ ] Button state changes from disabled to enabled

---

### Phase 5: Questionnaire Generation and Form Filling

#### Step 5.1: Navigate to Questionnaire
```javascript
// Click "Continue to Questionnaire" button
await page.click('button:has-text("Continue to Questionnaire")');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);
```

**Expected State:**
- URL: `http://localhost:8081/collection/adaptive-forms?flow_id=[UUID]`
- Page header displays asset name (e.g., "Analytics Engine")
- NOT "app-new" or UUID

**CRITICAL Validation Point:**
- [ ] **Header shows actual asset name, NOT "app-new" or UUID**
- [ ] This validates Fix #5 (UUID-to-name resolution)

#### Step 5.2: Verify Questionnaire Structure
```javascript
// Check for form sections
const sections = await page.$$('[data-testid^="form-section-"]');
const sectionCount = sections.length;

// Check for required fields
const requiredFields = await page.$$('[required]');
const requiredCount = requiredFields.length;

console.log(`📋 Form has ${sectionCount} sections with ${requiredCount} required fields`);
```

**Expected State:**
- Multiple form sections (e.g., 3 sections)
- Multiple required fields (e.g., 6 required fields)
- Sections include: Basic Information, Technical Details, Infrastructure

#### Step 5.3: Fill Form Fields
```javascript
// Example field values (adjust based on actual form structure)
const FORM_DATA = {
  // Basic Information section
  'compliance_requirements': 'Healthcare (HIPAA, FDA)',
  'stakeholder_impact': 'High - Critical patient data system affecting 500+ users',

  // Technical Details section
  'primary_language': 'Python',
  'database_system': 'PostgreSQL',

  // Infrastructure section
  'operating_system': 'Ubuntu 22.04 LTS',
  'infrastructure_specs': '8 vCPU, 32GB RAM, 500GB SSD',
  'availability_requirements': '99.99% uptime SLA'
};

// Fill each field
for (const [fieldId, value] of Object.entries(FORM_DATA)) {
  const field = await page.$(`[name="${fieldId}"], [data-field-id="${fieldId}"]`);

  if (field) {
    const fieldType = await field.getAttribute('type');

    if (fieldType === 'textarea' || await field.evaluate(el => el.tagName === 'TEXTAREA')) {
      await field.fill(value);
    } else if (fieldType === 'select-one') {
      await field.selectOption({ label: value });
    } else {
      await field.fill(value);
    }

    await page.waitForTimeout(200); // Allow validation
  }
}
```

**Expected State:**
- All required fields filled
- Data confidence score updates (should reach 100%)
- Progress percentage increases (e.g., 40%)

**Validation Points:**
- [ ] Data confidence: 100%
- [ ] Progress: 40% or higher
- [ ] No validation errors displayed
- [ ] Submit button becomes enabled

#### Step 5.4: Verify Asset Context
```javascript
// Verify asset_id is embedded in form metadata
const assetMetadata = await page.evaluate(() => {
  const metaElements = document.querySelectorAll('[data-asset-id]');
  return Array.from(metaElements).map(el => ({
    assetId: el.getAttribute('data-asset-id'),
    assetName: el.getAttribute('data-asset-name')
  }));
});

// Validate asset_id matches selection
const hasCorrectAsset = assetMetadata.some(meta =>
  meta.assetId === TEST_ASSET.id &&
  meta.assetName === TEST_ASSET.name
);

console.log(`✅ Asset context preserved: ${hasCorrectAsset}`);
```

---

### Phase 6: Form Submission

#### Step 6.1: Submit Form
```javascript
// Click Submit button
await page.click('button:has-text("Submit")');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000);
```

**Expected State:**
- Success notification appears
- Console log: "✅ Extracted asset_id from question metadata: [UUID]"
- Console log: "✅ Form submitted successfully"

**Validation Points:**
- [ ] Success notification displayed
- [ ] Asset ID logged in console
- [ ] No error messages

#### Step 6.2: Monitor Backend Processing
```javascript
// Watch console for backend confirmation
page.on('console', msg => {
  const text = msg.text();

  if (text.includes('Extracted asset_id')) {
    console.log('✅ Backend received asset_id:', text);
  }

  if (text.includes('Automatic transition to assessment')) {
    console.log('✅ Assessment flow triggered:', text);
  }
});
```

**Expected Backend Logs:**
```
✅ Extracted asset_id from question metadata: 778f9a98-1ed9-4acd-8804-bdcec659ac00
✅ Automatic transition to assessment flow initiated
✅ Assessment flow created with ID: [UUID]
```

---

### Phase 7: Assessment Flow Transition

#### Step 7.1: Wait for Assessment Flow
```javascript
// Wait for automatic redirect or status change
await page.waitForTimeout(3000);

// Check for assessment flow initialization
const assessmentFlowId = await page.evaluate(() => {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get('assessment_flow_id') ||
         urlParams.get('flow_id');
});

// Or extract from console logs
const assessmentLog = logs.find(log =>
  log.includes('Assessment flow created')
);
```

**Expected State:**
- Assessment flow ID generated (new UUID, different from collection flow)
- Status: "INITIALIZED"
- Phase: "initialization"
- Progress: 16%

**Validation Points:**
- [ ] Assessment flow ID is valid UUID
- [ ] Assessment flow ID ≠ Collection flow ID
- [ ] Status shows "INITIALIZED"
- [ ] Console log: "✅ Assessment flow created with ID: [UUID]"

#### Step 7.2: Navigate to Assessment Flow
```javascript
// If not auto-redirected, manually navigate
await page.goto(`http://localhost:8081/assessment/${assessmentFlowId}/app-on-page`);
await page.waitForLoadState('networkidle');
```

**Expected State:**
- URL: `http://localhost:8081/assessment/[UUID]/app-on-page`
- Page title: "Application Assessment Review"
- Asset name displayed correctly (e.g., "Analytics Engine")

---

### Phase 8: Assessment Agent Execution

#### Step 8.1: Trigger Agent Processing
```javascript
// Click "Continue to Application Review" button
await page.click('button:has-text("Continue to Application Review")');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(2000);
```

**Expected State:**
- "Check Status" button appears
- Console log: "⏳ Complexity analysis agent is now processing in background..."
- Backend log: "✅ Retrieved persistent agent 'complexity_analyst'"

**Validation Points:**
- [ ] "Check Status" button visible
- [ ] Agent processing started
- [ ] No 401 or 422 errors in console

#### Step 8.2: Check Agent Status
```javascript
// Click "Check Status" button
await page.click('button:has-text("Check Status")');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(1000);
```

**Expected State:**
- Phase changes from "initialization" to "complexity_analysis"
- Status changes from "INITIALIZED (16%)" to "IN PROGRESS (33%)"
- Page may navigate to assessment review page

**Validation Points:**
- [ ] Phase progression: initialization → complexity_analysis
- [ ] Status progression: INITIALIZED → IN PROGRESS
- [ ] Progress: 16% → 33%
- [ ] Console log: "✅ Phase changed to: complexity_analysis"

#### Step 8.3: Verify Agent Access to Collected Data
```javascript
// Monitor backend logs for agent activity
// Backend should show:
// - Agent created successfully
// - Agent accessing collected data
// - Agent processing with tools

// Check frontend for data availability indicators
const dataIndicators = await page.evaluate(() => {
  const indicators = document.querySelectorAll('[data-has-collected-data="true"]');
  return indicators.length > 0;
});

console.log(`✅ Agent can access collected data: ${dataIndicators}`);
```

**Expected Backend Logs:**
```
INFO - ✅ Retrieved persistent agent 'complexity_analyst' for phase 'complexity_analysis'
INFO - Task: Analyze migration complexity for applications based on:
       - Component complexity indicators: {'total_applications': 55, ...}
INFO - Agent created successfully with 7 tools
INFO - Using LiteLLM with model: deepinfra/meta-llama/Llama-4-Maverick-70B
```

**CRITICAL Validation Points:**
- [ ] **Agent created without asyncio.wrap_future() errors** (Fix #1)
- [ ] **Agent can access collected data** (Fix #5 validation)
- [ ] **No transaction rollback errors** (Fixes #3, #4)

---

## Complete Test Flow Summary

```
1. Login (demo@example.com / demo123)
   ↓
2. Navigate to Collection → Adaptive Forms
   ↓
3. Select Asset (e.g., "Analytics Engine")
   ↓
4. Generate Questionnaires
   ↓
5. Accept All Gaps
   ↓
6. Continue to Questionnaire
   ↓
7. Verify Asset Name (NOT "app-new") ← Fix #5
   ↓
8. Fill Form Fields (6 required fields)
   ↓
9. Submit Form (asset_id preserved)
   ↓
10. Automatic Transition to Assessment
    ↓
11. Continue to Application Review
    ↓
12. Check Status Button
    ↓
13. Verify Phase Progression ← Fixes #1, #3, #4
    ↓
14. Confirm Agent Access to Data
```

---

## Playwright Test Template

```typescript
import { test, expect } from '@playwright/test';

test.describe('Collection to Assessment Flow E2E', () => {
  let flowId: string;
  let assessmentFlowId: string;
  let assetId: string;
  let assetName: string;

  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('http://localhost:8081/login');
    await page.fill('input[type="email"]', 'demo@example.com');
    await page.fill('input[type="password"]', 'demo123');
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
  });

  test('should complete collection flow and transition to assessment', async ({ page }) => {
    // Phase 1: Navigate to Adaptive Forms
    await page.click('text=Collection');
    await page.waitForTimeout(500);
    await page.click('text=Adaptive Forms');
    await page.waitForLoadState('networkidle');

    // Phase 2: Select Asset
    await page.waitForSelector('[data-testid="asset-selector"]');
    await page.click('[data-testid="asset-selector"]');
    const firstAsset = await page.$('[role="option"]:not(:has-text("app-new"))');
    assetName = await firstAsset!.textContent() || '';
    await firstAsset!.click();

    // Phase 3: Generate and Accept Gaps
    await page.click('button:has-text("Generate Questionnaires")');
    await page.waitForTimeout(2000);

    const selectAllCheckbox = await page.$('[data-testid="select-all-gaps"]');
    await selectAllCheckbox!.click();

    await page.click('button:has-text("Continue to Questionnaire")');
    await page.waitForLoadState('networkidle');

    // CRITICAL: Verify asset name displayed correctly (Fix #5)
    const header = await page.textContent('h1, [data-testid="asset-header"]');
    expect(header).toContain(assetName);
    expect(header).not.toContain('app-new');
    expect(header).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/);

    // Phase 4: Fill and Submit Form
    await page.fill('[name="compliance_requirements"]', 'Healthcare (HIPAA, FDA)');
    await page.fill('[name="stakeholder_impact"]', 'High impact system');
    await page.fill('[name="primary_language"]', 'Python');
    await page.fill('[name="database_system"]', 'PostgreSQL');
    await page.fill('[name="operating_system"]', 'Ubuntu 22.04 LTS');
    await page.fill('[name="infrastructure_specs"]', '8 vCPU, 32GB RAM');

    await page.click('button:has-text("Submit")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Phase 5: Verify Assessment Transition
    const currentUrl = page.url();
    expect(currentUrl).toContain('/assessment/');

    // Phase 6: Trigger and Verify Agent Processing
    await page.click('button:has-text("Continue to Application Review")');
    await page.waitForTimeout(2000);

    await expect(page.locator('button:has-text("Check Status")')).toBeVisible();

    await page.click('button:has-text("Check Status")');
    await page.waitForTimeout(1000);

    // Verify phase progression (validates Fixes #1, #3, #4)
    const statusText = await page.textContent('[data-testid="flow-status"]');
    expect(statusText).toContain('IN PROGRESS');
    expect(statusText).toContain('33%');
  });
});
```

---

## Error Scenarios to Test

### Scenario 1: UUID Display Bug (Fixed)
**Test:** Verify asset name shows throughout flow, not UUID
**Expected:** "Analytics Engine" displayed
**Previous Bug:** "app-new" or UUID displayed
**Fix:** Pass `applications` array to `convertQuestionnairesToFormData()`

### Scenario 2: Assessment Agent Failure (Fixed)
**Test:** Verify agents create without asyncio errors
**Expected:** Agent created successfully, no 401/422 errors
**Previous Bug:** `TypeError: An asyncio.Future, a coroutine or an awaitable is required`
**Fix:** Use `asyncio.wrap_future()` in assessment executors

### Scenario 3: Transaction Rollback (Fixed)
**Test:** Verify phase results save correctly
**Expected:** Phase results persist to database
**Previous Bug:** Transaction aborted on missing servers table
**Fix:** Transaction rollback and retry logic

---

## Data Validation Checkpoints

At each phase, verify:

1. **Asset Selection:**
   - [ ] Asset name is human-readable
   - [ ] Asset UUID is valid format
   - [ ] Asset context preserved in state

2. **Questionnaire:**
   - [ ] Header shows asset name (NOT UUID)
   - [ ] Form fields contain asset metadata
   - [ ] asset_id in question metadata

3. **Form Submission:**
   - [ ] asset_id extracted correctly
   - [ ] Responses linked to correct asset
   - [ ] Backend confirms asset_id reception

4. **Assessment Flow:**
   - [ ] Assessment flow ID generated
   - [ ] Asset name displayed correctly
   - [ ] Collected data accessible to agents

5. **Agent Execution:**
   - [ ] Agents created successfully
   - [ ] Agents access collected data
   - [ ] Phase progression works
   - [ ] No asyncio or transaction errors

---

## Performance Benchmarks

Expected timings:
- Login: < 2 seconds
- Asset selection: < 1 second
- Gap analysis: < 3 seconds
- Form submission: < 2 seconds
- Assessment transition: < 3 seconds
- Agent initialization: < 2 seconds

---

## Debugging Tips

### If Asset Name Shows "app-new":
1. Check browser console for applications array
2. Verify `useApplications()` hook called
3. Check `convertQuestionnairesToFormData()` receives applications parameter
4. Inspect question metadata for asset_id field

### If Assessment Agents Fail:
1. Check backend logs for asyncio errors
2. Verify `asyncio.wrap_future()` used in executors
3. Check for transaction rollback messages
4. Verify LiteLLM model configuration

### If Form Data Not Accessible:
1. Verify asset_id in submission console log
2. Check database: `SELECT * FROM migration.collected_data WHERE asset_id = '[UUID]'`
3. Verify assessment flow can query collected data
4. Check agent input builders include collected data

---

## References

- **Fix #1:** asyncio.wrap_future() in assessment executors
  - Files: `risk_executor.py`, `complexity_executor.py`, `tech_debt_executor.py`, `sixr_executor.py`

- **Fix #2:** Flexible tool parameters for data validation
  - File: `base_tools.py`

- **Fix #3:** Transaction rollback for missing servers table
  - File: `readiness_queries.py`

- **Fix #4:** Phase results transaction recovery
  - File: `phase_results.py`

- **Fix #5:** UUID-to-name resolution in questionnaires
  - Files: `useAdaptiveFormFlow.ts`, `formDataTransformation.ts`

---

## Success Criteria

All tests PASS when:
- [ ] Asset names display correctly (no UUIDs)
- [ ] Forms submit with correct asset_id
- [ ] Assessment flow auto-initializes
- [ ] Agents create without errors
- [ ] Phase progression works correctly
- [ ] Collected data accessible to agents
- [ ] No console errors (401, 422, asyncio)
- [ ] End-to-end flow completes in < 30 seconds
