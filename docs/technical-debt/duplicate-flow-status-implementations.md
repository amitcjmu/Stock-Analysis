# Duplicate Flow Status Implementations - Technical Debt

## Overview
The codebase has multiple, inconsistent implementations of flow status handling, particularly around the `waiting_for_approval` state. This causes bugs where some components continue polling unnecessarily while others correctly stop.

## The Problem

### 1. Multiple API Endpoints
- **Legacy Discovery Flow API**: `/api/v1/discovery/flows/{flow_id}/status`
  - Uses proper response mappers
  - Correctly returns `awaiting_user_approval` field
  - Located in: `/backend/app/api/v1/endpoints/discovery_flows/`

- **Master Flow API**: `/api/v1/flows/{flow_id}/status`
  - Missing response mapper
  - Doesn't return `awaiting_user_approval` field
  - Located in: `/backend/app/api/v1/flows.py`

### 2. Inconsistent Frontend Hooks
- **SimplifiedFlowStatus.tsx**: ✅ Correctly stops polling for `waiting_for_approval`
- **useUnifiedDiscoveryFlow.ts**: ❌ Missing check for `waiting_for_approval`
- **useCMDBImport.ts**: ❌ Missing handling for `waiting_for_approval` status

### 3. Duplicate Status Indicators
- `status: "waiting_for_approval"` (string)
- `awaiting_user_approval: true` (boolean in JSONB)
- `awaitingUserApproval` (camelCase in API responses)
- Different components check different fields

## Existing Implementations

### Backend
```python
# Already exists in response_mappers.py:
awaiting_approval = flow.crewai_state_data.get("awaiting_user_approval", False)

# Already exists in status_calculator.py:
if flow_status == FlowStatus.WAITING_FOR_APPROVAL:
    return flow_status  # Preserve waiting status
```

### Frontend
```typescript
// Already exists in SimplifiedFlowStatus.tsx:
const shouldPoll = 
  (flowStatus.status === 'running' || flowStatus.status === 'processing' || flowStatus.status === 'active') &&
  !flowStatus.awaiting_user_approval &&
  flowStatus.status !== 'waiting_for_approval' &&
  // ... other conditions
```

## The Root Cause

When migrating from session-based to flow-based architecture (Phase 5), new endpoints were created without:
1. Reusing existing response mappers
2. Maintaining consistency with existing field names
3. Updating all frontend hooks to use the new endpoints properly

## Recommended Fix

### Short Term (Quick Fix)
1. Add `waiting_for_approval` check to `useUnifiedDiscoveryFlow.ts` ✅ (Done)
2. Use existing response mapper in master flow endpoints

### Long Term (Proper Fix)
1. **Consolidate to One API**: Use only master flow endpoints
2. **Standardize Response Format**: All endpoints return same fields
3. **Create Shared Utilities**:
   ```typescript
   // utils/flowStatus.ts
   export const shouldPollFlow = (status: FlowStatus): boolean => {
     const activeStates = ['running', 'processing', 'active'];
     const terminalStates = ['completed', 'failed', 'cancelled', 'waiting_for_approval'];
     
     return activeStates.includes(status.status) && 
            !status.awaitingUserApproval &&
            !terminalStates.includes(status.status);
   };
   ```
4. **Remove Duplicate Code**: Use shared utility everywhere

## Impact

This duplication causes:
- Unnecessary API calls (polling continues when it shouldn't)
- Confusion for developers (which field to check?)
- Bugs when new features don't implement all checks
- Increased maintenance burden

## Lessons Learned

1. **Always search for existing implementations** before creating new ones
2. **Maintain a single source of truth** for business logic
3. **Document API contracts** clearly
4. **Use shared utilities** for common patterns
5. **Complete migrations fully** - don't leave old and new systems running in parallel

---

*Last Updated: 2025-07-14*
*Related Issues: Perpetual polling, field mapping approval stuck*