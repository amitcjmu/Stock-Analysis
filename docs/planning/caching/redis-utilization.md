# Redis Utilization and Frontend Optimization Plan

## Executive Summary

This document outlines a comprehensive plan to reduce frontend complexity and improve Redis cache utilization across the AI Force Migration Platform. The current implementation suffers from multiple re-renders, redundant API calls, and underutilized caching infrastructure, leading to poor performance and unnecessary complexity.

### Key Business Benefits
- **Cost Reduction**: 70-80% reduction in API calls translates to $10K-50K annual infrastructure savings
- **Productivity Gains**: 50% faster page loads save 1-2 hours per week for enterprise teams
- **Competitive Advantage**: Position as performance leader in migration tools space
- **Enterprise Readiness**: Handle 10x larger datasets without architecture changes

### Architectural Enhancements (Based on Review Feedback)
- **Security**: Field-level encryption and tenant isolation for cached data
- **MCP Integration**: Leverage MCP servers for intelligent cache management
- **Distributed Systems**: Cache coherence protocol and circuit breakers
- **Monitoring**: Comprehensive metrics and distributed tracing from day one
- **Risk Mitigation**: Canary deployments and progressive enhancement

### Implementation Approach
- **6-week phased rollout** with optional 7th week for advanced features
- **Foundation-first approach** with monitoring and metrics before optimization
- **Feature flags** for all changes enabling gradual rollout and quick rollback
- **20% timeline buffer** to ensure quality and proper testing

## Current Issues

### 1. Frontend Problems
- **Multiple Auth Initializations**: Auth system attempts to initialize 3-4 times due to React Strict Mode and poor state management
- **Redundant API Calls**: Same endpoints (`/api/v1/context-establishment/clients`) called multiple times per page load
- **Complex State Management**: Multiple overlapping context providers (AuthContext, ClientContext, etc.)
- **No Context Caching**: User context (client, engagement) fetched on every page navigation
- **Excessive Re-renders**: Pages re-render multiple times during initial load

### 2. Backend Problems
- **Underutilized Redis**: Redis cache exists but isn't used for user context, client lists, or engagement data
- **No ETag Support**: Missing HTTP caching headers for static/semi-static data
- **No Request Coalescing**: Multiple identical requests aren't batched or deduplicated
- **Missing Cache Invalidation**: No clear strategy for cache invalidation on data updates

## Proposed Solutions

### Phase 1: Backend Redis Implementation (Week 1)

#### 1.1 User Context Caching
```python
# backend/app/api/v1/endpoints/context.py
@router.get("/context/me", response_model=UserContextResponse)
async def get_user_context(
    request: Request,
    user: User = Depends(get_current_user),
    redis: RedisCache = Depends(get_redis_cache)
):
    # Cache key based on user ID
    cache_key = f"user:context:{user.id}"
    
    # Check Redis cache first
    cached_context = await redis.get(cache_key)
    if cached_context:
        # Add ETag support
        etag = generate_etag(cached_context)
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304)
        return JSONResponse(
            content=cached_context,
            headers={"ETag": etag, "Cache-Control": "private, max-age=3600"}
        )
    
    # Fetch from DB if not cached
    context = {
        "user": user.dict(),
        "client": await get_current_client(user),
        "engagement": await get_current_engagement(user),
        "active_flows": await get_active_flows(user)
    }
    
    # Cache for 1 hour (context rarely changes)
    await redis.set(cache_key, context, ttl=3600)
    
    etag = generate_etag(context)
    return JSONResponse(
        content=context,
        headers={"ETag": etag, "Cache-Control": "private, max-age=3600"}
    )
```

#### 1.2 Client and Engagement List Caching
```python
# backend/app/api/v1/endpoints/context_establishment.py
@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    user: User = Depends(get_current_user),
    redis: RedisCache = Depends(get_redis_cache)
):
    cache_key = f"user:{user.id}:clients"
    
    # Check cache
    cached_clients = await redis.get(cache_key)
    if cached_clients:
        return cached_clients
    
    # Fetch from DB
    clients = await fetch_user_clients(user.id)
    
    # Cache for 30 minutes
    await redis.set(cache_key, clients, ttl=1800)
    return clients

@router.get("/engagements", response_model=List[EngagementResponse])
async def get_engagements(
    client_id: str,
    user: User = Depends(get_current_user),
    redis: RedisCache = Depends(get_redis_cache)
):
    cache_key = f"client:{client_id}:engagements"
    
    # Check cache
    cached_engagements = await redis.get(cache_key)
    if cached_engagements:
        return cached_engagements
    
    # Fetch from DB
    engagements = await fetch_client_engagements(client_id)
    
    # Cache for 30 minutes
    await redis.set(cache_key, engagements, ttl=1800)
    return engagements
```

