# Frontend Migration Checklist (FlowService/useFlow → masterFlowService/new hooks)

## Analysis Summary
**Generated:** 2025-09-06  
**Total legacy imports found:** 38 files (24 FlowService + 22 useFlow imports, some overlap)  
**Migration status:** ~50% of files already using masterFlowService patterns  

## Goals
- Eliminate imports of `src/services/FlowService.ts` and `src/hooks/useFlow.ts`
- Migrate to `src/services/api/masterFlowService.ts` and phase-specific hooks (e.g., `useUnifiedDiscoveryFlow`, `useDiscoveryFlowStatus`)

## Guardrails
- ESLint `no-restricted-imports` blocks new imports of legacy modules
- Do not remove legacy files until imports reach zero

## Complete File Inventory

### FILES IMPORTING FlowService (24 total)

#### ✅ ALREADY MIGRATED (using masterFlowService)
1. `src/components/discovery/FlowStatusWidget.tsx` - Uses masterFlowService.resumeFlow
2. `src/hooks/discovery/useFlowOperations.ts` - Uses masterFlowService.getActiveFlows

#### 🔄 PARTIALLY MIGRATED (mixed usage)
3. `src/hooks/useUnifiedDiscoveryFlow.ts` - Mentions FlowService but likely uses new patterns
4. `src/hooks/discovery/useDiscoveryFlow.ts` - May be hybrid implementation
5. `src/hooks/discovery/useDiscoveryFlowStatus.ts` - May be hybrid implementation

#### ❌ NEEDS MIGRATION (still using legacy FlowService)
6. `src/components/discovery/attribute-mapping/FieldMappingsTab/components/ThreeColumnFieldMapper/AutoMappedCard.tsx`
7. `src/components/FlowCrewAgentMonitor/hooks/useAgentMonitor.ts`
8. `src/components/discovery/attribute-mapping/FieldMappingsTab/types.ts`
9. `src/components/discovery/attribute-mapping/FieldMappingsTab/components/ThreeColumnFieldMapper/types.ts`
10. `src/components/discovery/attribute-mapping/FieldMappingsTab/components/FieldMappingLearningControls.tsx`
11. `src/components/discovery/attribute-mapping/AttributeMappingTabContent.tsx`
12. `src/components/discovery/FlowResumptionHandler.tsx`
13. `src/config/flowRoutes.ts`
14. `src/hooks/useLearningToasts.ts`
15. `src/pages/discovery/AttributeMapping/components/AttributeMappingContent.tsx`
16. `src/hooks/discovery/useAttributeMappingNavigation.ts`
17. `src/hooks/discovery/attribute-mapping/useSmartFlowResolver.ts`
18. `src/hooks/discovery/attribute-mapping/usePhaseAwareFlowResolver.ts`
19. `src/services/flowDeletionService.ts`
20. `src/hooks/discovery/useDiscoveryFlowList.ts`
21. `src/hooks/useFlow.ts` - The legacy hook itself
22. `src/hooks/discovery/useInventoryLogic.ts`
23. `src/hooks/useDiscoveryDashboard.ts`

### FILES IMPORTING useFlow (22 total)

#### ❌ HIGH-PRIORITY MIGRATIONS (Core UI components)
1. `src/components/flows/MasterFlowDashboard.tsx` - Uses legacy `useFlows` hook
2. `src/pages/discovery/EnhancedDiscoveryDashboard/index.tsx` - Main discovery page
3. `src/components/discovery/EnhancedFlowManagementDashboard.tsx` - Flow management UI

#### ❌ DISCOVERY AREA MIGRATIONS  
4. `src/pages/discovery/CMDBImport/hooks/useCMDBImport.ts`
5. `src/pages/discovery/CMDBImport/hooks/useFlowManagement.ts`
6. `src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts`
7. `src/hooks/discovery/attribute-mapping/useAttributeMappingComposition.ts`
8. `src/hooks/discovery/attribute-mapping/index.ts`
9. `src/hooks/discovery/useEnhancedFlowManagement.ts`
10. `src/pages/discovery/AttributeMapping/components/AgentReasoningDisplay.tsx`
11. `src/components/discovery/UploadBlocker.tsx`
12. `src/pages/discovery/EnhancedDiscoveryDashboard/components/MetricsPanel.tsx`

#### ❌ COLLECTION AREA MIGRATIONS
13. `src/pages/collection/AdaptiveForms.tsx` - Collection page (uses useFlowDeletion, not legacy useFlow)

#### ❌ UTILITY/WRAPPER HOOKS
14. `src/hooks/useOptimisticFlow.ts` - Wrapper around legacy useFlow
15. `src/hooks/useAssessmentFlowMigrated.ts` - Migration wrapper
16. `src/hooks/useUnifiedDiscoveryFlowMigrated.ts` - Migration wrapper

#### 📝 DOCUMENTATION/TESTS
17. `src/hooks/discovery/attribute-mapping/useAttributeMappingLogic.test.ts`
18. `src/hooks/discovery/attribute-mapping/README.md`
19. `src/hooks/discovery/attribute-mapping/types.ts`
20. `src/pages/discovery/EnhancedDiscoveryDashboard/index.barrel.ts`
21. `src/pages/discovery/CMDBImport/index.barrel.ts`

