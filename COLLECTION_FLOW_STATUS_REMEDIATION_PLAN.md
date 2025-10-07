# Collection Flow Status Remediation Plan

## Executive Summary

**Issue**: `CollectionFlowStatus` enum violates ADR-012 by mixing lifecycle states with operational phases.

**Root Cause**: Enum was created before ADR-012 (Flow Status Management Separation) was written.

**Impact**: 34 backend files, 1 frontend file affected. 2 critical bugs in production.

**Timeline**: 2-3 hours for complete remediation (development environment).

---

## Part 1: Enum Definition Changes

### File: `backend/app/models/collection_flow/schemas.py`

**Current (WRONG)**:
```python
class CollectionFlowStatus(str, Enum):
    """Collection Flow status values"""
    INITIALIZED = "initialized"
    ASSET_SELECTION = "asset_selection"      # ❌ PHASE - REMOVE
    GAP_ANALYSIS = "gap_analysis"            # ❌ PHASE - REMOVE
    MANUAL_COLLECTION = "manual_collection"  # ❌ PHASE - REMOVE
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**Required (CORRECT)**:
```python
class CollectionFlowStatus(str, Enum):
    """Collection Flow status values - lifecycle states only per ADR-012"""
    INITIALIZED = "initialized"
    RUNNING = "running"                      # ✅ ADD - Active execution
    PAUSED = "paused"                        # ✅ ADD - User action needed
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**Reference Implementation**: `backend/app/models/assessment_flow/enums_and_exceptions.py` (AssessmentFlowStatus)

---

## Part 2: Critical Bugs (Fix First)

### Bug #1: Flow Initialization Sets Wrong Status
**File**: `backend/app/services/collection_flow/state_management/commands.py:100`

**Current**:
```python
collection_flow = CollectionFlow(
    ...
    status=CollectionFlowStatus.GAP_ANALYSIS,  # ❌ WRONG - phase value
    current_phase=CollectionPhase.GAP_ANALYSIS.value,
)
```

**Fix**:
```python
collection_flow = CollectionFlow(
    ...
    status=CollectionFlowStatus.INITIALIZED,  # ✅ CORRECT - lifecycle state
    current_phase=CollectionPhase.GAP_ANALYSIS.value,
)
```

### Bug #2: Auto-Progression Service Broken
**File**: `backend/app/services/collection_phase_progression_service.py:49`

**Current**:
```python
stmt = select(CollectionFlow).where(
    CollectionFlow.current_phase == CollectionPhase.ASSET_SELECTION.value,  # ✅ CORRECT
    CollectionFlow.status == CollectionFlowStatus.ASSET_SELECTION.value,    # ❌ WRONG
)
```

**Fix**:
```python
stmt = select(CollectionFlow).where(
    CollectionFlow.current_phase == CollectionPhase.ASSET_SELECTION.value,
    CollectionFlow.status == CollectionFlowStatus.RUNNING,  # ✅ CORRECT
)
```

---

## Part 3: Status Assignment Violations (34 locations)

### Direct Assignment: `status = CollectionFlowStatus.PHASE_VALUE`

#### Repository Layer

**File**: `backend/app/repositories/collection_flow_repository.py`
- Line 50: `CollectionFlowStatus.ASSET_SELECTION` (active flows query)
- Line 51: `CollectionFlowStatus.GAP_ANALYSIS` (active flows query)
- Line 52: `CollectionFlowStatus.MANUAL_COLLECTION` (active flows query)
- Line 113: `status=CollectionFlowStatus.INITIALIZED` (✅ OK - keep)
- Line 154: `status=CollectionFlowStatus.GAP_ANALYSIS` (get_flows_with_gaps)

**Fix**: Change active_statuses to use `RUNNING`:
```python
active_statuses = [
    CollectionFlowStatus.INITIALIZED,
    CollectionFlowStatus.RUNNING,  # ✅ Single running state
    CollectionFlowStatus.PAUSED,
]
```

