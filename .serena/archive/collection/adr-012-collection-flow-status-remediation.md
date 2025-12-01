# ADR-012 Violation: Collection Flow Status Remediation

## Problem
CollectionFlowStatus enum violated ADR-012 by mixing lifecycle states with operational phases, causing 2 critical bugs and affecting 34 backend files.

**Root Cause**: Enum created before ADR-012 was written (pre-October 2025).

**Impact**:
- Flow initialization sets `status=GAP_ANALYSIS` instead of `INITIALIZED`
- Auto-progression service queries `status==ASSET_SELECTION` instead of checking phase
- 50+ code locations incorrectly use phase values in status field

## ADR-012 Pattern (MUST FOLLOW)

### Correct Architecture
```python
# ✅ CORRECT - Lifecycle states only
class CollectionFlowStatus(str, Enum):
    INITIALIZED = "initialized"  # Flow created
    RUNNING = "running"          # Active execution
    PAUSED = "paused"           # Waiting for user input
    COMPLETED = "completed"      # Finished successfully
    FAILED = "failed"           # Execution failed
    CANCELLED = "cancelled"     # User cancelled

# Phases are SEPARATE from status
class CollectionPhase(str, Enum):
    INITIALIZATION = "initialization"
    ASSET_SELECTION = "asset_selection"
    GAP_ANALYSIS = "gap_analysis"
    QUESTIONNAIRE_GENERATION = "questionnaire_generation"
    MANUAL_COLLECTION = "manual_collection"
    DATA_VALIDATION = "data_validation"
    FINALIZATION = "finalization"

# Flow has BOTH fields
class CollectionFlow:
    status: str              # Lifecycle state
    current_phase: str       # Operational phase
```

### Wrong Architecture (Legacy)
```python
# ❌ WRONG - Mixes lifecycle and phases
class CollectionFlowStatus(str, Enum):
    INITIALIZED = "initialized"
    ASSET_SELECTION = "asset_selection"      # PHASE - REMOVE
    GAP_ANALYSIS = "gap_analysis"            # PHASE - REMOVE
    MANUAL_COLLECTION = "manual_collection"  # PHASE - REMOVE
    COMPLETED = "completed"
```

## Critical Bugs Found

### Bug #1: Flow Initialization
**File**: `backend/app/services/collection_flow/state_management/commands.py:100`

```python
# ❌ WRONG
collection_flow = CollectionFlow(
    status=CollectionFlowStatus.GAP_ANALYSIS,  # Phase value!
    current_phase=CollectionPhase.GAP_ANALYSIS.value,
)

# ✅ CORRECT
collection_flow = CollectionFlow(
    status=CollectionFlowStatus.INITIALIZED,  # Lifecycle state
    current_phase=CollectionPhase.GAP_ANALYSIS.value,
)
```

### Bug #2: Auto-Progression Query
**File**: `backend/app/services/collection_phase_progression_service.py:49`

```python
# ❌ WRONG
stmt = select(CollectionFlow).where(
    CollectionFlow.status == CollectionFlowStatus.ASSET_SELECTION.value,
)

# ✅ CORRECT
stmt = select(CollectionFlow).where(
    CollectionFlow.current_phase == CollectionPhase.ASSET_SELECTION.value,
    CollectionFlow.status == CollectionFlowStatus.RUNNING,
)
```

## Common Violation Patterns

### Pattern 1: Phase-to-Status Mapping (WRONG)
```python
# ❌ DON'T DO THIS
def map_phase_to_status(phase: CollectionPhase) -> CollectionFlowStatus:
    phase_status_map = {
        CollectionPhase.ASSET_SELECTION: CollectionFlowStatus.ASSET_SELECTION,
        CollectionPhase.GAP_ANALYSIS: CollectionFlowStatus.GAP_ANALYSIS,
    }
    return phase_status_map[phase]
```

