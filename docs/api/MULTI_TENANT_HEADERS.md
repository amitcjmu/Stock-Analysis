# Multi-Tenant Header Specification

## Overview

All API requests (except authentication and health endpoints) MUST include multi-tenant context headers for security and data isolation.

## Required Headers

### Client Account ID (REQUIRED)
Identifies the organization/tenant making the request.

**Accepted Formats (case-insensitive):**
- `X-Client-Account-ID` (recommended - used by frontend)
- `X-Client-Account-Id`
- `x-client-account-id`
- `X-Client-ID`
- `x-client-id`
- `client-account-id`

**Value Format:** UUID string (e.g., `11111111-1111-1111-1111-111111111111`)

**Legacy Support:** Integer values like `"1"` are automatically converted to demo client UUID

### Engagement ID (OPTIONAL - required for some endpoints)
Identifies the specific project/migration engagement within a client account.

**Accepted Formats (case-insensitive):**
- `X-Engagement-ID` (recommended - used by frontend)
- `X-Engagement-Id`
- `x-engagement-id`
- `engagement-id`

**Value Format:** UUID string (e.g., `22222222-2222-2222-2222-222222222222`)

### User ID (OPTIONAL - extracted from JWT if not provided)
Identifies the user making the request.

**Accepted Formats (case-insensitive):**
- `X-User-ID` (recommended)
- `X-User-Id`
- `x-user-id`
- `user-id`

**Value Format:** UUID string

**Note:** If not provided, extracted automatically from `Authorization: Bearer <token>` JWT

### Flow ID (OPTIONAL - for flow-specific operations)
Identifies a specific workflow/flow instance.

**Accepted Formats (case-insensitive):**
- `X-Flow-ID` (recommended)
- `X-Flow-Id`
- `x-flow-id`

**Value Format:** UUID string

## HTTP Header Case-Insensitivity

**IMPORTANT:** HTTP headers are case-insensitive according to [RFC 7230](https://tools.ietf.org/html/rfc7230#section-3.2).

All of these are equivalent:
```
X-Client-Account-ID: <uuid>
X-Client-Account-Id: <uuid>
x-client-account-id: <uuid>
X-CLIENT-ACCOUNT-ID: <uuid>
```

The backend accepts ALL casings. However, for consistency:
- **Frontend SHOULD use:** `X-Client-Account-ID`, `X-Engagement-ID` (uppercase 'ID')
- **Backend RECOMMENDS:** `X-Client-Account-Id`, `X-Engagement-Id` (lowercase 'd' in error messages)
- **Tests SHOULD use:** Same as frontend (`X-Client-Account-ID`)

## Examples

### cURL Example
```bash
curl -X GET "http://localhost:8000/api/v1/master-flows?flow_type=assessment" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "X-Client-Account-ID: 11111111-1111-1111-1111-111111111111" \
  -H "X-Engagement-ID: 22222222-2222-2222-2222-222222222222"
```

### TypeScript Example
```typescript
const headers = {
  'Authorization': `Bearer ${token}`,
  'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
  'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
};

const response = await fetch('/api/v1/master-flows', { headers });
```

### Python Example
```python
headers = {
    'Authorization': f'Bearer {token}',
    'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
    'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
}

response = requests.get('/api/v1/master-flows', headers=headers)
```

### Playwright Test Example
```typescript
const TENANT_HEADERS = {
  'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
  'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
};

const response = await request.get(
  `${API_URL}/api/v1/master-flows`,
  { headers: TENANT_HEADERS }
);
```

## Error Responses

### Missing Client Account Header
```json
{
  "detail": "Client account context is required for multi-tenant security. Please provide one of: X-Client-Account-ID, X-Client-Account-Id, or x-client-account-id header. Note: HTTP headers are case-insensitive, any casing will work."
}
```
**Status Code:** 403 Forbidden

### Missing Engagement Header (when required)
```json
{
  "detail": "Engagement context is required for multi-tenant security. Please provide one of: X-Engagement-ID, X-Engagement-Id, or x-engagement-id header. Note: HTTP headers are case-insensitive, any casing will work."
}
```
**Status Code:** 403 Forbidden

## Exempt Endpoints

The following endpoints DO NOT require multi-tenant headers:

- `/health`
- `/api/v1/health/*`
- `/docs`, `/redoc`, `/openapi.json`
- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/auth/demo/*`
- `/api/v1/me` (for context initialization)

## Implementation Details

### Backend Header Extraction
Located in: `backend/app/core/header_extraction.py`

The backend checks multiple header variations in order:
1. Exact match (e.g., `X-Client-Account-ID`)
2. All lowercase (e.g., `x-client-account-id`)
3. Mixed case (e.g., `X-Client-Account-Id`)
4. Alternative formats (e.g., `X-Client-ID`, `client-account-id`)

### Frontend Header Creation
Located in: `src/utils/api/multiTenantHeaders.ts`

The frontend consistently uses:
- `X-Client-Account-ID` (uppercase 'ID')
- `X-Engagement-ID` (uppercase 'ID')
- `X-User-ID` (uppercase 'ID')

## Demo Client UUIDs

For testing and development:
- **Demo Client Account ID:** `11111111-1111-1111-1111-111111111111`
- **Demo Engagement ID:** `22222222-2222-2222-2222-222222222222`

Legacy integer value `"1"` is automatically converted to the demo client UUID.

## Security Notes

1. **Multi-tenant isolation** is MANDATORY - all database queries are scoped by client_account_id
2. **Engagement scoping** provides additional project-level isolation
3. **Missing headers** result in 403 Forbidden (not 401) to indicate authorization failure, not authentication failure
4. **Header validation** happens in middleware before reaching endpoints
5. **Context injection** makes tenant context available throughout the request lifecycle

## References

- Backend Implementation: `backend/app/core/middleware/context_middleware.py`
- Header Extraction: `backend/app/core/header_extraction.py`
- Context Validation: `backend/app/core/context_utils.py`
- Frontend Utilities: `src/utils/api/multiTenantHeaders.ts`
- E2E Test Example: `tests/e2e/assessment-flow-comprehensive.spec.ts`
