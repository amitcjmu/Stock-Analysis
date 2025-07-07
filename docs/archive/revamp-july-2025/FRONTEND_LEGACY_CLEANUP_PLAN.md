# Frontend Legacy API Cleanup Plan

## Current State (January 2025)

We've been patching legacy code instead of properly cleaning it up, creating more technical debt. This document identifies all legacy patterns that must be removed.

## Legacy Patterns to Remove

### 1. Direct Discovery API Calls (`/api/v1/discovery/*`)
These bypass the Master Flow Orchestrator and must be replaced:

| File | Legacy Pattern | Replace With |
|------|---------------|--------------|
| `useFlowOperations.ts` | `/api/v1/discovery/flow/${flowId}/resume` | `masterFlowService.resumeFlow(flowId)` |
| `useFlowOperations.ts` | `/api/v1/discovery/flow/${flowId}` (DELETE) | `masterFlowService.deleteFlow(flowId)` |
| `useDiscoveryFlowList.ts` | `/api/v1/discovery/flows/active` | `masterFlowService.getActiveFlows({ flowType: 'discovery' })` |
| `useDiscoveryDashboard.ts` | `/api/v1/discovery/metrics` | `masterFlowService.getFlowMetrics('discovery')` |
| `useDataCleansingAnalysis.ts` | `/discovery/flow/status/${flowId}` | `masterFlowService.getFlowStatus(flowId)` |
| `useRealTimeProcessing.ts` | `/api/v1/discovery/flow/status/${flow_id}` | `masterFlowService.getFlowStatus(flowId)` |
| `useTechDebtQueries.ts` | `/api/v1/discovery/tech-debt` | Remove or use master flow data |
| `MemoryKnowledgePanel.tsx` | `/api/v1/discovery/flow/memory/*` | Remove - not in master flow |
| `AgentCommunicationPanel.tsx` | `/api/v1/discovery/flow/communication/*` | Remove - not in master flow |
| `UploadBlocker.tsx` | `/api/v1/discovery/flow/${flowId}/complete` | `masterFlowService.completeFlow(flowId)` |

### 2. Session ID References
All `session_id` references must be replaced with `flow_id`:
- Already cleaned in most places
- Check `SessionComparisonMain.tsx` for admin usage

### 3. Mixed Hook Patterns
Replace multiple discovery hooks with single unified hook:

**Remove:**
- `useUnifiedDiscoveryFlow`
- `useDiscoveryFlow` 
- `useIncompleteFlowDetection`
- `useFlowResumption`
- `useFlowDeletion`

**Replace with:**
```typescript
import { useMasterFlow } from '@/hooks/useMasterFlow';

// Single hook for all flow operations
const { flow, operations } = useMasterFlow(flowId);
```

## Implementation Strategy

### Step 1: Create Master Flow Hook (2 hours)
```typescript
// src/hooks/useMasterFlow.ts
export const useMasterFlow = (flowId?: string) => {
  const { data: flow, mutate } = useSWR(
    flowId ? `/api/v1/flows/${flowId}/status` : null
  );
  
  const operations = {
    resume: () => masterFlowService.resumeFlow(flowId),
    delete: () => masterFlowService.deleteFlow(flowId),
    execute: (phase) => masterFlowService.executePhase(flowId, phase),
    complete: () => masterFlowService.completeFlow(flowId)
  };
  
  return { flow, operations, mutate };
};
```

### Step 2: Update All Components (4-6 hours)
Replace all legacy API calls with masterFlowService methods.

### Step 3: Remove Legacy Code (1 hour)
- Delete unused hooks
- Remove fallback patterns
- Clean up mixed API calls

## Success Criteria
1. NO direct `/api/v1/discovery/*` calls in frontend
2. NO session_id references
3. ALL flow operations go through Master Flow Orchestrator
4. Single source of truth for flow state

## Testing
1. Create flow
2. Resume flow
3. Delete flow
4. View flow status
5. Execute phase
6. Complete flow

All operations must use `/api/v1/flows/*` or `/api/v1/master-flows/*` endpoints only.

## Timeline
- **Day 1 Morning**: Create master flow hook and service updates
- **Day 1 Afternoon**: Update all components
- **Day 1 Evening**: Remove legacy code and test
- **Day 2**: Fix any remaining issues

## Note
DO NOT patch legacy code anymore. Replace it completely or leave it broken until we can replace it properly.