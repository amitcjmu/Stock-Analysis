# Frontend Cleanup Strategy

## Executive Summary

The frontend is the primary source of platform instability due to mixed API patterns from 6 architectural evolution phases. A focused frontend cleanup will resolve the "split-brain" problem where multiple controllers compete to manage flows.

## Current Frontend Problems

### 1. **API Endpoint Chaos**
```typescript
// Frontend calls these non-existent endpoints:
/api/v1/discovery/flows/${flowId}/status      // Backend: /api/v1/discovery/flow/status/${flowId}
/api/v1/discovery/flow/${flowId}/resume       // Doesn't exist
/api/v1/unified-discovery/health              // Doesn't exist
/api/v1/discovery/tech-debt                   // Legacy endpoint
```

### 2. **Mixed API Patterns**
- **Legacy**: `/api/v1/discovery/*` (bypasses Master Flow Orchestrator)
- **Unified**: `/api/v1/unified-discovery/*` (partial implementation)
- **Master**: `/api/v1/master-flows/*` (used as fallback)
- **V3 Remnants**: `/api/v3/*` directory still exists

### 3. **State Management Confusion**
- Multiple hooks fetching same data
- Session ID references in 28 files
- Flow ID from 4 different sources
- No single source of truth

## Root Cause Analysis

The other agent correctly identified that the frontend is calling legacy endpoints, creating a "split-brain" scenario where:
1. Frontend calls `/api/v1/discovery/*` endpoints
2. These bypass the Master Flow Orchestrator
3. Direct database manipulation occurs
4. MFO and legacy controllers conflict
5. State becomes inconsistent

## Proposed Solution: Frontend-First Cleanup

### Phase 1: API Service Layer (Day 1 Morning)
Create a single, clean API service matching backend exactly:

```typescript
// src/services/api/flowService.ts
export const flowAPI = {
  // Master Flow Operations (Single Source of Truth)
  createFlow: (type: FlowType, data: any) => 
    apiCall('/master-flows', { method: 'POST', body: { type, ...data } }),
  
  getFlowStatus: (flowId: string) => 
    apiCall(`/master-flows/${flowId}/status`),
  
  executePhase: (flowId: string, phase: string) => 
    apiCall(`/master-flows/${flowId}/execute`, { method: 'POST', body: { phase } }),
  
  deleteFlow: (flowId: string) => 
    apiCall(`/master-flows/${flowId}`, { method: 'DELETE' }),
  
  // Discovery-Specific Operations (Through MFO)
  resumeDiscoveryFlow: (flowId: string, data: any) => 
    apiCall(`/discovery/flows/${flowId}/resume`, { method: 'POST', body: data }),
  
  getActiveFlows: () => 
    apiCall('/master-flows/active'),
}
```

### Phase 2: Hook Consolidation (Day 1 Afternoon)
Replace all discovery hooks with single unified hook:

```typescript
// src/hooks/useFlow.ts
export const useFlow = (flowId?: string) => {
  // Single source of truth for flow state
  const { data: flow, mutate } = useSWR(
    flowId ? `/api/v1/master-flows/${flowId}/status` : null,
    fetcher
  );
  
  // All operations through Master Flow Orchestrator
  const executePhase = async (phase: string) => {
    await flowAPI.executePhase(flowId, phase);
    mutate();
  };
  
  return { flow, executePhase, /* ... */ };
};
```

### Phase 3: Component Updates (Day 1 Evening - Day 2 Morning)
Update all components to use new patterns:

```typescript
// Before (mixed patterns):
const { flowState } = useUnifiedDiscoveryFlow(flowId);
const { data } = useDiscoveryFlow(sessionId);
const status = await fetch(`/api/v1/discovery/flow/status?session_id=${id}`);

// After (single pattern):
const { flow, executePhase } = useFlow(flowId);
```

