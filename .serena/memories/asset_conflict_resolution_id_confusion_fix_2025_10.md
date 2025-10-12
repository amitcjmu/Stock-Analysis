# Asset Conflict Resolution: id vs flow_id Confusion Fix (Oct 2025)

## Problem Summary

Asset conflict detection UI failed to display conflicts despite backend correctly detecting them. Root cause was confusion between `id` (PK) and `flow_id` (business identifier) when updating phase_state.

## The Bug

**File**: `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py`

**Original Code** (line 234-267):
```python
# ❌ WRONG - Mixed up id (PK) vs flow_id (business identifier)
child_flow = await discovery_repo.get_by_master_flow_id(str(master_flow_id))
child_flow_id = child_flow.id  # Got PK, not flow_id!

# Passed PK to method expecting flow_id
await discovery_repo.set_conflict_resolution_pending(
    child_flow_id,  # ❌ PK value, but method expects flow_id for WHERE clause
    conflict_count=len(conflicts_data),
)
```

**Why It Failed**:
1. `get_by_master_flow_id()` returned flow with `id=f6c00a0c...` (PK) and `flow_id=1fb87128...` (business ID)
2. Code used `child_flow.id` (PK) and passed to repository
3. Repository tried: `WHERE flow_id = 'f6c00a0c...'` (PK value)
4. No matching row found (PK doesn't exist in flow_id column)
5. UPDATE affected 0 rows
6. Transaction committed with no changes
7. Frontend polled and saw empty phase_state

## The Fix

```python
# ✅ CORRECT - Separate PK (for FK) from flow_id (for WHERE)
flow_record = await discovery_repo.get_by_flow_id(str(discovery_flow_id))

flow_pk_id = flow_record.id  # PK for FK constraint in conflict records
# Use flow_id for repository WHERE clause
await discovery_repo.set_conflict_resolution_pending(
    UUID(discovery_flow_id),  # ✅ flow_id business identifier
    conflict_count=len(conflicts_data),
)
```

## Pattern Rules (from Serena Memories)

### Rule 1: id vs flow_id Usage

| Purpose | Use | Example |
|---------|-----|---------|
| FK Constraint | `flow.id` (PK) | `discovery_flow_id=flow.id` |
| WHERE Clause | `flow.flow_id` (business ID) | `WHERE flow_id = '1fb87128...'` |
| API/Frontend | `flow.flow_id` (business ID) | `/flows/1fb87128.../conflicts` |

### Rule 2: Repository Method Parameters

```python
# Repository methods ALWAYS expect flow_id (business identifier)
async def set_conflict_resolution_pending(
    self,
    flow_id: UUID,  # ✅ Business identifier, used in WHERE clause
    ...
):
    stmt = update(DiscoveryFlow).where(
        DiscoveryFlow.flow_id == flow_id,  # ✅ Queries flow_id column
        ...
    )
```

### Rule 3: Discovery Flow Table Structure

```sql
CREATE TABLE migration.discovery_flows (
    id UUID PRIMARY KEY,              -- Internal PK, for FK relationships
    flow_id UUID NOT NULL UNIQUE,     -- Business identifier, for queries/WHERE
    master_flow_id UUID,               -- References another flow's flow_id
    ...
);
```

**Key Insight**: `flow_id` and `master_flow_id` often have the SAME value (flow is both master and child).

## Additional Bug Fixed by QA Agent

**File**: `backend/app/api/v1/endpoints/asset_conflicts.py`

**Original Code** (lines 73, 98):
```python
# ❌ WRONG - Used id in WHERE, flow_id for FK
stmt = select(DiscoveryFlow).where(
    DiscoveryFlow.id == flow_id,  # ❌ id column, but parameter is flow_id!
)
conflicts = await db.execute(
    select(AssetConflictResolution).where(
        AssetConflictResolution.discovery_flow_id == flow.flow_id  # ❌ FK uses id, not flow_id
    )
)
```

**Fixed Code**:
```python
# ✅ CORRECT
stmt = select(DiscoveryFlow).where(
    DiscoveryFlow.flow_id == flow_id,  # ✅ Match parameter name with column
)
conflicts = await db.execute(
    select(AssetConflictResolution).where(
        AssetConflictResolution.discovery_flow_id == flow.id  # ✅ FK references PK
    )
)
```

## Testing Evidence

### Before Fix
```sql
-- Backend logs showed success
⏸️ Discovery flow f6c00a0c... paused for conflict resolution

-- But database was unchanged
SELECT phase_state FROM migration.discovery_flows
WHERE flow_id = '1fb87128...';
-- Result: {} (empty)
```

### After Fix
```sql
-- Backend logs
⏸️ Discovery flow 1fb87128... paused for conflict resolution

-- Database correctly updated
SELECT phase_state FROM migration.discovery_flows
WHERE flow_id = '1fb87128...';
-- Result: {"conflict_resolution_pending": true, "conflict_metadata": {...}}
```

## Related Patterns (ADR-012)

This fix also correctly separates:
- **status** (lifecycle): "discovery" (unchanged - flow still active)
- **phase_state** (operational): `{"conflict_resolution_pending": true}`

Per ADR-012:
- Status indicates lifecycle state (initialized, running, completed)
- Phase state indicates operational flags (paused for conflicts, awaiting input, etc.)

## Files Modified

1. `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py` (lines 228-269)
   - Changed from `get_by_master_flow_id()` to `get_by_flow_id()`
   - Separated PK retrieval from flow_id usage
   - Fixed parameter passed to `set_conflict_resolution_pending()`

2. `backend/app/api/v1/endpoints/asset_conflicts.py` (lines 73, 98)
   - Fixed WHERE clause to use `flow_id` column
   - Fixed FK query to use `id` (PK)

3. `backend/app/repositories/discovery_flow_repository/commands/flow_status_management.py` (lines 164, 208)
   - Removed premature commits (transaction boundary fix)
   - Repository methods now only flush, caller commits

4. `backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_executors.py` (line 214)
   - Added commit at phase executor level (proper transaction boundary)

## Prevention Checklist

Before writing code that accesses discovery_flows:

- [ ] Check if you need PK (`flow.id`) or business ID (`flow.flow_id`)
- [ ] FK constraints use `flow.id` (PK)
- [ ] WHERE clauses use `flow.flow_id` (business identifier)
- [ ] API parameters are `flow_id` (business identifier)
- [ ] Don't assume `flow_id == master_flow_id` (they're often equal but conceptually different)
- [ ] Update `phase_state` for operational flags, not `status`
- [ ] Repository methods flush but don't commit (caller commits)

## Related Memories

- `OBSOLETE-collection-flow-id-vs-flow-id-confusion-root-cause` - Same pattern for collection_flows
- `adr-012-collection-flow-status-remediation` - Status vs phase separation
- `discovery_flow_id_coordination_patterns_2025_09` - Flow ID coordination patterns
