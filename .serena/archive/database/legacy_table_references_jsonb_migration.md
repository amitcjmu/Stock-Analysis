# Handling Legacy Table References During Architecture Migration

## Problem
After migrating from multi-table to JSONB architecture, code still references non-existent tables:
```
ERROR: Unconsumed column names: ready_for_planning
sqlalchemy.exc.NoSuchTableError: SixRDecision
```

## Root Cause
Repository methods contain stale database operations from old architecture:
- Old: Separate `six_r_decisions` table with `ready_for_planning` column
- New: Data stored in `assessment_flows.phase_results` JSONB field

## Solution
Audit and fix repository methods referencing deprecated tables.

## Implementation

### Step 1: Identify Stale References
```python
# ❌ Old code - references non-existent table
await self.db.execute(
    update(SixRDecision)  # ← Table doesn't exist anymore
    .where(
        and_(
            SixRDecision.assessment_flow_id == flow_id,
            SixRDecision.application_id.in_(app_ids),
        )
    )
    .values(ready_for_planning=True)  # ← Column doesn't exist
)
```

### Step 2: Comment Out with Explanation
```python
# backend/app/repositories/assessment_flow_repository/commands/decision_commands.py

async def mark_apps_ready_for_planning(self, flow_id: str, app_ids: List[str]):
    """Mark applications as ready for planning flow"""

    # NOTE: SixRDecision table not used in new assessment flow architecture
    # 6R decisions are stored in phase_results JSONB, not separate table
    # Commenting out legacy code that referenced non-existent table:
    # await self.db.execute(
    #     update(SixRDecision)
    #     .where(...)
    #     .values(ready_for_planning=True)
    # )

    # Keep only valid operations for new architecture
    await self.db.execute(
        update(AssessmentFlow)
        .where(
            and_(
                AssessmentFlow.id == flow_id,
                AssessmentFlow.client_account_id == self.client_account_id,
            )
        )
        .values(apps_ready_for_planning=app_ids)  # ✅ This column exists
    )
    await self.db.commit()
```

## Common Migration Patterns

### Pattern 1: Table Consolidation
```
Old: Data split across multiple tables
  - flows table
  - decisions table
  - metadata table

New: Single table with JSONB columns
  - flows table (with phase_results JSONB, metadata JSONB)
```

### Pattern 2: Column Name Changes
```python
# Old
SixRDecision.ready_for_planning = True

# New
AssessmentFlow.apps_ready_for_planning = [app_ids]
```

### Pattern 3: Data Location Changes
```python
# Old: Separate table query
decisions = await db.execute(
    select(SixRDecision).where(...)
)

# New: JSONB field extraction
flow = await db.execute(
    select(AssessmentFlow.phase_results).where(...)
)
decisions = flow.phase_results.get('recommendation_generation', {})
```

## Audit Checklist

When migrating to JSONB architecture:

1. ✅ Search for old table model imports:
   ```bash
   grep -r "from.*SixRDecision" backend/
   ```

2. ✅ Find stale table operations:
   ```bash
   grep -r "update(SixRDecision)" backend/
   grep -r "insert(SixRDecision)" backend/
   ```

3. ✅ Check for column references:
   ```bash
   grep -r "ready_for_planning" backend/
   ```

4. ✅ Verify repository methods still in use:
   ```bash
   grep -r "mark_apps_ready_for_planning" backend/
   ```

5. ✅ Test all CRUD operations with actual data

## Best Practices

✅ Add explanatory comments when removing old code
✅ Keep valid operations, remove only stale ones
✅ Update method documentation to reflect new architecture
✅ Test all repository methods after migration
✅ Use database migrations to drop old tables (don't leave orphans)

## Anti-Patterns

❌ Silently deleting code without comments
❌ Leaving old imports in place
❌ Keeping stale table models in codebase
❌ Not testing repository methods after changes

## Related Migrations

- Assessment Flow: Multi-table → JSONB (ADR-012)
- 6R Analysis: Deprecated separate flow → Integrated with Assessment
- Discovery Flow: Separate tables → phase_results JSONB

## Files Modified
- `backend/app/repositories/assessment_flow_repository/commands/decision_commands.py:75-105`
- `backend/app/models/assessment_flow.py` (removed SixRDecision model)
