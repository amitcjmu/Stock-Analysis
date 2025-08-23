# Snake Case Standardization Plan
## Frontend Field Naming Convention Migration

### Executive Summary
This document outlines the comprehensive plan to standardize all frontend field names to snake_case, matching the backend API convention. This will eliminate the recurring snake_case/camelCase bugs that have plagued the codebase.

### Problem Statement
- Backend (Python/FastAPI) consistently returns snake_case fields
- Frontend (TypeScript/React) inconsistently uses both camelCase and snake_case
- Current transformation utilities add complexity and potential points of failure
- AI coding agents repeatedly introduce camelCase, causing recurring bugs
- Mixed conventions cause confusion and maintenance overhead

### Solution: Standardize on Snake Case
Adopt snake_case as the single field naming convention throughout the entire codebase (frontend and backend).

---

## Implementation Plan

### Phase 1: Setup and Preparation
**Branch**: `fix/standardize-snake-case-fields`

```bash
# Create new branch
git checkout -b fix/standardize-snake-case-fields

# Ensure clean working directory
git status
```

### Phase 2: Update Core Type Definitions (High Priority)

#### 2.1 Remove Transformation Utilities
- **DELETE**: `src/utils/api-field-transformer.ts`
  - This file creates confusion by supporting both conventions
  - Remove all imports of this file throughout the codebase

#### 2.2 Update Core Type Files
These files define the fundamental types used throughout the application:

1. **`src/types/flow.ts`** ✅ (Already uses snake_case)
2. **`src/types/guards.ts`**
   - Update all type guards to check for snake_case fields only
3. **`src/pages/discovery/EnhancedDiscoveryDashboard/types.ts`**
   - Already uses snake_case, add comment about convention

### Phase 3: Update API Service Layer (High Priority)

These files directly interact with the backend API:

1. **`src/services/api/masterFlowService.ts`**
   - Change all field references from camelCase to snake_case
   - Remove any transformation logic
   
2. **`src/services/api/masterFlowService.extensions.ts`**
   - Update extension methods to use snake_case

3. **`src/services/api/collection-flow.ts`**
   - Update all collection flow field names

4. **`src/services/api/discoveryFlowService.ts`**
   - Critical file for discovery flows
   - Update all field references

5. **`src/services/FlowService.ts`**
6. **`src/services/flowDeletionService.ts`**
7. **`src/services/flowProcessingService.ts`**

8. **`src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts`**
   - Remove transformation imports
   - Use snake_case fields directly

### Phase 4: Update Hooks (High Priority)

#### Collection Hooks
```
src/hooks/collection/useCollectionFlowManagement.ts
src/hooks/collection/useAdaptiveFormFlow.ts
src/hooks/collection/useProgressMonitoring.ts
```

#### Discovery Hooks
```
src/hooks/discovery/useDiscoveryFlowStatus.ts
src/hooks/discovery/useDiscoveryFlowList.ts
src/hooks/discovery/useDiscoveryFlowAutoDetection.ts
src/hooks/discovery/useFlowProgress.ts
src/hooks/discovery/useFlowOperations.ts
```

#### Attribute Mapping Hooks
```
src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts
src/hooks/discovery/attribute-mapping/useAttributeMappingComposition.ts
src/hooks/discovery/attribute-mapping/useFieldMappings.ts
src/hooks/discovery/attribute-mapping/useSmartFlowResolver.ts
src/hooks/discovery/attribute-mapping/usePhaseAwareFlowResolver.ts
```

#### Core Hooks
```
src/hooks/useFlow.ts
src/hooks/useFlowUpdates.ts
src/hooks/useFlowDeletion.ts
src/hooks/useUnifiedDiscoveryFlow.ts
src/hooks/useAssessmentFlow/useAssessmentFlow.ts
```

### Phase 5: Update Type Definition Files

#### API Types
```
src/types/api/discovery/field-mapping-types.ts
src/types/api/discovery/flow-management.ts
src/types/api/discovery/progress-tracking.ts
src/types/api/discovery/flow-state-management.ts
```

#### Module Types
```
src/types/modules/flow-orchestration/model-types/flow-models.ts
src/types/modules/discovery/data-models.ts
```

### Phase 6: Update Page Components

#### Discovery Pages
```
src/pages/discovery/EnhancedDiscoveryDashboard/index.tsx
src/pages/discovery/AttributeMapping/index.tsx
src/pages/discovery/CMDBImport/index.tsx
src/pages/discovery/DataCleansing.tsx
```