**Fix**: Status is independent of phase. Set explicitly based on execution state:
```python
# ✅ CORRECT
def determine_status(flow_state: str) -> CollectionFlowStatus:
    if flow_state == "waiting_for_user":
        return CollectionFlowStatus.PAUSED
    elif flow_state in ["executing", "processing"]:
        return CollectionFlowStatus.RUNNING
    elif flow_state == "finalized":
        return CollectionFlowStatus.COMPLETED
```

### Pattern 2: Active Flow Queries
```python
# ❌ WRONG - Checks phase values
active_statuses = [
    CollectionFlowStatus.ASSET_SELECTION,
    CollectionFlowStatus.GAP_ANALYSIS,
    CollectionFlowStatus.MANUAL_COLLECTION,
]

# ✅ CORRECT - Checks lifecycle states
active_statuses = [
    CollectionFlowStatus.INITIALIZED,
    CollectionFlowStatus.RUNNING,
    CollectionFlowStatus.PAUSED,
]
```

### Pattern 3: Status Updates During Phase Transition
```python
# ❌ WRONG - Changes status with phase
collection_flow.current_phase = "gap_analysis"
collection_flow.status = CollectionFlowStatus.GAP_ANALYSIS  # NO!

# ✅ CORRECT - Status independent of phase
collection_flow.current_phase = "gap_analysis"
# Status stays RUNNING (or PAUSED if waiting for input)
if needs_user_input(collection_flow.current_phase):
    collection_flow.status = CollectionFlowStatus.PAUSED
else:
    collection_flow.status = CollectionFlowStatus.RUNNING
```

## Search Commands for Finding Violations

```bash
# Find enum usage
grep -r "CollectionFlowStatus\\.ASSET_SELECTION" backend/
grep -r "CollectionFlowStatus\\.GAP_ANALYSIS" backend/
grep -r "CollectionFlowStatus\\.MANUAL_COLLECTION" backend/

# Find status assignments
grep -r 'status.*=.*"asset_selection"' backend/
grep -r 'status.*=.*"gap_analysis"' backend/

# Find status comparisons
grep -r 'status.*==.*ASSET_SELECTION' backend/
```

## Remediation Sequence (2-3 hours)

1. **Update Enum** (5 min) - Remove phase values, add RUNNING/PAUSED
2. **Fix Critical Bugs** (10 min) - Fix initialization and auto-progression
3. **Update Repository** (15 min) - Fix active_flows queries
4. **Update API Endpoints** (45 min) - 8 files with multiple locations
5. **Update CrewAI Services** (20 min) - Initialization and cleanup
6. **Update Integration** (10 min) - Discovery-collection bridge
7. **Deprecate Helpers** (15 min) - Remove map_phase_to_status()
8. **Database Migration** (10 min) - Migrate existing flows
9. **Testing** (30 min) - Verify all flows work correctly

## Database Migration

```python
def upgrade():
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
```

## Reference Implementation

AssessmentFlow (created after ADR-012) shows correct pattern:
**File**: `backend/app/models/assessment_flow/enums_and_exceptions.py`

```python
class AssessmentFlowStatus(str, Enum):
    INITIALIZED = "initialized"
    PROCESSING = "processing"              # Lifecycle state
    PAUSED_FOR_USER_INPUT = "paused_for_user_input"
    COMPLETED = "completed"
    ERROR = "error"

class AssessmentPhase(str, Enum):
    INITIALIZATION = "initialization"
    ARCHITECTURE_MINIMUMS = "architecture_minimums"  # Operational phase
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    # ... more phases
```

## Verification Checklist

- [ ] Enum contains only lifecycle states
- [ ] No code assigns phase values to status field
- [ ] No code queries status field against phase values
- [ ] map_phase_to_status() raises NotImplementedError
- [ ] Database migration completed
- [ ] All flows have valid status values
- [ ] Flow creation works (status=INITIALIZED)
- [ ] Flow execution works (status=RUNNING)
- [ ] User input works (status=PAUSED)
- [ ] Flow completion works (status=COMPLETED)

## Related ADRs
- ADR-006: Master Flow Orchestrator
- ADR-012: Flow Status Management Separation (defines this pattern)
