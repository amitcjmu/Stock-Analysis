# Common Pitfall: Transaction Management in Phase Executors

## The Problem
Phase executors in `execution_engine_crew_discovery/` receive `db_session` with an **active transaction already started**.

## ❌ WRONG Pattern (Causes "transaction already begun" error)
```python
async def _execute_phase(self, phase_input: Dict[str, Any]) -> Dict[str, Any]:
    async with self.db_session.begin():  # ERROR: Transaction already active!
        result = await executor.execute_asset_creation(flow_context)
    return result
```

## ✅ CORRECT Pattern
```python
async def _execute_phase(self, phase_input: Dict[str, Any]) -> Dict[str, Any]:
    # Use db_session directly - transaction already active
    result = await executor.execute_asset_creation(flow_context)
    await self.db_session.flush()  # Make IDs available for FK relationships
    # Caller will commit/rollback
    return result
```

## Context
- **Files**: `phase_executors.py`, `asset_inventory_executor.py`
- **Root Cause**: ExecutionEngine methods receive active session from MasterFlowOrchestrator
- **Solution**: Never nest transactions in phase executors

## Recent Fix
- Issue #520-522: Removed `async with db_session.begin()` from AssetInventoryExecutor.execute_asset_creation()
- Location: `asset_inventory_executor.py:157-190`