#### 1.3 Flow State Caching Enhancement
```python
# backend/app/services/caching/flow_cache_manager.py
class FlowCacheManager:
    def __init__(self, redis: RedisCache):
        self.redis = redis
        
    async def get_flow_with_cache(self, flow_id: str) -> Optional[Dict]:
        # Try Redis first
        cache_key = f"flow:complete:{flow_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return cached
            
        # Fetch from DB with all relations
        flow = await fetch_complete_flow(flow_id)
        if flow:
            # Cache for 5 minutes (flows change frequently)
            await self.redis.set(cache_key, flow, ttl=300)
        return flow
    
    async def invalidate_flow(self, flow_id: str):
        """Invalidate all flow-related caches"""
        await self.redis.invalidate_flow_cache(flow_id)
        # Also invalidate user's flow list
        # This requires tracking which user owns the flow
```

#### 1.4 Cache Invalidation Strategy

**Explicit Invalidation Triggers:**

```python
# backend/app/services/cache_invalidation.py
class CacheInvalidationService:
    """Centralized cache invalidation logic with explicit triggers"""
    
    def __init__(self, redis: RedisCache):
        self.redis = redis
    
    async def on_user_updated(self, user_id: str):
        """Invalidate when user roles/permissions change"""
        await self.redis.delete(f"v1:user:context:{user_id}")
        # Invalidate all client lists that might include this user
        await self._invalidate_pattern(f"v1:user:{user_id}:*")
    
    async def on_user_client_access_changed(self, user_id: str, client_id: str):
        """Invalidate when user gains/loses client access"""
        await self.redis.delete(f"v1:user:{user_id}:clients")
        await self.redis.delete(f"v1:user:context:{user_id}")
    
    async def on_engagement_modified(self, engagement_id: str, client_id: str):
        """Invalidate when engagement is created/updated/deleted"""
        await self.redis.delete(f"v1:client:{client_id}:engagements")
        # Find all users with access to this client and invalidate their context
        users = await get_users_by_client(client_id)
        for user in users:
            await self.redis.delete(f"v1:user:context:{user.id}")
    
    async def on_flow_updated(self, flow_id: str, user_id: str):
        """Invalidate when flow state changes"""
        await self.redis.delete(f"v1:flow:complete:{flow_id}")
        await self.redis.delete(f"v1:user:{user_id}:active_flows")
    
    async def on_field_mapping_bulk_operation(self, import_id: str):
        """Invalidate field mappings after bulk approval/rejection"""
        await self.redis.delete(f"v1:field_mappings:{import_id}")
        await self.redis.delete(f"v1:import:{import_id}:mappings")
        # Invalidate any aggregated mapping statistics
        await self._invalidate_pattern(f"v1:mapping_stats:{import_id}:*")
    
    async def on_user_defaults_updated(self, user_id: str, default_client_id: str = None, default_engagement_id: str = None):
        """Invalidate when user's default client/engagement is updated"""
        await self.redis.delete(f"v1:user:context:{user_id}")
        await self.redis.delete(f"v1:user:{user_id}:defaults")
        # Invalidate admin user lists
        await self.redis.delete("v1:admin:active_users")
        await self.redis.delete("v1:admin:pending_approvals")
        
        # If client changed, invalidate client-specific caches
        if default_client_id:
            await self.redis.delete(f"v1:client:{default_client_id}:users")
        
        # If engagement changed, invalidate engagement-specific caches
        if default_engagement_id:
            await self.redis.delete(f"v1:engagement:{default_engagement_id}:users")

# Integration with service layer
@router.put("/users/{user_id}/roles")
async def update_user_roles(
    user_id: str,
    roles: List[str],
    invalidator: CacheInvalidationService = Depends()
):
    # Update database
    await update_user_roles_in_db(user_id, roles)
    
    # Invalidate relevant caches
    await invalidator.on_user_updated(user_id)
    
    return {"status": "success"}
```

