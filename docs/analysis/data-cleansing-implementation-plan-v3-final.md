# Data Cleansing Implementation Plan v3 (FINAL)

## Implementation Ready - All Corrections Applied

### Critical Corrections from GPT5 Review
1. ✅ Use correct model import: `from app.models.data_import.core import RawImportRecord`
2. ✅ Use `self.db_session` (not `self.db`) in ExecutionEngineDiscoveryCrews
3. ✅ Add tenant scoping to ALL queries
4. ✅ Await cleansed_data update (no async fire-and-forget)
5. ✅ Add phase progression flag after successful cleansing

## Implementation Tasks

### Task 1: Verify CSV Import Pipeline (30 min)

#### 1.1 Add Logging to CSV Upload Handler
**File**: Find the CSV upload handler endpoint

**Add**:
```python
# After parsing CSV
logger.info(f"📥 Parsed {len(csv_rows)} CSV rows")

# After storage
await storage_manager.store_import_data(...)
await db.commit()
logger.info(f"✅ Stored {len(csv_rows)} raw_import_records for import {data_import_id}; committing...")
```

#### 1.2 Fix Column Classification
**File**: Check `helpers.extract_records_from_data`
- Ensure real CSV columns aren't classified as "metadata"
- Widen acceptance criteria if needed

---

### Task 2: Fix DataCleansingExecutor (2 hours)

#### 2.1 Configure Persistent Agent
**File**: `/backend/app/services/persistent_agents/agent_config_manager.py` (or similar)

**Add Configuration**:
```python
"data_cleansing": {
    "agent_type": "data_cleansing",
    "tools": ["type_conversion", "field_validation", "value_standardization"],
    "memory_enabled": True
}
```

**File**: `/backend/app/services/persistent_agents/agent_tool_manager.py`

**Add Tool Wiring**:
```python
# Wrap existing enrichment functions as tools
from app.services.agentic_intelligence.agentic_asset_enrichment import (
    # existing functions to wrap as tools
)
```

#### 2.2 Update DataCleansingExecutor
**File**: `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`

**Complete Replacement of execute_with_crew**:
```python
async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("🧠 Starting data cleansing with persistent multi-tenant agent")
    
    # Get raw records WITH tenant scoping
    raw_import_records = await self._get_raw_import_records_with_ids()
    logger.info(f"📋 Prepared {len(raw_import_records)} assets for cleansing")
    
    if not raw_import_records:
        raise RuntimeError("No raw import records found for data cleansing")
    
    # Get persistent agent from existing pool
    from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool
    
    agent_pool = TenantScopedAgentPool(
        client_account_id=str(self.state.client_account_id),
        engagement_id=str(self.state.engagement_id)
    )
    
    cleansing_agent = await agent_pool.get_agent(self.context, "data_cleansing")
    logger.info(f"🔧 Retrieved agent: data_cleansing")
    
    # Process with persistent agent (structured results, no JSON parsing)
    cleaned_data = await cleansing_agent.process(raw_import_records)
    
    # CRITICAL: Fix ID mapping before storage
    for record in cleaned_data:
        if 'raw_import_record_id' in record and 'id' not in record:
            record['id'] = record['raw_import_record_id']
    
    # CRITICAL: Await the update (no fire-and-forget)
    await self._update_cleansed_data_sync(cleaned_data)
    
    # Set phase completion flag
    await self._mark_phase_complete("data_cleansing")
    
    return {
        "cleaned_data": cleaned_data,
        "cleansing_summary": self._generate_cleansing_summary(cleaned_data),
        "quality_metrics": self._calculate_cleansing_quality_metrics(cleaned_data),
        "persistent_agent_used": True,
        "crew_based": False
    }
```

**Add Synchronous Update Method**:
```python
async def _update_cleansed_data_sync(self, cleaned_data: List[Dict[str, Any]]):
    """Update raw records with cleansed data - SYNCHRONOUS, no fire-and-forget"""
    from app.core.database import AsyncSessionLocal
    from app.services.data_import.storage_manager import ImportStorageManager
    
    async with AsyncSessionLocal() as db:
        storage_manager = ImportStorageManager(db, str(self.state.client_account_id))
        
        data_import_id = uuid.UUID(self.state.data_import_id)
        
        updated_count = await storage_manager.update_raw_records_with_cleansed_data(
            data_import_id=data_import_id,
            cleansed_data=cleaned_data,
            validation_results=getattr(self.state, 'data_validation_results', None)
        )
        
        await db.commit()
        logger.info(f"✅ Updated {updated_count} raw records with cleansed data")
```

**Fix _get_raw_import_records_with_ids WITH Tenant Scoping**:
```python
async def _get_raw_import_records_with_ids(self) -> List[Dict[str, Any]]:
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.data_import.core import RawImportRecord  # CORRECT IMPORT
    
    async with AsyncSessionLocal() as session:
        data_import_id = getattr(self.state, "data_import_id", None)
        if not data_import_id:
            logger.error("❌ No data_import_id found in state")
            return []
        
        # WITH TENANT SCOPING
        query = (
            select(RawImportRecord)
            .where(
                RawImportRecord.data_import_id == data_import_id,
                RawImportRecord.client_account_id == self.state.client_account_id,
                RawImportRecord.engagement_id == self.state.engagement_id
            )
        )
        
        result = await session.execute(query)
        raw_records = result.scalars().all()
        # ... rest of method
```

**Remove**:
- Entire `_process_crew_result()` method
- All references to `self.crew_manager.crewai_service`
- The asyncio.create_task in `_update_raw_records_with_cleansed_data`

---