#### API Endpoints - Bulk Import

**File**: `backend/app/api/v1/endpoints/collection_bulk_import.py`
- Line 55: `CollectionFlowStatus.ASSET_SELECTION.value` (allowed_statuses)
- Line 56: `CollectionFlowStatus.GAP_ANALYSIS.value` (allowed_statuses)
- Line 57: `CollectionFlowStatus.MANUAL_COLLECTION.value` (allowed_statuses)
- Line 162: `collection_flow.status = CollectionFlowStatus.ASSET_SELECTION.value` (update after import)
- Line 166: `collection_flow.status = CollectionFlowStatus.GAP_ANALYSIS.value` (update after import)

**Fix**:
```python
allowed_statuses = [
    CollectionFlowStatus.INITIALIZED.value,
    CollectionFlowStatus.RUNNING.value,
    CollectionFlowStatus.PAUSED.value,
]

# After successful import
if collection_flow.status == CollectionFlowStatus.INITIALIZED.value:
    collection_flow.status = CollectionFlowStatus.RUNNING.value
```

#### API Endpoints - CRUD Queries

**File**: `backend/app/api/v1/endpoints/collection_crud_queries/lists.py`
- Line 55: `CollectionFlowStatus.ASSET_SELECTION.value` (active flow check)
- Line 56: `CollectionFlowStatus.GAP_ANALYSIS.value` (active flow check)
- Line 57: `CollectionFlowStatus.MANUAL_COLLECTION.value` (active flow check)

**Fix**: Use `RUNNING` and `PAUSED` instead.

#### API Endpoints - Validators

**File**: `backend/app/api/v1/endpoints/collection_validators.py`
- Line 223: `CollectionFlowStatus.ASSET_SELECTION.value` (active_statuses)
- Line 224: `CollectionFlowStatus.GAP_ANALYSIS.value` (active_statuses)

**Fix**: Use `RUNNING` and `PAUSED` instead.

#### API Endpoints - Create Commands

**File**: `backend/app/api/v1/endpoints/collection_crud_create_commands.py`
- Line 118: `status=CollectionFlowStatus.INITIALIZED.value` (✅ OK - keep)
- Line 285: `CollectionFlowStatus.ASSET_SELECTION.value` (active flow check)
- Line 286: `CollectionFlowStatus.GAP_ANALYSIS.value` (active flow check)
- Line 287: `CollectionFlowStatus.MANUAL_COLLECTION.value` (active flow check)
- Line 398: `status=CollectionFlowStatus.ASSET_SELECTION.value` (new flow creation)

**Fix**:
```python
# Line 118: OK
status=CollectionFlowStatus.INITIALIZED.value

# Lines 285-287: active flow check
CollectionFlowStatus.INITIALIZED.value,
CollectionFlowStatus.RUNNING.value,
CollectionFlowStatus.PAUSED.value,

# Line 398: new flow creation
status=CollectionFlowStatus.INITIALIZED.value  # Start as INITIALIZED
```

#### API Endpoints - Execution Management

**File**: `backend/app/api/v1/endpoints/collection_crud_execution/management.py`
- Line 135: `collection_flow.status = CollectionFlowStatus.ASSET_SELECTION` (redirect to asset_selection)

**Fix**:
```python
collection_flow.status = CollectionFlowStatus.PAUSED  # Waiting for user input
```

#### API Endpoints - Status Utils

**File**: `backend/app/api/v1/endpoints/collection_status_utils.py`
- Lines 52-54: `phase_status_mapping` dictionary (entire function is wrong)
- Lines 56-57: More phase-to-status mappings