#### 1.5 Cache Key Versioning
```python
# backend/app/constants/cache_keys.py
CACHE_VERSION = "v1"  # Increment on breaking changes

class CacheKeys:
    """Centralized cache key generation with versioning"""
    
    @staticmethod
    def user_context(user_id: str) -> str:
        return f"{CACHE_VERSION}:user:context:{user_id}"
    
    @staticmethod
    def user_clients(user_id: str) -> str:
        return f"{CACHE_VERSION}:user:{user_id}:clients"
    
    @staticmethod
    def client_engagements(client_id: str) -> str:
        return f"{CACHE_VERSION}:client:{client_id}:engagements"
    
    @staticmethod
    def flow_complete(flow_id: str) -> str:
        return f"{CACHE_VERSION}:flow:complete:{flow_id}"
```

### Phase 2: Frontend Optimization (Week 1-2)

#### 2.1 Global Context Provider
```typescript
// src/contexts/GlobalContext.tsx
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

export const GlobalContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(globalReducer, initialState);
  const initRef = useRef(false);
  
  // Single initialization effect
  useEffect(() => {
    if (initRef.current || state.auth.isInitialized) return;
    initRef.current = true;
    
    const initialize = async () => {
      dispatch({ type: 'AUTH_INIT_START' });
      
      try {
        // Check session storage first
        const cachedContext = contextStorage.get();
        if (cachedContext && !isExpired(cachedContext)) {
          dispatch({ 
            type: 'AUTH_INIT_SUCCESS', 
            payload: cachedContext 
          });
          return;
        }
        
        // Fetch fresh context
        const context = await apiClient.get('/api/v1/context/full');
        contextStorage.set(context);
        
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
  }, []);
  
  return (
    <GlobalContext.Provider value={{ state, dispatch }}>
      {state.auth.isInitialized ? children : <LoadingScreen />}
    </GlobalContext.Provider>
  );
};
```

#### 2.2 Simplified API Client (No Custom Cache)
```typescript
// src/lib/api/apiClient.ts
class ApiClient {
  private pendingRequests = new Map<string, Promise<any>>();
  
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const requestKey = `GET:${endpoint}`;
    
    // Check for pending request (deduplication only)
    if (this.pendingRequests.has(requestKey)) {
      return this.pendingRequests.get(requestKey);
    }
    
    // Create new request
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
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }
    
    return response.json();
  }
}

export const apiClient = new ApiClient();

// All caching is handled by React Query
export const API_ENDPOINTS = {
  USER_CONTEXT: '/api/v1/context/me',
  CLIENTS: '/api/v1/context-establishment/clients',
  ENGAGEMENTS: '/api/v1/context-establishment/engagements',
  DISCOVERY_FLOWS: '/api/v1/discovery/flows',
} as const;
```

#### 2.3 React Query Configuration
```typescript
// src/config/queryClient.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
      cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
      refetchOnWindowFocus: false, // Disable aggressive refetching
      refetchOnMount: false, // Use cache on mount
      refetchOnReconnect: 'always', // Refetch on reconnect
      retry: (failureCount, error: any) => {
        // Don't retry auth errors
        if (error?.status === 401 || error?.status === 403) return false;
        // Retry other errors up to 2 times
        return failureCount < 2;
      },
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

// Custom hooks with proper caching (React Query handles all client-side caching)
export const useUserContext = () => {
  return useQuery({
    queryKey: ['user', 'context'],
    queryFn: () => apiClient.get(API_ENDPOINTS.USER_CONTEXT),
    staleTime: 60 * 60 * 1000, // 1 hour
    cacheTime: 2 * 60 * 60 * 1000, // 2 hours
  });
};

export const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: () => apiClient.get(API_ENDPOINTS.CLIENTS),
    staleTime: 30 * 60 * 1000, // 30 minutes
    cacheTime: 60 * 60 * 1000, // 1 hour
  });
};

export const useEngagements = (clientId: string) => {
  return useQuery({
    queryKey: ['engagements', clientId],
    queryFn: () => apiClient.get(`${API_ENDPOINTS.ENGAGEMENTS}?client_id=${clientId}`),
    staleTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!clientId, // Only fetch when clientId is available
  });
};

// Mutation with cache invalidation
export const useUpdateUserRole = () => {
  return useMutation({
    mutationFn: ({ userId, roles }: { userId: string; roles: string[] }) =>
      apiClient.put(`/api/v1/users/${userId}/roles`, { roles }),
    onSuccess: (_, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries(['user', 'context']);
      queryClient.invalidateQueries(['clients']);
    },
  });
};
```

