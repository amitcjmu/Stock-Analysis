# Playwright Runtime Validation Patterns

**Date**: October 27, 2025
**Context**: Runtime validation caught issues that code review missed

## Critical Insight
**Code review alone is insufficient.** Always validate fixes with Playwright in Docker environment.

## Validation Patterns by Issue Type

### 1. UI Polling/Loading State Issues
**Example**: Issue #806 - UI stuck in loading state

```typescript
// Validation approach
const validation = {
  navigate: "http://localhost:8081/collection/...",
  monitor: ["console logs", "UI transitions"],
  verify: [
    "automatic transition occurs",
    "no manual button click needed",
    "polling stops when ready"
  ]
}

// Evidence to capture
- Screenshot of successful transition
- Console logs showing polling behavior
- Time to interactive measurement
```

**Key Test**: Resume existing flow with ready state to verify automatic detection.

### 2. Console Error Issues
**Example**: Issue #807 - JavaScript TypeError

```typescript
// Validation approach
await page.goto("http://localhost:8081/collection/questionnaire");
const consoleErrors = [];
page.on('console', msg => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

// Interact with form
await page.click('input[type="checkbox"]');
await page.click('button[type="submit"]');

// Verify zero errors
assert(consoleErrors.length === 0);
assert(!consoleErrors.some(e => e.includes('response.json')));
```

**Key Test**: Trigger the exact user action that caused the original error.

### 3. Navigation/Redirect Issues
**Example**: Issue #808 - Wrong page shown

```typescript
// Validation approach
await page.goto("http://localhost:8081/assessment/tech-debt");
await page.waitForNavigation({ timeout: 5000 });

// Verify redirect
assert(page.url().includes('/assess/overview'));

// Verify no placeholder message
const placeholderText = await page.textContent('body');
assert(!placeholderText.includes('Integration In Progress'));
```

**Key Test**: Direct navigation to problematic URL and verify redirect.

### 4. React Warning Issues
**Example**: Issue #809 - TypeScript type warnings

```typescript
// Validation approach
const warnings = [];
page.on('console', msg => {
  if (msg.type() === 'warning') warnings.push(msg.text());
});

await page.goto("http://localhost:8081/assessment/[flowId]/...");

// Check for specific warning patterns
const reactWarnings = warnings.filter(w =>
  w.includes('non-boolean attribute') ||
  w.includes('jsx') ||
  w.includes('global')
);
assert(reactWarnings.length === 0);
```

**Key Test**: Load pages that use the fixed component, scan console.

### 5. Backend Calculation Issues
**Example**: Issue #810 - Progress calculation bug

```bash
# Validation approach (API + Database)

# 1. Query database for test data
docker exec migration_postgres psql -U postgres -d migration_db -c \
  "SELECT master_flow_id, progress, phase_results FROM assessment_flows WHERE phase_results IS NOT NULL LIMIT 5"

# 2. Call API endpoint
curl -H "X-Client-Account-ID: 1" -H "X-Engagement-ID: 1" \
  http://localhost:8000/api/v1/master-flows/{flow_id}/assessment-status

# 3. Compare results
# Database: progress=100, status='in_progress'
# API: progress_percentage=16, status='failed'  ✅ Correct recalculation
```

**Key Test**: Find flow with failed phases, verify API returns accurate progress.

## Evidence Collection Checklist

For each validation, capture:
- [ ] Screenshot of success state (`.playwright-mcp/issue-XXX-validation-*.png`)
- [ ] Console logs (filtered for errors/warnings)
- [ ] Backend logs (Docker logs for API calls)
- [ ] Database state (queries showing before/after)
- [ ] Network requests (verify API responses)
- [ ] Validation report (`tests/ISSUE_XXX_VALIDATION_RESULTS.md`)

## Docker Environment Setup

```bash
# Verify containers running
docker ps --filter "name=migration"

# Expected: 4 containers
# - migration_frontend (port 8081)
# - migration_backend (port 8000)
# - migration_postgres (port 5433)
# - migration_redis (port 6379)

# If not running
cd config/docker && docker-compose up -d
```

## Playwright MCP Usage

```typescript
// Navigate to page
await mcp__playwright__browser_navigate({
  url: "http://localhost:8081/..."
});

// Take snapshot (accessible tree for automation)
await mcp__playwright__browser_snapshot();

// Take screenshot (visual evidence)
await mcp__playwright__browser_take_screenshot({
  filename: "issue-XXX-validation.png"
});

// Get console messages
await mcp__playwright__browser_console_messages({
  onlyErrors: true
});

// Click elements
await mcp__playwright__browser_click({
  element: "Submit button",
  ref: "button[type='submit']"
});
```

## Common Validation Scenarios

### Scenario 1: Form Interaction
```typescript
// 1. Load form
// 2. Fill inputs
// 3. Submit
// 4. Verify: no console errors, form state updated, API called
```

### Scenario 2: Page Navigation
```typescript
// 1. Navigate to page A
// 2. Click link/button
// 3. Verify: redirect to page B, correct URL, content loaded
```

### Scenario 3: Polling Behavior
```typescript
// 1. Trigger async operation
// 2. Monitor console for polling logs
// 3. Verify: polling stops when complete, no infinite loops
```

### Scenario 4: Error States
```typescript
// 1. Trigger error condition (e.g., invalid input)
// 2. Verify: error message shown, no crashes, graceful handling
```

## Validation Report Structure

```markdown
# Issue #XXX Validation Results

## Executive Summary
- VALIDATION_STATUS: PASSED/FAILED
- Evidence: [list files]
- Confidence: XX%

## Test Environment
- Frontend: http://localhost:8081
- Backend: http://localhost:8000
- Database: PostgreSQL (port 5433)
- Browser: Chromium via Playwright

## Test Execution
1. Setup: [steps]
2. Test: [actions]
3. Verify: [checks]

## Results
- Expected: [behavior]
- Actual: [observed]
- Status: [PASS/FAIL]

## Evidence
- Screenshot: [path]
- Console logs: [captured]
- Backend logs: [relevant entries]
- Database state: [queries]

## Recommendation
[Production ready / Needs revision]
```

## When to Use Runtime Validation

**ALWAYS validate with Playwright for**:
- UI behavior changes (loading states, transitions)
- Form interactions (inputs, submissions)
- Navigation/routing changes (redirects, URL updates)
- Console error fixes (JavaScript errors)
- React component warnings (render issues)

**ALSO validate with API/Database for**:
- Backend calculation logic (progress, status)
- Data persistence (database writes)
- Multi-tenant scoping (client/engagement isolation)

## Success Criteria

Fix is production-ready when:
- ✅ Code review passed (syntax, patterns, types)
- ✅ Runtime validation passed (Playwright E2E)
- ✅ Evidence documented (screenshots, logs)
- ✅ No regressions detected (existing features work)
- ✅ Validation report created (comprehensive findings)

## Usage
Apply runtime validation to ALL code changes affecting user-facing behavior. Code review alone cannot catch runtime issues like race conditions, timing bugs, or environment-specific problems.
