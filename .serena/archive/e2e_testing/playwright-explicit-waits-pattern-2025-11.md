# Playwright Explicit Waits Pattern (Anti-Pattern Elimination)

## Problem
Tests using arbitrary `page.waitForTimeout(2000)` are flaky (fail intermittently) and slow (always wait full duration even if UI updates faster).

## Solution
Replace fixed timeouts with explicit waits for specific UI state changes. Use Playwright's `expect()` assertions with timeout options.

## Anti-Pattern Example
```typescript
// ❌ BAD - Flaky and slow
async function uploadCSVFile(page: Page, filePath: string): Promise<void> {
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(filePath);

  // Arbitrary wait - might be too short (flaky) or too long (slow)
  await page.waitForTimeout(2000);
}
```

**Problems**:
- If upload takes > 2000ms, test fails
- If upload takes < 2000ms, test wastes time
- No indication of actual upload success
- Fails unpredictably on slow systems

## Correct Pattern
```typescript
// ✅ GOOD - Fast and reliable
async function uploadCSVFile(page: Page, filePath: string): Promise<void> {
  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(filePath);

  // Wait for actual UI state change indicating upload complete
  await expect(page.locator('button:has-text("Next")')).toBeEnabled({
    timeout: 10000
  });
}
```

**Benefits**:
- Fails fast if upload actually fails (no waiting)
- Proceeds immediately when upload succeeds
- Clear failure message: "Expected button to be enabled"
- Reliable across different system speeds

## Common Explicit Wait Patterns

### 1. Wait for Element Visibility
```typescript
// After navigation
await expect(page.locator('.dashboard')).toBeVisible({ timeout: 5000 });
```

### 2. Wait for Element to Disappear
```typescript
// After deletion
await expect(page.locator('.loading-spinner')).not.toBeVisible({ timeout: 3000 });
```

### 3. Wait for Text Content
```typescript
// After API call
await expect(page.locator('.status-badge')).toHaveText('Approved', { timeout: 5000 });
```

### 4. Wait for Button State
```typescript
// After form fill
await expect(page.locator('button[type="submit"]')).toBeEnabled({ timeout: 3000 });
```

### 5. Wait for Count
```typescript
// After bulk operation
await expect(page.locator('.table-row')).toHaveCount(5, { timeout: 5000 });
```

## Timeout Guidelines

```typescript
// Short operations (1-3s)
{ timeout: 3000 }  // Form validation, button state changes

// Medium operations (3-5s)
{ timeout: 5000 }  // Navigation, simple API calls

// Long operations (5-10s)
{ timeout: 10000 } // File uploads, complex API calls, data processing

// Very long operations (10-30s)
{ timeout: 30000 } // Report generation, bulk operations
```

## When Fixed Timeouts ARE Acceptable

Only use `waitForTimeout()` for:
1. **Animations**: `await page.waitForTimeout(300)` after opening dropdown
2. **Debounce testing**: `await page.waitForTimeout(500)` after typing in search
3. **Rate limiting**: `await page.waitForTimeout(1000)` between API calls

**Key Rule**: If waiting for a UI change that CAN be observed, use explicit wait.

## Migration Strategy

### Before (Flaky)
```typescript
await page.click('button:has-text("Submit")');
await page.waitForTimeout(2000);  // ❌ Hope data loaded
const text = await page.locator('.result').textContent();
```

### After (Reliable)
```typescript
await page.click('button:has-text("Submit")');
await expect(page.locator('.result')).toBeVisible({ timeout: 5000 });  // ✅ Wait for actual result
const text = await page.locator('.result').textContent();
```

## Debugging Failed Waits

If explicit wait times out, Playwright provides clear error:
```
Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
Locator: page.locator('button:has-text("Next")')
Expected: visible
Received: hidden
```

Much better than:
```
Error: Cannot find element 'button:has-text("Next")'
```

## Reference
- Applied in: `attribute-mapping-ag-grid.spec.ts` (Qodo Bot suggestion)
- Pattern source: Playwright Best Practices documentation
- Issue: Code quality improvement in PR #1101
