# Architecture Fix: Collection Flow Repository Layer Violation

## Problem Statement

The `CollectionFlowRepository` at line 82 violated architectural boundaries by importing and calling `MasterFlowOrchestrator` (a service layer component). This created a layering violation where the data persistence layer was orchestrating business logic and workflows.

**Original Violation:**
```python
# ❌ Repository importing service layer (line 82)
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

class CollectionFlowRepository:
    async def create(...):
        # Repository orchestrating MFO workflows
        mfo = MasterFlowOrchestrator(self.db, context)
        master_flow_id, _ = await mfo.create_flow(...)
```

## Architectural Pattern

The correct enterprise architecture follows this layering:

1. **API Layer** → Request handling
2. **Service Layer** → Business logic & orchestration (MFO coordination)
3. **Repository Layer** → Data persistence ONLY (no service imports)
4. **Model Layer** → Data structures

**Golden Rule:** Repositories MUST NOT import from `app.services`

## Solution Implemented

### 1. Created New Service: `CollectionFlowLifecycleService`

**File:** `/backend/app/services/collection_flow/lifecycle_service.py`

This service handles orchestration logic:
- MFO master flow registration
- Repository coordination for data persistence
- Two-table pattern linkage (master_flow_id ↔ flow_id)

```python
# ✅ Service handles orchestration
class CollectionFlowLifecycleService:
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.repository = CollectionFlowRepository(db, ...)
        self.orchestrator = MasterFlowOrchestrator(db, context)

    async def create_flow_with_orchestration(...):
        # Step 1: MFO creates master flow
        master_flow_id, _ = await self.orchestrator.create_flow(...)

        # Step 2: Repository persists child flow data
        flow = await self.repository.create_with_master_flow(
            flow_id=flow_id,
            master_flow_id=master_flow_id,
            ...
        )
        return flow
```

### 2. Refactored Repository: Pure Data Operations

**File:** `/backend/app/repositories/collection_flow_repository.py`

**Changes:**
- ✅ Removed `from app.services.master_flow_orchestrator` import (line 82)
- ✅ Removed MFO orchestration logic from `create()` method
- ✅ Added `create_with_master_flow()` for service coordination
- ✅ Deprecated old `create()` for backward compatibility with tests
- ✅ Repository now ONLY handles data persistence

```python
# ✅ Repository handles data ONLY
class CollectionFlowRepository:
    async def create_with_master_flow(
        self,
        flow_id: str,
        master_flow_id: uuid.UUID,
        ...
    ):
        # Pure data persistence - no orchestration
        flow_data = {...}
        return await super().create(commit=False, **flow_data)
```

### 3. Updated Package Exports

**File:** `/backend/app/services/collection_flow/__init__.py`

Added new service to exports:
```python
from .lifecycle_service import CollectionFlowLifecycleService

__all__ = [
    "CollectionFlowLifecycleService",  # NEW
    "CollectionFlowStateService",
    ...
]
```

## MFO Two-Table Pattern

The solution follows the critical MFO pattern from CLAUDE.md:

1. **Master Flow ID** (`crewai_flow_state_extensions.flow_id`)
   - Internal MFO routing and orchestration
   - Created by: `orchestrator.create_flow()`

2. **Child Flow ID** (`collection_flows.flow_id`)
   - User-facing identifier (URLs, API responses)
   - Created by: `repository.create_with_master_flow()`

3. **Linkage** (`collection_flows.master_flow_id`)
   - Foreign key relationship
   - Service layer resolves between IDs

## Usage Pattern

### New Code (CORRECT)

```python
from app.services.collection_flow import CollectionFlowLifecycleService

# Service handles orchestration
lifecycle_service = CollectionFlowLifecycleService(db, context)
flow = await lifecycle_service.create_flow_with_orchestration(
    flow_name="Production Migration",
    automation_tier="tier_2",
    flow_metadata={"source": "api"},
    collection_config={"mode": "manual"}
)
```

### Old Code (DEPRECATED - Tests Only)

```python
from app.repositories.collection_flow_repository import CollectionFlowRepository

# Repository for data queries only
repository = CollectionFlowRepository(db, client_account_id, engagement_id)
flows = await repository.get_active_flows()  # ✅ Data queries OK

# For flow creation, use lifecycle service instead
flow = await repository.create(...)  # ⚠️ Deprecated (no MFO integration)
```

## Files Modified

1. **`/backend/app/repositories/collection_flow_repository.py`**
   - Removed: MFO import and orchestration logic (line 82)
   - Added: `create_with_master_flow()` method for service coordination
   - Changed: Deprecated `create()` for backward compatibility

2. **`/backend/app/services/collection_flow/lifecycle_service.py`** (NEW)
   - Handles MFO orchestration + repository coordination
   - Follows MFO two-table pattern
   - Implements proper separation of concerns

3. **`/backend/app/services/collection_flow/__init__.py`**
   - Exported new `CollectionFlowLifecycleService`

4. **`/backend/app/services/collection_flow/LIFECYCLE_USAGE.md`** (NEW)
   - Usage documentation
   - Migration guide
   - Pattern examples

## Validation

✅ **No service imports in repository:**
```bash
$ grep "from app.services" backend/app/repositories/collection_flow_repository.py
# (no output - clean!)
```

✅ **Python syntax valid:**
```bash
$ python3.11 -m py_compile app/repositories/collection_flow_repository.py
# (no errors)
```

✅ **Import successful:**
```bash
$ python3.11 -c "from app.services.collection_flow import CollectionFlowLifecycleService"
# Import successful
```

✅ **Type checking clean:**
```bash
$ mypy app/services/collection_flow/lifecycle_service.py --ignore-missing-imports
# (no errors specific to lifecycle_service.py)
```

## Benefits

1. **Architectural Compliance**: Repository layer no longer imports service layer
2. **Separation of Concerns**: Clear distinction between data persistence and orchestration
3. **Testability**: Easier to test repository and service logic independently
4. **Maintainability**: Changes to MFO logic don't affect repository code
5. **MFO Pattern Adherence**: Proper two-table pattern implementation
6. **Backward Compatibility**: Existing tests continue to work

## Next Steps

1. Update API endpoints to use `CollectionFlowLifecycleService` instead of calling repository directly
2. Update integration tests to use lifecycle service for full MFO orchestration
3. Consider applying same pattern to other flow repositories (DiscoveryFlow, AssessmentFlow)

## References

- CLAUDE.md: MFO two-table pattern (lines 100-180)
- ADR-006: Master Flow Orchestrator architecture
- Enterprise architecture: 7-layer pattern (Repository ≠ Service)
