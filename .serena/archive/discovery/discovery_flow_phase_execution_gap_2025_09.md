# Discovery Flow Phase Execution Gap - September 2025

## Critical Issue: Phase Completion Without Execution
**Problem**: Frontend "Continue to X" buttons advance phases without executing them
**Root Cause**: The `complete-phase` endpoint only updates `current_phase` in DB but doesn't trigger phase execution
**Evidence**:
```sql
-- Data shows phase advanced but not executed
current_phase: asset_inventory
data_cleansing_completed: false
cleansed_data IS NULL -- No data was actually cleansed
```

## The Execution Gap Pattern
**What Happens**:
1. User clicks "Continue to Inventory" after viewing data cleansing UI
2. Frontend calls `/complete-phase` which advances `current_phase`
3. Backend never calls `DataCleansingExecutor.execute_with_crew()`
4. No cleansed_data is persisted to `raw_import_records`
5. Asset inventory fails because no cleansed data exists

**Logs Confirming Issue**:
```
✅ Advanced current_phase from data_cleansing to asset_inventory
[No "Executing discovery data cleansing" log entry]
```

## Fixed Implementation (Already Applied)
**File**: `backend/app/services/flow_orchestration/execution_engine_crew_discovery.py`
```python
async def _execute_discovery_data_cleansing(self, phase_input: Dict[str, Any]):
    # Initialize DataCleansingExecutor (not legacy UnifiedFlowCrewManager)
    executor = DataCleansingExecutor(state)
    executor.db_session = self.db_session

    # Execute with crew - this actually cleanses data
    result = await executor.execute_with_crew(phase_input)

    # Persist the completion flag
    await self.db_session.execute(
        update(DiscoveryFlow)
        .where(DiscoveryFlow.master_flow_id == master_flow_id)
        .values(data_cleansing_completed=True)
    )
```

## Phase Mapping Fix
**Before**: `"data_cleansing": DiscoveryPhaseHandlers.execute_data_cleansing` (uses UnifiedFlowCrewManager)
**After**: `"data_cleansing": self._execute_discovery_data_cleansing` (uses DataCleansingExecutor)

## Required No-Fallback Policy
**CRITICAL**: Asset inventory MUST fail if no cleansed data exists
- NO raw data fallbacks allowed
- Return 422 CLEANSING_REQUIRED if cleansed_count == 0
- This forces proper phase execution

## Verification Queries
```sql
-- After data cleansing execution, these should be true:
SELECT COUNT(*) FROM migration.raw_import_records
WHERE data_import_id='X' AND cleansed_data IS NOT NULL; -- > 0

SELECT data_cleansing_completed FROM migration.discovery_flows
WHERE flow_id='X'; -- true

SELECT COUNT(*) FROM migration.assets
WHERE discovery_flow_id IN (SELECT id FROM migration.discovery_flows WHERE flow_id='X'); -- > 0
```

## Key Lesson
The UI showing "89% quality score" doesn't mean data cleansing executed - it's showing analysis results from the initial import. Always verify with DB queries that:
1. cleansed_data is persisted
2. phase completion flags are set
3. assets are linked to the specific flow_id