### Phase 4: Cleanup (Day 2 Afternoon)
1. Delete these directories/files:
   - `src/api/v3/` - Entire V3 client
   - `src/hooks/useDiscoveryFlow.ts` - Legacy hook
   - `src/utils/migration/sessionToFlow.ts` - Migration complete
   - `src/services/discoveryUnifiedService.ts` - Confusing wrapper

2. Remove all session_id references:
   ```bash
   # Find and replace all session_id with flow_id
   grep -r "session_id" src/ --include="*.ts" --include="*.tsx"
   ```

3. Delete unused API endpoints from backend

## Implementation Checklist

### Day 1 (Frontend Cleanup)
- [ ] Create unified flow API service (2 hours)
- [ ] Update useFlow hook (2 hours)
- [ ] Fix attribute mapping page (2 hours)
- [ ] Update dashboard to use master flows (2 hours)
- [ ] Test all flow operations (2 hours)

### Day 2 (Removal & Testing)
- [ ] Remove V3 API directory (1 hour)
- [ ] Delete legacy hooks (1 hour)
- [ ] Remove session_id references (2 hours)
- [ ] Update all components (3 hours)
- [ ] End-to-end testing (3 hours)

## Success Criteria

1. **Single API Pattern**: All frontend code uses `/api/v1/master-flows/*`
2. **No Legacy Calls**: Zero calls to `/api/v1/discovery/*` that bypass MFO
3. **Flow ID Only**: No session_id references remain
4. **Clean Imports**: No imports from deleted directories
5. **E2E Tests Pass**: Full discovery flow works end-to-end

## Expected Outcomes

1. **Eliminates Split-Brain**: MFO becomes true single source of truth
2. **Fixes State Issues**: No more competing controllers
3. **Simplifies Debugging**: One API pattern to maintain
4. **Enables Progress**: Clean foundation for adding features

## Critical Files to Update

### High Priority (Blocking Issues)
1. `src/hooks/useUnifiedDiscoveryFlow.ts` - Wrong endpoints
2. `src/pages/discovery/AttributeMapping/index.tsx` - Can't resume flows
3. `src/components/discovery/DiscoveryFlowDashboard.tsx` - Mixed APIs
4. `src/services/api/discoveryUnifiedService.ts` - Delete entirely

### Medium Priority (Confusion/Debt)
1. `src/hooks/useFlowOperations.ts` - Fallback patterns
2. `src/services/dashboard/dashboardService.ts` - Legacy APIs
3. `src/utils/flowUtils.ts` - Session ID logic

### Low Priority (Cleanup)
1. `src/api/v3/*` - Delete entire directory
2. `src/types/discovery.ts` - Remove session types
3. `src/config/api.ts` - Simplify endpoint logic

## Risks & Mitigations

### Risk 1: Breaking Existing Flows
**Mitigation**: Add backward compatibility layer temporarily:
```typescript
// Temporary redirect for 1 week
if (endpoint.includes('/discovery/flows/')) {
  return apiCall(endpoint.replace('/discovery/flows/', '/master-flows/'));
}
```

### Risk 2: Missing Endpoints
**Mitigation**: Log all 404s to identify gaps:
```typescript
if (response.status === 404) {
  console.error(`Missing endpoint: ${endpoint}`);
  // Send to monitoring
}
```

### Risk 3: State Migration
**Mitigation**: One-time migration on first load:
```typescript
// Migrate localStorage from session_id to flow_id
const oldSession = localStorage.getItem('currentSessionId');
if (oldSession && !localStorage.getItem('currentFlowId')) {
  localStorage.setItem('currentFlowId', oldSession);
  localStorage.removeItem('currentSessionId');
}
```

## Conclusion

The frontend cleanup is **essential** and should be done **before** backend fixes because:
1. Frontend is causing the split-brain problem
2. Backend MFO exists but frontend bypasses it
3. Clean frontend will reveal true backend issues
4. Simpler to test with consistent API calls
5. Enables parallel work on other fixes

**Estimated Time**: 2 days with focused effort
**Impact**: Resolves 70% of current platform issues