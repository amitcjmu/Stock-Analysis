# Download Functionality Authentication Fix

## Problem: Data Download Failing with 400 Errors
**Symptoms**:
- Download Raw/Cleaned Data buttons failing
- Backend logs: "Client account context is required for multi-tenant security"
- Missing X-Client-Account-ID header

## Root Causes
1. **URL Construction**: Using `${API_CONFIG.BASE_URL}` with empty value in Docker
2. **Wrong Auth Import**: Using incomplete contextUtils.getAuthHeaders()

## Solution
```typescript
// dataCleansingService.ts fixes

// 1. Fix import - use complete implementation
import { getAuthHeaders } from '../lib/api/apiClient';  // NOT contextUtils

// 2. Fix URL construction - remove BASE_URL prefix
// BEFORE:
const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/flows/${flowId}/data-cleansing/download/raw`, {

// AFTER:
const response = await fetch(`/api/v1/flows/${flowId}/data-cleansing/download/raw`, {
  method: 'GET',
  headers: getAuthHeaders()  // Now includes X-Client-Account-ID
});
```

## Docker Development Pattern
```typescript
// When running on port 8081 (Docker), use relative URLs
if (window.location.port === '8081') {
  url = '/api/endpoint';  // Let Vite proxy handle routing
} else {
  url = `${baseUrl}/api/endpoint`;
}
```

## Debugging Commands
```bash
# Check backend logs for auth errors
docker logs migration_backend -f | grep "Client account"

# Verify headers in browser
# Network tab → Request → Headers → X-Client-Account-ID should be present
```

## Prevention
- Always use apiClient.getAuthHeaders() for service files
- Test download functionality after auth changes
- Verify multi-tenant headers in Network tab
