# Collection Flow: id vs flow_id Confusion - Root Cause Analysis

## THE PROBLEM

Agents keep switching between `flow.id` and `flow.flow_id` causing recurring bugs. This has happened multiple times (Oct 1, Oct 5, etc.).

## ROOT CAUSE: SCHEMA DESIGN FLAW

The `collection_flows` table has **TWO different UUID columns** with **DIFFERENT values**:

```sql
SELECT id, flow_id FROM migration.collection_flows LIMIT 1;
-- id:      95ea124e-49e6-45fc-a572-5f6202f3408a  (Internal PK)
-- flow_id: f54241f6-4ed5-40fa-b85f-216ceda28f38  (Business identifier)
```

### FK Constraint is WRONG

```sql
-- CURRENT (INCORRECT):
FOREIGN KEY (collection_flow_id) REFERENCES collection_flows(id)

-- SHOULD BE:
FOREIGN KEY (collection_flow_id) REFERENCES collection_flows(flow_id)
```

### Why This Causes Issues

1. **Frontend/API uses `flow_id`**: URLs are `/flows/f54241f6/...`
2. **Backend looks up by `flow_id`**: `flow = await get_flow(flow_id="f54241f6")`
3. **Oct 1 fix used `flow.id`**: `collection_flow_id=flow.id` → Stores `95ea124e`
4. **Frontend can't find it**: Queries for `flow_id=f54241f6` but questionnaire has `95ea124e`

## EVIDENCE FROM QA TEST

- Questionnaire created for flow `f54241f6`
- Database shows `collection_flow_id = 95ea124e` (wrong flow!)
- FK constraint satisfied (points to valid `id`)
- Frontend polling failed (wrong `flow_id`)

## WHY OCT 1 MEMORY WAS MISLEADING

The Oct 1 memory said:
> "Use `flow.id` (PK) not `flow.flow_id` (business UUID)"

This was technically correct for **satisfying the FK constraint**, but:
- ✅ FK constraint satisfied
- ❌ Application logic broken (frontend uses `flow_id`)
- ❌ Data corruption (questionnaires linked to wrong flow)

## WHY OCT 5 FIX WILL FAIL

Changing to `flow.flow_id` will:
- ✅ Fix application logic (frontend can find questionnaires)
- ❌ **VIOLATE FK constraint** (f54241f6 doesn't exist in `id` column)
- ❌ Cause runtime errors on INSERT

## THE CORRECT SOLUTION ✅ IMPLEMENTED (Oct 5, 2025)

### Migration 081 Applied Successfully

**File**: `backend/alembic/versions/081_fix_questionnaire_collection_flow_fk.py`

**What Was Fixed**:
1. ✅ Dropped incorrect FK constraint (was pointing to `collection_flows.id`)
2. ✅ Migrated all 15 existing questionnaires: `collection_flow_id` updated from `id` → `flow_id`
3. ✅ Created correct FK constraint pointing to `collection_flows.flow_id`

**Verification Results**:
```sql
-- All questionnaires now correctly reference flow_id:
SELECT
  aq.collection_flow_id as current_ref,
  cf.flow_id,
  cf.id,
  CASE WHEN aq.collection_flow_id = cf.flow_id THEN '✅ CORRECT'
       ELSE '❌ WRONG' END as status
FROM migration.adaptive_questionnaires aq
JOIN migration.collection_flows cf ON aq.collection_flow_id = cf.flow_id;
-- Result: ALL 15 rows show ✅ CORRECT

-- FK constraint now points to flow_id:
SELECT ccu.column_name
FROM information_schema.constraint_column_usage ccu
WHERE ccu.constraint_name = 'fk_adaptive_questionnaires_collection_flow_id_collection_flows';
-- Result: flow_id (was: id before migration)
```

### Application Code Pattern (Now Enforced by FK)

```python
# ✅ ALWAYS use flow.flow_id - FK constraint enforces this
collection_flow_id=flow.flow_id  # Correct - works with FK
collection_flow_id=flow.id        # ❌ WRONG - will VIOLATE FK constraint
```

### Oct 1 Memory is Now Obsolete

The Oct 1 memory saying "use flow.id for FK" is **no longer valid** after migration 081. The FK constraint has been fixed to align with application logic.

## DECISION RULES FOR FUTURE AGENTS

### Before Making Changes

1. **Check FK constraint target**:
   ```sql
   SELECT ccu.column_name
   FROM information_schema.constraint_column_usage ccu
   WHERE ccu.constraint_name = 'fk_...'
   ```

2. **Check what application uses**:
   ```bash
   # URLs in frontend
   grep -r "flows/" src/

   # Queries in backend
   grep -r "flow_id" backend/
   ```

3. **If FK target != application field**: Schema is wrong, needs migration

### After Migration

- ✅ Use `flow.flow_id` for `collection_flow_id` (matches FK and application)
- ✅ FK points to `flow_id` column
- ✅ Frontend and backend use same identifier

## TESTING VERIFICATION

After migration:
```python
# Test 1: FK satisfied
questionnaire = AdaptiveQuestionnaire(
    collection_flow_id=flow.flow_id  # Should work
)

# Test 2: Frontend can find it
response = await client.get(f"/flows/{flow_id}/questionnaires")
# Should return the questionnaire
```

## FILES AFFECTED

- `backend/app/api/v1/endpoints/collection_crud_questionnaires/commands.py:49`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py:53`
- `backend/app/api/v1/endpoints/collection_agent_questionnaires/generation.py:215`

## COMMIT HISTORY

- Oct 1 (4878e1e2e): Changed to `flow.id` - satisfied FK, broke application
- Oct 5 (7c887854c): Changed to `flow.flow_id` - fixed application, will break FK
- **Needed**: Migration to fix FK constraint, then keep `flow.flow_id`

## KEY TAKEAWAY

**The FK constraint is defined incorrectly in the database schema.** No amount of code changes will fix this - it requires an Alembic migration to update the constraint.

Both previous fixes were "correct" for their perspective (FK vs application), but neither can work until the schema is fixed.
