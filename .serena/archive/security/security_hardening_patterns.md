# Security Hardening Patterns

## Token Protection Strategies

### 1. Never Log Sensitive Headers
```typescript
// BAD - Exposes bearer tokens
console.log('Headers:', headers);

// GOOD - Log only safe metadata
if (process.env.NODE_ENV !== 'production') {
  console.log('Request:', {
    endpoint,
    method,
    clientAccountId
  });
}
```

### 2. Centralize Header Management
```typescript
// Use shared utility for consistency
import { createMultiTenantHeaders } from '../../utils/api/multiTenantHeaders';
import type { MultiTenantContext } from '../../utils/api/apiTypes';

const getMultiTenantHeaders = (
  clientAccountId: string,
  engagementId?: string
): Record<string, string> => {
  const context: MultiTenantContext = {
    clientAccountId,
    engagementId
  };
  return {
    ...createMultiTenantHeaders(context),
    'Content-Type': 'application/json'
  };
};
```

### 3. Feature Flag Fallback Operations
```typescript
// Prevent dual operations with strict boolean parsing
const enableFallback = String(
  process.env.NEXT_PUBLIC_ENABLE_UNIFIED_DISCOVERY_FALLBACK || ''
).toLowerCase() === 'true';

if (!enableFallback) {
  console.warn('Fallback disabled by feature flag');
  throw error;
}
```

### 4. Environment-Specific Endpoints
```typescript
// Dual-gate demo endpoints
ASSETS: process.env.NODE_ENV === 'development' &&
        String(process.env.NEXT_PUBLIC_ENABLE_DEMO_ENDPOINT || '').toLowerCase() === 'true'
  ? '/auth/demo/assets'
  : '/unified-discovery/assets'
```

### 5. Regex Pattern Matching for Security
```typescript
// Use precise regex to prevent path traversal
const isAgenticActivity = (
  /\/flows\/execute(?:$|\?)/.test(endpoint) ||  // Exact match
  /\/flows\/[^/]+\/resume(?:$|\?)/.test(endpoint) ||  // With ID
  /\/assets\/analyze(?:$|\?)/.test(endpoint)
);
// NOT: endpoint.includes('/flows/execute') - too broad
```

### 6. FlowId Validation
```typescript
// Prevent malformed URLs
'initialization': (flowId: string) =>
  flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import'
```

## Review Response Patterns

### Systematic Security Review Handling
1. **Initial Review**: Address all critical security issues first
2. **Secondary Review**: Fix additional recommendations
3. **Validation**: Each fix gets separate verification

### Example from PR #126:
- Qodo Review 1: Remove token logging ✅
- Qodo Review 2: Add environment gating ✅
- GPT5 Review: Centralize headers ✅
- Qodo Review 3: Regex patterns for paths ✅

## Key Security Principles
1. **Defense in Depth**: Multiple layers of protection
2. **Explicit Over Implicit**: Require explicit flags for sensitive operations
3. **Fail Secure**: Default to secure state when uncertain
4. **Audit Everything**: Log operations without sensitive data
5. **Progressive Hardening**: Iterate through multiple review cycles
