# React State Race Condition Pattern in Context Switching

## Problem
When switching contexts in multi-tenant applications, async React state updates cause race conditions where stale state overwrites fresh localStorage data, creating mixed client/engagement states.

## Symptoms
- UI shows correct context immediately after switch
- localStorage contains mismatched client/engagement data
- Page refresh reverts to old context
- API calls use wrong tenant context
- Console logs claim success but data proves otherwise

## Root Cause Pattern
```typescript
// BAD: Race condition
setClient(newClient);              // React state update (ASYNC!)
persistClientData(newClient);      // Updates localStorage ✅
await switchEngagement();          // Reads from React state
  // Inside: client state NOT updated yet ❌
  // Uses OLD client value
  // Overwrites localStorage with stale data
```

## Solution Pattern
**Pre-update context storage BEFORE calling dependent functions**

```typescript
// GOOD: Pre-update context storage with fresh data
const currentContext = contextStorage.getContext() || {};
contextStorage.setContext({
  ...currentContext,
  client: fullClientData,  // Use API data, NOT React state
  timestamp: Date.now(),
  source: 'client_switch_before_engagement'
});

await switchEngagement(engagementId, engagementData);
// Now switchEngagement reads from context storage (correct!)
```

## Key Principle
**Context storage must be source of truth, not React state variables**

```typescript
// In dependent function (switchEngagement):
contextStorage.setContext({
  ...currentContext,
  client: currentContext.client || client,  // Trust storage first
  engagement: newEngagement,
  timestamp: Date.now()
});
```

## Verification
Test with Playwright:
1. Switch contexts (Demo → Canada Life)
2. Inspect localStorage immediately (should match new context)
3. Refresh page (should persist)
4. Check all localStorage keys match (client_id in engagement, user_context_selection)

## Files
- `src/contexts/AuthContext/services/authService.ts` (switchClient, switchEngagement)
- `src/contexts/AuthContext/storage.ts` (contextStorage, syncContextToIndividualKeys)

## When to Apply
Any time you have:
- Multi-step context operations with React state
- localStorage synchronization after state updates
- Dependent functions reading from React props/state
- Race conditions between async operations
