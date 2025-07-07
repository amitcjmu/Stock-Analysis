# ECHO Team Discovery Flow Execution Fix

## Problem Statement
Discovery flows were stuck at "initialized" status after creation and never progressed to "running" or beyond. This was blocking all migration activities as flows couldn't execute their phases.

## Root Cause Analysis

### 1. **Async Task Not Properly Stored**
The async task created for flow kickoff was not being stored, making it susceptible to garbage collection:

```python
# Before (problematic):
task = asyncio.create_task(run_discovery_flow())
# Task could be garbage collected before completion
```

### 2. **Database Session Issues in Background Task**
The background task was trying to use the same database session from the request context, which might have been closed:

```python
# Before (problematic):
await self.master_repo.update_flow_status(...)  # Using request's db session
```

### 3. **Flow Registry Singleton Issues**
The FlowConfigurationManager was creating its own instance of FlowTypeRegistry instead of using the global singleton, causing flow types to not be registered properly:

```python
# Before (problematic):
self.flow_registry = FlowTypeRegistry()  # Creating new instance
```

### 4. **State Updates Not Persisting**
The flow state bridge was delegating updates to MFO but not actually updating the database, causing state transitions to be lost.

## Fixes Applied

### 1. **Store Task Reference** ([ECHO] Fix)
```python
# After (fixed):
task = asyncio.create_task(run_discovery_flow())

# Store task reference to prevent garbage collection
if not hasattr(self, '_active_flow_tasks'):
    self._active_flow_tasks = {}
self._active_flow_tasks[flow_id] = task
```

### 2. **Use Fresh Database Session in Background Task** ([ECHO] Fix)
```python
# After (fixed):
async with AsyncSessionLocal() as fresh_db:
    fresh_repo = CrewAIFlowStateExtensionsRepository(
        fresh_db, 
        self.context.client_account_id,
        self.context.engagement_id,
        self.context.user_id
    )
    await fresh_repo.update_flow_status(...)
```

### 3. **Use Global Registry Singletons** ([ECHO] Fix)
```python
# After (fixed):
from app.services.flow_type_registry import flow_type_registry
from app.services.validator_registry import validator_registry  
from app.services.handler_registry import handler_registry

self.flow_registry = flow_type_registry  # Use global singleton
```

### 4. **Update Flow Status Immediately** ([ECHO] Fix)
Added immediate status update to "running" at the start of flow kickoff:

```python
# In @start() method:
await store.update_flow_status(self._flow_id, "running")
logger.info(f"✅ [ECHO] Updated flow status to 'running' at start of kickoff")
```

### 5. **Enhanced Logging** ([ECHO] Fix)
Added comprehensive logging with [ECHO] prefix throughout the execution chain to trace flow progression:

```python
logger.info(f"🎯 [ECHO] Starting CrewAI Discovery Flow kickoff for {flow_id}")
logger.info(f"🔍 [ECHO] Task reference stored to prevent GC: {task}")
logger.info(f"📊 [ECHO] Data import phase STARTED - flow is now executing!")
```

## Files Modified

1. `/backend/app/services/master_flow_orchestrator.py`
   - Added task storage to prevent GC
   - Use fresh DB sessions in background tasks
   - Enhanced logging for debugging

2. `/backend/app/services/crewai_flows/unified_discovery_flow/base_flow.py`
   - Update status to "running" immediately in @start()
   - Enhanced logging in @listen methods
   - Better state persistence in phase transitions

3. `/backend/app/services/flow_configs/__init__.py`
   - Use global registry singletons instead of creating new instances

## Testing

Created test scripts to validate the fix:
- `test_echo_flow_execution.py` - Full integration test
- `test_echo_flow_state_fix.py` - Unit test without database

## Expected Behavior After Fix

1. Flow created with status "initialized" ✅
2. Background task starts and updates status to "running" within 0.5 seconds ✅
3. @start() method executes and initializes flow state ✅
4. @listen() methods execute in sequence for each phase ✅
5. Progress percentage increases as phases complete ✅
6. Flow reaches "completed" status after all phases finish ✅

## Success Criteria

- Flows transition from "initialized" to "running" immediately after creation
- Data import phase starts and shows progress
- Flow phases execute sequentially
- Progress percentage updates correctly
- No silent failures or stuck states

## Notes

- The fix maintains 100% DFD compliance as requested
- No architectural changes were made, only execution fixes
- All changes are focused on making the existing architecture work properly
- Enhanced logging helps with future debugging

## Coordination with Other Teams

- Team Foxtrot's security fixes won't affect this implementation
- Team Golf's error handling improvements will complement these fixes
- No conflicts with other team's work areas