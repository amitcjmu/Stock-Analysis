# isFlowTerminal Polling Pattern

## Context
Frontend polling hooks must detect all terminal flow states to stop polling properly. Hardcoding specific states leads to missed edge cases.

## Implementation Pattern

Use the **centralized `isFlowTerminal()` helper** from `flowStates.ts`:

```typescript
import { isFlowTerminal } from "@/constants/flowStates";

// In polling logic:
if (isFlowTerminal(flowStatus.status) && flowStatus.status !== "completed") {
  console.error(`Flow entered terminal state '${flowStatus.status}':`, flowStatus.message);
  clearInterval(pollingIntervalId);
  reject(new Error(`Flow ended with status '${flowStatus.status}': ${flowStatus.message}`));
  return;
}
```

## Why This Pattern

Previously, polling only checked for `"error"` or `"failed"`:
```typescript
// ❌ WRONG - Misses cancelled, aborted, deleted, archived
if (flowStatus.status === "error" || flowStatus.status === "failed") { ... }
```

The `isFlowTerminal()` helper is the **single source of truth** covering all terminal states:
- `completed`, `failed`, `cancelled`, `aborted`, `deleted`, `archived`

## Terminal States Definition

Located in `src/constants/flowStates.ts`:
```typescript
export const TERMINAL_STATES = [
  'completed', 'cancelled', 'failed', 'aborted', 'deleted', 'archived'
] as const;

export const isFlowTerminal = (status: string | undefined | null): boolean => {
  if (!status) return false;
  return TERMINAL_STATES.includes(status.toLowerCase() as typeof TERMINAL_STATES[number]);
};
```

## Location
- `src/hooks/collection/adaptive-form/usePolling.ts`
- `src/constants/flowStates.ts`

## Related
- All polling hooks should use `isFlowTerminal()` instead of hardcoded status checks
