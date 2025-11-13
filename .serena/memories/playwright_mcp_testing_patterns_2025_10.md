# Playwright MCP Browser Testing Patterns

**Context**: Browser-based testing using Playwright MCP tools for web application validation
**Date**: October 2025
**Tools**: mcp__playwright__browser_* family

## Problem
Need to test web applications interactively through browser automation for QA validation.

## MCP Playwright Tools Overview

### Navigation & Setup
```javascript
// Navigate to URL
mcp__playwright__browser_navigate(url="http://localhost:8081")

// Take snapshot (accessibility tree view)
mcp__playwright__browser_snapshot()

// Take screenshot (visual capture)
mcp__playwright__browser_take_screenshot(filename="page.png")

// Close browser
mcp__playwright__browser_close()
```

### Interaction Patterns
```javascript
// Click element (requires element description + ref from snapshot)
mcp__playwright__browser_click(
  element="Sign In button",
  ref="e52"  // From accessibility snapshot
)

// Type text into input
mcp__playwright__browser_type(
  element="Email textbox",
  ref="e30",
  text="demo@demo-corp.com"
)

// Fill form (faster than type)
await page.getByRole('textbox', { name: 'Email' }).fill('demo@demo-corp.com');
```

### Waiting & Verification
```javascript
// Wait for text to appear
mcp__playwright__browser_wait_for(text="Login")

// Wait for element to disappear
mcp__playwright__browser_wait_for(textGone="Loading")

// Wait for time to pass
mcp__playwright__browser_wait_for(time=3)  // 3 seconds
```

### Console & Network Monitoring
```javascript
// Get console messages
mcp__playwright__browser_console_messages(onlyErrors=false)

// Get network requests
mcp__playwright__browser_network_requests()
```

## Testing Pattern: Login Flow

```javascript
// 1. Navigate
await mcp__playwright__browser_navigate(url="http://localhost:8081")

// 2. Wait for page load
await mcp__playwright__browser_wait_for(text="Sign In")

// 3. Take snapshot to get element refs
const snapshot = await mcp__playwright__browser_snapshot()

// 4. Fill credentials (use refs from snapshot)
await mcp__playwright__browser_type(
  element="Email textbox",
  ref="e30",  // From snapshot
  text="demo@demo-corp.com"
)

await mcp__playwright__browser_type(
  element="Password textbox",
  ref="e36",
  text="Demo123!"
)

// 5. Submit
await mcp__playwright__browser_click(
  element="Sign In button",
  ref="e52"
)

// 6. Verify success
const consoleMessages = await mcp__playwright__browser_console_messages()
// Check for: "Login Successful"
```

## Element Reference Pattern

**CRITICAL**: Always take snapshot first to get element `ref` values

```yaml
# Snapshot output shows:
- button "Sign In" [ref=e52] [cursor=pointer]

# Use ref in interaction:
mcp__playwright__browser_click(element="Sign In button", ref="e52")
```

**Why refs are required**:
- Playwright needs stable selectors
- Accessibility tree provides unique refs
- More reliable than CSS selectors

## Common Issues & Solutions

### Issue 1: Element Not Found
```
Error: locator.waitFor: Timeout 5000ms exceeded
```

**Solution**: Element may not be visible yet
```javascript
// Add wait before interaction
await mcp__playwright__browser_wait_for(text="Login")
// Then interact
```

### Issue 2: Wrong Element Ref
**Solution**: Always take fresh snapshot before interactions
```javascript
// ❌ WRONG: Using old ref
mcp__playwright__browser_click(element="button", ref="e52")

// ✅ CORRECT: Take snapshot first
const snapshot = await mcp__playwright__browser_snapshot()
// Use ref from current snapshot
```

### Issue 3: Page Not Loaded
**Solution**: Check page state in snapshot output
```yaml
Page state:
- Page URL: http://localhost:8081/login
- Page Title: AI powered Migration Orchestrator
```

## Testing Navigation Flow

```javascript
// 1. Login
await navigate_and_login()

// 2. Navigate to feature
await mcp__playwright__browser_click(
  element="Collection menu item",
  ref="e96"
)

// Submenu appears
const snapshot = await mcp__playwright__browser_snapshot()

// 3. Click submenu item
await mcp__playwright__browser_click(
  element="Adaptive Forms link",
  ref="e301"
)

// 4. Verify page loaded
const newSnapshot = await mcp__playwright__browser_snapshot()
// Check URL changed to /collection/adaptive-forms
```

## Console Monitoring Pattern

```javascript
// Navigate to page
await mcp__playwright__browser_navigate(url="http://localhost:8081/collection")

// Check for errors
const messages = await mcp__playwright__browser_console_messages(onlyErrors=true)

// Expected: Empty array (no errors)
// If errors found: Investigate and report
```

## Best Practices

1. **Always snapshot before interactions**
   - Get fresh refs for each page state
   - Verify element exists before clicking

2. **Use descriptive element names**
   ```javascript
   // ✅ Good
   element="Email textbox"

   // ❌ Bad
   element="input"
   ```

3. **Check console after navigation**
   ```javascript
   await navigate_to_page()
   const errors = await browser_console_messages(onlyErrors=true)
   if (errors.length > 0) {
     // Report errors
   }
   ```

4. **Close browser when done**
   ```javascript
   await mcp__playwright__browser_close()
   ```

5. **Monitor network requests for API testing**
   ```javascript
   await perform_action()
   const requests = await browser_network_requests()
   // Verify API calls made correctly
   ```

## Integration with QA Workflow

**Manual Testing** (5-10 minutes):
1. Navigate to application
2. Login with test credentials
3. Navigate to feature area
4. Verify basic functionality
5. Check console for errors

**Automated Testing** (via qa-playwright-tester agent):
- Comprehensive test coverage
- Defect reporting
- Screenshot capture on failures
- QA report generation

**Key Takeaway**: Use Playwright MCP tools for interactive browser testing. Always snapshot first, use refs from snapshot, and monitor console/network for errors.
