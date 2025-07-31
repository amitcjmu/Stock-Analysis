# Task Brief: nextjs-ui-architect

## Mission
Refactor the frontend architecture to eliminate custom caching, consolidate context providers, optimize React Query configuration, and reduce component re-renders by 60% while maintaining full functionality.

## Context
The frontend currently has multiple overlapping context providers, custom API caching that conflicts with backend caching, and excessive re-renders. Your task is to simplify the architecture and rely on React Query + backend Redis caching.

## Primary Objectives

### 1. Remove Custom API Cache (Week 4)
- Eliminate custom caching from `src/config/api.ts`
- Implement request deduplication without caching
- Maintain backward compatibility with feature flags
- Ensure no functionality is lost

### 2. Create GlobalContext Provider (Week 5)
- Design unified global state management
- Consolidate AuthContext, ClientContext, etc.
- Implement proper initialization flow
- Add session storage for offline support

### 3. Optimize React Query (Week 4)
- Configure optimal cache times for each endpoint
- Implement proper cache invalidation
- Add WebSocket listeners for cache events
- Configure request batching

### 4. Component Optimization (Week 5)
- Implement strategic memoization
- Reduce unnecessary re-renders
- Optimize heavy computations
- Add performance monitoring

## Specific Deliverables

### Week 4 Deliverables

```typescript
// 1. Simplified API Client (No Custom Cache)
// File: src/lib/api/apiClient.ts
import { getAuthHeaders } from '@/utils/auth';

class ApiClient {
  private pendingRequests = new Map<string, Promise<any>>();
  
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const requestKey = `GET:${endpoint}`;
    
    // Request deduplication only (no caching)
    if (this.pendingRequests.has(requestKey)) {
      return this.pendingRequests.get(requestKey);
    }
    
    const request = this.executeRequest<T>(endpoint, {
      ...options,
      method: 'GET'
    }).finally(() => {
      this.pendingRequests.delete(requestKey);
    });
    
    this.pendingRequests.set(requestKey, request);
    return request;
  }
  
  private async executeRequest<T>(
    endpoint: string,
    options: RequestInit
  ): Promise<T> {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
      },
      // Honor backend cache headers
      cache: FEATURE_FLAGS.ENABLE_CACHE_HEADERS ? 'default' : 'no-store',
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }
    
    return response.json();
  }
}

export const apiClient = new ApiClient();
```

```typescript
// 2. React Query Configuration with WebSocket Integration
// File: src/hooks/discovery/attribute-mapping/useFieldMappings.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from '@/hooks/useWebSocket';

export const useFieldMappings = (importId: string | null) => {
  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();
  
  // Listen for cache invalidation events
  useEffect(() => {
    if (!importId) return;
    
    const unsubscribe = subscribe('cache_invalidation', (event) => {
      if (event.entity === 'field_mappings' && event.import_id === importId) {
        queryClient.invalidateQueries({
          queryKey: ['field-mappings', importId],
          exact: true
        });
      }
    });
    
    return unsubscribe;
  }, [importId, queryClient, subscribe]);
  
  return useQuery({
    queryKey: ['field-mappings', importId],
    queryFn: () => apiClient.get(`/api/v1/field-mappings/${importId}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!importId,
  });
};
```

### Week 5 Deliverables

```typescript
// 3. Global Context Provider
// File: src/contexts/GlobalContext.tsx
import React, { createContext, useContext, useReducer, useRef, useEffect } from 'react';
import { contextStorage } from '@/utils/contextStorage';

interface GlobalState {
  auth: {
    user: User | null;
    isLoading: boolean;
    isInitialized: boolean;
  };
  context: {
    client: Client | null;
    engagement: Engagement | null;
    flow: Flow | null;
  };
  ui: {
    sidebarOpen: boolean;
    notifications: Notification[];
  };
}