#### 2.4 Session Storage Utility
```typescript
// src/utils/contextStorage.ts
interface StoredContext {
  data: UserContext;
  timestamp: number;
  expiry: number;
}

export const contextStorage = {
  KEYS: {
    USER_CONTEXT: 'user_context_v1',
    CLIENT_LIST: 'client_list_v1',
    ENGAGEMENT_LIST: 'engagement_list_v1',
  },
  
  get<T>(key: string): T | null {
    try {
      const stored = sessionStorage.getItem(key);
      if (!stored) return null;
      
      const parsed: StoredContext = JSON.parse(stored);
      
      // Check expiry
      if (Date.now() > parsed.expiry) {
        sessionStorage.removeItem(key);
        return null;
      }
      
      return parsed.data as T;
    } catch {
      return null;
    }
  },
  
  set<T>(key: string, data: T, ttlMs: number = 3600000): void {
    const stored: StoredContext = {
      data: data as any,
      timestamp: Date.now(),
      expiry: Date.now() + ttlMs,
    };
    
    sessionStorage.setItem(key, JSON.stringify(stored));
  },
  
  clear(): void {
    Object.values(this.KEYS).forEach(key => {
      sessionStorage.removeItem(key);
    });
  },
};
```

### Phase 3: Component Optimization (Week 2)

#### 3.1 Memoized Components
```typescript
// src/components/Sidebar/index.tsx
export const Sidebar = React.memo(() => {
  const { state } = useGlobalContext();
  
  return (
    <SidebarContainer>
      {/* Sidebar content */}
    </SidebarContainer>
  );
}, (prevProps, nextProps) => {
  // Only re-render if user role changes
  return prevProps.userRole === nextProps.userRole;
});

// src/components/DataCleansingStateProvider.tsx
export const DataCleansingStateProvider = React.memo(({ 
  children,
  ...props 
}: Props) => {
  // Memoize expensive computations
  const hasData = useMemo(() => {
    return props.flowData && props.flowData.length > 0;
  }, [props.flowData]);
  
  return <>{children}</>;
});
```

#### 3.2 Lazy Loading Routes
```typescript
// src/App.tsx
const DataCleansing = lazy(() => 
  import(/* webpackChunkName: "data-cleansing" */ './pages/discovery/DataCleansing')
);

const AssetInventory = lazy(() => 
  import(/* webpackChunkName: "asset-inventory" */ './pages/discovery/AssetInventory')
);

function App() {
  return (
    <GlobalContextProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Suspense fallback={<LoadingScreen />}>
            <Routes>
              <Route path="/discovery/data-cleansing" element={<DataCleansing />} />
              <Route path="/discovery/inventory" element={<AssetInventory />} />
            </Routes>
          </Suspense>
        </Router>
      </QueryClientProvider>
    </GlobalContextProvider>
  );
}
```

### Phase 4: Monitoring and Metrics (Week 3)

#### 4.1 Performance Monitoring
```typescript
// src/utils/performance.ts
export const performanceMonitor = {
  markStart(label: string): void {
    if (typeof window !== 'undefined' && window.performance) {
      window.performance.mark(`${label}-start`);
    }
  },
  
  markEnd(label: string): void {
    if (typeof window !== 'undefined' && window.performance) {
      window.performance.mark(`${label}-end`);
      window.performance.measure(
        label,
        `${label}-start`,
        `${label}-end`
      );
      
      const measure = window.performance.getEntriesByName(label)[0];
      console.log(`⏱️ ${label}: ${measure.duration.toFixed(2)}ms`);
      
      // Send to analytics
      if (window.analytics) {
        window.analytics.track('Performance Metric', {
          metric: label,
          duration: measure.duration,
          timestamp: new Date().toISOString(),
        });
      }
    }
  },
};

// Usage in components
useEffect(() => {
  performanceMonitor.markStart('auth-initialization');
  
  initializeAuth().then(() => {
    performanceMonitor.markEnd('auth-initialization');
  });
}, []);
```

