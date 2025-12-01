# Collection Flow Child Service Migration Pattern (Oct 2025)

## Problem: Hybrid State from Partial Migration

**Symptoms**: Collection flow E2E failures - flows create but cannot resume/execute
- Resume/Continue: "No crew_class registered" or "No execution handler"
- Phase transitions don't trigger agent execution

**Root Cause**: Partial migration left execution layer unmigrated
- ✅ Gap Analysis migrated to persistent agents (PR #506, #508)
- ✅ State Management migrated to CollectionFlowStateService (PR #518)
- ❌ Flow Execution still uses crew_class=UnifiedCollectionFlow (NOT MIGRATED)

**Cascade Failure**:
```python
# collection_flow_config.py - BROKEN
try:
    from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow
    # Import ALWAYS fails - UnifiedCollectionFlow imports deleted GapAnalysisAgent
except ImportError:
    UnifiedCollectionFlow = None

crew_class=(UnifiedCollectionFlow if COLLECTION_FLOW_AVAILABLE else None),  # Always None
```

## Solution: Complete Migration to child_flow_service

**Pattern**: Create `{Flow}ChildFlowService` matching Discovery pattern

```python
# backend/app/services/child_flow_services/collection.py
class CollectionChildFlowService(BaseChildFlowService):
    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)
        self.repository = CollectionFlowRepository(
            db=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        self.state_service = CollectionFlowStateService(db, context)

    async def execute_phase(self, flow_id: str, phase_name: str, phase_input: Dict) -> Dict:
        child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))

        if phase_name == "gap_analysis":
            gap_service = GapAnalysisService(self.db, self.context)
            result = await gap_service.execute_gap_analysis(
                collection_flow_id=child_flow.id,  # UUID PK (NOT flow_id)
                phase_input=phase_input
            )
            await self._auto_progress_phase(result)
            return result
```

**Config Update**:
```python
# collection_flow_config.py - AFTER
from app.services.child_flow_services import CollectionChildFlowService

FlowConfig(
    flow_type="collection",
    child_flow_service=CollectionChildFlowService,  # NEW
    # crew_class removed entirely
)
```

**MFO Update** (single path):
```python
# lifecycle_commands.py
if flow_config.child_flow_service:
    child_service = flow_config.child_flow_service(self.db, self.context)
    result = await child_service.execute_phase(...)
    return result
else:
    raise ValueError(f"No execution handler")  # Fail fast
```

## Simplification Methodology: 90% Complexity Reduction

**Before (Over-Engineered)**:
- 900+ lines documentation
- 6 phases, 2.5 hours
- Deprecation windows, feature flags, dual paths
- SSE/WebSockets, per-asset concurrency, secondary keys
- Complex idempotency, multi-tier rate limiting

**After (Simplified - GPT5 Approved)**:
- 600 lines documentation
- 3 phases, 1 hour
- Delete legacy immediately (no deprecation)
- Single execution path (child_flow_service ONLY)
- HTTP polling, sequential processing, single Redis keys
- Simple idempotency (Redis key exists check)

**Key Question**: "What can we DELETE?" not "What can we ADD?"

## Critical Corrections Applied

### 1. UUID Type Confusion
**WRONG Assumption**: `collection_flows.id` = Integer PK
**CORRECT (Verified)**: `collection_flows.id` = UUID PK

```python
# ✅ Always verify schema before assuming types
docker exec migration_postgres psql -U postgres -d migration_db -c "\d migration.collection_flows"

# Rules:
# - collection_flows.id (UUID PK) → ALL FKs, persistence, background jobs
# - collection_flows.flow_id (UUID) → MFO orchestrator calls ONLY
```

### 2. Explicit Wiring (No Implicit References)
```python
# ❌ DON'T: Rely on implicit repository
child_flow = await repository.get_by_master_flow_id(UUID(flow_id))

# ✅ DO: Explicit instantiation
repository = CollectionFlowRepository(
    db=db,
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id
)
redis = get_redis_manager().client
```

### 3. Fresh DB Session in Workers
```python
# ❌ DON'T: Use request scope session in background worker
async def worker(db: AsyncSession, ...):  # Wrong

# ✅ DO: Create fresh session
async def worker(client_account_id: str, ...):
    async with AsyncSessionLocal() as db:
        # worker logic
```

### 4. UUID Casts in Persistence
```python
# ✅ Always cast to UUID
await upsert_gap(
    db=db,
    collection_flow_id=UUID(collection_flow_id),  # UUID PK
    asset_id=UUID(gap["asset_id"]),  # UUID type
    ...
)
```

### 5. Tenant Scoping Everywhere
```python
# ✅ Every repository query MUST include tenant context
# Repository internally adds:
# .where(CollectionFlow.client_account_id == self.client_account_id)
# .where(CollectionFlow.engagement_id == self.engagement_id)
```

## Implementation Pattern

### Phase 1: Create ChildFlowService (20 min)
- File: `backend/app/services/child_flow_services/collection.py`
- Match Discovery pattern exactly
- Update `__init__.py` exports

### Phase 2: Delete Legacy & Update Config (20 min)
- Delete: `unified_collection_flow.py` immediately (no deprecation)
- Revert: `GapAnalysisAgent` placeholder (wrong fix)
- Update: `collection_flow_config.py` (crew_class → child_flow_service)

### Phase 3: Update MFO Resume (20 min)
- Check `child_flow_service` ONLY (remove crew_class fallback)
- Fail fast if no handler
- File: `lifecycle_commands.py`

### Testing: 4 Minimal Tests
1. E2E: Submit gaps → 202; progress; upserts; phase advances
2. >200 gaps → 400 (validation)
3. Second submission while running → 409 (idempotency)
4. Rerun after completion → no duplicates (upsert)

## Documentation Created

1. **ADR-025**: `docs/adr/025-collection-flow-child-service-migration.md`
   - Architectural decision record
   - Context, decision, consequences
   - Alignment with ADR-006, 012, 015, 024

2. **Simplified Plan**: `docs/development/collection_flow/COLLECTION_FLOW_MIGRATION_PLAN_SIMPLIFIED.md`
   - Implementation guide (GPT5 approved)
   - 3 phases with code examples
   - Explicit wiring patterns

3. **Comprehensive Plan**: `docs/development/collection_flow/COLLECTION_FLOW_MIGRATION_PLAN.md`
   - Detailed reference
   - Risk assessment, rollback procedures

## When to Use This Pattern

**Apply when**:
- Partial migration leaves execution layer unmigrated
- crew_class import fails due to deleted dependencies
- Flow creates successfully but cannot resume/execute
- E2E tests show "No execution handler" errors

**Steps**:
1. Identify what's already migrated (gap analysis? state management?)
2. Create `{Flow}ChildFlowService` for execution layer
3. Delete legacy immediately (if already broken)
4. Update config: crew_class → child_flow_service
5. Update MFO: single path, fail fast

**Result**: Architectural consistency, simplified maintenance, working E2E flow
