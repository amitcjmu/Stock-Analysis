# Playwright QA Agent: Browser Automation Requirements

## Problem
QA agent (qa-playwright-tester) defaults to curl commands and log inspection instead of visual browser testing, missing frontend crashes and console errors.

## Solution
Explicitly instruct agent to use Playwright browser automation with visual verification.

## Required Instructions Pattern

When invoking `qa-playwright-tester` agent:

```markdown
CRITICAL REQUIREMENT: USE BROWSER AUTOMATION

You MUST use Playwright browser automation for ALL testing. Do NOT rely solely on curl commands or backend logs.

### Required Actions:
1. ✅ Navigate pages with `mcp__playwright__browser_navigate`
2. ✅ Take screenshots with `mcp__playwright__browser_take_screenshot`
3. ✅ Check console errors with `mcp__playwright__browser_console_messages`
4. ✅ Monitor network requests with `mcp__playwright__browser_network_requests`
5. ✅ Click elements and fill forms with browser interactions
6. ✅ Capture visual state at each test step

### Do NOT:
❌ Skip browser tests in favor of curl
❌ Assume API success means UI works
❌ Skip console error checks

### Test Each Feature:
- Navigate to page via browser
- Screenshot initial state
- Interact with UI elements
- Check console for errors
- Verify API responses in Network tab
- Screenshot final state
```

## Example Test Workflow

```markdown
# Test: Assessment Overview Page

## Step 1: Navigate and Screenshot
- Navigate to: http://localhost:8081/assess/overview
- Screenshot: assessment-overview-initial.png
- Check console: No errors expected

## Step 2: Verify Application Groups Widget
- Locate: ApplicationGroupsWidget component
- Verify: Canonical application names display
- Verify: Asset counts accurate
- Screenshot: application-groups-expanded.png

## Step 3: Check Network Requests
- Monitor: GET /api/v1/master-flows/{flow_id}/assessment-applications
- Verify: 200 OK response
- Verify: Response structure matches TypeScript interface

## Step 4: Verify Console
- Check: `mcp__playwright__browser_console_messages(onlyErrors: true)`
- Expected: No TypeError, no API errors
```

## Why Browser Automation Is Required

| Testing Method | What It Catches | What It Misses |
|----------------|-----------------|----------------|
| **curl + logs** | Backend errors, API failures | Frontend crashes, console errors, visual bugs |
| **Browser automation** | ✅ All of the above + UI state, visual rendering, client-side errors | - |

## Common Issues Found Only with Browser Testing
1. **Frontend Crashes**: `TypeError: Cannot read properties of undefined`
2. **Console Errors**: React rendering errors, API contract mismatches
3. **Network Failures**: 404s from frontend code not visible in backend logs
4. **Visual Bugs**: Empty states, missing data, broken layouts
5. **State Management**: Client-side caching issues, stale data

## When to Use This Pattern
- **All E2E testing** with qa-playwright-tester agent
- **Bug verification** after fixes
- **Regression testing** before PR merges
- **Feature validation** for frontend changes

## Related Session
- Session Date: October 16, 2025
- Issue: QA agent relied on curl, missed frontend crash
- Fix: Explicit browser automation instructions
- Result: Found P0 bug (TypeError on assessment page)

## Tool References
- `mcp__playwright__browser_navigate` - Page navigation
- `mcp__playwright__browser_take_screenshot` - Visual capture
- `mcp__playwright__browser_console_messages` - Error checking
- `mcp__playwright__browser_network_requests` - API monitoring
- `mcp__playwright__browser_click` - UI interaction

## Success Metrics
After applying this pattern, QA agent should:
- Generate 5-10 screenshots per test flow
- Check console errors at each step
- Monitor all API requests
- Detect frontend crashes before production
- Provide visual evidence of bugs
