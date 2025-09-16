# Phase Completion Sync Arguments Fix

## Insight 1: FlowPhaseManagementCommands Parameter Mismatch
**Problem**: TypeError - update_phase_completion() takes 3-6 args but 7 given
**Solution**: Remove crew_status parameter, merge into data dict
**Code**:
```python
# In base_repository.py update_phase_completion method
# ❌ WRONG - Passing crew_status as separate arg
return await self.flow_commands.update_phase_completion(
    flow_id, phase, data, crew_status, completed, agent_insights
)

# ✅ CORRECT - Merge crew_status into data
if crew_status and data:
    data['crew_status'] = crew_status
elif crew_status:
    data = {'crew_status': crew_status}

return await self.flow_commands.update_phase_completion(
    flow_id, phase, data, completed, agent_insights
)
```
**Usage**: When syncing phase completion between flow layers

## Insight 2: Extract Completed Flag from Phase Data
**Problem**: flow_manager passing wrong parameters to repository
**Solution**: Extract completed flag from phase_data
**Code**:
```python
# In flow_manager.py
completed = phase_data.get("completed", False)

flow = await self.flow_repo.update_phase_completion(
    flow_id=flow_id,
    phase=phase,
    data=phase_data,
    completed=completed,
    agent_insights=agent_insights,
)
```

## Files Fixed:
- `backend/app/repositories/discovery_flow_repository/base_repository.py`
- `backend/app/services/discovery_flow_service/core/flow_manager.py`
