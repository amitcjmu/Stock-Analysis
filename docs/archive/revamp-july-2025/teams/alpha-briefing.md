# Team Alpha - API Service Consolidation Briefing

## Mission Statement
Team Alpha is responsible for consolidating API service patterns, eliminating duplication, and establishing a clean, consistent API layer that serves as the foundation for all frontend interactions.

## Team Objectives
1. Unify all API service calls to use v1 endpoints exclusively
2. Remove deprecated v2/v3 service patterns
3. Establish standardized error handling and response patterns
4. Ensure all API calls include proper multi-tenant headers

## Specific Tasks

### Task 1: Frontend API Service Consolidation
**Files to modify:**
- `/src/services/api.ts`
- `/src/services/discoveryFlow.ts`
- `/src/services/clientEngagement.ts`
- `/src/services/dataImport.ts`
- `/src/services/flowManagement.ts`

**Required changes:**
```typescript
// Before (mixed patterns)
const response = await api.post('/api/v2/discovery-flows/initialize');
const result = await fetch('/api/v3/flows/status');

// After (unified v1 pattern)
const response = await api.post('/api/v1/unified-discovery/flow/initialize');
const result = await api.get('/api/v1/unified-discovery/flow/status/{flowId}');
```

### Task 2: Remove Deprecated Service Files
**Files to delete:**
- `/src/services/v2/` (entire directory if exists)
- `/src/services/v3/` (entire directory if exists)
- Any files with `_old`, `_deprecated`, or `_legacy` suffixes

### Task 3: Standardize API Headers
**Create central header management:**
```typescript
// /src/services/apiHeaders.ts
export const getMultiTenantHeaders = (
  clientAccountId: number,
  engagementId?: string,
  userId?: number
) => ({
  'X-Client-Account-ID': clientAccountId.toString(),
  ...(engagementId && { 'X-Engagement-ID': engagementId }),
  ...(userId && { 'X-User-ID': userId.toString() }),
  'Content-Type': 'application/json'
});
```

### Task 4: Implement Centralized Error Handling
**Create error handler:**
```typescript
// /src/services/apiErrors.ts
export class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export const handleAPIError = (error: any): never => {
  if (error.response) {
    throw new APIError(
      error.response.status,
      error.response.data.message || 'API request failed',
      error.response.data
    );
  }
  throw error;
};
```

### Task 5: Update Service Methods
**Pattern to follow:**
```typescript
// Example: Discovery Flow Service
export const discoveryFlowService = {
  async initializeFlow(
    clientAccountId: number,
    engagementId: string,
    data: InitializeFlowRequest
  ): Promise<FlowResponse> {
    try {
      const response = await api.post(
        '/api/v1/unified-discovery/flow/initialize',
        data,
        {
          headers: getMultiTenantHeaders(clientAccountId, engagementId)
        }
      );
      return response.data;
    } catch (error) {
      handleAPIError(error);
    }
  },
  
  async getFlowStatus(
    clientAccountId: number,
    flowId: string
  ): Promise<FlowStatus> {
    try {
      const response = await api.get(
        `/api/v1/unified-discovery/flow/status/${flowId}`,
        {
          headers: getMultiTenantHeaders(clientAccountId)
        }
      );
      return response.data;
    } catch (error) {
      handleAPIError(error);
    }
  }
};
```

## Success Criteria
1. All API calls use v1 endpoints exclusively
2. No references to v2/v3 endpoints remain in codebase
3. All API calls include proper multi-tenant headers
4. Centralized error handling implemented and used consistently
5. Service layer has no direct fetch() calls, only axios/api client
6. All deprecated service files removed
7. API response types properly typed with TypeScript

## Common Issues and Solutions

### Issue 1: Missing Multi-Tenant Headers
**Symptom:** 401/403 errors from API
**Solution:** Ensure all API calls include headers from `getMultiTenantHeaders()`

### Issue 2: Endpoint Not Found
**Symptom:** 404 errors after updating to v1
**Solution:** Check backend `/backend/app/api/v1/` for correct endpoint paths

### Issue 3: Type Mismatches
**Symptom:** TypeScript errors after API updates
**Solution:** Update response types to match v1 API responses

### Issue 4: Session ID References
**Symptom:** API calls still using session_id parameter
**Solution:** Replace all session_id with flow_id

## Rollback Procedures
1. **Before making changes:**
   ```bash
   git checkout -b alpha-api-consolidation
   git push origin alpha-api-consolidation
   ```

2. **If issues arise:**
   ```bash
   # Revert specific file
   git checkout main -- src/services/api.ts
   
   # Or full rollback
   git checkout main
   git branch -D alpha-api-consolidation
   ```

3. **Emergency rollback:**
   - Keep backup of original service files in `/src/services/_backup/`
   - Can quickly restore if production issues

## Testing Requirements
1. **Unit tests for each service:**
   ```typescript
   // /src/services/__tests__/discoveryFlow.test.ts
   describe('Discovery Flow Service', () => {
     it('should include multi-tenant headers', async () => {
       // Test implementation
     });
     
     it('should handle API errors properly', async () => {
       // Test implementation
     });
   });
   ```

2. **Integration tests:**
   - Test each API endpoint with Postman/Thunder Client
   - Verify multi-tenant isolation works

## Status Report Template
```markdown
# Alpha Team Status Report - [DATE]

## Completed Tasks
- [ ] Task 1: Frontend API Service Consolidation
- [ ] Task 2: Remove Deprecated Service Files  
- [ ] Task 3: Standardize API Headers
- [ ] Task 4: Implement Centralized Error Handling
- [ ] Task 5: Update Service Methods

## Files Modified
- List of files changed

## Issues Encountered
- Issue description and resolution

## Remaining Work
- Outstanding tasks

## Blockers
- Any blocking issues

## Next Steps
- Planned activities
```

## Resources
- Backend API Routes: `/backend/app/api/v1/`
- API Documentation: `/docs/api/v1-endpoints.md`
- TypeScript Types: `/src/types/api/`
- Axios Configuration: `/src/config/axios.ts`

## Contact
- Team Lead: Alpha Team
- Slack Channel: #alpha-api-consolidation
- Backend Support: #backend-team