### Task 3: Fix Asset Inventory (1 hour)

#### 3.1 Update ExecutionEngineDiscoveryCrews
**File**: `/backend/app/services/flow_orchestration/execution_engine_crew_discovery.py`
**Method**: `_execute_discovery_asset_inventory`

**Add Cleansed Data Query with Correct Imports and Tenant Scoping**:
```python
async def _execute_discovery_asset_inventory(self, agent_pool, phase_input):
    logger.info(f"📦 Entry: Processing asset inventory phase")
    
    data_import_id = phase_input.get("data_import_id")
    if not data_import_id:
        raise ValueError("No data_import_id provided")
    
    # CORRECT IMPORTS
    from sqlalchemy import select, func
    from app.models.data_import.core import RawImportRecord  # CORRECT PATH
    
    # Query for cleansed data WITH TENANT SCOPING
    result = await self.db_session.execute(  # USE db_session, not db
        select(RawImportRecord).where(
            RawImportRecord.data_import_id == data_import_id,
            RawImportRecord.cleansed_data.isnot(None),
            RawImportRecord.client_account_id == self.context.client_account_id,  # TENANT
            RawImportRecord.engagement_id == self.context.engagement_id  # TENANT
        )
    )
    records = result.scalars().all()
    
    cleansed_count = len(records)
    
    # Count raw records for comparison
    raw_result = await self.db_session.execute(
        select(func.count(RawImportRecord.id)).where(
            RawImportRecord.data_import_id == data_import_id,
            RawImportRecord.client_account_id == self.context.client_account_id,
            RawImportRecord.engagement_id == self.context.engagement_id
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
    
    # Get field mappings
    field_mappings = await self._get_approved_field_mappings(phase_input)
    
    # Get flow IDs
    master_flow_id = phase_input.get("master_flow_id") or phase_input.get("flow_id")
    discovery_flow_id = await self._get_discovery_flow_id(master_flow_id)
    
    # Normalize using cleansed data
    normalized_assets = await self._normalize_assets_for_creation(
        cleansed_data,  # USE CLEANSED DATA
        field_mappings,
        master_flow_id,
        discovery_flow_id
    )
    
    logger.info(f"📋 Normalized {len(normalized_assets)}/{cleansed_count} records")
    
    # Continue with asset creation...
    # (rest of existing method)
```

---

### Task 4: Remove Legacy Code (1 hour)

#### 4.1 Files to Remove
- Any stub AssetInventoryExecutor that returns fake success
- Crew-era data cleansing crews
- Handler-based inventory routes in `flow_configs/discovery_handlers`

#### 4.2 Methods to Remove
- `DataCleansingExecutor._process_crew_result()` - entire method
- `DataCleansingExecutor._prepare_assets_for_agentic_analysis()` - if replaced
- All `FlowStateManager.load_state()` usages

#### 4.3 Replace FlowStateManager
**Find and Replace All**:
```python
# OLD
FlowStateManager.load_state(...)

# NEW
flow_state_bridge.load_state(...)
```

---

### Task 5: Add Phase Progression (30 min)

#### 5.1 Mark Phase Complete
**Add to DataCleansingExecutor**:
```python
async def _mark_phase_complete(self, phase_name: str):
    """Mark phase as complete for progression tracking"""
    from app.services.discovery.phase_transition_service import PhaseTransitionService
    
    async with AsyncSessionLocal() as db:
        transition_service = PhaseTransitionService(db)
        await transition_service.mark_phase_complete(
            flow_id=self.state.flow_id,
            phase_name=phase_name
        )
        await db.commit()
        logger.info(f"✅ Marked phase {phase_name} as complete")
```

---

## Testing Checklist

### 1. CSV Import
- [ ] Upload CSV file
- [ ] Check logs for "📥 Parsed N CSV rows"
- [ ] Check logs for "✅ Stored N raw_import_records"
- [ ] Query DB: `SELECT COUNT(*) FROM raw_import_records WHERE data_import_id = ?`

### 2. Data Cleansing
- [ ] Run data cleansing phase
- [ ] Check logs for "📋 Prepared N assets for cleansing"
- [ ] Check logs for "✅ Updated N raw records with cleansed data"
- [ ] Query DB: `SELECT COUNT(*) FROM raw_import_records WHERE cleansed_data IS NOT NULL`

### 3. Asset Inventory
- [ ] Run asset inventory phase
- [ ] Check logs for "📊 Using cleansed rows: X; raw fallback: 0 (blocked)"
- [ ] Verify 422 error if no cleansed data
- [ ] Check assets created with proper names/types

### 4. Multi-Tenant Isolation
- [ ] Verify all queries include client_account_id and engagement_id
- [ ] Test with different tenants to ensure isolation

---

## Rollback Plan
```bash
# If issues arise
git stash  # Save current changes
git checkout main  # Or previous working branch
cd config/docker && docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

---

## Success Metrics
✅ Raw import records created from CSV
✅ Cleansed_data column populated with correct IDs
✅ Asset inventory uses ONLY cleansed data
✅ 422 error when no cleansed data exists
✅ Phase progression tracked properly
✅ Multi-tenant isolation maintained
✅ No crew-era JSON parsing remains
✅ Clear observability logs at each step

---

## Implementation Order
1. Task 1: CSV Import Verification (30 min)
2. Task 2: DataCleansingExecutor (2 hours)
3. Task 3: Asset Inventory (1 hour)  
4. Task 4: Legacy Removal (1 hour)
5. Task 5: Phase Progression (30 min)

**Total: ~5 hours**

---

## READY FOR IMPLEMENTATION
All corrections applied. No further review needed.