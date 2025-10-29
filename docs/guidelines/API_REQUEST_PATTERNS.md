# API Request Patterns - CRITICAL GUIDELINES

## ⚠️ MANDATORY: Request Body vs Query Parameters

### The Problem
This codebase has experienced **recurring bugs** where developers and AI coding agents incorrectly use query parameters for POST/PUT/DELETE requests, causing 422 Unprocessable Entity errors.

### The Rule - NEVER BREAK THIS

#### ✅ CORRECT Pattern for POST/PUT/DELETE
```typescript
// Always use request body for data
const response = await apiCall('/api/v1/endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    field1: 'value1',
    field2: 'value2'
  })
});
```

#### ❌ WRONG Pattern (Causes 422 Errors)
```typescript
// NEVER do this for POST/PUT/DELETE
const params = new URLSearchParams({ field1: 'value1' });
const response = await apiCall(`/api/v1/endpoint?${params}`, {
  method: 'POST'
});
```

### Why This Happens
1. **Backend**: FastAPI with Pydantic models expects request bodies for POST/PUT/DELETE
2. **Frontend**: JavaScript developers often default to query parameters
3. **AI Agents**: May not understand the backend's expectations without clear documentation

### Backend Schema Examples

The backend defines Pydantic models like:
```python
class LearningApprovalRequest(BaseModel):
    approval_note: Optional[str]
    learn_from_approval: bool = True
    metadata: Optional[Dict[str, Any]]
```

These models **ONLY** accept request body data, not query parameters.

### Files That Follow This Pattern
- `/src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts`
- `/src/pages/discovery/AttributeMapping/services/mappingService.ts`
- All field mapping related endpoints

### Historical Context
This issue has been fixed multiple times:
- September 2024: Initial fix for field mapping endpoints
- October 2024: Fixed again after regression
- November 2024: Fixed again after AI agent reverted the pattern
- December 2024: Added this documentation to prevent future occurrences

### For AI Coding Agents
**BEFORE** modifying any API call:
1. Check if it's a POST/PUT/DELETE request
2. If yes, ALWAYS use request body
3. NEVER use URLSearchParams for these methods
4. Look for the Pydantic schema in the backend to understand expected fields

### Testing Checklist
- [ ] No query parameters on POST requests
- [ ] No query parameters on PUT requests  
- [ ] No query parameters on DELETE requests
- [ ] Request body matches backend Pydantic schema
- [ ] No 422 errors in browser console

## Exception: GET Requests
GET requests CAN and SHOULD use query parameters:
```typescript
const params = new URLSearchParams({ filter: 'active', page: '1' });
const response = await apiCall(`/api/v1/endpoint?${params}`);
```

## Red Flags in Code Review
If you see any of these patterns, it's likely wrong:
- `URLSearchParams` used with POST/PUT/DELETE
- `?` in URL for POST/PUT/DELETE requests
- Empty body for POST/PUT requests that should send data
- 422 errors in the browser console

## How to Fix 422 Errors
1. Check browser DevTools Network tab
2. Look at the request - is it sending query params instead of body?
3. Find the frontend code making the request
4. Change from query parameters to request body
5. Ensure body matches backend Pydantic schema

## Assessment Flow API Patterns

### Create Assessment Flow (POST with request body)
```typescript
// ✅ CORRECT
await apiCall('/api/v1/assessment-flow/initialize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    application_ids: ['uuid1', 'uuid2'],
    parameters: {
      business_value: 8,
      technical_complexity: 6,
      migration_urgency: 7
    }
  })
});

// ❌ WRONG - Causes 422 errors
await apiCall('/api/v1/assessment-flow/initialize?application_ids=uuid1,uuid2', {
  method: 'POST'
});
```

### Get Assessment Status (GET with query parameters)
```typescript
// ✅ CORRECT
await apiCall(`/api/v1/assessment-flow/${flowId}/status`);

// With optional app filter
await apiCall(`/api/v1/assessment-flow/${flowId}/sixr-decisions?app_id=${appId}`);
```

### Accept Recommendation (POST with request body)
```typescript
// ✅ CORRECT
await apiCall(`/api/v1/assessment-flow/${flowId}/sixr-decisions/${appId}/accept`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    strategy: 'rehost',
    reasoning: 'Low complexity migration',
    confidence_level: 0.9
  })
});

// ❌ WRONG - Causes 422 errors
await apiCall(
  `/api/v1/assessment-flow/${flowId}/sixr-decisions/${appId}/accept?strategy=rehost`,
  { method: 'POST' }
);
```

### Export Assessment Results (POST with query parameter for format)
```typescript
// ✅ CORRECT - Format in query param, empty body
await apiCall(`/api/v1/assessment-flow/${flowId}/export?format=json`, {
  method: 'POST'
});

// Also acceptable with format in body
await apiCall(`/api/v1/assessment-flow/${flowId}/export`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ format: 'json' })
});
```

### Pause/Resume Assessment Flow (POST with no body)
```typescript
// ✅ CORRECT - No body needed for lifecycle operations
await apiCall(`/api/v1/assessment-flow/${flowId}/pause`, {
  method: 'POST'
});

await apiCall(`/api/v1/assessment-flow/${flowId}/resume`, {
  method: 'POST'
});
```

### Key Principles for Assessment Flow

1. **snake_case fields**: All field names use snake_case (NOT camelCase)
   ```typescript
   // ✅ CORRECT
   { application_ids: [...], confidence_level: 0.9 }

   // ❌ WRONG
   { applicationIds: [...], confidenceLevel: 0.9 }
   ```

2. **Multi-tenant headers**: Always include tenant context
   ```typescript
   const headers = {
     'X-Client-Account-ID': clientAccountId,
     'X-Engagement-ID': engagementId
   };
   ```

3. **MFO integration**: All endpoints route through MFO architecture
   - Master flow: `crewai_flow_state_extensions` (lifecycle)
   - Child flow: `assessment_flows` (operational state)

4. **Deprecated endpoints**: Do NOT use `/api/v1/6r/*` (returns HTTP 410 Gone)
   - Old: `/api/v1/6r/analysis/create`
   - New: `/api/v1/assessment-flow/initialize`

### Backend Schema References

Assessment Flow uses these Pydantic models (request bodies ONLY):

```python
# Create Assessment
class AssessmentFlowCreateRequest(BaseModel):
    application_ids: List[UUID]
    parameters: Optional[Dict[str, Any]]

# Accept Recommendation
class AcceptRecommendationRequest(BaseModel):
    strategy: str
    reasoning: str
    confidence_level: float

# Export Request
class ExportRequest(BaseModel):
    format: Literal["json", "pdf", "excel"]
```

### Common Mistakes to Avoid

1. ❌ Using `/api/v1/6r/*` endpoints (deprecated Oct 2025)
2. ❌ Query parameters for POST/PUT requests
3. ❌ camelCase field names (use snake_case)
4. ❌ Missing multi-tenant headers
5. ❌ Calling child flow endpoints directly (use MFO integration)