# Auth Headers Consolidation Pattern

## Problem: Multiple Redundant Auth Header Implementations
**Issue**: Three different `getAuthHeaders()` functions across codebase causing bugs
- `/lib/api/apiClient.ts` - Complete implementation
- `/contexts/AuthContext` - Complete for React
- `/utils/contextUtils.ts` - Incomplete, missing X-Client-Account-ID

## Solution: Two-System Architecture
**Pattern**: Keep apiClient for services, AuthContext for React components

### Migration Strategy
```typescript
// Services (non-React) - use apiClient
import { getAuthHeaders } from '@/lib/api/apiClient';
const headers = getAuthHeaders(); // No parameters needed

// React components - use AuthContext
import { useAuth } from '@/contexts/AuthContext';
const { getAuthHeaders } = useAuth();
const headers = getAuthHeaders(); // Reactive to auth state
```

### Critical Headers Required
```typescript
// All API calls MUST include:
{
  'Authorization': `Bearer ${token}`,
  'X-User-ID': userId,
  'X-Client-Account-ID': clientId,  // CRITICAL for multi-tenant
  'X-Engagement-ID': engagementId,
  'X-Flow-ID': flowId
}
```

## Common Bugs Fixed
1. **Missing X-Client-Account-ID**: Causes 400/403 errors
2. **Wrong import source**: Using contextUtils instead of apiClient
3. **Type errors**: useAuthHeaders returning JSX.Element instead of function

## Verification Commands
```bash
# Find remaining contextUtils usage
grep -r "from.*contextUtils" src/

# Check auth header usage
grep -r "getAuthHeaders" src/ --include="*.ts" --include="*.tsx"
```

## When to Apply
- Consolidating redundant utility functions
- Fixing multi-tenant security issues
- Migrating from legacy patterns