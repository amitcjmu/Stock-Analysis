# Modularization Quick Action Guide

## Immediate Actions (This Sprint)

### 🔥 Top 5 Files Requiring Immediate Attention

1. **`src/types/api/discovery.ts` (1,759 LOC)**
   - **Action**: Split into 8-10 focused type modules
   - **Effort**: 2-3 days
   - **Impact**: High - Used across entire frontend

2. **`backend/app/services/master_flow_orchestrator.py` (1,150 LOC)**
   - **Action**: Extract 6 separate service classes
   - **Effort**: 3-4 days
   - **Impact**: Critical - Core backend orchestrator

3. **`src/types/components/admin.ts` (1,261 LOC)**
   - **Action**: Split into 7 admin-focused modules
   - **Effort**: 2 days
   - **Impact**: Medium - Admin interface types

4. **`backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py` (1,053 LOC)**
   - **Action**: Extract flow management classes
   - **Effort**: 3 days
   - **Impact**: High - Core flow logic

5. **`src/components/discovery/attribute-mapping/FieldMappingsTab/components/ThreeColumnFieldMapper.tsx` (726 LOC)**
   - **Action**: Extract 5 sub-components and 3 hooks
   - **Effort**: 1-2 days
   - **Impact**: Medium - Complex UI component

## Refactoring Recipes

### Python Service Extraction Pattern
```python
# BEFORE (1,150 LOC monolith)
class MasterFlowOrchestrator:
    # All responsibilities mixed together

# AFTER (6 focused classes)
class FlowOrchestrator:           # ~200 LOC - Main coordination
class ExecutionCoordinator:       # ~200 LOC - Execution logic  
class StateCoordinator:           # ~150 LOC - State management
class LifecycleManager:           # ~200 LOC - Lifecycle events
class ErrorManager:               # ~150 LOC - Error handling
class AuditManager:               # ~150 LOC - Audit logging
```

### TypeScript Type Module Pattern
```typescript
// BEFORE (1,759 LOC single file)
// src/types/api/discovery.ts

// AFTER (Modular structure)
src/types/api/discovery/
├── flow-management.ts     # 300 LOC - Flow operations
├── data-import.ts         # 250 LOC - Import types
├── field-mapping.ts       # 250 LOC - Mapping types
├── analysis.ts            # 200 LOC - Analysis types
├── export-import.ts       # 200 LOC - Export types
├── validation.ts          # 150 LOC - Validation types
├── monitoring.ts          # 150 LOC - Monitoring types
├── reporting.ts           # 150 LOC - Report types
└── index.ts               # 100 LOC - Re-exports
```

### React Component Decomposition
```tsx
// BEFORE (726 LOC component)
const ThreeColumnFieldMapper = () => {
  // All logic and UI mixed together
};

// AFTER (Focused components)
const ThreeColumnFieldMapper = () => {
  const mappingState = useFieldMapping();
  const validation = useMappingValidation();
  const bulkOps = useBulkOperations();
  
  return (
    <FieldMapperContainer>
      <MappingColumn type="source" />
      <MappingColumn type="target" />
      <ActionColumn />
      <BulkActionToolbar />
    </FieldMapperContainer>
  );
};
```

## Weekly Targets

### Week 1: Type System Refactoring
- [ ] Split `discovery.ts` into modules
- [ ] Split `admin.ts` into focused files
- [ ] Update import paths across codebase
- [ ] Validate TypeScript compilation

### Week 2: Backend Service Extraction
- [ ] Extract MasterFlowOrchestrator components
- [ ] Extract UnifiedDiscoveryFlow classes
- [ ] Create service interfaces
- [ ] Update dependency injection

### Week 3: Component Decomposition
- [ ] Break down ThreeColumnFieldMapper
- [ ] Extract reusable hooks
- [ ] Create component library patterns
- [ ] Update tests

### Week 4: Integration & Testing
- [ ] End-to-end testing
- [ ] Performance validation
- [ ] Documentation updates
- [ ] Developer training

## Success Metrics

### Daily Tracking
- Files over 500 LOC: Target 0 (Currently 15)
- Files over 400 LOC: Target <50 (Currently 124)
- Files over 350 LOC: Target <100 (Currently 404)

### Quality Gates
- ✅ No new files over 300 LOC
- ✅ All extracted modules have tests
- ✅ TypeScript compilation passes
- ✅ No performance regression
- ✅ Documentation updated

## Risk Mitigation

### Breaking Changes Prevention
1. Use barrel exports (`index.ts`) to maintain import paths
2. Implement gradual migration with deprecation warnings
3. Feature flags for new vs. old implementations
4. Comprehensive regression testing

### Rollback Strategy
1. Git branch per refactoring effort
2. Automated testing pipeline validation
3. Performance monitoring alerts
4. Quick revert procedures documented

## Tools and Scripts

### File Size Monitoring
```bash
# Run daily compliance check
python backend/modularization_analysis.py

# Watch for new large files
find . -name "*.py" -o -name "*.ts" -o -name "*.tsx" | \
xargs wc -l | sort -nr | head -20
```

### Automated Refactoring Helpers
```bash
# TypeScript module splitter (create custom script)
./scripts/split-types-module.sh src/types/api/discovery.ts

# Python class extractor (create custom script)  
./scripts/extract-python-services.sh backend/app/services/master_flow_orchestrator.py
```

---
*Quick Action Guide - Start Here for Immediate Impact*