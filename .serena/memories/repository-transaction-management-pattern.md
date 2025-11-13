# Repository Transaction Management: Flush vs Commit Pattern

## Problem
Adding `async with db.begin():` wrapper around repository calls causes:
```
InvalidRequestError: A transaction is already begun on this Session
```

## Root Cause Analysis

### Repository Pattern
Repository methods do `flush()` but NOT `commit()`:
```python
# File: backend/app/repositories/planning_flow_repository/planning_flow_operations.py
async def update_planning_flow(self, ...) -> Optional[PlanningFlow]:
    stmt = update(PlanningFlow).where(...).values(**updates)
    await self.db.execute(stmt)
    await self.db.flush()  # ✅ Flushes to DB but doesn't commit

    updated_flow = await self.get_planning_flow_by_id(...)
    return updated_flow
```

**Why flush without commit?**
- Allows caller to batch multiple operations in one transaction
- Repository doesn't assume transaction boundaries
- Caller manages commit/rollback based on business logic

### Incorrect Caller Pattern (Creates Nested Transaction)
```python
# ❌ WRONG - Creates nested transaction error
async with db.begin():  # Starts transaction
    updated_flow = await repo.update_planning_flow(...)  # Already in transaction
    await db.flush()
# Tries to auto-commit on exit, but transaction already active
```

### Correct Caller Pattern
```python
# ✅ CORRECT - Let repository handle flush, caller commits
updated_flow = await repo.update_planning_flow(
    planning_flow_id=planning_flow_uuid,
    client_account_id=client_account_uuid,
    engagement_id=engagement_uuid,
    **update_data,
)
await db.commit()  # Explicit commit after repository operation
```

## When to Use Each Pattern

### Use `async with db.begin():`
When doing MULTIPLE operations that need atomicity:
```python
async with db.begin():
    # Multiple raw DB operations
    await db.execute(insert_stmt_1)
    await db.execute(update_stmt_2)
    await db.execute(delete_stmt_3)
    # Auto-commits on successful exit, auto-rollback on exception
```

### Use `await db.commit()`
When calling repository methods that already flush:
```python
# Repository already did flush(), just need commit
result = await repository.update_entity(...)
await db.commit()
```

### Repository Method Pattern
```python
async def update_entity(self, entity_id: UUID, **updates):
    stmt = update(Entity).where(Entity.id == entity_id).values(**updates)
    await self.db.execute(stmt)
    await self.db.flush()  # Send to DB but don't commit

    # Fetch updated entity within same transaction
    updated = await self.get_entity_by_id(entity_id)
    return updated
    # Caller will commit
```

## Error Message Lookup

If you see: `InvalidRequestError: A transaction is already begun on this Session`

**Check**:
1. Repository method does `await self.db.flush()`
2. Caller wraps repository call in `async with db.begin():`
3. **Fix**: Remove wrapper, use `await db.commit()` after repository call

## Related Bug
- Issue #1000: Planning Flow Wave Creation Transaction Error
- File: `backend/app/api/v1/master_flows/planning/update.py` (line 159-166)
- Fix: Removed `async with db.begin():` wrapper, kept `await db.commit()`

## Best Practice
Repository layer should:
- Execute SQL statements
- Flush to database (`await db.flush()`)
- NOT commit (leave to caller)

Caller/endpoint should:
- Call repository method
- Commit transaction (`await db.commit()`)
- Handle exceptions and rollback if needed
