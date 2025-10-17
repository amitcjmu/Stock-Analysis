# Collection to Assessment Transition - Foreign Key Fix

## Problem: FK Violation on Collection Flow Linkage

**Error**:
```
ForeignKeyViolationError: insert or update on table "crewai_flow_state_extensions"
violates foreign key constraint "fk_crewai_flow_ext_collection_flow_id"
DETAIL: Key (collection_flow_id)=(2799fbfc-4ee7-4325-b906-51852c0af67c)
is not present in table "collection_flows"
```

**Root Cause**: Code passed master flow UUID instead of primary key

The FK constraint references the PRIMARY KEY:
```sql
FOREIGN KEY (collection_flow_id) REFERENCES collection_flows(id)
                                                           ^^^^ Primary key
```

But code was passing `collection_flows.flow_id` (master flow UUID) instead of `collection_flows.id` (PK).

## Solution: Pass Primary Key Not Master Flow UUID

**File**: `backend/app/services/collection_transition_service.py:221-228`

**Before** (❌ Wrong):
```python
assessment_flow_id = await assessment_repo.create_assessment_flow(
    engagement_id=str(self.context.engagement_id),
    selected_application_ids=selected_app_ids,
    created_by=str(self.context.user_id) if self.context.user_id else None,
    collection_flow_id=str(collection_flow_id),  # ❌ Master flow UUID
)
```

**After** (✅ Correct):
```python
assessment_flow_id = await assessment_repo.create_assessment_flow(
    engagement_id=str(self.context.engagement_id),
    selected_application_ids=selected_app_ids,
    created_by=str(self.context.user_id) if self.context.user_id else None,
    collection_flow_id=str(collection_flow.id),  # ✅ Primary key
)
```

## Key Insight: Two-ID Pattern in Flow Tables

**Master Flow Orchestrator Pattern**: Each child flow table has TWO UUID columns:
1. **`id`** (Primary Key) - Child flow's own identity
2. **`flow_id`** (Foreign Key to MFO) - Master flow UUID for coordination

**When to Use Each**:
- **FK constraints between child tables**: Use `id` (primary key)
- **MFO registration/coordination**: Use `flow_id` (master flow UUID)
- **Cross-flow references**: Use `id` to maintain referential integrity

## Verification Query

Check the two IDs in database:
```sql
SELECT
  id AS collection_flow_pk,        -- Primary key
  flow_id AS master_flow_uuid      -- Master flow reference
FROM migration.collection_flows
WHERE flow_id = '2799fbfc-4ee7-4325-b906-51852c0af67c';

-- Result:
-- collection_flow_pk: 977f56be-287a-4b21-9662-89d8e47784e3 ✅ Use for FK
-- master_flow_uuid:   2799fbfc-4ee7-4325-b906-51852c0af67c ❌ Not for FK
```

## Usage Pattern

When creating cross-flow references (e.g., collection → assessment):
1. Query to get source flow object: `collection_flow = await get_collection_flow(flow_id)`
2. Pass PRIMARY KEY to FK fields: `collection_flow_id=str(collection_flow.id)`
3. Pass MASTER UUID to MFO: `await create_master_flow(..., collection_flow_id=str(collection_flow.id))`

**Anti-Pattern**: Never pass method parameters directly to FK fields without first fetching the entity and using its `id` attribute.
