# Cross-Tenant Security Patterns

## Database Query Scoping (CRITICAL)
**ALWAYS** include tenant context in database queries to prevent cross-tenant data access

### Core Pattern: and_() Clauses for Multi-Field Scoping
```python
from sqlalchemy import select, and_

# WRONG - No tenant scoping (HIGH SECURITY RISK)
data_import_query = select(DataImport).where(DataImport.id == UUID(data_import_id))

# CORRECT - Tenant-scoped query with and_()
data_import_query = select(DataImport).where(
    and_(
        DataImport.id == UUID(data_import_id),
        DataImport.client_account_id == client_account_id,
        DataImport.engagement_id == engagement_id,
    )
)
```

### DELETE Operations - Critical for Cleanup
```python
from sqlalchemy import delete, and_

# CORRECT - Tenant-scoped delete to avoid cross-tenant data loss
delete_stmt = delete(ImportFieldMapping).where(
    and_(
        ImportFieldMapping.data_import_id == data_import_id,
        ImportFieldMapping.client_account_id == client_account_id,
    )
)
```

### Asset Loading with Tenant Scoping
```python
# CORRECT - Comprehensive tenant scoping for Asset table
asset = await db.scalar(
    select(Asset).where(
        and_(
            Asset.id == asset_id,
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        )
    )
)
```

## Files Recently Fixed (2025-09)
Critical security fixes applied to:
- `backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py`
- `backend/app/api/v1/endpoints/collection_applications.py`
- `backend/app/api/v1/endpoints/collection_crud_queries.py`
- `backend/app/services/collection_flow/state_management.py`

## Required for All Multi-Tenant Tables
Tables that MUST include tenant scoping:
- `DataImport` - Always scope with client_account_id
- `ImportFieldMapping` - Scope with client_account_id + engagement_id
- `DiscoveryFlow` - Scope with client_account_id + engagement_id
- `CollectionFlow` - Scope with client_account_id + engagement_id
- `Asset` - Scope with client_account_id + engagement_id
- `FlowExecution`
- `CrewAIFlowStateExtension`
- Any table with `client_account_id` and `engagement_id` fields

## Master Flow Query Pattern
```python
# CORRECT - Include engagement_id in master flow queries
master_flow_result = await db.execute(
    select(CrewAIFlowStateExtension).where(
        and_(
            CrewAIFlowStateExtension.flow_id == master_flow_id,
            CrewAIFlowStateExtension.client_account_id == client_account_id,
            CrewAIFlowStateExtension.engagement_id == engagement_id,
        )
    )
)
```

## Cache Key Scoping
**CRITICAL**: Always scope cache keys with tenant context to prevent data leakage

### Pattern
```python
# WRONG - Cross-tenant data exposure risk
cache_key = CacheKeys.user_clients(str(user.id))

# CORRECT - Tenant-scoped caching
cache_key = CacheKeys.user_clients(str(user.id))
if client_account_id:
    cache_key = f"{cache_key}:client:{client_account_id}"
if engagement_id:
    cache_key = f"{cache_key}:engagement:{engagement_id}"
```

## Service Instance Caching
**AVOID**: Don't cache service instances by session ID (causes memory leaks)

```python
# WRONG - Memory leak
_service_cache: Dict[str, DiscoveryFlowService] = {}
def get_service(session_id: str):
    if session_id not in _service_cache:
        _service_cache[session_id] = DiscoveryFlowService()
    return _service_cache[session_id]

# CORRECT - Create fresh instances
def get_service(db: AsyncSession):
    return DiscoveryFlowService(db=db)
```

## LRU Cache in Multi-Tenant Context
**NEVER** use @lru_cache for functions returning tenant-specific data

```python
# WRONG - Returns same data for all tenants
@lru_cache(maxsize=1)
def get_tenant_data():
    return fetch_data()

# CORRECT - Accept tenant context parameters
def get_tenant_data(client_account_id: str = None, engagement_id: str = None):
    # Return fresh data per context
    return fetch_data_for_tenant(client_account_id, engagement_id)
```

## Validation Points
- Check all database queries for tenant scoping (HIGH PRIORITY)
- Always use `and_()` for multiple WHERE conditions
- Include both client_account_id AND engagement_id where available
- Check all cache operations for tenant scoping
- Review service caching patterns for memory leaks
- Audit @lru_cache usage in multi-tenant code
- Ensure context parameters flow through all layers
