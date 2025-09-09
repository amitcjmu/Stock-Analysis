# Headed Browser Testing Patterns for Debugging

## When to Use Headed Mode
- Tests timeout in headless but need to see why
- Debugging blocking flows and user journeys
- Validating UI element visibility issues
- Understanding redirect chains

## Running Tests in Headed Mode

### Playwright Command
```bash
# Run specific test in headed mode
npx playwright test path/to/test.spec.ts --headed --reporter=list

# With specific browser
npx playwright test --headed --browser=chromium

# Keep browser open after test
npx playwright test --headed --debug
```

### Debug Test Pattern
```typescript
test('Debug user journey', async ({ page }) => {
  // Set longer timeout for observation
  test.setTimeout(120000);
  
  // Take screenshots at each step
  await page.screenshot({ path: 'debug-1-login.png' });
  
  // Log detailed information
  console.log(`📍 Current URL: ${page.url()}`);
  
  // Check element visibility with logging
  const element = page.locator('[data-testid="blocking-flow"]');
  const isVisible = await element.isVisible().catch(() => false);
  console.log(`Element visible: ${isVisible}`);
  
  // Keep browser open for observation
  await page.waitForTimeout(10000);
});
```

## Visual Debugging Techniques

### 1. Progressive Screenshots
```typescript
await page.screenshot({ path: 'step-1-before-action.png' });
await page.click('button');
await page.screenshot({ path: 'step-2-after-action.png' });
```

### 2. Console Logging Navigation
```typescript
page.on('framenavigated', () => {
  console.log(`Navigated to: ${page.url()}`);
});
```

### 3. Element State Checking
```typescript
const buttons = ['Continue', 'Next', 'Save'];
for (const btnText of buttons) {
  const btn = page.locator(`button:has-text("${btnText}")`);
  if (await btn.count() > 0) {
    const enabled = await btn.isEnabled();
    console.log(`${btnText}: ${enabled ? 'ENABLED' : 'DISABLED'}`);
  }
}
```

## Key Insights
- Headed mode reveals timing issues not visible in headless
- Visual confirmation helps identify wrong selectors
- Browser stays open with debug flag for manual inspection
- Screenshots provide evidence of test state at failure point