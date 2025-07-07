# Team Delta - State Management Fix Briefing

## Mission Statement
Team Delta is responsible for fixing state management issues, implementing proper context providers, resolving routing problems, and ensuring consistent application state across the platform.

## Team Objectives
1. Fix multi-tenant context implementation and prop drilling issues
2. Resolve routing issues (404s, navigation failures)
3. Implement proper global state management
4. Fix localStorage/sessionStorage usage patterns
5. Ensure state persistence and recovery

## Specific Tasks

### Task 1: Fix Multi-Tenant Context Implementation
**Current Issue:** X-Client-Account-ID header shows as "[object Object]"

**Files to fix:**
- `/src/contexts/MultiTenantContext.tsx`
- `/src/providers/MultiTenantProvider.tsx`
- `/src/hooks/useMultiTenant.ts`

**Correct Implementation:**
```typescript
// /src/contexts/MultiTenantContext.tsx
interface MultiTenantContextValue {
  clientAccountId: number | null;
  engagementId: string | null;
  userId: number | null;
  setClientAccountId: (id: number) => void;
  setEngagementId: (id: string) => void;
  setUserId: (id: number) => void;
  isLoading: boolean;
  error: Error | null;
}

const MultiTenantContext = createContext<MultiTenantContextValue | undefined>(undefined);

export const MultiTenantProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<{
    clientAccountId: number | null;
    engagementId: string | null;
    userId: number | null;
  }>(() => {
    // Initialize from localStorage with proper parsing
    const stored = localStorage.getItem('multiTenantContext');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        return {
          clientAccountId: parsed.clientAccountId ? Number(parsed.clientAccountId) : null,
          engagementId: parsed.engagementId || null,
          userId: parsed.userId ? Number(parsed.userId) : null
        };
      } catch (e) {
        console.error('Failed to parse stored context:', e);
      }
    }
    return { clientAccountId: null, engagementId: null, userId: null };
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  // Persist to localStorage whenever state changes
  useEffect(() => {
    if (state.clientAccountId !== null) {
      localStorage.setItem('multiTenantContext', JSON.stringify(state));
    }
  }, [state]);
  
  // Validate and set client account ID
  const setClientAccountId = useCallback((id: number) => {
    if (typeof id !== 'number' || isNaN(id)) {
      setError(new Error('Invalid client account ID'));
      return;
    }
    setState(prev => ({ ...prev, clientAccountId: id }));
    setError(null);
  }, []);
  
  const setEngagementId = useCallback((id: string) => {
    if (!id || typeof id !== 'string') {
      setError(new Error('Invalid engagement ID'));
      return;
    }
    setState(prev => ({ ...prev, engagementId: id }));
    setError(null);
  }, []);
  
  const setUserId = useCallback((id: number) => {
    if (typeof id !== 'number' || isNaN(id)) {
      setError(new Error('Invalid user ID'));
      return;
    }
    setState(prev => ({ ...prev, userId: id }));
    setError(null);
  }, []);
  
  // Load initial context from API or auth
  useEffect(() => {
    const loadContext = async () => {
      try {
        const user = await authService.getCurrentUser();
        if (user) {
          setClientAccountId(user.clientAccountId);
          setUserId(user.id);
          if (user.currentEngagementId) {
            setEngagementId(user.currentEngagementId);
          }
        }
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadContext();
  }, [setClientAccountId, setEngagementId, setUserId]);
  
  const value = {
    ...state,
    setClientAccountId,
    setEngagementId,
    setUserId,
    isLoading,
    error
  };
  
  return (
    <MultiTenantContext.Provider value={value}>
      {children}
    </MultiTenantContext.Provider>
  );
};

// Hook with validation
export const useMultiTenant = () => {
  const context = useContext(MultiTenantContext);
  if (!context) {
    throw new Error('useMultiTenant must be used within MultiTenantProvider');
  }
  return context;
};
```

### Task 2: Fix Routing Issues
**Current Issues:** 404 errors, navigation failures, incorrect route registration

**Files to fix:**
- `/src/routes/index.tsx`
- `/src/config/flowRoutes.ts`
- `/src/components/Navigation.tsx`

