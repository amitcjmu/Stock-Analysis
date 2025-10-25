# Frontend Missing X-User-ID Header Fix (Oct 2025)

## Problem
Collection flow start failing with 400 errors:
```
❌ Rejected collection request - Missing headers: ['User ID']
```

Backend middleware enforces multi-tenant headers but frontend polling `/api/v1/collection/status` missing X-User-ID.

## Root Cause
Direct `fetch()` calls bypass `apiCall()` utility which auto-adds authentication headers from localStorage.

**Affected**: `src/pages/collection/Index.tsx` line 103-131

## Solution Pattern

### 1. Extract User ID from localStorage
```typescript
const authToken = localStorage.getItem('auth_token');
const clientId = localStorage.getItem('auth_client_id');
const engagementStr = localStorage.getItem('auth_engagement');
const userStr = localStorage.getItem('auth_user');

let engagementId = '';
let userId = '';

// Parse engagement JSON
if (engagementStr) {
  try {
    const engagement = JSON.parse(engagementStr);
    engagementId = engagement.id;
  } catch (e) {
    console.error('Failed to parse engagement data:', e);
  }
}

// Parse user JSON
if (userStr) {
  try {
    const user = JSON.parse(userStr);
    userId = user.id;
  } catch (e) {
    console.error('Failed to parse user data:', e);
  }
}
```

### 2. Include in fetch() Headers
```typescript
const response = await fetch('/api/v1/collection/status', {
  headers: {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json',
    'X-Client-Account-ID': clientId || '',
    'X-Engagement-ID': engagementId || '',
    'X-User-ID': userId || ''  // ✅ FIXED
  }
});
```

## Audit Process

### Files Using Collection API
```bash
# Search all collection API calls
grep -r "/api/v1/collection" src/

# Found 12 files:
src/pages/collection/*.tsx
src/services/*Service.ts
```

### Audit Results
- **11/12 files**: Use `apiCall()` utility → Auto-adds headers via `src/config/api.ts`
- **1/12 files**: Direct `fetch()` → Missing headers ✅ FIXED

## Prevention Pattern

### DO: Use apiCall() Utility
```typescript
import { apiCall } from '@/config/api';

const response = await apiCall('/api/v1/collection/status', {
  method: 'GET'
});
// Headers auto-added from localStorage
```

### DON'T: Use Direct fetch()
```typescript
// ❌ WRONG - bypasses header injection
const response = await fetch('/api/v1/collection/status', {
  headers: { /* must manually add all headers */ }
});
```

## Backend Middleware Enforcement
```python
# app/middleware/context_establishment_middleware.py
required_headers = [
    "X-Client-Account-ID",
    "X-Engagement-ID",
    "X-User-ID"  # Enforced since Aug 2025
]

if missing := [h for h in required_headers if not request.headers.get(h)]:
    return JSONResponse(
        status_code=400,
        content={"error": f"Missing headers: {missing}"}
    )
```

## Testing Validation
```bash
# Check browser console for 400 errors
# Network tab: Verify X-User-ID header present
# Backend logs: No "Missing headers" warnings
```

## Commit Reference
- Commit: `b561f733c`
- File: `src/pages/collection/Index.tsx:103-131`
- PR: #790
