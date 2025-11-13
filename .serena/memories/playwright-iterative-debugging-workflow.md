# Iterative Debugging with Playwright E2E Testing

## Workflow Pattern
Use Playwright for comprehensive validation AFTER each fix attempt, not just at the end.

## Why This Works
- Catches incomplete fixes immediately
- Reveals hidden bugs (mixed state, race conditions)
- Provides concrete evidence (screenshots, localStorage, console logs)
- Tests real user flows, not just unit paths

## Iteration Cycle
```
1. Identify bug → 2. Apply fix → 3. Playwright test
                        ↓ FAIL
                  4. Analyze failure → 5. Refine fix → 6. Playwright test
                                                              ↓ PASS
                                                         7. Done
```

## Example from Session
**Bug**: Context switching not persisting

**Iteration 1**:
- Fix: Added `contextStorage.setContext()` calls
- Playwright Result: ❌ FAIL - engagement mismatch
- Discovery: Reading from wrong data source (React state vs API data)

**Iteration 2**:
- Fix: Use API data instead of React state
- Playwright Result: ❌ FAIL - mixed state (Demo client + Canada engagement)
- Discovery: Race condition with async state updates

**Iteration 3**:
- Fix: Pre-update context storage BEFORE calling switchEngagement()
- Playwright Result: ✅ PASS - 9/9 tests, all localStorage correct

## Playwright Test Structure
```typescript
// Test BOTH immediate state AND persistence
test('context persistence', async () => {
  // 1. Perform action
  await switchContext('Canada Life');

  // 2. Verify immediate localStorage state
  const before = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('auth_client'))
  );
  expect(before.id).toBe('canada-life-uuid');

  // 3. Test persistence
  await page.reload();

  // 4. Verify after refresh
  const after = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('auth_client'))
  );
  expect(after.id).toBe('canada-life-uuid');

  // 5. Verify consistency across keys
  const engagement = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('auth_engagement'))
  );
  expect(engagement.client_id).toBe('canada-life-uuid'); // Must match!
});
```

## Critical Verification Points
1. **Immediate state** - Check localStorage right after action
2. **Page refresh** - Does state persist?
3. **Cross-key consistency** - Do all related keys match?
4. **Backend alignment** - Check backend logs for RequestContext
5. **Console errors** - Any warnings or failures?

## When to Use Iterative Testing
- Multi-tenant context operations
- State synchronization bugs
- Race condition suspects
- Data persistence issues
- Complex user flows

## Tools
- `qa-playwright-tester` agent with detailed test objectives
- Screenshots for visual evidence
- localStorage inspection commands
- Backend log analysis