**Correct Route Configuration:**
```typescript
// /src/config/flowRoutes.ts
export const FLOW_ROUTES = {
  discovery: {
    base: '/discovery',
    cmdbImport: '/discovery/cmdb-import',
    attributeMapping: '/discovery/attribute-mapping',
    dataCleansing: '/discovery/data-cleansing',
    dashboard: '/discovery/dashboard'
  },
  assessment: {
    base: '/assessment',
    start: '/assessment/start',
    questions: '/assessment/questions',
    results: '/assessment/results'
  },
  admin: {
    base: '/admin',
    clients: '/admin/clients',
    createClient: '/admin/clients/create',
    editClient: '/admin/clients/:clientId/edit',
    users: '/admin/users',
    settings: '/admin/settings'
  }
} as const;

// Type-safe route builder
export const buildRoute = (
  route: string,
  params?: Record<string, string | number>
): string => {
  let path = route;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      path = path.replace(`:${key}`, String(value));
    });
  }
  return path;
};

// /src/routes/index.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { FLOW_ROUTES } from '@/config/flowRoutes';

export const AppRoutes = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const { clientAccountId } = useMultiTenant();
  
  if (isLoading) return <LoadingScreen />;
  
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      
      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        
        {/* Discovery Flow Routes */}
        <Route path={FLOW_ROUTES.discovery.base}>
          <Route index element={<DiscoveryDashboard />} />
          <Route path="cmdb-import" element={<CMDBImport />} />
          <Route path="attribute-mapping" element={<AttributeMapping />} />
          <Route path="data-cleansing" element={<DataCleansing />} />
          <Route path="dashboard" element={<FlowDashboard />} />
        </Route>
        
        {/* Assessment Routes */}
        <Route path={FLOW_ROUTES.assessment.base}>
          <Route index element={<AssessmentStart />} />
          <Route path="start" element={<AssessmentStart />} />
          <Route path="questions" element={<AssessmentQuestions />} />
          <Route path="results" element={<AssessmentResults />} />
        </Route>
        
        {/* Admin Routes */}
        <Route path={FLOW_ROUTES.admin.base} element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="clients" element={<ClientList />} />
          <Route path="clients/create" element={<CreateClient />} />
          <Route path="clients/:clientId/edit" element={<EditClient />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="settings" element={<AdminSettings />} />
        </Route>
      </Route>
      
      {/* 404 catch-all */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};
```

### Task 3: Implement Global State Management
**Create proper state management with Zustand:**

```typescript
// /src/stores/appStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface AppState {
  // Multi-tenant context
  clientAccountId: number | null;
  engagementId: string | null;
  userId: number | null;
  
  // Active flows
  activeFlows: Map<string, Flow>;
  
  // UI state
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
  
  // Actions
  setMultiTenantContext: (context: {
    clientAccountId: number;
    engagementId?: string;
    userId?: number;
  }) => void;
  
  addActiveFlow: (flow: Flow) => void;
  updateActiveFlow: (flowId: string, updates: Partial<Flow>) => void;
  removeActiveFlow: (flowId: string) => void;
  
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  
  reset: () => void;
}

const initialState = {
  clientAccountId: null,
  engagementId: null,
  userId: null,
  activeFlows: new Map(),
  sidebarCollapsed: false,
  theme: 'light' as const
};

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      immer((set) => ({
        ...initialState,
        
        setMultiTenantContext: (context) => set((state) => {
          state.clientAccountId = context.clientAccountId;
          if (context.engagementId) state.engagementId = context.engagementId;
          if (context.userId) state.userId = context.userId;
        }),
        
        addActiveFlow: (flow) => set((state) => {
          state.activeFlows.set(flow.id, flow);
        }),
        
        updateActiveFlow: (flowId, updates) => set((state) => {
          const flow = state.activeFlows.get(flowId);
          if (flow) {
            state.activeFlows.set(flowId, { ...flow, ...updates });
          }
        }),
        
        removeActiveFlow: (flowId) => set((state) => {
          state.activeFlows.delete(flowId);
        }),
        
        toggleSidebar: () => set((state) => {
          state.sidebarCollapsed = !state.sidebarCollapsed;
        }),
        
        setTheme: (theme) => set((state) => {
          state.theme = theme;
        }),
        
        reset: () => set(() => initialState)
      })),
      {
        name: 'app-store',
        partialize: (state) => ({
          clientAccountId: state.clientAccountId,
          engagementId: state.engagementId,
          theme: state.theme,
          sidebarCollapsed: state.sidebarCollapsed
        })
      }
    ),
    {
      name: 'AppStore'
    }
  )
);

// Selectors
export const useMultiTenantIds = () => {
  const { clientAccountId, engagementId, userId } = useAppStore();
  return { clientAccountId, engagementId, userId };
};

export const useActiveFlows = () => {
  const activeFlows = useAppStore((state) => state.activeFlows);
  return Array.from(activeFlows.values());
};
```

### Task 4: Fix Navigation State
**Implement proper navigation with state preservation:**