#### Collection Pages
```
src/pages/collection/Index.tsx
src/pages/collection/AdaptiveForms.tsx
src/pages/collection/Progress.tsx
```

#### Assessment Pages
```
src/pages/assessment/[flowId]/architecture.tsx
src/pages/assessment/[flowId]/tech-debt.tsx
src/pages/assessment/[flowId]/summary.tsx
src/pages/assessment/[flowId]/sixr-review.tsx
```

### Phase 7: Update Components

```
src/components/discovery/FlowStatusWidget.tsx
src/components/discovery/SimplifiedFlowStatus.tsx
src/components/FlowCrewAgentMonitor/index.tsx
src/components/collection/progress/ProgressMonitorContainer.tsx
src/components/collection/progress/FlowDetailsCard.tsx
```

---

## Field Mapping Reference

| Current (camelCase) | New (snake_case) |
|-------------------|------------------|
| flowId | flow_id |
| clientAccountId | client_account_id |
| engagementId | engagement_id |
| createdAt | created_at |
| updatedAt | updated_at |
| currentPhase | current_phase |
| progressPercentage | progress_percentage |
| activeAgents | active_agents |
| dataSources | data_sources |
| successCriteriaMet | success_criteria_met |
| flowType | flow_type |
| clientName | client_name |
| engagementName | engagement_name |
| masterFlowId | master_flow_id |
| childFlows | child_flows |
| sourceField | source_field |
| targetField | target_field |
| confidenceScore | confidence_score |
| startedAt | started_at |
| completedAt | completed_at |
| errorMessage | error_message |
| responseTime | response_time |
| flowState | flow_state |
| phaseCompletion | phase_completion |
| awaitingUserApproval | awaiting_user_approval |
| fieldMappings | field_mappings |
| estimatedCompletion | estimated_completion |
| lastUpdated | last_updated |
| crewCount | crew_count |
| totalSuccessCriteria | total_success_criteria |

---

## Implementation Steps for Each File

### Step 1: Search and Replace
For each file, perform these replacements:

```typescript
// Example for a service file
// BEFORE:
const flow = {
  flowId: response.flow_id,
  clientAccountId: response.client_account_id,
  currentPhase: response.current_phase
};

// AFTER:
const flow = {
  flow_id: response.flow_id,
  client_account_id: response.client_account_id,
  current_phase: response.current_phase
};
```

### Step 2: Update Interface Definitions
```typescript
// BEFORE:
interface FlowResponse {
  flowId: string;
  clientAccountId: string;
  currentPhase: string;
}

// AFTER:
interface FlowResponse {
  flow_id: string;
  client_account_id: string;
  current_phase: string;
}
```

### Step 3: Update Object Property Access
```typescript
// BEFORE:
if (flow.flowId && flow.currentPhase === 'field_mapping') {
  console.log(flow.clientAccountId);
}

// AFTER:
if (flow.flow_id && flow.current_phase === 'field_mapping') {
  console.log(flow.client_account_id);
}
```

### Step 4: Update Destructuring
```typescript
// BEFORE:
const { flowId, clientAccountId, currentPhase } = flow;

// AFTER:
const { flow_id, client_account_id, current_phase } = flow;
```

---

## Testing Plan

### 1. Unit Tests
- Update all test files to use snake_case fields
- Remove tests for transformation utilities
- Add tests to verify snake_case field access

### 2. Integration Tests
- Test API endpoints return snake_case fields
- Test frontend correctly reads snake_case fields
- Verify no transformation is happening

### 3. E2E Tests
- Run full flow creation and management scenarios
- Verify Discovery, Collection, and Assessment flows work
- Check that all dashboards display correct data

---

## ESLint Configuration

Create `.eslintrc.snake-case.js`:

```javascript
module.exports = {
  rules: {
    // Enforce snake_case for object properties that match API fields
    '@typescript-eslint/naming-convention': [
      'error',
      {
        selector: 'objectLiteralProperty',
        format: ['snake_case'],
        filter: {
          regex: '^(flow_id|client_account_id|engagement_id|created_at|updated_at|current_phase|progress_percentage|active_agents|data_sources|success_criteria_met|flow_type|client_name|engagement_name|master_flow_id|child_flows|source_field|target_field|confidence_score|started_at|completed_at|error_message|response_time)$',
          match: true
        },
        message: 'API field names must use snake_case'
      }
    ],
    
    // Prohibit camelCase variants of known API fields
    'no-restricted-syntax': [
      'error',
      {
        selector: 'Identifier[name="flowId"]',
        message: 'Use flow_id instead of flowId'
      },
      {
        selector: 'Identifier[name="clientAccountId"]',
        message: 'Use client_account_id instead of clientAccountId'
      },
      {
        selector: 'Identifier[name="engagementId"]',
        message: 'Use engagement_id instead of engagementId'
      },
      {
        selector: 'Identifier[name="currentPhase"]',
        message: 'Use current_phase instead of currentPhase'
      },
      {
        selector: 'Identifier[name="progressPercentage"]',
        message: 'Use progress_percentage instead of progressPercentage'
      }
    ]
  }
};
```

