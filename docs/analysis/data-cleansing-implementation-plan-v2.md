# Data Cleansing Implementation Plan v2 (Revised)

## Objective
Fix the data cleansing pipeline to use existing persistent multi-tenant agents and ensure cleaned data is properly stored and used for asset creation.

## Key Corrections from Review
1. **TenantScopedAgentPool EXISTS** at `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py` - reuse it
2. **Agentic enrichment module EXISTS** but has crew-era coupling - wrap as tools for persistent agent
3. **Asset inventory execution** already in `ExecutionEngineDiscoveryCrews._execute_discovery_asset_inventory` - don't duplicate
4. **CSV import** may not be storing raw records - verify and fix

## Implementation Plan (Revised)

### Phase 1: Configure Persistent Agent for Data Cleansing

#### 1.1 Extend Existing TenantScopedAgentPool
**File**: `/backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`
- Add "data_cleansing" agent type to existing pool
- Use existing `AgentToolManager` and `AgentConfigManager`
- No new files needed

#### 1.2 Wrap Enrichment Functions as Tools
**File**: `/backend/app/services/agentic_intelligence/agentic_asset_enrichment.py`
- Wrap existing enrichment functions as tools for persistent agent
- Remove crew-era coupling
- Return structured Python objects (not JSON strings)

### Phase 2: Fix DataCleansingExecutor

#### 2.1 Use Existing Persistent Agent Infrastructure
**File**: `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`

**Changes**:
```python
# Import existing pool
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
    # Get persistent agent from existing pool
    agent_pool = TenantScopedAgentPool(
        client_account_id=str(self.state.client_account_id),
        engagement_id=str(self.state.engagement_id)
    )
    
    cleansing_agent = await agent_pool.get_agent("data_cleansing")
    
    # Process with persistent agent (structured results, no JSON parsing)
    cleaned_data = await cleansing_agent.process(raw_import_records)
    
    # Fix ID mapping before storage
    for record in cleaned_data:
        if 'raw_import_record_id' in record and 'id' not in record:
            record['id'] = record['raw_import_record_id']
    
    # Update with proper storage manager
    updated_count = await storage_manager.update_raw_records_with_cleansed_data(
        data_import_id=data_import_id,
        cleansed_data=cleaned_data,
        validation_results=validation_results
    )
    
    # Commit and log
    await db.commit()
    logger.info(f"✅ Updated {updated_count} raw records with cleansed data")
```

**Remove**:
- All `_process_crew_result()` method and JSON parsing
- References to `self.crew_manager.crewai_service`
- Crew-based kickoff patterns

### Phase 3: Fix Asset Inventory (Use Existing Persistent Path)

#### 3.1 Modify Existing Asset Inventory Executor
**File**: `/backend/app/services/flow_orchestration/execution_engine_crew_discovery.py`
**Method**: `_execute_discovery_asset_inventory`

**Add Cleansed Data Query**:
```python
async def _execute_discovery_asset_inventory(self, agent_pool, phase_input):
    # Log entry
    logger.info(f"📦 Executing discovery asset inventory with {len(phase_input.get('raw_data', []))} input records")
    
    # Get data_import_id
    data_import_id = phase_input.get("data_import_id")
    if not data_import_id:
        raise ValueError("No data_import_id provided")
    
    # Query for cleansed data ONLY
    from app.models.raw_import_record import RawImportRecord
    
    result = await self.db.execute(
        select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import_id,
            RawImportRecord.cleansed_data.isnot(None),  # REQUIRE cleansed_data
            RawImportRecord.client_account_id == self.context.client_account_id,
            RawImportRecord.engagement_id == self.context.engagement_id
        )
    )
    records = result.scalars().all()
    
    cleansed_count = len(records)
    
    # Count raw records for comparison (but don't use them)
    raw_result = await self.db.execute(
        select(func.count(RawImportRecord.id)).where(
            RawImportRecord.data_import_id == data_import_id
        )
    )
    raw_count = raw_result.scalar()
    
    logger.info(f"📊 Using cleansed rows: {cleansed_count}; raw fallback: 0 (blocked)")
    
    # NO FALLBACK - fail if no cleansed data
    if cleansed_count == 0:
        return {
            "status": "error",
            "error_code": "CLEANSING_REQUIRED",
            "message": "No cleansed data available. Run data cleansing first.",
            "counts": {"raw": raw_count, "cleansed": 0}
        }
    
    # Extract cleansed data
    cleansed_data = [r.cleansed_data for r in records]
    
    # Continue with normalization and asset creation...
```