**Fix**: Replace function logic:
```python
def determine_next_phase_status(next_phase: str, current_status: str = None) -> str:
    """Determine the appropriate flow status based on next phase.

    Per ADR-012: Status reflects lifecycle, not phase.
    """
    # If already running, stay running unless at finalization
    if next_phase == "finalization":
        return CollectionFlowStatus.COMPLETED.value

    # If initialized and moving to first active phase
    if current_status == CollectionFlowStatus.INITIALIZED.value:
        # Check if phase requires user input
        if next_phase in ["asset_selection"]:
            return CollectionFlowStatus.PAUSED.value
        return CollectionFlowStatus.RUNNING.value

    # Otherwise preserve current status (RUNNING/PAUSED)
    return current_status or CollectionFlowStatus.RUNNING.value
```

#### API Endpoints - Flow Lifecycle

**File**: `backend/app/api/v1/endpoints/collection_flow_lifecycle.py`
- Lines 49-51: Active statuses (4 occurrences in different methods)
- Lines 128-130: Active statuses
- Lines 272-274: Active statuses
- Lines 361-363: Active statuses

**Fix**: Replace all 4 occurrences:
```python
active_statuses = [
    CollectionFlowStatus.INITIALIZED.value,
    CollectionFlowStatus.RUNNING.value,
    CollectionFlowStatus.PAUSED.value,
]
```

#### CrewAI Services - Initialization Handler

**File**: `backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/initialization_handler.py`
- Line 93: `status=CollectionFlowStatus.ASSET_SELECTION.value` (database update)

**Fix**:
```python
status=CollectionFlowStatus.RUNNING.value,  # Flow is now actively running
```

#### CrewAI Services - Cleanup Service (Base)

**File**: `backend/app/services/crewai_flows/collection_flow_cleanup_service/base.py`
- Lines 70-72: Stale flow check (3 phase values)

**Fix**:
```python
if (
    flow.status in [
        CollectionFlowStatus.INITIALIZED.value,
        CollectionFlowStatus.RUNNING.value,
        CollectionFlowStatus.PAUSED.value,
    ]
    and age_days > 7
):
```

#### CrewAI Services - Cleanup Service (Expired Flows)

**File**: `backend/app/services/crewai_flows/collection_flow_cleanup_service/expired_flows.py`
- Lines 60-62: Force cleanup active (3 phase values)

**Fix**: Use `RUNNING` and `PAUSED`.

#### Integration Services - Discovery-Collection Bridge

**File**: `backend/app/services/integration/discovery_collection_bridge.py`
- Line 144: `status=CollectionFlowStatus.INITIALIZED.value` (✅ OK - keep)
- Line 167: `collection_flow.status = CollectionFlowStatus.GAP_ANALYSIS.value` (trigger gap analysis)

**Fix**:
```python
# Line 144: OK
status=CollectionFlowStatus.INITIALIZED.value

# Line 167: trigger gap analysis
collection_flow.status = CollectionFlowStatus.RUNNING.value  # Now actively running
```

#### State Management - Base Utils

**File**: `backend/app/services/collection_flow/state_management/base.py`
- Lines 72-74: `phase_status_map` dictionary (WRONG - entire mapping is incorrect)

**Fix**: Remove this mapping function entirely. Status should NOT be derived from phase.
```python
@staticmethod
def map_phase_to_status(phase: CollectionPhase) -> CollectionFlowStatus:
    """
    DEPRECATED per ADR-012. Status is independent of phase.
    Use explicit status management instead.
    """
    raise NotImplementedError(
        "Status should not be derived from phase per ADR-012. "
        "Set status explicitly based on lifecycle state."
    )
```

---

## Part 4: Status Comparison Violations

### File: `backend/app/services/monitoring/flow_health_monitor.py`
- Lines 87-90: Non-terminal statuses check

**Current**:
```python
CollectionFlow.status.notin_([
    CollectionFlowStatus.COMPLETED.value,
    CollectionFlowStatus.FAILED.value,
    CollectionFlowStatus.CANCELLED.value,
])
```

**Fix**: ✅ This one is CORRECT - no changes needed.

---

## Part 5: Frontend Changes

