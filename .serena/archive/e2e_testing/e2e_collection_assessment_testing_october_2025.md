# E2E Collection-to-Assessment Flow Testing - October 2025

## Session Context
**Date**: October 23, 2025
**Branch**: `fix/security-tenant-filtering-week1-foundation-20251023`
**Goal**: Create comprehensive E2E Playwright tests for collection-to-assessment workflow that validate UUID-to-name resolution (Fix #5 regression detection)

## Critical Learnings

### 1. Dynamic Asset Selection in Playwright Tests
**Problem**: Hardcoded asset names cause tests to fail with different datasets, especially when QA teams run locally.

**Solution**: Extract asset names dynamically from page content using regex patterns:
```typescript
// STEP 1: Extract the first asset name BEFORE clicking anything
selectedAssetName = await page.evaluate(() => {
  const pageText = document.body.innerText;

  // Pattern: asset name followed by "Asset ID:"
  const matches = pageText.matchAll(/^(.+?)\s*Asset ID:\s*[a-f0-9-]+$/gm);

  for (const match of matches) {
    let name = match[1].trim();
    name = name.replace(/Discovered\s*$/i, '').trim();

    if (name &&
        name.length < 50 &&
        !name.includes('Asset Selection') &&
        !name.includes('Select')) {
      return name;
    }
  }
  return null;
});
```

**Why Important**:
- Tests work with ANY dataset
- No maintenance needed when test data changes
- QA teams can run locally without modifications

### 2. Avoiding "Select All" in Checkbox Lists
**Problem**: Tests accidentally clicking "Select All" checkbox instead of individual item checkboxes, leading to wrong test behavior.

**Solution**: Filter checkboxes by parent element content to exclude "Select All":
```typescript
// STEP 2: Click ONLY the first asset checkbox (not "Select All")
const firstAssetCheckbox = await page.evaluateHandle(() => {
  const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));

  const assetCheckboxes = checkboxes.filter(cb => {
    const id = cb.id || '';
    const parent = cb.closest('div, li, tr');
    const parentText = parent?.textContent || '';

    // Exclude "Select All"
    if (id.toLowerCase().includes('select') && id.toLowerCase().includes('all')) return false;
    if (parentText.includes('Select All')) return false;

    // Include only asset checkboxes
    if (parentText.includes('Asset ID:')) return true;
    return false;
  });

  return assetCheckboxes[0] || null;
});

await firstAssetCheckbox.click();
```

**Why Important**:
- Ensures precise test targeting
- Prevents accidental bulk operations
- Makes test behavior predictable

### 3. Proper Wait Strategy for Async Data Loading
**Problem**: Tests clicking buttons before async operations complete, causing failures or incorrect behavior.

**Solution**: Multi-layer wait strategy - Page load → Data ready → UI stabilization:
```typescript
// STEP 3: Wait for gaps to fully load before proceeding
console.log('⏳ Waiting for gap analysis to complete...');

await page.waitForSelector('text=Gap Analysis', { timeout: 15000 });

// Wait for gaps to finish loading
await page.waitForFunction(
  () => {
    const bodyText = document.body.textContent || '';
    const hasGaps = document.querySelectorAll('[data-testid*="gap"]').length > 0;
    const hasNoGapsMessage = bodyText.includes('no gaps') || bodyText.includes('No gaps');
    const hasLoadingText = bodyText.includes('Loading') || bodyText.includes('Analyzing');

    return (hasGaps || hasNoGapsMessage) && !hasLoadingText;
  },
  { timeout: 30000 }
);

await page.waitForTimeout(2000); // Extra time for UI to stabilize
```

**Why Important**:
- Prevents race conditions
- Ensures data is fully loaded before interactions
- Reduces flaky test failures

### 4. Network Noise Handling in SPAs with Polling
**Problem**: `waitForLoadState('networkidle')` never completes in apps with polling, keep-alive, or WebSocket connections.

**Solution**: Replace with `load` + explicit timeout pattern:
```typescript
// ❌ BEFORE - Never completes due to polling
await page.waitForLoadState('networkidle');

// ✅ AFTER - Works reliably
await page.waitForLoadState('load');
await page.waitForTimeout(1000);
```

**Applied Throughout**: All 15+ navigation points in test file.

**Why Important**:
- Tests complete successfully instead of hanging
- Works with modern SPAs that have background polling
- Railway deployment (WebSocket-free, HTTP polling) compatible

### 5. Regex Pattern for Extracting Label-Value Pairs
**Pattern**: Extract structured data from unstructured page text without relying on specific DOM structure:
```typescript
// Pattern: Label followed by value (e.g., "Asset ID: abc-123")
const matches = pageText.matchAll(/^(.+?)\s*Asset ID:\s*[a-f0-9-]+$/gm);
```

**Use Cases**:
- Asset names extraction
- ID extraction
- Any label-value pair in UI

**Why Important**:
- Resilient to DOM structure changes
- Works across different UI frameworks
- Easy to adapt for other label-value patterns

## Navigation Pattern Discovery

### Modal-Based Flow Creation
**Discovery**: Collection flows start via Collection → Overview → New Flow → Modal selection (not by deleting existing flows).

**Implementation**:
```typescript
// Navigate to Collection -> Overview to start a new flow
await page.click('text=Collection');
await page.waitForTimeout(500);
await page.click('text=Overview');
await page.waitForLoadState('load');

// Click "New Flow" button
const newFlowButton = await page.$('button:has-text("New Flow")');
await newFlowButton.click();

// Select "1-50 applications → Adaptive Forms" in modal
const adaptiveFormsRadio = await page.$('text=1-50 applications');
await adaptiveFormsRadio.click();

// Click "Start Collection" button
const startCollectionButton = await page.$('button:has-text("Start Collection")');
await startCollectionButton.click();
```

**Why Important**: Reflects actual user workflow, no need to delete test data between runs.

## Button Visibility Pattern

### Scrolling for Below-the-Fold Buttons
**Problem**: Buttons not visible without scrolling cause test timeouts.

**Solution**: Scroll to bottom before clicking:
```typescript
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
await page.waitForTimeout(1000);
```

**Why Important**: Ensures all interactive elements are visible and clickable.

## Test Configuration

### Correct Login Credentials
```typescript
const TEST_CONFIG = {
  baseUrl: 'http://localhost:8081',
  credentials: {
    username: 'demo@demo-corp.com',
    password: 'Demo123!',  // Case-sensitive, includes exclamation mark
  },
  context: {
    organization: 'Democorp',
    engagement: 'Cloud Migration 2024',
  },
  timeouts: {
    login: 5000,
    navigation: 10000,
    gapAnalysis: 5000,
    formSubmit: 5000,
    agentInit: 3000,
  },
};
```

## Regression Detection

### UUID-to-Name Resolution (Fix #5)
**What to Detect**: Asset names showing as "app-new" or UUID instead of actual names.

**Test Validation**:
```typescript
// 1. Extract asset name from asset selection page
const selectedAssetName = await page.evaluate(/* ... */);

// 2. Verify it appears correctly in questionnaire (not as "app-new" or UUID)
const questionnaireHeader = await page.textContent('h2, h3, [data-testid="questionnaire-header"]');
expect(questionnaireHeader).toContain(selectedAssetName);
expect(questionnaireHeader).not.toContain('app-new');
expect(questionnaireHeader).not.toMatch(/[a-f0-9-]{36}/); // No UUID
```

**Why Important**: Prevents regression of critical bug where UUIDs displayed instead of user-friendly names.

## Files Delivered

### Test Files (570+ lines)
1. **`tests/e2e/collection-to-assessment-flow.spec.ts`** - Main E2E test suite (570+ lines)
2. **`tests/e2e/diagnostic-login.spec.ts`** - Login verification diagnostic tool (110 lines)

### Documentation (1,400+ lines)
1. **`docs/testing/E2E_COLLECTION_TO_ASSESSMENT_FLOW.md`** - Manual testing guide (495 lines)
2. **`tests/e2e/README-COLLECTION-ASSESSMENT.md`** - Usage documentation (484 lines)
3. **`docs/testing/PLAYWRIGHT_TEST_FIXES.md`** - Test fixes documentation (300+ lines)
4. **`docs/testing/E2E_FINAL_STATUS.md`** - Final status report
5. **`docs/testing/E2E_TEST_STATUS.md`** - Progress tracking

**Total**: 3,138 lines of tests and documentation

## Key Achievements

✅ **100% Login Authentication Working** - Credentials resolved
✅ **100% Network Noise Fixed** - All `networkidle` replaced with `load` + timeout
✅ **100% Navigation Working** - Collection → Overview → New Flow → Modal selection
✅ **100% Modal Handling** - Flow type selection working
✅ **100% Flow Creation** - Successfully creates collection flows
✅ **100% Asset Selection** - Dynamic extraction, no hardcoded names
✅ **100% Async Data Handling** - Proper waits for gaps and questionnaires
✅ **100% Regression Detection** - Validates UUID-to-name resolution (Fix #5)

## Git Integration

### Branch Workflow
- **Branch**: `fix/security-tenant-filtering-week1-foundation-20251023`
- **PR**: Approved and merged
- **Commit Message**: Comprehensive description of features and fixes

### Commit Pattern Used
```bash
git add tests/e2e/collection-to-assessment-flow.spec.ts
git add tests/e2e/diagnostic-login.spec.ts
git add docs/testing/*

git commit -m "$(cat <<'EOF'
feat: Add comprehensive E2E tests for collection-to-assessment workflow

Implemented end-to-end Playwright tests to validate collection flow, gap analysis,
and questionnaire generation with proper UUID-to-name resolution.

Key Features:
- Dynamic asset name extraction (no hardcoded values)
- Correct single-asset selection (not "Select All")
- Proper wait handling for gaps and questionnaire generation
- Validates Fix #5: UUID-to-name resolution in questionnaire headers
- Comprehensive documentation and usage guides

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Running the Tests

### Full Test Suite
```bash
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts
```

### Specific Test
```bash
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts \
  --grep "should display asset name"
```

### Debug Mode (Headed Browser)
```bash
npx playwright test tests/e2e/collection-to-assessment-flow.spec.ts --headed --debug
```

### Diagnostic Login Test
```bash
npx playwright test tests/e2e/diagnostic-login.spec.ts
```

## Common Pitfalls to Avoid

❌ **Don't**: Hardcode asset names or IDs
✅ **Do**: Extract dynamically from page content

❌ **Don't**: Click "Select All" when testing single-item operations
✅ **Do**: Filter checkboxes by parent content to find specific items

❌ **Don't**: Use `waitForLoadState('networkidle')` in apps with polling
✅ **Do**: Use `waitForLoadState('load')` + explicit timeout

❌ **Don't**: Click buttons immediately after page load
✅ **Do**: Wait for data to finish loading using `waitForFunction`

❌ **Don't**: Assume buttons are visible
✅ **Do**: Scroll to reveal below-the-fold elements

## Future Enhancements

### Potential Additions
1. Test data cleanup utilities
2. Multi-browser testing (Chrome, Firefox, Safari)
3. Visual regression testing with screenshots
4. Performance metrics collection
5. Parallel test execution

### Pattern Extensions
- Reuse dynamic extraction pattern for other flows (discovery, assessment)
- Apply wait strategies to other E2E tests
- Create shared utilities for common operations

## References

- **Fix #5**: UUID-to-name resolution bug in questionnaire headers
- **ADR-010**: Docker-First Development Mandate
- **Railway Deployment**: WebSocket-free, HTTP polling only
- **Playwright Docs**: https://playwright.dev/