---

## Documentation Updates

### 1. Update CLAUDE.md
```markdown
## CRITICAL: Field Naming Convention

### SINGLE CONVENTION: snake_case EVERYWHERE

1. **Backend (Python/FastAPI)**: Returns snake_case fields
2. **Frontend (TypeScript/React)**: Uses snake_case fields
3. **No Transformation**: Fields are used as-is from the API
4. **No camelCase**: NEVER use camelCase for API field names

### Common Field Names (ALWAYS snake_case):
- flow_id (NOT flowId)
- client_account_id (NOT clientAccountId)
- engagement_id (NOT engagementId)
- current_phase (NOT currentPhase)
- created_at (NOT createdAt)
- updated_at (NOT updatedAt)

### Enforcement:
- ESLint rules will flag camelCase API fields as errors
- Pre-commit hooks will prevent camelCase fields
- Code reviews must check for snake_case consistency
```

### 2. Create FIELD_NAMING_CONVENTION.md
Document the complete list of API fields and their correct snake_case names.

---

## Git Commit Strategy

### Commit 1: Remove Transformation Layer
```bash
git add -A
git commit -m "refactor: Remove API field transformation layer

- Delete api-field-transformer.ts utility
- Remove all transformation imports
- Prepare for snake_case standardization

This is step 1 of eliminating snake_case/camelCase confusion"
```

### Commit 2: Update Type Definitions
```bash
git add src/types/**/*.ts
git commit -m "refactor: Standardize type definitions to snake_case

- Update all TypeScript interfaces to use snake_case
- Remove camelCase field definitions
- Add documentation about snake_case convention"
```

### Commit 3: Update Services and Hooks
```bash
git add src/services/**/*.ts src/hooks/**/*.ts
git commit -m "refactor: Convert services and hooks to snake_case

- Update all service layer files
- Update all React hooks
- Remove field transformations"
```

### Commit 4: Update Components and Pages
```bash
git add src/components/**/*.tsx src/pages/**/*.tsx
git commit -m "refactor: Convert components and pages to snake_case

- Update all React components
- Update all page components
- Ensure consistent field access"
```

### Commit 5: Add Linting and Documentation
```bash
git add .eslintrc.snake-case.js CLAUDE.md docs/
git commit -m "docs: Add snake_case enforcement and documentation

- Add ESLint rules for snake_case enforcement
- Update CLAUDE.md with clear convention
- Document field naming standards"
```

---

## Pre-commit Checks

Before pushing, ensure:

1. **Run ESLint**: `npm run lint`
2. **Run TypeScript Check**: `npm run type-check`
3. **Run Tests**: `npm test`
4. **Run E2E Tests**: `npm run test:e2e`
5. **Check for camelCase**: `grep -r "flowId\|clientAccountId\|engagementId\|currentPhase" src/`

---

## Rollback Plan

If issues arise:

1. **Revert Branch**: `git checkout main`
2. **Keep Backup Branch**: `git branch backup/snake-case-attempt`
3. **Document Issues**: Note what failed for future attempts
4. **Gradual Migration**: Consider file-by-file migration if full conversion fails

---

## Success Metrics

1. **Zero camelCase API fields** in frontend code
2. **All tests passing** with snake_case fields
3. **No transformation utilities** needed
4. **Consistent field names** across frontend and backend
5. **No more recurring** snake_case/camelCase bugs

---

## Timeline

- **Day 1**: Setup, core types, and services (Phases 1-3)
- **Day 2**: Hooks and additional types (Phases 4-5)
- **Day 3**: Components and pages (Phase 6-7)
- **Day 4**: Testing and validation
- **Day 5**: Documentation and merge

---

## Notes for AI Agents

When CC agents work on this:

1. **NEVER use camelCase** for API field names
2. **ALWAYS use snake_case** exactly as shown in the mapping table
3. **DO NOT create transformation utilities** - use fields as-is
4. **CHECK the field mapping table** before making changes
5. **RUN pre-commit checks** before committing
6. **TEST thoroughly** after each phase

This plan will permanently eliminate the snake_case/camelCase confusion that has been causing recurring bugs.