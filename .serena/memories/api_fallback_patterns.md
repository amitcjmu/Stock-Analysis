# API Fallback Patterns

## MFO-First with Unified-Discovery Fallback

### Implementation Pattern
```typescript
async getActiveFlows(
  clientAccountId: string,
  engagementId?: string
): Promise<ActiveFlowSummary[]> {
  try {
    // Primary: Master Flow Orchestrator
    const response = await apiClient.get('/flows/active', { headers });
    return transformResponse(response);
  } catch (error) {
    // Check feature flag before fallback
    if (!process.env.NEXT_PUBLIC_ENABLE_UNIFIED_DISCOVERY_FALLBACK) {
      throw error;
    }

    try {
      // Fallback: Unified Discovery
      const fallback = await apiClient.get('/unified-discovery/flows/active', { headers });
      return transformFallbackResponse(fallback);
    } catch (fallbackError) {
      // Log both errors for debugging
      console.error('Primary error:', error);
      console.error('Fallback error:', fallbackError);
      throw error; // Throw original
    }
  }
}
```

### Response Normalization
```typescript
// Handle multiple field naming conventions
interface UnifiedDiscoveryFlowResponse {
  flow_id?: string;
  flowId?: string;
  id?: string;
  flow_type?: string;
  flowType?: string;
  type?: string;
  status: string;
  phase?: string;
  current_phase?: string;
  currentPhase?: string;
}

// Transform to standard format
const flowId = flow.flow_id || flow.flowId || flow.id || '';
const flowType = flow.flow_type || flow.flowType || flow.type || 'discovery';
```

### Routing Configuration Updates

#### Fix View Button Navigation (Issue #103)
```typescript
// src/config/flowRoutes.ts
export const FLOW_PHASE_ROUTES = {
  discovery: {
    // Before: All went to /discovery/cmdb-import
    // After: Route to monitoring with flowId validation
    'initialization': (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
    'error': (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  }
};

// src/App.tsx - Add new route
<Route path="/discovery/monitor/:flowId" element={<LazyDiscoveryDashboard />} />
```

### Timeout Configuration for AI Operations

#### Fix Monitor Timeout (Issue #102)
```typescript
// src/config/api.ts
const isAgenticActivity = (
  /\/flow-processing\/continue(?:$|\?)/.test(endpoint) ||  // No timeout
  /\/flows\/[^/]+\/resume(?:$|\?)/.test(endpoint) ||     // Recovery ops
  /\/flows\/[^/]+\/retry(?:$|\?)/.test(endpoint)        // Retry ops
);

const timeoutMs = options.timeout || (
  isAgenticActivity ? null :      // No timeout for AI
  endpoint.includes('/bulk') ? 180000 :  // 3 min for bulk
  60000  // 1 min default
);
```

### Demo Endpoint Switching

#### Fix Filter Issues (Issue #100)
```typescript
// Temporary fix using demo endpoint
ASSETS: process.env.NODE_ENV === 'development' &&
        process.env.NEXT_PUBLIC_ENABLE_DEMO_ENDPOINT === 'true'
  ? '/auth/demo/assets'     // Working demo endpoint
  : '/unified-discovery/assets'  // Production endpoint (404 currently)
```

## Key Principles
1. **Primary First**: Always try MFO endpoint first
2. **Feature Flag Control**: Gate fallbacks behind flags
3. **Field Flexibility**: Support multiple naming conventions
4. **Error Preservation**: Throw original error if both fail
5. **Timeout Awareness**: Long-running ops need special handling