### File: `src/pages/collection/ApplicationSelection.tsx`
- Line 382: Default phase fallback

**Current**:
```typescript
const currentPhase = flowDetails.current_phase || "gap_analysis";
```

**Fix**: ✅ This is about `current_phase` (not status), so it's CORRECT.

---

## Part 6: Database Migration

### Migration File: `backend/alembic/versions/XXXXX_fix_collection_flow_status.py`

```python
"""Fix CollectionFlowStatus enum values per ADR-012

Revision ID: XXXXX
Revises: YYYYY
Create Date: 2025-01-XX XX:XX:XX
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Update flows with phase values in status field
    op.execute("""
        UPDATE migration.collection_flows
        SET status = CASE
            WHEN status = 'asset_selection' THEN 'running'
            WHEN status = 'gap_analysis' THEN 'running'
            WHEN status = 'manual_collection' THEN 'running'
            ELSE status
        END
        WHERE status IN ('asset_selection', 'gap_analysis', 'manual_collection')
    """)

    # Log the migration
    op.execute("""
        INSERT INTO migration.migration_logs (migration_name, status, message)
        VALUES (
            'fix_collection_flow_status_adr012',
            'completed',
            'Migrated collection flows from phase-based status to lifecycle-based status per ADR-012'
        )
    """)

def downgrade():
    # Cannot reliably downgrade - phase information lost
    # Would require looking at current_phase to restore
    pass
```

---

## Part 7: Sequence of Changes

### Phase 1: Update Enum (5 minutes)
1. Update `backend/app/models/collection_flow/schemas.py`
   - Remove `ASSET_SELECTION`, `GAP_ANALYSIS`, `MANUAL_COLLECTION`
   - Add `RUNNING`, `PAUSED`
2. Restart backend to ensure enum changes are loaded

### Phase 2: Fix Critical Bugs (10 minutes)
1. Fix `backend/app/services/collection_flow/state_management/commands.py:100`
2. Fix `backend/app/services/collection_phase_progression_service.py:49`
3. Test flow creation

### Phase 3: Update Repository Layer (15 minutes)
1. Fix `backend/app/repositories/collection_flow_repository.py`
2. Test active flows query

### Phase 4: Update API Endpoints (45 minutes)
1. Fix `collection_bulk_import.py`
2. Fix `collection_crud_queries/lists.py`
3. Fix `collection_validators.py`
4. Fix `collection_crud_create_commands.py`
5. Fix `collection_crud_execution/management.py`
6. Fix `collection_status_utils.py` (rewrite function)
7. Fix `collection_flow_lifecycle.py` (4 locations)
8. Test all affected endpoints

### Phase 5: Update CrewAI Services (20 minutes)
1. Fix `initialization_handler.py`
2. Fix `collection_flow_cleanup_service/base.py`
3. Fix `collection_flow_cleanup_service/expired_flows.py`

### Phase 6: Update Integration Services (10 minutes)
1. Fix `discovery_collection_bridge.py`

### Phase 7: Update State Management (15 minutes)
1. Deprecate `map_phase_to_status()` in `base.py`
2. Remove all calls to this function

### Phase 8: Database Migration (10 minutes)
1. Create Alembic migration
2. Run migration on dev database
3. Verify all flows updated correctly

### Phase 9: Testing (30 minutes)
1. Test flow creation from scratch
2. Test flow creation from discovery
3. Test bulk import
4. Test phase progression
5. Test continue/resume flow
6. Test cleanup services
7. Verify status displayed correctly in UI

---

## Part 8: Verification Checklist

### Backend Verification
- [ ] All imports of `CollectionFlowStatus` use only: INITIALIZED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
- [ ] No code assigns phase values to `status` field
- [ ] No code checks `status` field against phase values
- [ ] `map_phase_to_status()` function raises NotImplementedError
- [ ] All status queries use lifecycle states only
- [ ] Database migration completed successfully
- [ ] All existing flows have valid status values

