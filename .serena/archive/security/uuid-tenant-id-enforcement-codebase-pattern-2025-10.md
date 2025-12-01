# UUID Tenant ID Enforcement: Codebase-Wide Migration Pattern (Oct 2025)

## Problem

After database migration 115 converted tenant IDs to UUID, application code was still treating them as integers, causing runtime errors:

```
sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError:
operator does not exist: uuid = integer
HINT: No operator matches the given name and argument types.
You might need to add explicit type casts.
```

## Root Cause

**Anti-Pattern**: Converting UUID tenant IDs to integers throughout the codebase:

```python
# ❌ BAD - Converting UUID to integer
if isinstance(client_account_id, str):
    client_account_id_int = 1 if "1111111" in client_account_id else int(client_account_id)
else:
    client_account_id_int = int(client_account_id)
```

This creates type mismatches when querying database UUID columns.

## Solution: Systematic UUID Enforcement

### 1. Repository Layer - Accept UUID Types

```python
# ❌ BEFORE
class PlanningFlowRepository(ContextAwareRepository[PlanningFlow]):
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,  # ❌ Wrong type
        engagement_id: Optional[str] = None,      # ❌ Wrong type
    ):
        pass

    async def get_planning_flow_by_id(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,  # ❌ Wrong type
        engagement_id: int,      # ❌ Wrong type
    ) -> Optional[PlanningFlow]:
        pass

# ✅ AFTER
class PlanningFlowRepository(ContextAwareRepository[PlanningFlow]):
    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[uuid.UUID] = None,  # ✅ UUID
        engagement_id: Optional[uuid.UUID] = None,      # ✅ UUID
    ):
        pass

    async def get_planning_flow_by_id(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: uuid.UUID,  # ✅ UUID
        engagement_id: uuid.UUID,      # ✅ UUID
    ) -> Optional[PlanningFlow]:
        pass
```

### 2. API Endpoints - Convert to UUID, Never Integer

```python
# ❌ BEFORE
@router.get("/status/{planning_flow_id}")
async def get_planning_status(
    planning_flow_id: str,
    context: RequestContext = Depends(get_current_context_dependency),
):
    # Convert to integer (WRONG!)
    client_account_id_int = 1 if "1111111" in context.client_account_id else int(context.client_account_id)

    repo = PlanningFlowRepository(
        db=db,
        client_account_id=client_account_id_int,  # ❌ Passing int
        engagement_id=engagement_id_int,
    )

# ✅ AFTER
@router.get("/status/{planning_flow_id}")
async def get_planning_status(
    planning_flow_id: str,
    context: RequestContext = Depends(get_current_context_dependency),
):
    # Convert to UUID (CORRECT!)
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

    repo = PlanningFlowRepository(
        db=db,
        client_account_id=client_account_uuid,  # ✅ Passing UUID
        engagement_id=engagement_uuid,
    )
```

### 3. Service Layer - Store UUID Objects

```python
# ❌ BEFORE
class WavePlanningService:
    def __init__(self, db: AsyncSession, context: RequestContext):
        # Store as integers (WRONG!)
        self.client_account_id_int = int(context.client_account_id)
        self.engagement_id_int = int(context.engagement_id)

# ✅ AFTER
class WavePlanningService:
    def __init__(self, db: AsyncSession, context: RequestContext):
        # Store as UUIDs (CORRECT!)
        self.client_account_uuid = (
            UUID(context.client_account_id)
            if isinstance(context.client_account_id, str)
            else context.client_account_id
        )
        self.engagement_uuid = (
            UUID(context.engagement_id)
            if isinstance(context.engagement_id, str)
            else context.engagement_id
        )
```

### 4. Search Pattern for Violations

```bash
# Find all integer conversions of tenant IDs (potential violations)
grep -r "int(client_account_id)" backend/
grep -r "int(engagement_id)" backend/
grep -r "client_account_id_int" backend/
grep -r "engagement_id_int" backend/

# Find repository instantiations to check types
grep -r "PlanningFlowRepository(" backend/
```

## Migration Checklist

When enforcing UUID tenant IDs across codebase:

- [ ] **Repository `__init__`**: Change `Optional[str]` → `Optional[uuid.UUID]`
- [ ] **All repository methods**: Change `int` → `uuid.UUID` for tenant ID parameters
- [ ] **API endpoints**: Remove `int()` conversion, use `UUID()` instead
- [ ] **Service classes**: Store `client_account_uuid`, not `client_account_id_int`
- [ ] **Method calls**: Update all callers to pass UUID objects
- [ ] **Remove integer conversion logic**: Delete all `1 if "1111111" in x else int(x)` patterns
- [ ] **Test in Docker**: Verify queries execute without type errors

## Files Changed (Planning Flow Example)

1. `backend/app/repositories/planning_flow_repository.py` - 22 method signatures
2. `backend/app/api/v1/master_flows/planning/status.py` - Endpoint conversion
3. `backend/app/api/v1/master_flows/planning/update.py` - Endpoint conversion
4. `backend/app/api/v1/master_flows/planning/execute.py` - Endpoint conversion
5. `backend/app/api/v1/master_flows/planning/export.py` - Endpoint conversion
6. `backend/app/services/planning/wave_planning_service.py` - Service layer
7. `backend/app/api/v1/endpoints/plan.py` - Legacy endpoint
8. `backend/app/api/v1/endpoints/wave_planning.py` - Legacy endpoint

## Testing

```bash
# Restart backend
docker restart migration_backend

# Test endpoint with UUID headers
curl -X GET 'http://localhost:8000/api/v1/master-flows/planning/status/{uuid}' \
  -H 'X-Client-Account-ID: 11111111-1111-1111-1111-111111111111' \
  -H 'X-Engagement-ID: 22222222-2222-2222-2222-222222222222'

# Check logs for type errors
docker logs migration_backend --tail 50 | grep -i "operator does not exist"
```

## Key Principle

**NEVER convert tenant IDs to integers - always use UUID objects throughout the codebase.**

Demo UUIDs are still UUIDs:
- Client: `11111111-1111-1111-1111-111111111111` (UUID, not integer 1)
- Engagement: `22222222-2222-2222-2222-222222222222` (UUID, not integer 1)

## When to Use

- After Alembic migration converts database columns from INTEGER to UUID
- When seeing "operator does not exist: uuid = integer" errors
- When enforcing multi-tenant UUID architecture codebase-wide
- During repository/service layer refactoring

## Reference

- Issue: Planning flow queries failing with UUID type mismatch
- PR: fix/plan-flow-frontend-backend-integration-20251029-193739
- Migration: 115_fix_planning_flows_tenant_columns.py
- Pattern: Enforce UUID types in signatures, convert at API boundary only