#### 3.2 Remove Duplicate/Stub Executors
**Files to Remove/Clean**:
- `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py` (if stub)
- Any crew-era inventory executors
- `flow_configs/discovery_handlers.asset_inventory` handler-based fallbacks

### Phase 4: Fix CSV Import Pipeline

#### 4.1 Verify Raw Record Storage
**File**: Check CSV upload handler

**Add Logging**:
```python
# In CSV upload handler
logger.info(f"📥 Parsed {len(csv_rows)} CSV rows")

# After ImportStorageManager.store_import_data
await storage_manager.store_import_data(...)
await db.commit()
logger.info(f"✅ Stored {len(csv_rows)} raw_import_records for import {data_import_id}; committing...")
```

#### 4.2 Fix Column Classification
**Check**: `helpers.extract_records_from_data`
- Ensure CSV columns aren't misclassified as "CrewAI metadata"
- Widen acceptance criteria if needed

### Phase 5: Remove Legacy Code

#### 5.1 Remove Crew-Era Files
- Crew-based cleansing executors (keep only persistent agent version)
- JSON parsing methods
- `FlowStateManager.load_state` usages (use flow_state_bridge)

#### 5.2 De-sprawl Routing
- Remove simplified handlers that bypass persistent execution
- Ensure single path through `ExecutionEngineDiscoveryCrews`

### Phase 6: Add Observability

#### 6.1 Critical Log Points
```python
# Data Cleansing
logger.info(f"📋 Prepared {len(records)} assets for cleansing")
logger.info(f"✅ Updated {updated_count} raw records with cleansed data")

# Asset Inventory
logger.info(f"📦 Entry: Processing {record_count} records")
logger.info(f"🔧 Retrieved agent: {agent_name}")
logger.info(f"📊 Using cleansed rows: {cleansed_count}; raw fallback: 0 (blocked)")
logger.info(f"📋 Normalized {normalized_count}/{total_count} records")
logger.info(f"✅ Assets created: {created_count}, failed: {failed_count}")
```

### Error Handling Policy

#### Partial Cleansing Failures
- Update `is_valid` and `validation_errors` per row
- Proceed with valid rows only
- Include counts in response:
```json
{
  "total_records": 100,
  "cleansed_successfully": 90,
  "failed_cleansing": 10,
  "validation_errors": [...]
}
```

#### No Raw Fallback
- If cleansed_count == 0 → Return 422 with CLEANSING_REQUIRED
- Never use raw data for asset creation

### Performance & Safety

#### Batching
- Process 100-200 records per batch for:
  - Data cleansing
  - Bulk asset creation

#### Multi-Tenant Scoping
All queries MUST include:
```python
.where(
    Model.client_account_id == client_account_id,
    Model.engagement_id == engagement_id
)
```

## Testing Plan

### Unit Tests
1. ID mapping in cleansed_data update
2. No raw fallback enforcement
3. Multi-tenant query scoping

### Integration Tests
1. Full pipeline: CSV → raw_import_records → cleansed_data → assets
2. Verify cleansed_data populated correctly
3. Verify 422 returned when no cleansed data

### Manual Verification
1. Upload CSV with mixed data types
2. Check logs for all critical points
3. Query database to verify:
   - raw_import_records created
   - cleansed_data populated
   - assets created from cleansed data only

## Implementation Order

1. **Fix CSV Import** (30 min)
   - Add logging to verify raw records stored
   - Fix column classification if needed

2. **Fix DataCleansingExecutor** (1-2 hours)
   - Use existing TenantScopedAgentPool
   - Fix ID mapping
   - Add logging

3. **Fix Asset Inventory** (1 hour)
   - Modify existing persistent executor
   - Add cleansed data query
   - Block raw fallback

4. **Remove Legacy Code** (1 hour)
   - Clean up crew-era patterns
   - Remove duplicate executors

5. **Add Observability** (30 min)
   - Add all critical log points
   - Verify in Docker logs

## Success Metrics
✅ CSV import creates raw_import_records (see logs)
✅ Data cleansing populates cleansed_data column
✅ Asset inventory uses ONLY cleansed data
✅ 422 error when cleansing not done
✅ Clear logs at each step
✅ Multi-tenant isolation maintained
✅ No crew-era JSON parsing

## Rollback Plan
```bash
# If issues arise
git revert HEAD~n  # Revert n commits
cd config/docker && docker-compose -f docker-compose.dev.yml restart
```

## Questions Resolved
1. **Partial failures**: Update per-row validation, proceed with valid rows
2. **No raw fallback**: Strict requirement, return 422 if no cleansed data
3. **Batching**: Yes, 100-200 records per batch
4. **Legacy removal**: Remove entirely (no commented backup)
5. **Audit trail**: Log counts and critical operations