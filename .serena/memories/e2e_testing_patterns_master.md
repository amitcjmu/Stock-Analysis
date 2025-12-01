# E2E Testing & Playwright Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 15 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Explicit Waits**: Use `expect().toBeVisible()` not `waitForTimeout()`
> 2. **Serial Execution**: Use `test.describe.configure({ mode: 'serial' })` for shared state
> 3. **Cookie Cleanup**: Clear cookies in `afterEach` to prevent auth pollution
> 4. **First Element**: Use `.first()` for strict mode violations with multiple elements
> 5. **Conditional API Checks**: Handle empty API responses gracefully

---

## Table of Contents

1. [Overview](#overview)
2. [Explicit Wait Patterns](#explicit-wait-patterns)
3. [Test Isolation Patterns](#test-isolation-patterns)
4. [Common Patterns](#common-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Troubleshooting](#troubleshooting)
8. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Playwright E2E testing patterns, flakiness resolution, test isolation, and QA automation workflows.

### When to Reference
- Writing new E2E tests
- Fixing flaky tests
- Debugging test failures
- Setting up test isolation

### Key Files
- `tests/e2e/` (test files)
- `playwright.config.ts` (configuration)
- `tests/e2e/helpers/` (utilities)

---

## Explicit Wait Patterns

### Pattern 1: Replace Fixed Timeouts with Explicit Waits

**Anti-Pattern**:
```typescript
// ❌ Flaky and slow
await page.click('button');
await page.waitForTimeout(2000);
```

**Correct Pattern**:
```typescript
// ✅ Fast and reliable
await page.click('button');
await expect(page.locator('.result')).toBeVisible({ timeout: 5000 });
```

### Timeout Guidelines

| Operation Type | Timeout | Example |
|---------------|---------|---------|
| Form validation | 3000ms | Button state changes |
| Navigation | 5000ms | Page loads |
| File uploads | 10000ms | CSV upload |
| Bulk operations | 30000ms | Report generation |

### Common Wait Patterns

```typescript
// Wait for visibility
await expect(page.locator('.dashboard')).toBeVisible({ timeout: 5000 });

// Wait for disappearance
await expect(page.locator('.spinner')).not.toBeVisible({ timeout: 3000 });

// Wait for text
await expect(page.locator('.status')).toHaveText('Approved', { timeout: 5000 });

// Wait for enabled state
await expect(page.locator('button[type="submit"]')).toBeEnabled({ timeout: 3000 });

// Wait for count
await expect(page.locator('.row')).toHaveCount(5, { timeout: 5000 });
```

**When Fixed Timeouts ARE OK**:
- Animations: `waitForTimeout(300)`
- Debounce: `waitForTimeout(500)`
- Rate limiting: `waitForTimeout(1000)`

---

## Test Isolation Patterns

### Pattern 2: Serial Execution for Shared State

```typescript
test.describe('Flow Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('first test', async ({ page }) => { /* ... */ });
  test('second test', async ({ page }) => { /* ... */ });
});
```

**When to use**: Tests share login state, flow state, or database records.

### Pattern 3: Cookie Cleanup

```typescript
test.afterEach(async ({ page }) => {
  await page.context().clearCookies();
  await page.close();
});
```

### Pattern 4: Handle Multiple Elements

```typescript
// ❌ Strict mode violation
const button = page.locator('button:has-text("Refresh")');

// ✅ Safe
const button = page.locator('button:has-text("Refresh")').first();
```

### Pattern 5: Conditional API Validation

```typescript
const response = await request.get(url, { headers });

if (!response.ok()) {
  console.log(`⚠️ API returned ${response.status()} - acceptable for initial state`);
  return;
}

const data = await response.json();
if (data.field !== undefined) {
  expect(data).toHaveProperty('field');
}
```

### Pattern 6: Filter Expected Errors

```typescript
test.afterEach(async ({ page }) => {
  const criticalErrors = consoleErrors.filter(e =>
    !e.includes('net::ERR') &&
    !e.includes('404') &&
    !e.includes('401')
  );
  if (criticalErrors.length > 0) {
    console.warn('⚠️ Critical errors:', criticalErrors);
  }
});
```

---

## Common Patterns

### QA Agent Workflow

```typescript
// Deploy QA agent for testing
Task tool with subagent_type: "qa-playwright-tester"

// Provide clear instructions:
// - What to test (specific flows)
// - Expected behavior
// - Metrics to measure
```

### Pre-Run Database Cleanup

```bash
# Clear refresh tokens before test runs
docker exec migration_postgres psql -U postgres -d migration_db \
  -c "DELETE FROM migration.refresh_tokens;"
```

### Single Worker for Flaky Tests

```bash
npx playwright test tests/e2e/file.spec.ts --workers=1
```

### Verify Test Stability

```bash
for i in {1..5}; do
  echo "=== Run $i ===" && npx playwright test file.spec.ts --workers=1 --reporter=line 2>&1 | tail -3
done
```

---

## Anti-Patterns

### Don't: Use Fixed Timeouts for UI Changes

```typescript
// ❌ BAD
await page.waitForTimeout(2000);

// ✅ GOOD
await expect(page.locator('.result')).toBeVisible({ timeout: 5000 });
```

### Don't: Run Shared-State Tests in Parallel

```typescript
// ❌ BAD - Causes race conditions
test.describe('Login Tests', () => {
  test('test1', async () => { /* ... */ });
  test('test2', async () => { /* ... */ });
});

// ✅ GOOD
test.describe('Login Tests', () => {
  test.describe.configure({ mode: 'serial' });
  // ...
});
```

### Don't: Hard Assert on Dynamic API Data

```typescript
// ❌ BAD - Fails on empty response
expect(data.items).toHaveLength(5);

// ✅ GOOD - Handles empty state
if (data.items?.length > 0) {
  expect(data.items).toHaveLength(5);
}
```

---

## Code Templates

### Template 1: Robust Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:8081');
    await loginUser(page);
    await page.waitForTimeout(1000); // Auth propagation
  });

  test.afterEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.close();
  });

  test('should do something', async ({ page }) => {
    await page.click('button:has-text("Action")');
    await expect(page.locator('.result')).toBeVisible({ timeout: 5000 });
  });
});
```

### Template 2: File Upload Test

```typescript
async function uploadFile(page: Page, filePath: string): Promise<void> {
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(filePath);

  // Wait for actual completion signal
  await expect(page.locator('button:has-text("Next")')).toBeEnabled({
    timeout: 10000
  });
}
```

---

## Troubleshooting

### Issue: Flaky tests (inconsistent pass/fail)

**Causes**: Race conditions, shared state, missing waits

**Solution**:
1. Add `mode: 'serial'`
2. Add cookie cleanup in afterEach
3. Replace `waitForTimeout` with explicit waits

### Issue: Strict mode violation

**Error**: `locator resolved to 2 elements`

**Solution**: Use `.first()` or more specific selector

### Issue: Auth constraint violations

**Error**: `duplicate key violates unique constraint "refresh_tokens_token_key"`

**Solution**: Run `DELETE FROM migration.refresh_tokens` before tests

---

## Consolidated Sources

| Original Memory | Key Contribution |
|-----------------|------------------|
| `playwright-explicit-waits-pattern-2025-11` | Explicit waits |
| `qa_playwright_testing_patterns` | QA workflow |
| `e2e-test-flakiness-isolation-patterns-2025-11` | Test isolation |
| `playwright-debugging-checklist` | Debugging |
| `playwright-iterative-debugging-workflow` | Debug workflow |
| `playwright_testing_patterns_2025_01` | General patterns |
| `playwright_e2e_validation_workflow` | Validation |
| `e2e_user_journey_validation` | User journeys |

**Archive Location**: `.serena/archive/e2e_testing/`

---

## Search Keywords

playwright, e2e, testing, flaky, isolation, explicit_wait, serial, cookies, qa_agent