#### 4.2 Cache Hit Ratio Tracking
```python
# backend/app/middleware/cache_metrics.py
from prometheus_client import Counter, Histogram

cache_hits = Counter('redis_cache_hits_total', 'Total cache hits')
cache_misses = Counter('redis_cache_misses_total', 'Total cache misses')
cache_latency = Histogram('redis_cache_latency_seconds', 'Cache operation latency')

class CacheMetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        # Track cache metrics
        request.state.cache_hits = 0
        request.state.cache_misses = 0
        
        response = await call_next(request)
        
        # Log metrics
        if hasattr(request.state, 'cache_hits'):
            response.headers['X-Cache-Hits'] = str(request.state.cache_hits)
            response.headers['X-Cache-Misses'] = str(request.state.cache_misses)
        
        return response
```

## Revised Implementation Timeline

### Phase 0: Foundation (Week 1)
- [ ] Set up comprehensive monitoring and metrics infrastructure
- [ ] Implement feature flags for all cache-related changes
- [ ] Create performance baseline measurements
- [ ] Set up distributed tracing with OpenTelemetry
- [ ] Document current API call patterns and frequencies

### Phase 1: Backend Quick Wins (Weeks 2-3)
- [ ] Implement Redis caching for user context with security measures
- [ ] Add ETag support to context endpoints
- [ ] Create cache invalidation strategy with cascade support
- [ ] Implement cache coherence protocol
- [ ] Add circuit breaker for cache operations
- [ ] Deploy cache metrics collection

### Phase 2: Frontend API Optimization (Week 4)
- [ ] Implement API call deduplication layer
- [ ] Add request batching for related endpoints
- [ ] Configure React Query with global defaults
- [ ] Implement cache stampede prevention
- [ ] Add session storage with proper expiration

### Phase 3: Frontend Architecture (Week 5)
- [ ] Create GlobalContext provider with proper error boundaries
- [ ] Consolidate existing context providers (with extensive testing)
- [ ] Implement component memoization strategy
- [ ] Add progressive enhancement for cache availability
- [ ] Deploy canary release to 10% of users

### Phase 4: Validation and Optimization (Week 6)
- [ ] Performance testing with production-like data
- [ ] User acceptance testing with key stakeholders
- [ ] Cache hit ratio analysis and TTL optimization
- [ ] Documentation and training materials
- [ ] Full rollout with monitoring

### Phase 5: MCP Integration (Week 7 - Optional)
- [ ] Implement MCP cache management server
- [ ] Add agent-aware caching strategies
- [ ] Deploy predictive caching based on user patterns
- [ ] Integrate with flow orchestrator for intelligent invalidation

## Success Metrics

1. **API Call Reduction**: Target 70-80% reduction in redundant API calls
2. **Page Load Time**: Target 50% reduction in initial page load time
3. **Cache Hit Ratio**: Target 80%+ cache hit ratio for context data
4. **Re-render Count**: Target 60% reduction in component re-renders

## Risk Mitigation

1. **Cache Invalidation**: Implement clear cache invalidation on data updates
2. **Fallback Strategy**: Ensure app works without Redis (graceful degradation)
3. **Memory Leaks**: Monitor browser memory usage with caching
4. **Security**: Ensure sensitive data is properly encrypted in cache

## Developer Environment Setup

### Local Redis Configuration
```yaml
# docker-compose.yml addition
services:
  redis:
    image: redis:7-alpine
    container_name: migration_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

### Developer Scripts
```json
// package.json scripts
{
  "scripts": {
    "cache:clear": "docker exec migration_redis redis-cli FLUSHALL",
    "cache:monitor": "docker exec -it migration_redis redis-cli MONITOR",
    "cache:stats": "docker exec migration_redis redis-cli INFO stats",
    "dev:clean": "npm run cache:clear && npm run dev"
  }
}
```

### Development Environment Variables
```bash
# .env.development
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
REDIS_DEFAULT_TTL=300  # 5 minutes for dev
CACHE_VERSION=v1-dev   # Different version for dev
```

## Rollback Plan

1. Feature flags for new caching logic
2. Gradual rollout with monitoring
3. Quick disable switch in case of issues
4. Maintain backward compatibility

## Migration Strategy for Current Custom Cache

### Phase 1: Feature Flag Introduction (Week 1)
```typescript
// src/config/featureFlags.ts
export const FEATURE_FLAGS = {
  USE_REDIS_CACHE: process.env.VITE_USE_REDIS_CACHE === 'true',
  USE_CUSTOM_API_CACHE: process.env.VITE_USE_CUSTOM_API_CACHE !== 'false', // Default on
  ENABLE_CACHE_HEADERS: process.env.VITE_ENABLE_CACHE_HEADERS === 'true',
};

