# Collection Flow Repository Layering Fix

## Architecture Violation (BEFORE)

```
┌─────────────────────────────────────────────────┐
│ API Layer                                        │
│ /api/v1/endpoints/collection_crud_execution/    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ Repository Layer (❌ VIOLATION)                  │
│ CollectionFlowRepository                         │
│                                                  │
│ async def create(...):                           │
│   from app.services import MasterFlowOrchestrator│  ← ❌ Repository importing Service!
│   orchestrator = MasterFlowOrchestrator(...)     │
│   master_flow_id = await orchestrator.create()   │  ← ❌ Repository orchestrating workflows!
│   flow_data = {...}                              │
│   return await super().create(**flow_data)       │
└─────────────────────────────────────────────────┘

Problem:
- Repository (data layer) importing Service layer components
- Repository orchestrating business logic and MFO workflows
- Violates enterprise layering principles
- Creates tight coupling between layers
```

## Correct Architecture (AFTER)

```
┌─────────────────────────────────────────────────┐
│ API Layer                                        │
│ /api/v1/endpoints/collection_crud_execution/    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ Service Layer (✅ ORCHESTRATION)                 │
│ CollectionFlowLifecycleService                   │
│                                                  │
│ async def create_flow_with_orchestration(...):   │
│   # Step 1: MFO creates master flow             │
│   master_id = await orchestrator.create_flow()   │  ← ✅ Service handles orchestration
│                                                  │
│   # Step 2: Repository persists data            │
│   flow = await repository.create_with_master()   │  ← ✅ Service coordinates layers
│   return flow                                    │
└────────────┬──────────────┬─────────────────────┘
             │              │
             ▼              ▼
    ┌────────────┐  ┌──────────────────────────┐
    │ MFO Service│  │ Repository Layer          │
    │            │  │ CollectionFlowRepository  │
    │ Workflow   │  │ (✅ DATA ONLY)            │
    │ Orchestr.  │  │                           │
    └────────────┘  │ async def create_with_master│
                    │     flow(...):             │
                    │   flow_data = {...}        │
                    │   return super().create()  │  ← ✅ Pure data persistence
                    └────────────────────────────┘

Benefits:
✅ Repository ONLY handles data persistence
✅ Service handles orchestration and coordination
✅ No cross-layer imports (Repository → Service)
✅ Clear separation of concerns
✅ Easier testing and maintenance
```

## Layer Responsibilities

### API Layer
- Request validation
- Authentication/authorization
- Response formatting
- **Calls:** Service layer only

### Service Layer (NEW: CollectionFlowLifecycleService)
- Business logic
- Workflow orchestration
- MFO coordination
- Multi-service coordination
- **Calls:** Orchestrator + Repository

### Repository Layer (FIXED: CollectionFlowRepository)
- Data persistence ONLY
- CRUD operations
- Query optimization
- **Calls:** Database only (NO service imports)

### Model Layer
- Data structures
- Validation rules
- Type definitions

## Code Flow Comparison

### BEFORE (Violation)

```python
# API Endpoint
@router.post("/collection-flows")
async def create_flow(db: AsyncSession):
    repo = CollectionFlowRepository(db, ...)
    # Repository orchestrates MFO internally (❌ wrong layer)
    flow = await repo.create(...)
    return flow
```

### AFTER (Correct)

```python
# API Endpoint
@router.post("/collection-flows")
async def create_flow(db: AsyncSession, context: RequestContext):
    # Service handles orchestration (✅ correct layer)
    lifecycle = CollectionFlowLifecycleService(db, context)
    flow = await lifecycle.create_flow_with_orchestration(...)
    return flow

# Service Layer
class CollectionFlowLifecycleService:
    async def create_flow_with_orchestration(...):
        # Orchestrate MFO + Repository
        master_id = await self.orchestrator.create_flow(...)
        flow = await self.repository.create_with_master_flow(
            master_flow_id=master_id, ...
        )
        return flow

# Repository Layer
class CollectionFlowRepository:
    async def create_with_master_flow(...):
        # Pure data persistence
        return await super().create(**flow_data)
```

## MFO Two-Table Pattern

The fix properly implements the MFO two-table pattern:

```
Master Flow (MFO Routing)          Child Flow (User Data)
┌──────────────────────────┐      ┌───────────────────────────┐
│ crewai_flow_state_       │      │ collection_flows          │
│ extensions               │      │                           │
│                          │      │                           │
│ flow_id (UUID) PK        │◄─────┤ master_flow_id (UUID) FK  │
│ flow_type: "collection"  │      │ flow_id (UUID) - user ID  │
│ flow_status: "running"   │      │ status: operational state │
│ current_phase: "init"    │      │ current_phase: sync copy  │
└──────────────────────────┘      └───────────────────────────┘
         ▲                                    ▲
         │                                    │
         │ Service Layer Resolves IDs         │
         │                                    │
   Orchestrator.create()          Repository.create_with_master()
```

## Migration Path

1. **Immediate (Done)**
   - ✅ Created `CollectionFlowLifecycleService`
   - ✅ Removed MFO import from repository
   - ✅ Added `create_with_master_flow()` to repository

2. **Short-term (Next PR)**
   - Update API endpoints to use lifecycle service
   - Update integration tests for full orchestration
   - Add usage examples to endpoint documentation

3. **Long-term (Future)**
   - Apply same pattern to DiscoveryFlowRepository
   - Apply same pattern to AssessmentFlowRepository
   - Add pre-commit hook to prevent repository → service imports

## Testing Strategy

### Unit Tests (Repository)
```python
# Test repository data operations ONLY
async def test_repository_create():
    repo = CollectionFlowRepository(db, ...)
    flow = await repo.create_with_master_flow(
        flow_id="123",
        master_flow_id=uuid4(),  # Provided by test
        ...
    )
    assert flow.flow_id == "123"
    # No MFO orchestration tested here
```

### Integration Tests (Service)
```python
# Test full orchestration flow
async def test_lifecycle_service_create():
    service = CollectionFlowLifecycleService(db, context)
    flow = await service.create_flow_with_orchestration(...)

    # Verify MFO master flow created
    assert flow.master_flow_id is not None

    # Verify child flow data persisted
    assert flow.flow_id is not None
    assert flow.status == "initialized"
```

## Architectural Principles Enforced

1. **Separation of Concerns**
   - Repository: Data persistence
   - Service: Orchestration
   - API: Request handling

2. **Dependency Direction**
   - API → Service → Repository
   - NEVER: Repository → Service

3. **Single Responsibility**
   - Each layer has ONE job
   - No cross-cutting concerns

4. **Testability**
   - Mock orchestrator for repository tests
   - Mock repository for service tests
   - Integration tests for full flow

5. **Maintainability**
   - Clear boundaries
   - Easy to locate logic
   - Reduce coupling

## References

- **CLAUDE.md**: MFO two-table pattern documentation
- **ADR-006**: Master Flow Orchestrator architecture decision
- **Enterprise Architecture**: 7-layer pattern requirements
- **Martin Fowler**: Patterns of Enterprise Application Architecture
