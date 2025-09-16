# API Request Patterns - 422 Errors Fix

## Insight 1: POST/PUT/DELETE Must Use Request Body
**Problem**: Frontend sending query parameters to FastAPI causes 422 errors
**Solution**: Always use request body for POST/PUT/DELETE operations
**Code**:
```typescript
// ❌ WRONG - Causes 422
const url = `/api/endpoint?param=value`;
await apiCall(url, { method: 'POST' });

// ✅ CORRECT
const url = `/api/endpoint`;
await apiCall(url, {
  method: 'POST',
  body: JSON.stringify({ param: 'value' })
});
```
**Usage**: All POST/PUT/DELETE operations with FastAPI/Pydantic backends

## Insight 2: Learning Service Endpoints
**Problem**: Approval/reject endpoints expect LearningApprovalRequest body
**Solution**: Match Pydantic schema exactly
**Code**:
```typescript
// For approval endpoint
const requestBody = {
  approval_note: 'User approved',
  learn_from_approval: true,
  metadata: { flow_id: flowId }
};

// For rejection endpoint
const requestBody = {
  rejection_reason: 'Reason here',
  metadata: { flow_id: flowId }
};
```
**Usage**: Field mapping approval/rejection endpoints

## Files Fixed:
- `src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts`
- `src/pages/discovery/AttributeMapping/services/mappingService.ts`
- `docs/guidelines/API_REQUEST_PATTERNS.md` (created)
