# Discovery Flow Phase Progression Fix - January 2025

## Problem: UI Navigation Doesn't Update Database Phase
**Issue**: When users click "Continue" in Discovery flow, the UI navigates to the next phase but `current_phase` in database remains unchanged, causing state inconsistency.

## Root Cause
The `continue_flow_processing` endpoint in `flow_processing.py` was determining next phase but only returning it to frontend without updating database.

## Solution: Update Database During Navigation

### Implementation Location
File: `backend/app/api/v1/endpoints/flow_processing.py`

### Code Changes

1. **Import Phase Management Commands**:
```python
from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
    FlowPhaseManagementCommands
)
```

2. **Fast Path Update** (after line ~256):
```python
if fast_response:
    next_phase = fast_response.get("next_phase")
    if next_phase and next_phase != current_phase:
        phase_mgmt = FlowPhaseManagementCommands(db, context.client_account_id, context.engagement_id)
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase=next_phase,
            completed=False,  # Don't mark complete, just update current_phase
            data=None,
            agent_insights=None
        )
        logger.info(f"✅ Advanced current_phase from {current_phase} to {next_phase}")
```

3. **Simple Logic Path Update** (after line ~290):
```python
from app.services.flow_orchestration.transition_utils import _get_next_phase_simple

next_phase = _get_next_phase_simple(flow_type, current_phase)
if next_phase and next_phase != current_phase:
    phase_mgmt = FlowPhaseManagementCommands(db, context.client_account_id, context.engagement_id)
    await phase_mgmt.update_phase_completion(
        flow_id=flow_id,
        phase=next_phase,
        completed=False,
        data=None,
        agent_insights=None
    )
```

## Critical Details
- Use `completed=False` to avoid corrupting progress flags
- Check `next_phase != current_phase` to avoid redundant writes
- Update happens in BOTH Fast Path and Simple Logic paths

## Testing Verification
```sql
SELECT flow_id, current_phase, field_mapping_completed
FROM migration.discovery_flows
WHERE flow_id = 'YOUR_FLOW_ID';
```

Should show `current_phase = 'data_cleansing'` after completing field_mapping.