## Migration Priority Matrix

### 🚨 HIGH RISK - MIGRATE FIRST
**Core dashboard and navigation components:**
- `src/components/flows/MasterFlowDashboard.tsx`
- `src/pages/discovery/EnhancedDiscoveryDashboard/index.tsx`
- `src/components/discovery/EnhancedFlowManagementDashboard.tsx`

**Why high risk:** These are main user-facing components that likely have complex state management and polling logic.

### ⚠️ MEDIUM RISK - MIGRATE SECOND
**Discovery flow operations:**
- `src/hooks/discovery/useEnhancedFlowManagement.ts`
- `src/pages/discovery/CMDBImport/hooks/useFlowManagement.ts`
- `src/hooks/discovery/attribute-mapping/*` (multiple files)

**Why medium risk:** These handle flow operations and may have interdependencies.

### ✅ LOW RISK - MIGRATE LAST
**Wrapper/utility hooks:**
- `src/hooks/useOptimisticFlow.ts`
- `src/hooks/useAssessmentFlowMigrated.ts`
- `src/hooks/useUnifiedDiscoveryFlowMigrated.ts`

**Why low risk:** These are adapters that can be safely migrated once core components are done.

## Replacement Patterns

### FlowService → masterFlowService
```typescript
// OLD
import { FlowService } from '@/services/FlowService';
const flowService = FlowService.getInstance();
const flows = await flowService.getFlows();

// NEW (align with actual masterFlowService API)
import { masterFlowService } from '@/services/api/masterFlowService';
// If service reads tenant headers from a global http client config:
const flows = await masterFlowService.getActiveFlows('discovery');
// If service requires explicit tenant params (verify signature):
// const flows = await masterFlowService.getActiveFlows(clientAccountId, engagementId, 'discovery');
```

### useFlow → Specialized hooks
```typescript
// OLD
import { useFlow } from '@/hooks/useFlow';
const [state, actions] = useFlow({ autoRefresh: true });

// NEW - for discovery flows
import { useUnifiedDiscoveryFlow } from '@/hooks/useUnifiedDiscoveryFlow';
import { useDiscoveryFlowStatus } from '@/hooks/discovery/useDiscoveryFlowStatus';
const { data: flowStatus } = useDiscoveryFlowStatus(flowId);
```

## Field Name Migration Notes
- **CRITICAL:** All new code must use snake_case field names (flow_id, client_account_id, current_phase)
- **Legacy compatibility:** Some files may still have camelCase (flowId) - convert during migration
- **API consistency:** masterFlowService returns snake_case fields consistently

## Refreshing the Inventory (repeatable)
```bash
# Where FlowService is imported
rg -n "from '(.*/)?services/FlowService'|from \"(.*/)?services/FlowService\"" src --type ts --type tsx

# Where useFlow is imported
rg -n "from '(.*/)?hooks/useFlow'|from \"(.*/)?hooks/useFlow\"" src --type ts --type tsx
```

## Old→New Mapping Table (quick reference)
- createFlow → masterFlowService.createFlow (ensure flow_type provided)
- getFlows → masterFlowService.getActiveFlows (verify signature)
- getFlowStatus → masterFlowService.getFlowStatus
- executePhase → masterFlowService.execute (phase_name, phase_input)
- pauseFlow/resumeFlow/deleteFlow → same names under masterFlowService

## Migration Stop Criteria
- Both checks return zero results:
```bash
rg -n "from '(.*/)?services/FlowService'|from \"(.*/)?services/FlowService\"" src --type ts --type tsx | wc -l
rg -n "from '(.*/)?hooks/useFlow'|from \"(.*/)?hooks/useFlow\"" src --type ts --type tsx | wc -l
```

## Barrel Files Caveat
- Update any `index.ts` or `*.barrel.ts` files that re-export legacy imports to avoid indirect reintroduction.

## Validation Checklist
- [ ] Multi-tenant headers preserved (X-Client-Account-ID, X-Engagement-ID)
- [ ] HTTP polling patterns used (not WebSockets)
- [ ] snake_case field names in all new interfaces
- [ ] Error handling with structured responses
- [ ] No hardcoded /api/v1/discovery/* endpoints

## Migration Steps
1. **Start with high-risk components** (MasterFlowDashboard, main discovery pages)
2. **Update one file at a time** - don't batch to reduce risk
3. **Test each migration** with Docker on localhost:8081
4. **Check browser console** for 404s or field name mismatches
5. **Preserve existing functionality** - don't add new features during migration
6. **Update imports last** - ensure all functionality works before cleaning up imports

## Notes
- Preserve tenant headers and flow_id propagation
- Prefer polling patterns documented in `docs/analysis/Notes/000-lessons.md`
- Consider that some "legacy" files may already be partially migrated
- The actual migration effort is smaller than the file count suggests - many files just need import updates
