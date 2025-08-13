# Service Registry Migration Guide

## Overview
This guide provides step-by-step instructions for migrating from the legacy AsyncSessionLocal pattern to the new Service Registry architecture.

## Table of Contents
1. [Background](#background)
2. [Migration Strategy](#migration-strategy)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Testing](#testing)
5. [Rollback Plan](#rollback-plan)
6. [Troubleshooting](#troubleshooting)

## Background

### Problems with Legacy Pattern
- **Session Leaks**: Tools create their own database sessions, leading to resource leaks
- **No Transaction Control**: Multiple commits within single operation
- **Multi-tenant Issues**: Inconsistent tenant isolation
- **No Service Lifecycle Management**: Services recreated on every call

### Service Registry Benefits
- **Centralized Session Management**: Orchestrator owns all database sessions
- **Transaction Control**: Single commit per operation
- **Service Caching**: Reuse services within execution context
- **Multi-tenant Safety**: Enforced context isolation
- **Performance Monitoring**: Built-in metrics and monitoring

## Migration Strategy

### Phase 1: Enable Feature Flag (Current)
```bash
# Enable Service Registry for testing
export USE_SERVICE_REGISTRY=true
```

### Phase 2: Gradual Rollout
1. Start with non-critical flows
2. Monitor performance metrics
3. Expand to all flows
4. Remove legacy code

### Phase 3: Full Migration
1. Make Service Registry default
2. Remove feature flag
3. Archive legacy code

## Step-by-Step Migration

### 1. Update Tool Creation Functions

**Before (Legacy):**
```python
def create_asset_creation_tools(context: Dict[str, Any]) -> List[BaseTool]:
    async def create_asset(**kwargs):
        async with AsyncSessionLocal() as db:  # ❌ Creates own session
            repository = AssetRepository(db, context)
            asset = await repository.create(**kwargs)
            await db.commit()  # ❌ Commits directly
            return asset

    return [Tool(create_asset)]
```

**After (Service Registry):**
```python
def create_asset_creation_tools(
    context: Dict[str, Any],
    registry: Optional[ServiceRegistry] = None
) -> List[BaseTool]:
    if registry:
        # ✅ Use ServiceRegistry pattern
        from app.services.crewai_flows.tools.asset_creation_tool import (
            AssetCreationToolWithService
        )
        return [AssetCreationToolWithService(registry)]
    else:
        # Legacy fallback (will be removed)
        from .asset_creation_tool_legacy import AssetCreationTool
        return [AssetCreationTool()]
```

### 2. Update Flow Executors

**Before:**
```python
class FlowCrewExecutor:
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
```

**After:**
```python
class FlowCrewExecutor:
    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        service_registry: Optional[ServiceRegistry] = None
    ):
        self.db = db
        self.context = context
        self.service_registry = service_registry or ServiceRegistry(db, context)
```

### 3. Update Agent Pools

**Before:**
```python
agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
    client_id, engagement_id
)
```

**After:**
```python
agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
    client_id, engagement_id, service_registry=self.service_registry
)
```

### 4. Implement Cleanup

**Always cleanup Service Registry:**
```python
async with ServiceRegistry(db, context) as registry:
    # Use registry for operations
    result = await execute_with_registry(registry)
    # Automatic cleanup on exit
```

Or manually:
```python
registry = ServiceRegistry(db, context)
try:
    result = await execute_with_registry(registry)
finally:
    await registry.cleanup()
```

## Testing

### 1. Unit Tests
```python
# Test with ServiceRegistry
async def test_with_service_registry():
    mock_session = AsyncMock()
    context = RequestContext(client_account_id="test")

    async with ServiceRegistry(mock_session, context) as registry:
        service = registry.get_service(AssetService)
        assert service is not None
        # Verify service reuse
        service2 = registry.get_service(AssetService)
        assert service is service2  # Same instance
```

### 2. Integration Tests
```bash
# Run with Service Registry enabled
USE_SERVICE_REGISTRY=true pytest tests/integration/

# Compare with legacy
USE_SERVICE_REGISTRY=false pytest tests/integration/
```

### 3. Performance Tests
```python
from app.services.service_registry_metrics import get_monitor

monitor = get_monitor()
# ... run operations ...
summary = monitor.get_performance_summary(registry_id)
assert summary["cache_hit_rate"] > 80
assert summary["healthy"] is True
```

## Rollback Plan

If issues arise, rollback is simple:

### 1. Disable Feature Flag
```bash
export USE_SERVICE_REGISTRY=false
```

### 2. Monitor Legacy Path
- Check logs for deprecation warnings
- Monitor session usage
- Track memory leaks

### 3. Fix Issues
- Address identified problems
- Re-enable Service Registry
- Continue migration

## Troubleshooting

### Common Issues

#### 1. "ServiceRegistry instance is required"
**Cause:** Feature flag enabled but no registry provided
**Solution:** Ensure orchestrator creates and passes ServiceRegistry

#### 2. Low Cache Hit Rate
**Cause:** Services not being reused effectively
**Solution:** Check service lifecycle, ensure proper registry scope

#### 3. Memory Growth
**Cause:** Registry not being cleaned up
**Solution:** Use context manager or call cleanup() explicitly

#### 4. Transaction Errors
**Cause:** Service trying to commit when it shouldn't
**Solution:** Ensure services use commit=False for repository operations

### Monitoring Commands

```bash
# Check for violations
python scripts/check_service_registry.py

# Monitor metrics
python -c "
from app.services.service_registry_metrics import get_monitor
monitor = get_monitor()
print(monitor.export_metrics())
"
```

## Best Practices

1. **Always use context managers** for Service Registry
2. **Never commit in services** - orchestrator owns transactions
3. **Monitor cache hit rates** - should be >80%
4. **Clean up registries** - prevent memory leaks
5. **Use metrics** - track performance and issues

## Timeline

- **Week 1-2**: Enable in development environment
- **Week 3-4**: Deploy to staging with 10% traffic
- **Week 5-6**: Increase to 50% traffic
- **Week 7-8**: Full production rollout
- **Week 9-10**: Remove legacy code

## Support

For issues or questions:
1. Check this migration guide
2. Review test examples in `tests/test_service_registry*.py`
3. Monitor metrics dashboard
4. Contact platform team

## Appendix: Code Examples

### Complete Tool Migration Example
See `app/services/crewai_flows/tools/asset_creation_tool.py`

### Complete Executor Migration Example
See `app/services/flow_orchestration/execution_engine_crew.py`

### Metrics Integration Example
See `app/services/service_registry_metrics.py`
