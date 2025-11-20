# Collection Flow Lifecycle Service Usage

## Overview

The `CollectionFlowLifecycleService` separates data persistence from orchestration logic, following the architectural pattern:

- **Repository**: ONLY handles data persistence (create, read, update, delete)
- **Service**: Handles business logic and orchestration (MFO integration, workflow coordination)

## Architecture Fix

Previously, the repository violated architectural boundaries by importing and calling `MasterFlowOrchestrator`. This created a layering violation where the data layer was orchestrating workflows.

Now:
- Repository: Pure data operations, no service imports
- Service: Orchestrates MFO + repository coordination

## Usage Pattern

### Creating a Collection Flow (New Code)

```python
from app.services.collection_flow import CollectionFlowLifecycleService
from app.core.context import RequestContext

# In your endpoint or service:
async def create_collection_flow(
    db: AsyncSession,
    context: RequestContext,
    flow_name: str,
    automation_tier: str
):
    # Use lifecycle service for orchestration
    lifecycle_service = CollectionFlowLifecycleService(db, context)

    # This handles:
    # 1. MFO master flow creation
    # 2. Child flow data persistence
    # 3. Linking the two tables
    collection_flow = await lifecycle_service.create_flow_with_orchestration(
        flow_name=flow_name,
        automation_tier=automation_tier,
        flow_metadata={"source": "api"},
        collection_config={"mode": "manual"}
    )

    return collection_flow
```

### Repository Pattern (Data Only)

```python
from app.repositories.collection_flow_repository import CollectionFlowRepository

# For direct data operations (no orchestration):
async def query_collection_flows(
    db: AsyncSession,
    client_account_id: str,
    engagement_id: str
):
    repository = CollectionFlowRepository(
        db=db,
        client_account_id=client_account_id,
        engagement_id=engagement_id
    )

    # Repository handles ONLY data queries
    flows = await repository.get_active_flows()
    return flows
```

## MFO Two-Table Pattern

The service follows the MFO two-table pattern from CLAUDE.md:

1. **Master Flow ID** (crewai_flow_state_extensions.flow_id)
   - Internal MFO routing
   - Used for orchestration calls
   - Created by `orchestrator.create_flow()`

2. **Child Flow ID** (collection_flows.flow_id)
   - User-facing identifier
   - Used in URLs and API responses
   - Created by `repository.create_with_master_flow()`

3. **Linkage** (collection_flows.master_flow_id)
   - Foreign key relationship
   - Service resolves between IDs

## Migration Guide

### Old Pattern (DEPRECATED)

```python
# ❌ Repository doing orchestration (violates architecture)
repository = CollectionFlowRepository(db, client_account_id, engagement_id)
flow = await repository.create(
    flow_name="Test",
    automation_tier="tier_1"
)
```

### New Pattern (CORRECT)

```python
# ✅ Service handles orchestration, repository handles data
lifecycle_service = CollectionFlowLifecycleService(db, context)
flow = await lifecycle_service.create_flow_with_orchestration(
    flow_name="Test",
    automation_tier="tier_1"
)
```

## Testing

The repository's `create()` method is retained for backward compatibility with existing tests:

```python
# Tests can still use repository directly (no MFO integration)
repository = CollectionFlowRepository(db, client_account_id, engagement_id)
flow = await repository.create(
    flow_name="Test",
    automation_tier="tier_1",
    master_flow_id=uuid.uuid4()  # Provide master_flow_id if needed
)
```

For integration tests requiring full MFO orchestration, use the lifecycle service.

## Files Modified

1. `/backend/app/repositories/collection_flow_repository.py`
   - Removed MFO import and orchestration logic
   - Added `create_with_master_flow()` for service coordination
   - Deprecated `create()` for backward compatibility

2. `/backend/app/services/collection_flow/lifecycle_service.py`
   - New service for orchestration logic
   - Handles MFO integration + repository coordination
   - Follows MFO two-table pattern

3. `/backend/app/services/collection_flow/__init__.py`
   - Exported new lifecycle service
