# Data Cleansing Implementation Plan

## Objective
Fix the data cleansing pipeline to use persistent multi-tenant agents and ensure cleaned data is properly stored and used for asset creation.

## Current Issues
1. **DataCleansingExecutor** tries to import non-existent `agentic_asset_enrichment` module
2. **TenantScopedAgentPool** doesn't exist in codebase (needs to be created)
3. **cleansed_data** column update fails due to ID mapping issue
4. **Asset creation** uses raw data instead of cleansed data
5. **AssetInventoryExecutor** is a stub that doesn't create assets
6. **Crew-based patterns** still being used instead of persistent agents

## Implementation Plan

### Phase 1: Create Persistent Agent Infrastructure

#### 1.1 Create TenantScopedAgentPool
**New File**: `/backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`
- Create agent pool that manages persistent agents per tenant
- Methods needed:
  - `__init__(client_account_id, engagement_id)`
  - `async get_agent(agent_type: str)` - Returns persistent agent for data_cleansing
  - `async release_agent(agent_type: str)` - Cleanup method
- Multi-tenant isolation using client_account_id + engagement_id as key
- Agent types to support: "data_cleansing", "asset_inventory"

#### 1.2 Create Data Cleansing Agent
**New File**: `/backend/app/services/persistent_agents/data_cleansing_agent.py`
- Persistent agent specifically for data cleansing
- Tools to attach:
  - Type conversion tool (string → number, date parsing)
  - Field validation tool
  - Value standardization tool
  - Format normalization tool
- Returns structured Python objects (not JSON strings)

### Phase 2: Fix DataCleansingExecutor

#### 2.1 Remove Non-existent Import
**File**: `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`

**Remove**:
```python
from app.services.agentic_intelligence.agentic_asset_enrichment import (
    enrich_assets_with_agentic_intelligence,
)
```

**Replace with**:
```python
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
```

#### 2.2 Replace Crew-based Processing
**Current Pattern** (Remove):
- `self.crew_manager.crewai_service`
- JSON parsing of `crew_result.raw`
- `_process_crew_result` method entirely

**New Pattern** (Add):
```python
async def _process_with_persistent_agent(self, agent, raw_records):
    # Direct agent execution with tools
    # Returns structured data, no JSON parsing
```

#### 2.3 Fix ID Mapping for cleansed_data Update
**Problem**: Update expects `id` field but cleaned records have `raw_import_record_id`

**Fix in** `_update_raw_records_with_cleansed_data`:
```python
# Before passing to storage manager, map the ID correctly
for record in cleaned_data:
    if 'raw_import_record_id' in record and 'id' not in record:
        record['id'] = record['raw_import_record_id']
```

**Add Logging**:
```python
logger.info(f"✅ Updated {updated_count} raw records with cleansed data")
```

### Phase 3: Fix Asset Inventory to Use Cleansed Data

#### 3.1 Modify Asset Inventory Executor
**File**: `/backend/app/services/flow_orchestration/execution_engine_crew_discovery.py`

**In** `_execute_discovery_asset_inventory`:

**Current** (Remove):
```python
# Uses raw_data directly
raw_data = phase_input.get("raw_data", [])
```

**New** (Add):
```python
# Query raw_import_records for cleansed_data
async def get_cleansed_records(data_import_id):
    result = await session.execute(
        select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import_id,
            RawImportRecord.cleansed_data.isnot(None)  # REQUIRE cleansed_data
        )
    )
    records = result.scalars().all()
    
    cleansed_count = len(records)
    raw_fallback_count = 0  # NO FALLBACK ALLOWED
    
    logger.info(f"📊 Using cleansed rows: {cleansed_count}; raw fallback: {raw_fallback_count} (blocked)")
    
    if cleansed_count == 0:
        raise ValueError("CLEANSING_REQUIRED: No cleansed data available. Run data cleansing first.")
    
    return [r.cleansed_data for r in records]
```