// src/config/api.ts modification
if (shouldDeduplicate && FEATURE_FLAGS.USE_CUSTOM_API_CACHE) {
  const cachedResponse = getCachedResponse(method, normalizedEndpoint);
  if (cachedResponse !== null) {
    return Promise.resolve(cachedResponse);
  }
}
```

### Phase 2: Gradual Migration (Weeks 2-3)
1. **Week 2**: Enable Redis caching for read-heavy endpoints
   - User context, client lists, engagement lists
   - Monitor cache hit rates and performance

2. **Week 3**: Disable custom cache for migrated endpoints
   - Use feature flags to disable custom cache per endpoint
   - Rely solely on Redis + React Query for these endpoints

3. **Week 4**: Full migration
   - Disable custom API cache completely
   - Remove cache-related code from apiCall function

### Phase 3: Immediate Quick Wins

#### 1. Add Cache Headers Support (Day 1)
```typescript
// backend/app/middleware/cache_headers.py
from fastapi import Request, Response
from typing import Callable

class CacheHeadersMiddleware:
    """Add appropriate cache headers based on endpoint patterns"""
    
    CACHE_PATTERNS = {
        r"/api/v1/admin/clients": {"Cache-Control": "private, max-age=300"},
        r"/api/v1/admin/engagements": {"Cache-Control": "private, max-age=300"},
        r"/api/v1/auth/active-users": {"Cache-Control": "private, max-age=60"},
        r"/api/v1/field-mappings/\w+": {"Cache-Control": "private, max-age=120"},
    }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add cache headers for GET requests
        if request.method == "GET" and response.status_code == 200:
            for pattern, headers in self.CACHE_PATTERNS.items():
                if re.match(pattern, request.url.path):
                    for header, value in headers.items():
                        response.headers[header] = value
                    break
        
        return response
