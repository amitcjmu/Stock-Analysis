# Collection Flow UUID Pattern - Quick Reference

**CRITICAL**: Collection Flow has a **different UUID pattern** than Assessment/Discovery flows.

---

## The Three-UUID Architecture

```python
class CollectionFlow(Base):
    id = Column(UUID, primary_key=True, default=uuid.uuid4)  # AUTO-GENERATED
    flow_id = Column(UUID, unique=True)                      # MANUALLY SET AT CREATION
    master_flow_id = Column(UUID, ForeignKey(...))           # FK TO MASTER FLOW
```

**KEY INSIGHT**: All three UUIDs are **DIFFERENT** values!

Example from database:
```
id                  = c184ec01-341b-4041-a4e6-015c3f762c39  (child PK)
flow_id             = d083d66c-bd92-418b-bbff-2dbb7b1ad920  (manually set)
master_flow_id      = 1eab4344-98e8-4636-a71e-d5cf329ac93c  (FK to master)
```

---

## The MANDATORY Pattern

### ❌ WRONG (Causes "Collection flow not found")
```python
@router.get("/flows/{flow_id}/questionnaires")
async def get_questionnaires(flow_id: str, db: AsyncSession):
    # BUG: Only checks flow_id column
    result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == UUID(flow_id),
        )
    )
```

### ✅ CORRECT (Flexible Lookup)
```python
@router.get("/flows/{flow_id}/questionnaires")
async def get_questionnaires(flow_id: str, db: AsyncSession):
    # MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
    flow_uuid = UUID(flow_id)
    result = await db.execute(
        select(CollectionFlow).where(
            (CollectionFlow.flow_id == flow_uuid)
            | (CollectionFlow.id == flow_uuid),
        )
    )
```

---

## Why Flexible Lookup?

Frontend can pass **EITHER**:
1. `CollectionFlow.flow_id` (from creation response)
2. `CollectionFlow.id` (from flow lists/status endpoints)

**We don't control which one**, so queries MUST accept both.

---

## Update Pattern Optimization

When updating after querying, use the **flow object's PK**:

```python
# Query the flow
flow = await db.execute(
    select(CollectionFlow).where(
        (CollectionFlow.flow_id == flow_uuid) | (CollectionFlow.id == flow_uuid)
    )
).scalar_one_or_none()

# Update using flow.id (PK) - NOT flow_id from URL!
await db.execute(
    update(CollectionFlow)
    .where(CollectionFlow.id == flow.id)  # ✅ Use flow object PK
    .values(status="completed")
)
```

**Why**: More efficient, clearer intent, no UUID ambiguity.

---

## Copy-Paste Template

```python
# MFO Two-Table Pattern: Query by EITHER flow_id OR id (flexible lookup)
flow_uuid = UUID(flow_id)
result = await db.execute(
    select(CollectionFlow).where(
        (CollectionFlow.flow_id == flow_uuid)
        | (CollectionFlow.id == flow_uuid),
        CollectionFlow.engagement_id == context.engagement_id,
        CollectionFlow.client_account_id == context.client_account_id,
    )
)
flow = result.scalar_one_or_none()

if not flow:
    raise HTTPException(status_code=404, detail="Collection flow not found")
```

---

## Pre-Commit Check

Before committing Collection Flow code:
```bash
# Search for broken pattern
grep -r "CollectionFlow.flow_id == UUID(flow_id)" backend/app/api/v1/endpoints/collection*

# Should return 0 results!
```

---

## Reference Files

**Working Examples**:
- `/backend/app/api/v1/endpoints/collection_crud_queries/status.py` (line 116-117)
- `/backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py` (line 42-43)

**Full Documentation**:
- `/docs/fixes/MFO_UUID_MISMATCH_FIX_SUMMARY.md`
- `/.serena/memories/mfo_two_table_flow_id_pattern_critical.md`

---

## Common Mistakes

1. ❌ `CollectionFlow.flow_id == UUID(flow_id)` (only checks one column)
2. ❌ Conditional logic based on parameter (removed in validators.py)
3. ❌ Using `flow_id` from URL in updates (use `flow.id` instead)

---

## Quick Checklist

- [ ] Use flexible lookup: `(flow_id == uuid) | (id == uuid)`
- [ ] Add MFO pattern comment for clarity
- [ ] Use `flow.id` for updates when flow object available
- [ ] Include tenant scoping (engagement_id, client_account_id)
- [ ] Handle `scalar_one_or_none()` with 404 if not found

**When in doubt**: Copy the pattern from `collection_crud_queries/status.py`!