```typescript
// /src/components/Navigation/NavigationProvider.tsx
interface NavigationState {
  history: string[];
  currentPath: string;
  pendingNavigation: string | null;
  navigationBlocked: boolean;
}

export const NavigationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [state, setState] = useState<NavigationState>({
    history: [location.pathname],
    currentPath: location.pathname,
    pendingNavigation: null,
    navigationBlocked: false
  });
  
  // Block navigation when forms have unsaved changes
  const blockNavigation = useCallback((blocked: boolean) => {
    setState(prev => ({ ...prev, navigationBlocked: blocked }));
  }, []);
  
  // Enhanced navigation with guards
  const navigateTo = useCallback((path: string, options?: NavigateOptions) => {
    if (state.navigationBlocked) {
      setState(prev => ({ ...prev, pendingNavigation: path }));
      // Show confirmation dialog
      return;
    }
    
    // Add to history
    setState(prev => ({
      ...prev,
      history: [...prev.history, path].slice(-10), // Keep last 10
      currentPath: path
    }));
    
    navigate(path, options);
  }, [navigate, state.navigationBlocked]);
  
  // Navigate back with history
  const navigateBack = useCallback(() => {
    const history = [...state.history];
    history.pop(); // Remove current
    const previous = history.pop(); // Get previous
    
    if (previous) {
      navigateTo(previous);
    } else {
      navigateTo('/dashboard');
    }
  }, [state.history, navigateTo]);
  
  const value = {
    ...state,
    navigateTo,
    navigateBack,
    blockNavigation
  };
  
  return (
    <NavigationContext.Provider value={value}>
      {children}
      {state.pendingNavigation && (
        <ConfirmNavigationDialog
          onConfirm={() => {
            setState(prev => ({ ...prev, navigationBlocked: false }));
            navigateTo(state.pendingNavigation!);
          }}
          onCancel={() => {
            setState(prev => ({ ...prev, pendingNavigation: null }));
          }}
        />
      )}
    </NavigationContext.Provider>
  );
};
```

### Task 5: Fix localStorage Usage
**Implement safe localStorage wrapper:**

```typescript
// /src/utils/storage.ts
class SafeStorage {
  private prefix: string;
  
  constructor(prefix: string = 'aiforce_') {
    this.prefix = prefix;
  }
  
  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }
  
  setItem<T>(key: string, value: T): void {
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(this.getKey(key), serialized);
    } catch (error) {
      console.error(`Failed to save ${key} to localStorage:`, error);
      // Handle quota exceeded error
      if (error instanceof DOMException && error.code === 22) {
        this.clearOldItems();
        // Retry once
        try {
          const serialized = JSON.stringify(value);
          localStorage.setItem(this.getKey(key), serialized);
        } catch (retryError) {
          console.error('Failed to save after clearing old items:', retryError);
        }
      }
    }
  }
  
  getItem<T>(key: string, defaultValue?: T): T | undefined {
    try {
      const item = localStorage.getItem(this.getKey(key));
      if (item === null) return defaultValue;
      return JSON.parse(item);
    } catch (error) {
      console.error(`Failed to parse ${key} from localStorage:`, error);
      return defaultValue;
    }
  }
  
  removeItem(key: string): void {
    localStorage.removeItem(this.getKey(key));
  }
  
  clear(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => localStorage.removeItem(key));
  }
  
  private clearOldItems(): void {
    const now = Date.now();
    const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days
    
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => {
        try {
          const item = localStorage.getItem(key);
          if (item) {
            const parsed = JSON.parse(item);
            if (parsed._timestamp && now - parsed._timestamp > maxAge) {
              localStorage.removeItem(key);
            }
          }
        } catch {
          // Remove corrupted items
          localStorage.removeItem(key);
        }
      });
  }
}

export const storage = new SafeStorage();
export const sessionStorage = new SafeStorage('aiforce_session_');
```

### Task 6: Implement State Recovery
**Handle state recovery after errors or page refresh:**