### Frontend Verification
- [ ] UI displays status correctly (not showing phase values)
- [ ] Flow routing uses `current_phase` field (not `status`)
- [ ] Continue button works correctly

### Integration Testing
- [ ] Create new collection flow → status = INITIALIZED
- [ ] Start flow execution → status = RUNNING
- [ ] Flow waiting for user input → status = PAUSED
- [ ] Complete flow → status = COMPLETED
- [ ] Flow progression maintains correct status throughout

---

## Part 9: Files Requiring Changes Summary

### Backend Files (34)
1. `backend/app/models/collection_flow/schemas.py` - Enum definition
2. `backend/app/repositories/collection_flow_repository.py` - Repository queries
3. `backend/app/services/collection_flow/state_management/commands.py` - Critical bug #1
4. `backend/app/services/collection_phase_progression_service.py` - Critical bug #2
5. `backend/app/api/v1/endpoints/collection_bulk_import.py` - Bulk import
6. `backend/app/api/v1/endpoints/collection_crud_queries/lists.py` - List queries
7. `backend/app/api/v1/endpoints/collection_validators.py` - Validators
8. `backend/app/api/v1/endpoints/collection_crud_create_commands.py` - Create commands
9. `backend/app/api/v1/endpoints/collection_crud_execution/management.py` - Execution management
10. `backend/app/api/v1/endpoints/collection_status_utils.py` - Status utilities
11. `backend/app/api/v1/endpoints/collection_flow_lifecycle.py` - Lifecycle management
12. `backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/initialization_handler.py` - Initialization
13. `backend/app/services/crewai_flows/collection_flow_cleanup_service/base.py` - Cleanup base
14. `backend/app/services/crewai_flows/collection_flow_cleanup_service/expired_flows.py` - Cleanup expired
15. `backend/app/services/crewai_flows/collection_flow_cleanup_service/recommendations.py` - Cleanup recommendations
16. `backend/app/services/crewai_flows/collection_flow_cleanup_service/orphaned_flows.py` - Cleanup orphaned
17. `backend/app/services/integration/discovery_collection_bridge.py` - Discovery integration
18. `backend/app/services/collection_flow/state_management/base.py` - State management base
19. `backend/app/services/collection_flow_analyzer.py` - Flow analyzer
20. `backend/app/services/monitoring/flow_health_monitor.py` - Health monitor (no change)

### Frontend Files (1)
1. `src/pages/collection/ApplicationSelection.tsx` - No change needed

### Database
1. New Alembic migration file

---

## Part 10: Risk Assessment

### High Risk
- Changing enum values may cause runtime errors if not all locations updated
- Database migration is irreversible (cannot restore phase-based status)

### Medium Risk
- Frontend may show stale status values until page refresh
- Active flows during migration may have inconsistent state

### Low Risk
- Test coverage should catch most issues
- Development environment allows safe testing

### Mitigation
1. **Comprehensive search**: Completed (this document)
2. **Staged rollout**: Fix enum → Fix critical bugs → Fix all other code → Migrate DB
3. **Testing**: Full test suite after each phase
4. **Rollback plan**: Keep old enum values commented out for 1 sprint

---

## Part 11: Success Criteria

### Functional
- ✅ All collection flows can be created successfully
- ✅ Status field contains only lifecycle states (never phase values)
- ✅ Phase progression works correctly
- ✅ Auto-transition to assessment works
- ✅ Cleanup services work correctly

### Architectural
- ✅ ADR-012 compliance: Status = lifecycle, Phase = operational
- ✅ Consistency with AssessmentFlow implementation
- ✅ No `map_phase_to_status()` calls in production code

### Data Quality
- ✅ Zero flows with phase values in status field
- ✅ All flows have valid lifecycle status
- ✅ Migration logged in migration_logs table

---

**TOTAL ESTIMATED TIME: 2-3 hours**

**READY TO EXECUTE**: Yes - all locations identified and fixes specified