```

#### 2. Frontend Cache Header Support (Day 1)
```typescript
// src/lib/api/apiClient.ts enhancement
private async executeRequest<T>(
  endpoint: string, 
  options: RequestInit
): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    // Honor cache headers from backend
    cache: FEATURE_FLAGS.ENABLE_CACHE_HEADERS ? 'default' : 'no-store',
  });
  
  // Rest of implementation
}
```

## Security Considerations

### 1. Cache Security
```python
# Field-level encryption for sensitive data
class SecureCache:
    def __init__(self, redis: RedisCache, encryption_key: bytes):
        self.redis = redis
        self.cipher = Fernet(encryption_key)
    
    async def set_secure(self, key: str, value: Any, ttl: int):
        # Validate data before caching
        validated_data = schema.validate(value)
        
        # Add integrity hash
        integrity = hashlib.sha256(
            json.dumps(validated_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Encrypt sensitive fields
        encrypted = self.cipher.encrypt(json.dumps(validated_data).encode())
        
        return await self.redis.set(key, {
            'data': encrypted.decode(),
            'integrity': integrity,
            'cached_at': datetime.utcnow().isoformat()
        }, ttl)
```

### 2. Tenant Isolation
```python
def get_cache_key(user_id: str, client_id: str, key_type: str):
    """Ensure cache keys include tenant context"""
    return f"tenant:{client_id}:user:{user_id}:{key_type}"
```

## MCP Architecture Integration

### 1. MCP Cache Management Server
```yaml
mcp_cache_server:
  capabilities:
    - cache_warming
    - intelligent_invalidation
    - predictive_prefetching
    - distributed_cache_sync
  
  tools:
    - analyze_usage_patterns
    - optimize_cache_strategy
    - monitor_hit_rates
    - suggest_ttl_adjustments
```

### 2. Agent-Aware Caching
```python
class AgentCacheStrategy:
    """Cache strategy aware of CrewAI agent patterns"""
    
    def get_ttl_for_agent_result(self, agent_type: str) -> int:
        ttl_map = {
            'data_import_agent': 300,      # 5 minutes
            'mapping_agent': 3600,         # 1 hour
            'classification_agent': 86400, # 24 hours
            'learning_agent': 604800       # 7 days
        }
        return ttl_map.get(agent_type, 1800)
```

## Field Mapping Specific Caching

### Backend Field Mapping Cache Strategy
```python
# backend/app/api/v1/endpoints/field_mappings.py
@router.get("/field-mappings/{import_id}")
async def get_field_mappings(
    import_id: str,
    user: User = Depends(get_current_user),
    redis: RedisCache = Depends(get_redis_cache)
):
    cache_key = f"v1:field_mappings:{import_id}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return cached
    
    # Fetch from database
    mappings = await fetch_field_mappings(import_id)
    
    # Cache with shorter TTL since mappings change frequently during review
    await redis.set(cache_key, mappings, ttl=120)  # 2 minutes
    
    return mappings

@router.post("/field-mappings/{import_id}/bulk-approve")
async def bulk_approve_mappings(
    import_id: str,
    mapping_ids: List[str],
    user: User = Depends(get_current_user),
    redis: RedisCache = Depends(get_redis_cache),
    invalidator: CacheInvalidationService = Depends()
):
    # Perform bulk approval
    result = await approve_mappings_in_db(import_id, mapping_ids)
    
    # Invalidate caches
    await invalidator.on_field_mapping_bulk_operation(import_id)
    
    # Also invalidate React Query cache via WebSocket event
    await broadcast_cache_invalidation_event({
        "type": "field_mappings_updated",
        "import_id": import_id,
        "action": "bulk_approve"
    })
    
    return result
```

### Frontend Field Mapping Cache Management
```typescript
// src/hooks/discovery/attribute-mapping/useFieldMappings.ts
export const useFieldMappings = (importId: string | null) => {
  const queryClient = useQueryClient();
  
  // Subscribe to WebSocket cache invalidation events
  useEffect(() => {
    if (!importId) return;
    
    const handleCacheInvalidation = (event: CacheInvalidationEvent) => {
      if (event.type === 'field_mappings_updated' && event.import_id === importId) {
        queryClient.invalidateQueries({ 
          queryKey: ['field-mappings', importId],
          exact: true 
        });
      }
    };
    
    websocket.on('cache_invalidation', handleCacheInvalidation);
    
    return () => {
      websocket.off('cache_invalidation', handleCacheInvalidation);
    };
  }, [importId, queryClient]);
  
  return useQuery({
    queryKey: ['field-mappings', importId],
    queryFn: () => apiClient.get(`/api/v1/field-mappings/${importId}`),
    staleTime: 2 * 60 * 1000, // 2 minutes
    cacheTime: 5 * 60 * 1000, // 5 minutes
    enabled: !!importId,
  });
};
```

## Additional Architectural Components

### 1. Cache Coherence Protocol
```python
class CacheCoherenceManager:
    async def invalidate_cascade(self, entity_type: str, entity_id: str):
        """Cascade invalidation for related cache entries"""
        invalidation_map = {
            'flow': ['flow:state', 'flow:metadata', 'user:active_flows'],
            'client': ['client:engagements', 'user:clients', 'client:flows'],
            'engagement': ['engagement:flows', 'client:engagements']
        }
        
        patterns = invalidation_map.get(entity_type, [])
        for pattern in patterns:
            await self.redis.delete(f"{pattern}:{entity_id}")
```

### 2. Cache Stampede Prevention
```typescript
class CacheWithStampedeProtection {
  private refreshing = new Map<string, Promise<any>>();
  
  async getWithRefresh<T>(
    key: string, 
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    const cached = await this.get(key);
    
    if (cached && !this.isStale(cached)) {
      return cached.data;
    }
    
    // Prevent stampede
    if (!this.refreshing.has(key)) {
      this.refreshing.set(key, 
        fetcher().then(data => {
          this.set(key, data, ttl);
          this.refreshing.delete(key);
          return data;
        })
      );
    }
    
    return this.refreshing.get(key);
  }
}
```

### 3. Circuit Breaker for Cache Operations
```python
class CacheCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.is_open = False
    
    async def call(self, operation, *args, **kwargs):
        if self.is_open and self._should_attempt_reset():
            self.is_open = False
        
        if self.is_open:
            return None  # Fast fail
        
        try:
            result = await operation(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

## Enhanced Monitoring and Metrics

### 1. Distributed Tracing
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@router.get("/context/me")
async def get_user_context(request: Request):
    with tracer.start_as_current_span("get_user_context") as span:
        span.set_attribute("user.id", user.id)
        
        # Check cache
        with tracer.start_as_current_span("redis.get"):
            cached = await redis.get(cache_key)
            span.set_attribute("cache.hit", cached is not None)
```

### 2. Comprehensive Metrics
```python
class CacheMetrics:
    def __init__(self):
        self.hit_rate = prometheus_client.Gauge('cache_hit_rate', 
            'Cache hit rate by endpoint', ['endpoint', 'cache_type'])
        self.miss_rate = prometheus_client.Gauge('cache_miss_rate',
            'Cache miss rate by endpoint', ['endpoint', 'cache_type'])
        self.latency = prometheus_client.Histogram('cache_latency_seconds',
            'Cache operation latency', ['operation', 'cache_type'])
        self.size = prometheus_client.Gauge('cache_size_bytes',
            'Current cache size in bytes', ['cache_type'])
```

## Future Enhancements

1. **GraphQL Implementation**: Replace REST with GraphQL for better data fetching (evaluate after Phase 3 metrics)
2. **WebSocket Support**: Real-time updates for specific use cases (agent progress, flow status)
3. **Service Worker**: Offline support and advanced caching
4. **Edge Caching**: CDN integration for static assets
5. **Predictive Caching**: Use ML to predict and pre-cache user's next actions
6. **Cache Warming**: Proactive cache population for predictable workflows

## Summary of Gemini Pro 2.5 Feedback Integration

Based on the comprehensive review by Gemini Pro 2.5, the following enhancements were incorporated:

1. **Explicit Cache Invalidation Strategy**: Added detailed triggers for when each cache type should be invalidated, with a centralized `CacheInvalidationService` that integrates with the service layer.

2. **Simplified Frontend Caching**: Removed redundant custom caching from `ApiClient`, relying solely on React Query for all client-side caching needs. This eliminates complexity and potential synchronization issues.

3. **Cache Key Versioning**: Implemented versioned cache keys (e.g., `v1:user:context:{id}`) to handle API schema evolution gracefully.

4. **Developer Environment**: Added comprehensive local development setup including Docker configuration, developer scripts, and environment-specific cache settings.

5. **Centralized Constants**: Replaced "magic strings" with centralized constants for API endpoints and cache key generation, improving maintainability and reducing bugs.

These improvements address the key architectural concerns while maintaining the plan's focus on performance, security, and scalability.

## Summary of Additional Tweaks Added

Based on the production cache issues identified, the following enhancements have been added to the plan:

### 1. **Field Mapping Cache Invalidation**
- Added `on_field_mapping_bulk_operation()` method to `CacheInvalidationService`
- Implemented WebSocket-based cache invalidation events for React Query
- Specific cache strategy for field mappings with shorter TTL (2 minutes)
- Bulk operation support with proper invalidation cascade

### 2. **User Management Cache Invalidation**
- Added `on_user_defaults_updated()` method for handling default client/engagement changes
- Comprehensive invalidation of admin user lists when defaults change
- Client and engagement-specific cache invalidation when user associations change

### 3. **Migration Strategy for Custom Cache**
- Feature flag-based approach to gradually disable custom API cache
- Three-phase migration plan over 4 weeks
- Maintains backward compatibility during transition
- Clear rollback capability at each phase

### 4. **Immediate Quick Wins**
- Cache headers middleware for backend (implementable Day 1)
- Frontend support for honoring backend cache headers
- No code changes needed for basic caching benefits
- Progressive enhancement approach

### 5. **Field Mapping Specific Section**
- Dedicated caching strategy for field mapping workflows
- WebSocket integration for real-time cache invalidation
- React Query configuration optimized for field mapping use cases
- Handles the specific challenge of bulk operations

These additions directly address the cache issues experienced in production while maintaining the overall architectural integrity of the Redis caching plan.