```typescript
// /src/providers/StateRecoveryProvider.tsx
export const StateRecoveryProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isRecovering, setIsRecovering] = useState(true);
  const { setMultiTenantContext } = useAppStore();
  const navigate = useNavigate();
  
  useEffect(() => {
    const recoverState = async () => {
      try {
        // 1. Check for saved authentication
        const authToken = storage.getItem('authToken');
        if (!authToken) {
          navigate('/login');
          return;
        }
        
        // 2. Validate token and get user context
        const user = await authService.validateToken(authToken);
        if (!user) {
          navigate('/login');
          return;
        }
        
        // 3. Restore multi-tenant context
        setMultiTenantContext({
          clientAccountId: user.clientAccountId,
          engagementId: user.currentEngagementId,
          userId: user.id
        });
        
        // 4. Restore active flows
        const savedFlows = storage.getItem<Flow[]>('activeFlows', []);
        for (const flow of savedFlows) {
          // Verify flow still exists
          try {
            const currentFlow = await flowService.getStatus(
              user.clientAccountId,
              flow.id
            );
            if (currentFlow && currentFlow.status !== 'completed') {
              useAppStore.getState().addActiveFlow(currentFlow);
            }
          } catch {
            // Flow no longer exists
          }
        }
        
        // 5. Restore navigation state
        const lastPath = storage.getItem('lastPath', '/dashboard');
        if (window.location.pathname === '/') {
          navigate(lastPath);
        }
        
      } catch (error) {
        console.error('State recovery failed:', error);
        // Clear corrupted state
        storage.clear();
        navigate('/login');
      } finally {
        setIsRecovering(false);
      }
    };
    
    recoverState();
  }, [setMultiTenantContext, navigate]);
  
  if (isRecovering) {
    return <LoadingScreen message="Restoring your session..." />;
  }
  
  return <>{children}</>;
};
```

## Success Criteria
1. Multi-tenant headers correctly formatted (numbers, not "[object Object]")
2. All routes working without 404 errors
3. State persists across page refreshes
4. Navigation history maintained
5. No prop drilling - proper context usage
6. localStorage usage is safe and quota-aware
7. State recovery after errors/crashes
8. Zustand store properly typed and tested

## Common Issues and Solutions

### Issue 1: Context Lost on Refresh
**Symptom:** User logged out after refresh
**Solution:** Implement StateRecoveryProvider with proper token validation

### Issue 2: Invalid Header Format
**Symptom:** "[object Object]" in API headers
**Solution:** Ensure proper type conversion:
```typescript
headers: {
  'X-Client-Account-ID': String(clientAccountId),
  'X-Engagement-ID': engagementId || ''
}
```

### Issue 3: Route Not Found
**Symptom:** 404 errors on valid routes
**Solution:** Check route registration order, exact vs non-exact matches

### Issue 4: State Out of Sync
**Symptom:** UI showing stale data
**Solution:** Implement proper state subscriptions and updates

## Rollback Procedures
1. **Create branch for state management fixes:**
   ```bash
   git checkout -b delta-state-management
   git push origin delta-state-management
   ```

2. **Test each fix independently:**
   - Fix multi-tenant context first
   - Then routing
   - Then global state
   - Finally storage

3. **Emergency rollback:**
   ```bash
   # Revert context changes
   git checkout main -- src/contexts/
   git checkout main -- src/providers/
   ```

## Testing Requirements
```typescript
// Test multi-tenant context
describe('MultiTenantContext', () => {
  it('should properly format headers', () => {
    const { result } = renderHook(() => useMultiTenant(), {
      wrapper: MultiTenantProvider
    });
    
    act(() => {
      result.current.setClientAccountId(123);
    });
    
    expect(result.current.clientAccountId).toBe(123);
    expect(typeof result.current.clientAccountId).toBe('number');
  });
});

// Test routing
describe('Routing', () => {
  it('should navigate to correct paths', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/discovery/cmdb-import']}>
        <AppRoutes />
      </MemoryRouter>
    );
    
    expect(container.querySelector('.cmdb-import')).toBeInTheDocument();
  });
});
```

## Status Report Template
```markdown
# Delta Team Status Report - [DATE]

## Completed Tasks
- [ ] Task 1: Fix Multi-Tenant Context Implementation
- [ ] Task 2: Fix Routing Issues
- [ ] Task 3: Implement Global State Management
- [ ] Task 4: Fix Navigation State
- [ ] Task 5: Fix localStorage Usage
- [ ] Task 6: Implement State Recovery

## Bug Fixes
| Issue | Status | Impact | Resolution |
|-------|--------|--------|------------|
| [object Object] headers | Fixed | High | Proper type conversion |
| 404 on routes | Fixed | High | Route registration |

## State Management Status
- Context Providers: X/Y implemented
- Zustand Stores: X/Y migrated
- Prop Drilling: X instances removed

## Test Coverage
- Unit Tests: X%
- Integration Tests: X%
- E2E Tests: X%

## Performance Impact
- State updates: X% faster
- Memory usage: X MB reduction

## Next Steps
- Additional state optimizations
- Performance monitoring setup
```

## Resources
- React Context Best Practices: https://react.dev/learn/passing-data-deeply-with-context
- Zustand Documentation: https://docs.pmnd.rs/zustand/getting-started/introduction
- React Router v6: https://reactrouter.com/en/main
- Web Storage API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API

## Contact
- Team Lead: Delta Team
- Slack Channel: #delta-state-management
- Backend Support: #backend-team
- DevOps Support: #devops-team