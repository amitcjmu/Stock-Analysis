# Discovery Flow Consolidation Plan

## Phase 1: Delete Unused Files (Safe)

### Frontend
```bash
# Archive hooks with no references
rm src/archive/hooks/discovery/useDiscoveryFlowV2.ts
rm src/archive/hooks/discovery/useIncompleteFlowDetectionV2.ts
```

### Backend
```bash
# Remove backup/original files
rm backend/app/api/v1/endpoints/discovery_flows_original.py

# Move test files to proper location
mv backend/test_etag_implementation.py backend/tests/
mv backend/docs/etag_polling_implementation.md docs/implementation/
```

## Phase 2: Remove Unused Endpoints

### Backend Endpoints to Remove
1. `/api/v1/discovery/flow/abort` - No frontend usage
2. `/api/v1/discovery/flows/agentic-analysis-status` - No frontend usage
3. `/api/v1/discovery/flows/processing-status` - No frontend usage

### Keep These Active Endpoints
1. `/api/v1/discovery/flows/active` - Used by dashboard
2. `/api/v1/discovery/flows/{flow_id}/status` - Used by flow status
3. `/api/v1/discovery/flow/crews/monitoring/{flow_id}` - Used by crew monitor
4. `/api/v1/discovery/flows/{flow_id}/agent-insights` - Used by useAgentQuestions
5. `/api/v1/discovery/agents/discovery/agent-questions` - Used by useAgentQuestions

## Phase 3: Consolidate Frontend Hooks

### Create Core Hooks
1. **useDiscoveryFlowStatus.ts**
   - Consolidate polling logic from SimplifiedFlowStatus and useUnifiedDiscoveryFlow
   - Single source of truth for status polling
   - Configurable polling intervals

2. **useDiscoveryFlowOperations.ts**
   - Consolidate create/delete/update operations
   - Move from useUnifiedDiscoveryFlow

### Update Components
1. SimplifiedFlowStatus.tsx - Use new useDiscoveryFlowStatus hook
2. CMDBImport - Use new hooks instead of custom polling
3. Remove duplicate polling logic

## Phase 4: Migrate to Master Flow APIs

### Gradual Migration
1. Update frontend to use `/api/v1/flows/` instead of `/api/v1/discovery/flows/`
2. Keep minimal discovery endpoints for backward compatibility
3. Eventually remove all discovery-specific endpoints

## Phase 5: Type Consolidation

### Create Single Type Definition
```typescript
// types/flow.ts - Single source of truth
export interface Flow {
  flow_id: string;
  flow_type: string;
  status: FlowStatus;
  awaiting_user_approval?: boolean;
  // ... rest of fields
}
```

### Remove Duplicate Types
- Consolidate discovery.ts, flow.ts, flow-orchestration.ts
- Single FlowStatus enum
- Single Flow interface

## Implementation Order

1. **Immediate**: Delete unused archived files (no risk)
2. **Next Sprint**: Remove unused endpoints after verifying
3. **Following Sprint**: Consolidate frontend hooks
4. **Future**: Complete migration to master flow APIs

## Success Metrics

- Reduce API endpoints from ~15 to ~5
- Reduce frontend hooks from 6 to 2
- Single polling implementation
- Consistent status handling
- No duplicate type definitions