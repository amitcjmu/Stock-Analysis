# Discovery Flow Phase Progression Bug (November 2025)

## Problem Pattern
Assets not being created in inventory phase. Flows stuck at initialization phase even after field_mapping completes.

## Root Cause - Architecture Disconnect

### Two Separate Systems Operating Independently

**System 1 - Navigation** (`/api/v1/flow-processing/continue/{flow_id}`):
- Purpose: Determine where UI should navigate next
- Logic: Uses `transition_utils.py` lines 326-372 for phase sequences
- Updates: Returns routing decision only
- **DOES NOT update `current_phase` in database**

**System 2 - Execution** (`/api/v1/unified-discovery/flows/{flow_id}/execute`):
- Purpose: Actually run CrewAI phases
- Logic: Executes phases via Master Flow Orchestrator
- Updates: Sets `current_phase` when phases execute (lines 271, 397 in flow_execution_service.py)
- **Only runs when phases are executed, not on navigation**

### Why Flows Get Stuck

1. User completes field mapping
2. Clicks "Continue" → calls `/flow-processing/continue/{flow_id}`
3. Navigation system returns next route → UI navigates correctly
4. **Gap**: `current_phase` never updates in database
5. Database remains at `current_phase = 'initialization'` despite `field_mapping_completed = true`

### Phase Sequence (from transition_utils.py:331-337)
```python
discovery_phases = [
    "data_import",
    "field_mapping",
    "data_cleansing",
    "asset_inventory",
    "dependency_analysis",
]
```

## Intelligent Flow Agent Role (Clarified)

**NOT responsible for normal phase progression**
- Located: `/backend/app/services/agents/intelligent_flow_agent/agent.py`
- Called only for: Complex scenarios, errors, field mapping validation
- Function: Makes routing decisions, not phase execution
- Normal progression: Uses simple hardcoded sequence

## Current_phase Update Locations

Only updated in 2 places in `flow_execution_service.py`:
- Line 271: Sets to "field_mapping_suggestions"
- Line 397: Sets to "asset_inventory"

Missing updates for other phases!

## Required Fix

Modify `/api/v1/flow-processing/continue/{flow_id}` endpoint to:
1. Determine next phase (existing logic)
2. **Update `current_phase` in database** (missing step)
3. Return routing decision (existing logic)

```python
# In flow_processing.py after determining next phase
from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
    FlowPhaseManagementCommands
)

# After line ~300 where next_phase is determined
if next_phase and next_phase != current_phase:
    phase_mgmt = FlowPhaseManagementCommands(db, client_account_id, engagement_id)
    await phase_mgmt.update_current_phase(flow_id, next_phase)
    await db.commit()
```

## Testing Evidence
```sql
-- Shows the disconnect
SELECT flow_id, current_phase, field_mapping_completed, data_cleansing_completed
FROM migration.discovery_flows
WHERE flow_id = '923100ed-3bd0-4297-a8af-0a47cc274bde';
-- Result: current_phase='initialization', field_mapping_completed=true
```

## Misconceptions Corrected

**Previous Wrong Assumptions**:
- ❌ Intelligent Flow Agent controls phase progression
- ❌ Phase name mismatch between agent and system
- ❌ master_flow_id linking issues
- ❌ ServiceRegistry initialization problems

**Actual Issue**:
- ✅ Simple architectural disconnect between navigation and state management
- ✅ Navigation system doesn't update database state
- ✅ Phase names are consistent across the system

## Architecture Pattern
Two-layer flow system where navigation and execution are decoupled. This allows UI to navigate freely but causes state synchronization issues.

## Long-term Recommendation
Consider consolidating navigation and state management to prevent this disconnect. The separation may have been intentional for flexibility but causes state consistency issues.
