# window.location.reload() Anti-Pattern in React (CRITICAL - Nov 2025)

## Pattern Status: ❌ BANNED - DO NOT USE

## Summary
Using `window.location.reload()` in React components is an anti-pattern that causes:
1. **Infinite reload loops** - Component detects state change → triggers reload → re-initializes → detects state change → infinite loop
2. **Loss of React state** - All component state is destroyed on reload
3. **Poor user experience** - Full page refresh instead of smooth React re-render
4. **Backend load** - Repeated API calls on every reload cycle

## Historical Context

### Initial Problem (Nov 2025 - Bug #1102)
- PR #1100 introduced `window.location.reload()` as a "fix" for questionnaire rendering issues
- Qodo bot correctly warned this was an anti-pattern
- Previous CC agent dismissed the warning and kept the reload approach ❌ WRONG DECISION
- Result: Infinite reload loops at `/collection/adaptive-forms`

### Proper Fix (Commit 2234a5cd9)
- Removed ALL `window.location.reload()` calls from `useAdaptiveFormFlow.ts`
- Replaced with proper React state updates using `setState()`
- Result: Stable page, proper React rendering, no reload loops ✅

### Regression (Commit 035c4b872 - Qodo PR #1101)
- Qodo bot suggestions ADDED BACK the window.reload() calls
- Same anti-pattern re-introduced despite previous fix
- Result: Same infinite reload bug returned

### Second Fix (Nov 20, 2025)
- Removed window.reload() calls AGAIN from `useAdaptiveFormFlow.ts`
- This time created memory to prevent future regressions

## The Correct Pattern

### ❌ WRONG - Anti-Pattern
```typescript
// BAD: Causes infinite reload loops
const handleQuestionnaireReady = () => {
  toast({ title: "Questionnaire Ready" });
  setTimeout(() => {
    window.location.reload(); // ❌ NEVER DO THIS
  }, 500);
};
```

### ✅ CORRECT - React State Update
```typescript
// GOOD: Proper React state management
const handleQuestionnaireReady = () => {
  // Update state with form data and saved responses
  setTimeout(() => {
    setState((prev) => ({
      ...prev,
      formData: adaptiveFormData,
      formValues: existingResponses,
      questionnaires: questionnaires,
      isLoading: false,
      error: null
    }));
  }, 0);

  toast({
    title: "Questionnaire Ready",
    description: "Your adaptive form is now ready.",
  });
};
```

## Why setState() Works Better

1. **React Re-rendering**: Component re-renders with new state, no full page reload
2. **State Preservation**: Other component state remains intact
3. **No Reload Loops**: State updates don't trigger page reload → component initialization
4. **Better UX**: Smooth transition instead of jarring page refresh
5. **Performance**: No need to re-fetch all data, re-initialize all hooks

## Files Fixed

### Primary Fix
- `src/hooks/collection/useAdaptiveFormFlow.ts` (lines 237-252, 288-304)
  - Removed 2 instances of `window.location.reload()`
  - Replaced with `setState()` updates

### Other Files with window.reload() (Not Recently Changed)
These are older and may serve legitimate purposes (error recovery):
- `src/pages/collection/adaptive-forms/index.tsx:98` - handleQuestionnaireReady callback
- `src/pages/collection/adaptive-forms/index.tsx:699` - onRefresh error recovery
- `src/pages/collection/adaptive-forms/index.tsx:819` - onGenerationRetry error recovery
- `src/components/ErrorBoundary.tsx` - Error recovery mechanism
- `src/utils/toast.ts:146` - Error recovery action

**Note**: Error recovery is a legitimate use case for page reload. The anti-pattern specifically applies to **normal flow operations** like questionnaire rendering.

## Detection Criteria

### When window.reload() is WRONG:
1. In success callbacks after data fetching
2. After state updates that should trigger re-renders
3. In polling hooks when new data arrives
4. As a workaround for "state not updating" issues

### When window.reload() is ACCEPTABLE:
1. User-initiated "refresh" button
2. Error boundary recovery after crash
3. Authentication failure requiring re-login
4. Explicit "retry" action after failure

## Backend Impact

The infinite reload loop causes:
- Repeated API calls to `/api/v1/collection-crud-questionnaires/queries`
- Backend logs show same flow queried multiple times per second
- Database connection pool exhaustion under load

Example backend logs during reload loop:
```
2025-11-20 07:27:16,249 - INFO - Getting adaptive questionnaires for flow 42681138-fccd-4a78-92d6-28c27a88e254
2025-11-20 07:27:17,499 - INFO - Getting adaptive questionnaires for flow 42681138-fccd-4a78-92d6-28c27a88e254
2025-11-20 07:27:18,841 - INFO - Getting adaptive questionnaires for flow 42681138-fccd-4a78-92d6-28c27a88e254
```
(Same query every 1-2 seconds = reload loop)

## References
- Bug #1102: Original infinite reload bug
- Commit 2234a5cd9: First proper fix
- Commit 035c4b872: Qodo regression (re-added reloads)
- Current fix: Nov 20, 2025 - Second removal

## Rule for All Agents

**MANDATORY**: Before adding `window.location.reload()` or `window.reload()` to ANY React component:

1. ❓ Ask: "Is this an error recovery scenario?"
   - If NO → Use `setState()` instead
   - If YES → Proceed, but document why

2. ❓ Ask: "Am I working around a state update issue?"
   - If YES → Fix the state update logic, don't reload
   - If NO → Proceed

3. ❓ Ask: "Will this run after data fetching/polling?"
   - If YES → Use `setState()` instead
   - If NO → Proceed

4. ❓ Ask: "Have I checked Serena memory for this pattern?"
   - If NO → Read this memory first
   - If YES → Proceed

**IF IN DOUBT**: Use `setState()` instead of `window.location.reload()`

## Credits
- Qodo bot: Correctly identified anti-pattern (PR #1100)
- User: Identified regression and infinite reload bug
- CC Agent (2234a5cd9): Implemented proper React state fix
- This memory: Prevents third occurrence of same bug

## Status
- ✅ Fixed in useAdaptiveFormFlow.ts (Nov 20, 2025)
- 📝 Memory created to prevent future regressions
- ⚠️ May need to review other files listed above for similar issues