const GlobalContext = createContext<{
  state: GlobalState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export const GlobalContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(globalReducer, initialState);
  const initRef = useRef(false);
  
  // Single initialization with proper error handling
  useEffect(() => {
    if (initRef.current || state.auth.isInitialized) return;
    initRef.current = true;
    
    const initialize = async () => {
      dispatch({ type: 'AUTH_INIT_START' });
      
      try {
        // Check session storage first
        const cachedContext = contextStorage.get('user_context');
        if (cachedContext && !isExpired(cachedContext)) {
          dispatch({ 
            type: 'AUTH_INIT_SUCCESS', 
            payload: cachedContext 
          });
          return;
        }
        
        // Fetch fresh context
        const context = await apiClient.get('/api/v1/context/full');
        contextStorage.set('user_context', context);
        
        dispatch({ 
          type: 'AUTH_INIT_SUCCESS', 
          payload: context 
        });
      } catch (error) {
        dispatch({ 
          type: 'AUTH_INIT_ERROR', 
          payload: error 
        });
      }
    };
    
    initialize();
  }, [state.auth.isInitialized]);
  
  return (
    <GlobalContext.Provider value={{ state, dispatch }}>
      <ErrorBoundary>
        {state.auth.isInitialized ? children : <LoadingScreen />}
      </ErrorBoundary>
    </GlobalContext.Provider>
  );
};

export const useGlobalContext = () => {
  const context = useContext(GlobalContext);
  if (!context) {
    throw new Error('useGlobalContext must be used within GlobalContextProvider');
  }
  return context;
};
```

```typescript
// 4. Component Memoization Strategy
// File: src/components/discovery/attribute-mapping/FieldMappingsTab/index.tsx
import React, { memo, useMemo, useCallback } from 'react';

export const FieldMappingsTab = memo(({ 
  importId,
  onMappingUpdate 
}: FieldMappingsTabProps) => {
  const { data: mappings, isLoading } = useFieldMappings(importId);
  
  // Memoize expensive computations
  const mappingStats = useMemo(() => {
    if (!mappings) return null;
    return calculateMappingStatistics(mappings);
  }, [mappings]);
  
  // Memoize callbacks to prevent child re-renders
  const handleBulkApprove = useCallback(async (selectedIds: string[]) => {
    await bulkApproveMappings(importId, selectedIds);
    onMappingUpdate?.();
  }, [importId, onMappingUpdate]);
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <ThreeColumnFieldMapper
      mappings={mappings}
      stats={mappingStats}
      onBulkApprove={handleBulkApprove}
    />
  );
}, (prevProps, nextProps) => {
  // Custom comparison for re-render optimization
  return prevProps.importId === nextProps.importId;
});
```

## Technical Requirements

### Performance Requirements
- 60% reduction in component re-renders
- Page load time < 2 seconds
- Time to interactive < 3 seconds
- Memory usage stable over time

### Migration Requirements
- Use feature flags for gradual rollout
- Maintain backward compatibility
- No breaking changes to public APIs
- Comprehensive testing at each stage

### Integration Requirements
- WebSocket integration for cache events
- Session storage for offline support
- React Query for all data fetching
- Performance monitoring integration

## Success Criteria
- Custom API cache completely removed
- All contexts consolidated into GlobalContext
- React Query handling all client caching
- 60% reduction in re-renders achieved

## Resources
- React Query v5 documentation
- Next.js 14 performance guide
- Current frontend structure in `src/`
- WebSocket implementation examples

## Migration Strategy

### Phase 1: Feature Flag Setup (Day 1)
```typescript
export const FEATURE_FLAGS = {
  USE_GLOBAL_CONTEXT: false,
  DISABLE_CUSTOM_CACHE: false,
  ENABLE_WEBSOCKET_CACHE: false,
};
```

### Phase 2: Gradual Migration (Week 4-5)
1. Enable WebSocket cache invalidation
2. Disable custom cache for specific endpoints
3. Test thoroughly with feature flags
4. Roll out GlobalContext to beta users
5. Monitor performance metrics

### Phase 3: Full Rollout (Week 6)
1. Enable all features for 100% users
2. Remove old code paths
3. Update documentation
4. Performance validation

## Communication
- Daily updates to progress dashboard
- Coordinate with python-crewai-fastapi-expert on WebSocket events
- Work with qa-playwright-tester on frontend tests
- Weekly sync with orchestrator

## Timeline
- Week 4: Remove custom cache, optimize React Query
- Week 5: Implement GlobalContext, component optimization
- Week 6: Testing and gradual rollout
- Ongoing: Performance monitoring and adjustments

---
**Assigned by**: Claude Code (Orchestrator)
**Start Date**: Week 4 of project
**Priority**: Critical Path