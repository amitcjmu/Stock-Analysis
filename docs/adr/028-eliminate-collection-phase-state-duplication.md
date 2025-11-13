# ADR-028: Eliminate Collection Flow Phase State Duplication

## Status
Accepted - 2025-10-18

## Context

### Problem: Duplicated Phase Tracking

Collection flows currently maintain phase state in **two separate locations**:

1. **Child Flow Table** (`collection_flows.phase_state` JSONB):
   ```json
   {
       "current_phase": "asset_selection",
       "phase_history": [{
           "phase": "asset_selection",
           "status": "active",
           "started_at": "2025-10-14T17:54:02.698447+00:00",
           "metadata": {...}
       }],
       "phase_metadata": {...}
   }
   ```

2. **Master Flow Table** (`crewai_flow_state_extensions.phase_transitions` JSONB):
   ```json
   [{
       "phase": "asset_selection",
       "status": "active",
       "timestamp": "2025-10-14T17:54:02.698447+00:00",
       "metadata": {...}
   }]
   ```

### Consequences of Duplication

1. **Data Inconsistency** (Bug #648)
   - `collection_flows.current_phase` = "questionnaire_generation"
   - `collection_flows.phase_state.current_phase` = "asset_selection"
   - Two different values for same flow!

2. **Architectural Violations**
   - Violates ADR-006 (Master Flow Orchestrator as single source of truth)
   - Violates DRY (Don't Repeat Yourself) principle
   - Confusing for developers: Which field is authoritative?

3. **Maintenance Burden**
   - Must synchronize multiple fields
   - Risk of divergence on every update
   - Wasted storage

4. **Discovery/Assessment Flows Don't Have This Problem**
   - Discovery: Uses simple `current_phase` column only
   - Assessment: Similar pattern to Discovery
   - Collection: Unique in having dual tracking

### Root Cause

Collection flow was built **before ADR-006** established Master Flow Orchestrator pattern. The `phase_state` JSONB was added for rich tracking, but Master Flow already provides this capability.

**This is architectural debt**, not a necessary feature.

## Decision

### Eliminate `phase_state` from Collection Flows

**Use Master Flow's tracking as single source of truth:**

```python
# ❌ OLD: Duplicate tracking in child flow
collection_flow.phase_state = {
    "current_phase": "asset_selection",
    "phase_history": [...],      # ← Duplicate!
    "phase_metadata": {...}
}
collection_flow.current_phase = "asset_selection"  # ← Diverges!

# ✅ NEW: Single source in master flow
master_flow.add_phase_transition(
    phase="asset_selection",
    status="active",
    metadata={
        "source": "collection_overview",
        "requires_user_selection": True
    }
)
collection_flow.current_phase = master_flow.get_current_phase()  # Synchronized
```

### Architecture After Change

```
┌─────────────────────────────────────┐
│  Master Flow (Single Source)       │
│  crewai_flow_state_extensions      │
├─────────────────────────────────────┤
│  - phase_transitions (JSONB array) │ ← All phase history
│  - error_history (JSONB array)     │ ← All error tracking
│  - phase_execution_times (JSONB)   │ ← All timing data
│  - flow_persistence_data (JSONB)   │ ← All state data
└─────────────────────────────────────┘
           ↓ Synchronizes
┌─────────────────────────────────────┐
│  Collection Flow (Child)           │
│  collection_flows                  │
├─────────────────────────────────────┤
│  - current_phase (String column)   │ ← Derived from master
│  - phase_state (REMOVED)           │ ← ELIMINATED
└─────────────────────────────────────┘
```

### What to Keep

1. **`current_phase` column** - For fast SQL queries and indexing
   - Updated automatically from master flow
   - Read-only from application perspective
   - Performance optimization, not source of truth

2. **Master Flow tracking** - Single source of truth
   - `phase_transitions` - Phase history
   - `error_history` - Error tracking
   - `phase_execution_times` - Performance metrics
   - `flow_metadata` - Phase-specific metadata

### What to Remove

1. **`collection_flows.phase_state` JSONB** - Architectural debt
   - Duplicates master flow's `phase_transitions`
   - Causes synchronization bugs
   - No unique value

## Implementation

### Phase 1: Data Migration (Alembic)

**File**: `backend/alembic/versions/093_eliminate_collection_phase_state.py`

```python
"""Eliminate collection flow phase_state duplication (ADR-028)

Revision ID: 093
Revises: 092
Create Date: 2025-10-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '093'
down_revision = '092'

def upgrade():
    # Step 1: Migrate existing phase_state data to master flow
    op.execute("""
        -- Copy phase_history to master flow's phase_transitions
        UPDATE migration.crewai_flow_state_extensions mf
        SET phase_transitions = COALESCE(
            (
                SELECT cf.phase_state->'phase_history'
                FROM migration.collection_flows cf
                WHERE cf.master_flow_id = mf.flow_id
                  AND cf.phase_state ? 'phase_history'
            ),
            mf.phase_transitions
        )
        WHERE mf.flow_type = 'collection'
          AND EXISTS (
              SELECT 1 FROM migration.collection_flows cf
              WHERE cf.master_flow_id = mf.flow_id
          );
    """)

    # Step 2: Synchronize current_phase from phase_state
    op.execute("""
        -- Ensure current_phase matches phase_state.current_phase
        UPDATE migration.collection_flows
        SET current_phase = phase_state->>'current_phase'
        WHERE phase_state ? 'current_phase'
          AND current_phase IS DISTINCT FROM phase_state->>'current_phase';
    """)

    # Step 3: Remove phase_state column
    op.drop_column('collection_flows', 'phase_state', schema='migration')

def downgrade():
    # Recreate column if needed (not recommended)
    op.add_column(
        'collection_flows',
        sa.Column(
            'phase_state',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default='{}',
            nullable=False
        ),
        schema='migration'
    )
```

### Phase 2: Code Updates

#### Update Phase Transition Method

**File**: `backend/app/services/collection_flow/state_management/commands.py`

```python
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

async def transition_phase(
    db: AsyncSession,
    collection_flow: CollectionFlow,
    new_phase: CollectionPhase,
    phase_metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Transition collection flow to new phase.

    Per ADR-028: Uses master flow as single source of truth.
    """
    # Get master flow
    master_flow = await db.get(
        CrewAIFlowStateExtensions,
        collection_flow.master_flow_id
    )

    if not master_flow:
        raise ValueError(
            f"Master flow {collection_flow.master_flow_id} not found. "
            "Violates ADR-006."
        )

    # Complete previous phase in master flow
    if master_flow.phase_transitions:
        last_transition = master_flow.phase_transitions[-1]
        if last_transition.get("status") == "active":
            last_transition["status"] = "completed"
            last_transition["completed_at"] = datetime.now().isoformat()

    # Add new phase transition to master flow (single source of truth)
    master_flow.add_phase_transition(
        phase=new_phase.value,
        status="active",
        metadata=phase_metadata or {}
    )

    # Synchronize current_phase column for query performance
    collection_flow.current_phase = new_phase.value

    await db.commit()
```

#### Update Phase Query Methods

**File**: `backend/app/services/collection_flow/state_management/queries.py`

```python
async def get_current_phase(
    db: AsyncSession,
    flow_id: UUID
) -> Optional[str]:
    """
    Get current phase from master flow.

    Per ADR-028: Master flow is single source of truth.
    """
    collection_flow = await get_collection_flow(db, flow_id)

    # Fast path: Use synchronized column
    if collection_flow.current_phase:
        return collection_flow.current_phase

    # Fallback: Query master flow
    if collection_flow.master_flow_id:
        master_flow = await db.get(
            CrewAIFlowStateExtensions,
            collection_flow.master_flow_id
        )
        return master_flow.get_current_phase() if master_flow else None

    return None

async def get_phase_history(
    db: AsyncSession,
    flow_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get phase history from master flow.

    Per ADR-028: Master flow is single source of truth.
    """
    collection_flow = await get_collection_flow(db, flow_id)

    if not collection_flow.master_flow_id:
        return []

    master_flow = await db.get(
        CrewAIFlowStateExtensions,
        collection_flow.master_flow_id
    )

    return master_flow.phase_transitions if master_flow else []
```

### Phase 3: Remove All phase_state References

**Files to Update**:
1. `backend/app/services/collection_flow/state_management/commands.py`
2. `backend/app/services/collection_flow/state_management/completion.py`
3. `backend/app/services/integration/discovery_collection_bridge.py`
4. `backend/app/services/collection_flow/audit_logging/utils.py`

**Pattern**:
```python
# ❌ REMOVE: Direct phase_state access
flow.phase_state["current_phase"] = "new_phase"
flow.phase_state["phase_history"].append(...)

# ✅ REPLACE: Use master flow methods
master_flow.add_phase_transition(
    phase="new_phase",
    status="active",
    metadata={...}
)
flow.current_phase = master_flow.get_current_phase()
```

## Consequences

### Positive

1. **Single Source of Truth**
   - No more synchronization bugs (fixes Bug #648)
   - Clear: Master flow is authoritative
   - Impossible for data to diverge

2. **Consistency with Other Flows**
   - Discovery: Uses master flow tracking
   - Assessment: Uses master flow tracking
   - Collection: Now aligned with both

3. **Simplified Code**
   - Less code to maintain
   - Fewer fields to update
   - Clearer logic

4. **Better Storage Efficiency**
   - Remove duplicate JSONB column
   - Reduce table size

5. **ADR Compliance**
   - Aligns with ADR-006 (Master Flow Orchestrator)
   - Aligns with ADR-027 (Universal FlowTypeConfig)
   - Establishes pattern for future flows

### Negative

1. **Migration Effort**
   - Must update all phase_state access code
   - Risk if migration script fails
   - Testing required

2. **Query Performance**
   - Joins to master flow table for history
   - Mitigated by keeping `current_phase` column

3. **Breaking Change**
   - API responses may change if exposing phase_state
   - Frontend may read phase_state

### Mitigation

1. **Comprehensive Migration**
   - Test migration on staging first
   - Verify all data copied correctly
   - Rollback plan ready

2. **Performance**
   - Keep `current_phase` column for fast queries
   - Use eager loading for master flow joins
   - Index `master_flow_id` foreign key

3. **API Compatibility**
   - Check if API exposes `phase_state` directly
   - Update serializers to use master flow
   - Maintain backward-compatible response structure

## Testing

### Migration Testing

```bash
# Test migration on staging
docker exec migration_backend alembic upgrade 093

# Verify data integrity
docker exec migration_postgres psql -U postgres -d migration_db -c "
SELECT
  cf.flow_id,
  cf.current_phase,
  mf.phase_transitions
FROM migration.collection_flows cf
JOIN migration.crewai_flow_state_extensions mf ON mf.flow_id = cf.master_flow_id
LIMIT 5;
"
```

### Code Testing

```python
# Test phase transition
async def test_phase_transition_uses_master_flow():
    # Create collection flow with master flow
    master_flow = await create_master_flow(...)
    collection_flow = await create_collection_flow(
        master_flow_id=master_flow.flow_id
    )

    # Transition phase
    await transition_phase(db, collection_flow, CollectionPhase.GAP_ANALYSIS)

    # Verify master flow updated
    assert master_flow.phase_transitions[-1]["phase"] == "gap_analysis"

    # Verify child flow synchronized
    assert collection_flow.current_phase == "gap_analysis"

    # Verify no phase_state column exists
    assert not hasattr(collection_flow, 'phase_state')
```

## References

- **ADR-006**: Master Flow Orchestrator
- **ADR-027**: Universal FlowTypeConfig Pattern
- **Bug #648**: Phase state inconsistency in collection_flows
- **DRY Principle**: Don't Repeat Yourself
- **Single Source of Truth**: Database design best practice

## Related Issues

- Fixes: Bug #648 (Phase state inconsistency)
- Relates to: Bug #646 (Missing master flow - ensures master flow exists)
- Relates to: Bug #649 (UI displays wrong phase - uses correct source)

## Approval

- [x] Architecture Review: Eliminates architectural debt
- [x] Tech Lead: Aligns with ADR-006 and ADR-027
- [ ] QA Lead: Migration and testing strategy review needed
- [ ] Product Owner: No user-facing impact expected

## Timeline

- ADR Approval: 2025-10-18
- Migration Created: 2025-10-18
- Code Updated: 2025-10-18
- Testing Complete: 2025-10-18
- Deployment: 2025-10-18 (with Bug #648 fix)

## Success Metrics

1. ✅ Zero collection flows with `phase_state` column
2. ✅ All phase transitions in master flow `phase_transitions`
3. ✅ No synchronization bugs between tables
4. ✅ `current_phase` column matches master flow current phase
5. ✅ All tests passing after migration
