# Team Beta - Hook Consolidation Briefing

## Mission Statement
Team Beta is responsible for consolidating React hooks, eliminating duplication, and establishing a clean, consistent hook layer that provides efficient state management and API integration for all components.

## Team Objectives
1. Consolidate duplicate hooks into single, well-tested implementations
2. Remove hooks with mixed v1/v2/v3 API calls
3. Implement proper error boundaries and loading states
4. Ensure all hooks follow React best practices and naming conventions

## Specific Tasks

### Task 1: Audit and Map Existing Hooks
**Files to audit:**
- `/src/hooks/useDiscoveryFlow.ts`
- `/src/hooks/useUnifiedDiscoveryFlow.ts`
- `/src/hooks/useClientEngagement.ts`
- `/src/hooks/useDataImport.ts`
- `/src/hooks/useFlowNavigation.ts`
- `/src/hooks/useFlowState.ts`
- `/src/hooks/useMultiTenant.ts`

**Create mapping document:**
```typescript
// /src/hooks/HOOK_MAPPING.md
| Current Hook | Purpose | API Calls | To Be Replaced By |
|--------------|---------|-----------|-------------------|
| useDiscoveryFlow | Legacy discovery | v2/v3 mixed | useFlow |
| useUnifiedDiscoveryFlow | New discovery | v1/v3 mixed | useFlow |
```

### Task 2: Create Consolidated Core Hooks
**Create new unified hooks:**

```typescript
// /src/hooks/core/useFlow.ts
import { useState, useEffect, useCallback } from 'react';
import { flowService } from '@/services/flowService';
import { useMultiTenant } from './useMultiTenant';
import { useErrorHandler } from './useErrorHandler';

export const useFlow = (flowType: FlowType = 'discovery') => {
  const [flow, setFlow] = useState<Flow | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const { clientAccountId, engagementId } = useMultiTenant();
  const { handleError } = useErrorHandler();
  
  const initializeFlow = useCallback(async (data: InitializeFlowData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await flowService.initialize(
        clientAccountId,
        engagementId,
        flowType,
        data
      );
      setFlow(response);
      return response;
    } catch (err) {
      const error = handleError(err);
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [clientAccountId, engagementId, flowType, handleError]);
  
  const refreshFlow = useCallback(async () => {
    if (!flow?.id) return;
    
    try {
      const updated = await flowService.getStatus(
        clientAccountId,
        flow.id
      );
      setFlow(updated);
    } catch (err) {
      handleError(err);
    }
  }, [flow?.id, clientAccountId, handleError]);
  
  // Auto-refresh every 5 seconds when flow is active
  useEffect(() => {
    if (!flow?.id || flow.status === 'completed') return;
    
    const interval = setInterval(refreshFlow, 5000);
    return () => clearInterval(interval);
  }, [flow?.id, flow?.status, refreshFlow]);
  
  return {
    flow,
    loading,
    error,
    initializeFlow,
    refreshFlow,
    updateFlow: async (updates: Partial<Flow>) => {
      // Implementation
    },
    deleteFlow: async () => {
      // Implementation
    }
  };
};
```

### Task 3: Create Specialized Hooks
**Build on top of core hooks:**

```typescript
// /src/hooks/flows/useDiscoveryFlow.ts
export const useDiscoveryFlow = () => {
  const flowHook = useFlow('discovery');
  
  // Add discovery-specific methods
  const startDataImport = useCallback(async (importData: ImportData) => {
    return flowService.discoveryDataImport(
      flowHook.flow?.id,
      importData
    );
  }, [flowHook.flow?.id]);
  
  const mapAttributes = useCallback(async (mappings: AttributeMapping[]) => {
    return flowService.discoveryMapAttributes(
      flowHook.flow?.id,
      mappings
    );
  }, [flowHook.flow?.id]);
  
  return {
    ...flowHook,
    startDataImport,
    mapAttributes,
    // Discovery-specific state
    currentPhase: flowHook.flow?.metadata?.currentPhase || 'initialization'
  };
};
```

### Task 4: Implement Error and Loading States
**Create consistent patterns:**

```typescript
// /src/hooks/core/useErrorHandler.ts
export const useErrorHandler = () => {
  const { showNotification } = useNotification();
  
  const handleError = useCallback((error: any): Error => {
    console.error('Hook error:', error);
    
    let message = 'An unexpected error occurred';
    let statusCode = 500;
    
    if (error.response) {
      message = error.response.data?.message || error.message;
      statusCode = error.response.status;
    } else if (error.message) {
      message = error.message;
    }
    
    // Show user-friendly notification
    showNotification({
      type: 'error',
      title: 'Error',
      message,
      duration: 5000
    });
    
    // Return standardized error
    return new Error(message);
  }, [showNotification]);
  
  return { handleError };
};
```

### Task 5: Remove Deprecated Hooks
**Files to remove after migration:**
- Hooks with `_old`, `_deprecated`, `_legacy` suffixes
- Hooks using v2/v3 API calls
- Duplicate implementations

