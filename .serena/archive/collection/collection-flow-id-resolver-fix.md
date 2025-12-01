# Collection Flow ID Resolver - Correct Fix (Oct 5, 2025)

## THE ACTUAL ROOT CAUSE

**The bug was in `resolve_collection_flow_id()`, NOT in FK constraints.**

### What Was Wrong

The resolver was querying by `id` when it should query by `flow_id`, and returning the wrong value:

```python
# ❌ BROKEN (Oct 1-5, 2025)
stmt = select(CollectionFlow).where(CollectionFlow.id == flow_uuid)  # Wrong column!
return str(collection_flow.id)  # Would return PK if found, but query fails
```

**Problem**: Frontend passes `flow_id` (business identifier), but resolver queried by `id` (PK). Query fails, no flow found, errors cascade.

### Why FK Retargeting Was WRONG

**Migrations 081/082 incorrectly changed FK constraints to point to `flow_id`:**

```sql
-- ❌ WRONG (Migrations 081/082)
FOREIGN KEY (collection_flow_id) REFERENCES collection_flows(flow_id)

-- ✅ CORRECT (ORM expectation)
FOREIGN KEY (collection_flow_id) REFERENCES collection_flows(id)
```

**Why This Broke Things**:
1. **ORM Mismatch**: SQLAlchemy models define `ForeignKey("collection_flows.id")`
2. **Cascade Failures**: ORM expects FK on PRIMARY KEY for proper cascades
3. **Performance**: Non-PK joins are slower, missing PK index benefits
4. **Architectural Violation**: FKs MUST reference PRIMARY KEYS per PostgreSQL/SQLAlchemy best practices

## THE CORRECT FIX ✅ (Migrations 083/084)

### Architecture Rules

**ALWAYS**:
- FK constraints point to PRIMARY KEY (`collection_flows.id`)
- `flow_id` is a business identifier for external APIs
- Use resolver to translate `flow_id` → `id` before FK writes

### Correct Resolver Implementation

```python
async def resolve_collection_flow_id(
    flow_id: str,
    db: AsyncSession,
) -> str:
    """
    Resolve collection flow PRIMARY KEY (id) from business flow_id.

    CRITICAL ARCHITECTURE:
    - Input: flow_id (business identifier from frontend/API)
    - Output: id (PRIMARY KEY for FK relationships)
    - WHY: FK constraints reference collection_flows.id (PK), not flow_id
    """
    flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

    # Query by flow_id (business ID from frontend)
    stmt = select(CollectionFlow).where(CollectionFlow.flow_id == flow_uuid)
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        # Return PRIMARY KEY (id) for FK storage
        return str(collection_flow.id)

    # Also check if input is master_flow_id
    stmt = select(CollectionFlow).where(CollectionFlow.master_flow_id == flow_uuid)
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if collection_flow:
        return str(collection_flow.id)  # Return PK

    raise ValueError(f"No collection flow found for: {flow_id}")
```

### Correct FK Usage in Endpoints

```python
# ✅ CORRECT - Use PK for FK relationships
from .data_loader import resolve_collection_flow_id

# Resolve business flow_id to PK
flow_pk = await resolve_collection_flow_id(flow_id, db)

# Create record with FK to PK
questionnaire = AdaptiveQuestionnaire(
    collection_flow_id=flow_pk,  # Uses PK for FK
    ...
)
```

## WHAT WAS FIXED

### Migrations 083/084 (Reversion)
1. ✅ Dropped FK constraints pointing to `flow_id`
2. ✅ Migrated data: `flow_id` values → `id` (PK) values
3. ✅ Recreated FK constraints pointing to `id` (PRIMARY KEY)

### Code Fixes
1. ✅ `resolve_collection_flow_id()` - Query by `flow_id`, return `id`
2. ✅ `commands.py:49` - Use `flow.id` (PK) for FK relationship
3. ✅ `queries.py:54` - Query by `flow.id` (PK) for FK match
4. ✅ `generation.py:215` - Use `flow.id` (PK) for FK relationship

### Verification Results

**FK Constraints (Correct)**:
```sql
SELECT foreign_column_name
FROM information_schema.constraint_column_usage
WHERE table_name = 'adaptive_questionnaires'
AND constraint_name LIKE '%collection_flow_id%';
-- Result: id (PRIMARY KEY) ✅

SELECT foreign_column_name
FROM information_schema.constraint_column_usage
WHERE table_name = 'collection_data_gaps'
AND constraint_name LIKE '%collection_flow_id%';
-- Result: id (PRIMARY KEY) ✅
```

**Data Integrity (Correct)**:
```sql
-- All questionnaires use PK
SELECT COUNT(*) FROM adaptive_questionnaires aq
JOIN collection_flows cf ON aq.collection_flow_id = cf.id;
-- Result: 15 rows ✅

-- All gaps use PK
SELECT COUNT(*) FROM collection_data_gaps g
JOIN collection_flows cf ON g.collection_flow_id = cf.id;
-- Result: 162 rows ✅
```

## FILES AFFECTED

### Migrations
- `083_revert_questionnaire_fk_to_id.py` - Reverts 081, restores FK to PK ✅
- `084_revert_gaps_fk_to_id.py` - Reverts 082, restores FK to PK ✅

### Code (Correct Pattern)
- `data_loader.py:58-114` - Resolver queries by `flow_id`, returns `id` (PK) ✅
- `commands.py:49` - Uses `flow.id` (PK) for FK relationship ✅
- `queries.py:54` - Queries by `flow.id` (PK) for FK match ✅
- `generation.py:215` - Uses `flow.id` (PK) for FK relationship ✅

## DECISION RULES FOR FUTURE AGENTS

### Before Writing FK Data
1. **Always use resolver** to translate business `flow_id` → PK `id`
2. **Never store `flow_id` in FK columns** - only store PK `id`
3. **Query by `flow.id`** when matching FK relationships

### When Creating New FK Relationships
1. **FK definition**: `ForeignKey("collection_flows.id")` (PRIMARY KEY)
2. **Data write**: Use resolver to get PK before writing
3. **Query**: Match on PK for FK joins

### Architecture Principles
- **flow_id**: Business identifier for external APIs (URLs, frontend)
- **id**: PRIMARY KEY for internal FK relationships (database)
- **master_flow_id**: Links to master orchestrator flow

## COMMIT HISTORY

- Oct 1 (4878e1e2e): Incorrect - Changed to `flow.id` without fixing resolver
- Oct 5 (450a88e88): **WRONG** - Changed FK to point to `flow_id` (Migrations 081/082)
- Oct 5 (d8b88f97e): **CORRECT** - Reverted FK to point to `id`, fixed resolver (Migrations 083/084)

## KEY TAKEAWAY ✅

**Foreign keys MUST point to PRIMARY KEYS.** The bug was in the resolver (querying wrong column), not in FK definitions.

The correct fix:
1. ✅ Keep FK constraints on `collection_flows.id` (PK)
2. ✅ Fix resolver to query by `flow_id`, return `id`
3. ✅ Use resolver in all code that writes FK data

**Never retarget FK constraints to non-PK columns!**