#### 3.2 Update AssetInventoryExecutor
**File**: `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

Replace stub implementation with actual persistent agent execution:
```python
async def execute(self, flow_context):
    # Get persistent agent
    agent_pool = TenantScopedAgentPool(...)
    inventory_agent = await agent_pool.get_agent("asset_inventory")
    
    # Process with agent
    assets = await inventory_agent.process(cleansed_data)
    
    # Create assets using ServiceRegistry
    # Return actual counts
```

### Phase 4: Remove Legacy Code

#### 4.1 Crew-era Files to Remove
- `/backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py` (if exists)
- `/backend/app/services/crewai_flows/crews/data_cleansing_crew.py` (crew-based cleansing)

#### 4.2 Methods to Remove
- `DataCleansingExecutor._process_crew_result()` - entire method
- `DataCleansingExecutor._prepare_assets_for_agentic_analysis()` - if using persistent agent
- Any `FlowStateManager.load_state()` usages

#### 4.3 Cleanup Placeholder Executors
- Remove any executor that returns `{"status": "completed", "assets_created": 0}`

### Phase 5: Add Safety Guardrails

#### 5.1 API Validation
**In flow execution endpoints**, add:
```python
if not field_mapping_completed:
    return JSONResponse(
        status_code=422,
        content={
            "status": "not_ready",
            "error_code": "FIELD_MAPPING_REQUIRED",
            "message": "Field mappings must be approved before data cleansing"
        }
    )

if cleansed_data_count == 0:
    return JSONResponse(
        status_code=422,
        content={
            "status": "not_ready", 
            "error_code": "CLEANSING_REQUIRED",
            "counts": {"raw": raw_count, "cleansed": 0}
        }
    )
```

#### 5.2 Observability
Add logging at key points:
- Entry to each phase with record counts
- Cleansed vs raw data usage
- Tool execution results
- Asset creation success/failure

### Testing Plan

1. **Unit Tests**:
   - TenantScopedAgentPool isolation
   - ID mapping in cleansed_data update
   - No raw data fallback in asset creation

2. **Integration Tests**:
   - Full flow: import → map → cleanse → inventory
   - Verify cleansed_data column populated
   - Verify assets created from cleansed data only

3. **Manual Testing**:
   - Upload CSV with mixed data types
   - Verify cleansing converts types correctly
   - Verify assets have proper names and types

### Rollback Plan
If issues arise:
1. Git revert the commits
2. Restart docker containers
3. Previous working state (with raw data usage) will be restored

### Success Criteria
- ✅ No import errors for non-existent modules
- ✅ Persistent agents used (not crews)
- ✅ cleansed_data column populated with correct IDs
- ✅ Assets created from cleansed_data only
- ✅ No raw data fallback
- ✅ Proper multi-tenant isolation
- ✅ Clear error messages when cleansing required

### Estimated Time
- Phase 1: 2-3 hours (create persistent agent infrastructure)
- Phase 2: 1-2 hours (fix DataCleansingExecutor)
- Phase 3: 1-2 hours (fix asset inventory)
- Phase 4: 1 hour (remove legacy code)
- Phase 5: 1 hour (add guardrails)
- Testing: 2 hours

**Total: 8-11 hours**

## Questions for Review

1. **Persistent Agent Tools**: What specific data cleansing operations should the agent perform?
   - Type conversion (string → number, dates)
   - Value standardization (environments, asset types)
   - Field validation
   - What else?

2. **Error Handling**: How should we handle partial failures?
   - If 90% of records cleanse successfully but 10% fail, should we:
     - Fail the entire batch?
     - Process the 90% and mark the 10% as invalid?
     - Store error details for manual review?

3. **Legacy Code Removal**: Should we keep crew-based code as commented backup or remove entirely?

4. **Performance**: Should we process records in batches for large imports?
   - Current: All at once
   - Proposed: Batches of 100-500 records

5. **Audit Trail**: Should we log before/after values for cleansing operations?

## Next Steps
1. Review and approve this plan
2. Answer the questions above
3. Begin implementation in the specified order
4. Test each phase before moving to next