**Migration checklist for each deprecated hook:**
1. Identify all components using the hook
2. Update components to use new consolidated hook
3. Run tests to ensure functionality
4. Remove deprecated hook file
5. Update imports in all affected files

### Task 6: Implement Hook Tests
**Test structure:**

```typescript
// /src/hooks/__tests__/useFlow.test.tsx
import { renderHook, act } from '@testing-library/react-hooks';
import { useFlow } from '../core/useFlow';

describe('useFlow', () => {
  it('should initialize flow with proper data', async () => {
    const { result } = renderHook(() => useFlow('discovery'));
    
    await act(async () => {
      await result.current.initializeFlow({
        name: 'Test Flow',
        description: 'Test Description'
      });
    });
    
    expect(result.current.flow).toBeDefined();
    expect(result.current.flow?.name).toBe('Test Flow');
  });
  
  it('should handle errors gracefully', async () => {
    // Test error scenarios
  });
  
  it('should auto-refresh active flows', async () => {
    // Test auto-refresh functionality
  });
});
```

## Success Criteria
1. All duplicate hooks consolidated into core implementations
2. No hooks making v2/v3 API calls
3. Consistent error handling across all hooks
4. Proper loading states implemented
5. All hooks have comprehensive tests
6. TypeScript types properly defined
7. Auto-refresh implemented for active flows
8. Memory leaks prevented (proper cleanup)

## Common Issues and Solutions

### Issue 1: Circular Dependencies
**Symptom:** Import errors, undefined hooks
**Solution:** 
- Use barrel exports: `/src/hooks/index.ts`
- Avoid hooks importing each other directly
- Use dependency injection pattern where needed

### Issue 2: Stale Closures
**Symptom:** Callbacks using old state values
**Solution:**
- Use `useCallback` with proper dependencies
- Consider using `useRef` for latest values
- Implement proper dependency arrays

### Issue 3: Memory Leaks
**Symptom:** Performance degradation, warnings in console
**Solution:**
```typescript
useEffect(() => {
  let mounted = true;
  
  const fetchData = async () => {
    const data = await api.getData();
    if (mounted) {
      setData(data);
    }
  };
  
  fetchData();
  
  return () => {
    mounted = false;
  };
}, []);
```

### Issue 4: Race Conditions
**Symptom:** Inconsistent state, wrong data displayed
**Solution:**
- Use AbortController for cancellable requests
- Implement request deduplication
- Use proper state machines

## Rollback Procedures
1. **Before making changes:**
   ```bash
   git checkout -b beta-hook-consolidation
   git push origin beta-hook-consolidation
   ```

2. **Incremental migration:**
   - Keep old hooks temporarily with `@deprecated` JSDoc
   - Migrate components gradually
   - Remove deprecated hooks only after full migration

3. **If issues arise:**
   ```bash
   # Revert specific hook
   git checkout main -- src/hooks/useDiscoveryFlow.ts
   
   # Or restore from backup
   cp src/hooks/_backup/useDiscoveryFlow.ts src/hooks/
   ```

## Testing Requirements
1. **Unit tests for each hook**
2. **Integration tests with components**
3. **Performance tests for auto-refresh**
4. **Memory leak detection**

## Hook Guidelines
1. **Naming Convention:**
   - `use` prefix for all hooks
   - Descriptive names: `useFlow`, not `useF`
   - Domain-specific: `useDiscoveryFlow`, `useAssessmentFlow`

2. **Structure:**
   - State at top
   - Effects in order of dependency
   - Callbacks last
   - Return object with clear naming

3. **Performance:**
   - Memoize expensive computations
   - Use `useMemo` and `useCallback` appropriately
   - Avoid unnecessary re-renders

## Status Report Template
```markdown
# Beta Team Status Report - [DATE]

## Completed Tasks
- [ ] Task 1: Audit and Map Existing Hooks
- [ ] Task 2: Create Consolidated Core Hooks
- [ ] Task 3: Create Specialized Hooks
- [ ] Task 4: Implement Error and Loading States
- [ ] Task 5: Remove Deprecated Hooks
- [ ] Task 6: Implement Hook Tests

## Hooks Status
| Hook Name | Status | Components Using | Tests |
|-----------|--------|------------------|-------|
| useFlow | Complete | 12 | ✓ |
| useDiscoveryFlow | In Progress | 8 | ✗ |

## Migration Progress
- Components migrated: X/Y
- Old hooks removed: X/Y
- Tests written: X/Y

## Issues Encountered
- Issue description and resolution

## Performance Metrics
- Bundle size change: +/- X KB
- Re-render count: Reduced by X%

## Next Steps
- Planned activities
```

## Resources
- React Hooks Documentation: https://react.dev/reference/react
- Testing Library: https://testing-library.com/docs/react-testing-library/intro/
- Hook Patterns: `/docs/frontend/hook-patterns.md`
- Service Layer: `/src/services/`

## Contact
- Team Lead: Beta Team
- Slack Channel: #beta-hook-consolidation
- Frontend Support: #frontend-team