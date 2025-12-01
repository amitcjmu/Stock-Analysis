# Security Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 12 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Tenant Scoping**: ALWAYS use `and_(client_account_id, engagement_id)` in queries
> 2. **UUID Types**: NEVER convert tenant IDs to integers - always UUID
> 3. **Required Headers**: X-Client-Account-ID, X-Engagement-ID, X-User-ID
> 4. **apiCall() Utility**: Always use for API calls - auto-adds auth headers
> 5. **Never Log Tokens**: Log metadata only, never Authorization headers

---

## Table of Contents

1. [Overview](#overview)
2. [Multi-Tenant Security](#multi-tenant-security)
3. [UUID Type Enforcement](#uuid-type-enforcement)
4. [Authentication Headers](#authentication-headers)
5. [Security Hardening](#security-hardening)
6. [Anti-Patterns](#anti-patterns)
7. [Code Templates](#code-templates)
8. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Multi-tenant data isolation, authentication header management, UUID type enforcement, and security hardening patterns for enterprise security.

### When to Reference
- Implementing database queries
- Adding API endpoints
- Fixing cross-tenant security issues
- Debugging authentication failures

### Key Files
- `backend/app/middleware/context_establishment_middleware.py`
- `src/lib/api/apiClient.ts`
- `src/utils/api/multiTenantHeaders.ts`

---

## Multi-Tenant Security

### Pattern 1: Database Query Scoping (CRITICAL)

**ALWAYS** include tenant context in queries to prevent cross-tenant data access.

```python
from sqlalchemy import select, and_

# WRONG - No tenant scoping (HIGH SECURITY RISK)
data = select(DataImport).where(DataImport.id == UUID(data_import_id))

# CORRECT - Tenant-scoped query
data = select(DataImport).where(
    and_(
        DataImport.id == UUID(data_import_id),
        DataImport.client_account_id == client_account_id,
        DataImport.engagement_id == engagement_id,
    )
)
```

### Pattern 2: Delete Operations

```python
from sqlalchemy import delete, and_

# CORRECT - Tenant-scoped delete
delete_stmt = delete(ImportFieldMapping).where(
    and_(
        ImportFieldMapping.data_import_id == data_import_id,
        ImportFieldMapping.client_account_id == client_account_id,
    )
)
```

### Tables Requiring Tenant Scoping

| Table | Required Scopes |
|-------|----------------|
| DataImport | client_account_id |
| ImportFieldMapping | client_account_id + engagement_id |
| DiscoveryFlow | client_account_id + engagement_id |
| CollectionFlow | client_account_id + engagement_id |
| Asset | client_account_id + engagement_id |
| FlowExecution | client_account_id + engagement_id |
| CrewAIFlowStateExtension | client_account_id + engagement_id |

### Cache Key Scoping

```python
# WRONG - Cross-tenant data exposure risk
cache_key = CacheKeys.user_clients(str(user.id))

# CORRECT - Tenant-scoped caching
cache_key = f"{CacheKeys.user_clients(str(user.id))}:client:{client_account_id}:engagement:{engagement_id}"
```

---

## UUID Type Enforcement

### Pattern 3: NEVER Convert Tenant IDs to Integers

After migration 115, tenant IDs are UUIDs. Integer conversion causes runtime errors:

```
sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError:
operator does not exist: uuid = integer
```

**Wrong Pattern**:
```python
# BAD - Converting UUID to integer
if isinstance(client_account_id, str):
    client_account_id_int = 1 if "1111111" in client_account_id else int(client_account_id)
```

**Correct Pattern**:
```python
# GOOD - Convert to UUID
client_account_uuid = (
    UUID(context.client_account_id)
    if isinstance(context.client_account_id, str)
    else context.client_account_id
)
```

### UUID Enforcement Checklist

- [ ] Repository `__init__`: Change `Optional[str]` → `Optional[uuid.UUID]`
- [ ] Repository methods: Change `int` → `uuid.UUID` for tenant IDs
- [ ] API endpoints: Remove `int()` conversion, use `UUID()`
- [ ] Service classes: Store `client_account_uuid`, not `client_account_id_int`

### Search for Violations

```bash
grep -r "int(client_account_id)" backend/
grep -r "int(engagement_id)" backend/
grep -r "client_account_id_int" backend/
```

---

## Authentication Headers

### Pattern 4: Required Headers

Backend middleware enforces these headers:

```python
required_headers = [
    "X-Client-Account-ID",
    "X-Engagement-ID",
    "X-User-ID"
]
```

### Pattern 5: Use apiCall() Utility

**DO**:
```typescript
import { apiCall } from '@/config/api';

const response = await apiCall('/api/v1/collection/status', {
  method: 'GET'
});
// Headers auto-added from localStorage
```

**DON'T**:
```typescript
// WRONG - bypasses header injection
const response = await fetch('/api/v1/collection/status', {
  headers: { /* must manually add all headers */ }
});
```

### Pattern 6: Manual Header Extraction (When Required)

```typescript
const authToken = localStorage.getItem('auth_token');
const clientId = localStorage.getItem('auth_client_id');
const userStr = localStorage.getItem('auth_user');

let userId = '';
if (userStr) {
  try {
    const user = JSON.parse(userStr);
    userId = user.id;
  } catch (e) {
    console.error('Failed to parse user data:', e);
  }
}

const headers = {
  'Authorization': `Bearer ${authToken}`,
  'Content-Type': 'application/json',
  'X-Client-Account-ID': clientId || '',
  'X-Engagement-ID': engagementId || '',
  'X-User-ID': userId || ''
};
```

### Auth Header Architecture

**Two-System Pattern**:
- Services (non-React): Use `apiClient.getAuthHeaders()`
- React components: Use `useAuth().getAuthHeaders()`

```typescript
// Services
import { getAuthHeaders } from '@/lib/api/apiClient';
const headers = getAuthHeaders();

// React components
import { useAuth } from '@/contexts/AuthContext';
const { getAuthHeaders } = useAuth();
const headers = getAuthHeaders();
```

---

## Security Hardening

### Pattern 7: Never Log Sensitive Headers

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

### Pattern 8: Feature Flag Gating

```typescript
// Explicit feature flag for fallback operations
const enableFallback = String(
  process.env.NEXT_PUBLIC_ENABLE_FALLBACK || ''
).toLowerCase() === 'true';

if (!enableFallback) {
  console.warn('Fallback disabled by feature flag');
  throw error;
}
```

### Pattern 9: Environment-Specific Endpoints

```typescript
// Dual-gate demo endpoints
const ASSETS_ENDPOINT =
  process.env.NODE_ENV === 'development' &&
  String(process.env.NEXT_PUBLIC_ENABLE_DEMO_ENDPOINT || '').toLowerCase() === 'true'
    ? '/auth/demo/assets'
    : '/unified-discovery/assets';
```

### Pattern 10: Regex for Security Paths

```typescript
// Use precise regex to prevent path traversal
const isAgenticActivity = (
  /\/flows\/execute(?:$|\?)/.test(endpoint) ||
  /\/flows\/[^/]+\/resume(?:$|\?)/.test(endpoint)
);

// NOT: endpoint.includes('/flows/execute') - too broad
```

---

## Anti-Patterns

### Don't: Skip Tenant Scoping

```python
# WRONG - High security risk
query = select(Asset).where(Asset.id == asset_id)

# CORRECT
query = select(Asset).where(
    and_(
        Asset.id == asset_id,
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
)
```

### Don't: Convert UUID to Integer

```python
# WRONG - Causes type errors
client_account_id_int = int(context.client_account_id)

# CORRECT
client_account_uuid = UUID(context.client_account_id)
```

### Don't: Use @lru_cache for Tenant Data

```python
# WRONG - Returns same data for all tenants
@lru_cache(maxsize=1)
def get_tenant_data():
    return fetch_data()

# CORRECT - Accept tenant context
def get_tenant_data(client_account_id, engagement_id):
    return fetch_data_for_tenant(client_account_id, engagement_id)
```

### Don't: Cache Service Instances by Session

```python
# WRONG - Memory leak
_service_cache: Dict[str, Service] = {}
def get_service(session_id: str):
    if session_id not in _service_cache:
        _service_cache[session_id] = Service()
    return _service_cache[session_id]

# CORRECT - Create fresh instances
def get_service(db: AsyncSession):
    return Service(db=db)
```

---

## Code Templates

### Template 1: Tenant-Scoped Repository

```python
class TenantScopedRepository:
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Entity]:
        result = await self.db.execute(
            select(Entity).where(
                and_(
                    Entity.id == entity_id,
                    Entity.client_account_id == self.client_account_id,
                    Entity.engagement_id == self.engagement_id,
                )
            )
        )
        return result.scalar_one_or_none()
```

### Template 2: API Endpoint with UUID Conversion

```python
@router.get("/status/{flow_id}")
async def get_status(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_async_db),
):
    # Convert to UUID (NEVER to int)
    client_account_uuid = (
        UUID(context.client_account_id)
        if isinstance(context.client_account_id, str)
        else context.client_account_id
    )
    engagement_uuid = (
        UUID(context.engagement_id)
        if isinstance(context.engagement_id, str)
        else context.engagement_id
    )

    repo = FlowRepository(
        db=db,
        client_account_id=client_account_uuid,
        engagement_id=engagement_uuid,
    )

    return await repo.get_by_id(UUID(flow_id))
```

---

## Troubleshooting

### Issue: "Missing headers: ['User ID']" 400 error

**Cause**: Direct `fetch()` bypassing apiCall() utility.

**Fix**: Use apiCall() or manually add X-User-ID header.

### Issue: "operator does not exist: uuid = integer"

**Cause**: Converting tenant ID to int instead of UUID.

**Fix**: Replace `int(client_account_id)` with `UUID(client_account_id)`.

### Issue: Cross-tenant data exposure

**Cause**: Missing tenant scoping in query.

**Fix**: Add `and_(client_account_id, engagement_id)` to WHERE clause.

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `cross_tenant_security_patterns` | 2025-09 | Query scoping |
| `uuid-tenant-id-enforcement-codebase-pattern-2025-10` | 2025-10 | UUID enforcement |
| `security_hardening_patterns` | 2025-09 | Hardening patterns |
| `auth-headers-consolidation-pattern` | 2025-10 | Header architecture |
| `frontend_auth_header_missing_userid_fix_2025_10` | 2025-10 | Header fix |
| `dependency_security_management_patterns` | 2025-09 | Dependency security |
| `security_best_practices` | 2025-09 | Best practices |
| `security_vulnerability_fixes_2025_09` | 2025-09 | Vulnerability fixes |
| `user_registration_security_fix_2025_23` | 2025-09 | Registration security |
| `download-functionality-auth-fix` | 2025-09 | Download auth |
| `data-driven-refactoring-and-security-patterns-2025-01` | 2025-01 | Refactoring patterns |
| `pre_commit_security_fixes` | 2025-09 | Pre-commit security |

**Archive Location**: `.serena/archive/security/`

---

## Search Keywords

security, multi_tenant, tenant_scoping, uuid, authentication, headers, cross_tenant, authorization
