# Playwright E2E Validation for Multi-Step Workflows

## Pattern: Validate Fix with Real Browser Testing

Used for validating bug #801 fix (questionnaire rendering) with actual user flow simulation.

## Complete E2E Test Flow

### 1. Navigate Through Application
```typescript
// Login
await mcp__playwright__browser_navigate({ url: "http://localhost:8081/login" });
await mcp__playwright__browser_snapshot();

// Find and click login elements from snapshot
await mcp__playwright__browser_click({
  element: "Email input field",
  ref: "textbox \"Email\""
});

// Collection flow start
await mcp__playwright__browser_navigate({
  url: "http://localhost:8081/collection"
});

// Asset selection (2 assets)
await mcp__playwright__browser_click({
  element: "First asset checkbox",
  ref: "checkbox \"1.9.3\""
});
```

### 2. Capture Console Logs for Debugging
```typescript
// Get console output during page operations
const consoleMessages = await mcp__playwright__browser_console_messages({
  onlyErrors: false
});

// Check for specific debug output
console.log("Console output:", consoleMessages);

// Look for:
// - "Converting questionnaire with questions: []" (bug symptom)
// - "Polling (elapsed: 5s / 720s)" (polling active)
// - "Status is ready but questions not yet available" (validation working)
```

### 3. Take Screenshots for Visual Verification
```typescript
// Capture current page state
await mcp__playwright__browser_take_screenshot({
  filename: "questionnaire-loading-state.png",
  fullPage: true
});

// Visual indicators to look for:
// ✅ Spinner animation visible
// ✅ "Generating Questionnaire" heading
// ✅ Status message showing time remaining
// ✅ "Check if Ready" button present
// ❌ Blank "app-new" form (bug symptom)
```

### 4. Verification Checklist

**Bug Symptom Identified** (First validation):
```
❌ Page shows blank form with "0/0 fields"
❌ Console: "Converting questionnaire with questions: []"
❌ Console: "Waiting for manual_collection phase (current: questionnaire_generation)"
```

**Fix Working** (Second validation):
```
✅ LoadingStateDisplay renders correctly
✅ Spinner and status message visible
✅ Console shows polling active during questionnaire_generation phase
✅ No blank form rendered
```

## Key Commands

### Start Browser Session
```typescript
// Browser automatically starts on first navigation
await mcp__playwright__browser_navigate({ url: "http://localhost:8081" });
```

### Fill Multi-Field Forms
```typescript
await mcp__playwright__browser_fill_form({
  fields: [
    {
      name: "Email field",
      type: "textbox",
      ref: "textbox \"Email\"",
      value: "admin@example.com"
    },
    {
      name: "Password field",
      type: "textbox",
      ref: "textbox \"Password\"",
      value: "password"
    }
  ]
});
```

### Wait for Async Operations
```typescript
// Wait for specific text to appear
await mcp__playwright__browser_wait_for({
  text: "Generating Questionnaire"
});

// Or wait for text to disappear
await mcp__playwright__browser_wait_for({
  textGone: "Loading..."
});
```

### Clean Up
```typescript
await mcp__playwright__browser_close();
```

## Validation Strategy

### 1. Reproduce the Bug First
- Run complete flow before applying fix
- Capture screenshots showing broken state
- Save console logs as evidence

### 2. Apply Fix and Verify
- Restart backend with new code
- Run same flow again
- Compare screenshots and console output

### 3. Document Evidence
- Store screenshots showing before/after
- Include console logs in commit message
- Reference specific error messages fixed

## When to Use Playwright for Validation

✅ **Use Playwright when**:
- Testing multi-step user workflows
- Verifying UI state changes
- Checking async loading/polling behavior
- Validating error handling in real browser
- Need visual proof of fix working

❌ **Don't use Playwright when**:
- Simple API endpoint testing (use curl/requests)
- Unit test coverage (use jest/pytest)
- Quick code verification (use linting/type checking)

## Common Issues

### Browser Not Installed
```bash
# If you get "browser not installed" error
mcp__playwright__browser_install()
```

### Element Not Found
```bash
# Always use browser_snapshot first to see available elements
await mcp__playwright__browser_snapshot();

# Use exact ref from snapshot output:
# ❌ ref: "login button"
# ✅ ref: "button \"Login\""
```

### Timing Issues
```bash
# Use wait_for instead of arbitrary timeouts
await mcp__playwright__browser_wait_for({ text: "Dashboard" });

# Not: await new Promise(resolve => setTimeout(resolve, 5000));
```

## Related Files
- `tests/e2e/collection-flow.spec.ts` - Automated E2E tests
- `docs/testing/PLAYWRIGHT_PATTERNS.md` - Additional patterns
