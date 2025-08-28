# Cross-Tenant Security Patterns

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
- Check all cache operations for tenant scoping
- Review service caching patterns for memory leaks
- Audit @lru_cache usage in multi-tenant code
- Ensure context parameters flow through all layers
