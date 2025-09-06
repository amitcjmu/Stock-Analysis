# Discovery Flow Wiring Implementation Plan v2
*Updated with GPT5's corrections and validations*

## Executive Summary
After GPT5's review and my verification, I confirm that **the Import→Asset linkage code DOES exist** but isn't executing properly. The core issue is transaction boundaries and session management causing the linkage to fail silently. This updated plan addresses the real problems while preserving existing working code.

---

## Key Corrections from GPT5 Review

### What I Got Wrong vs What's Actually There

| My Original Claim | GPT5's Correction | Verification Result |
|-------------------|-------------------|---------------------|
| "No code sets raw_import_records.asset_id" | Code exists in `_link_assets_to_raw_records` | ✅ **CONFIRMED** - Found at line 758-806 |
| "Fallback throws RuntimeError" | Different fallback exists in data_import endpoint | ✅ **CONFIRMED** - Found at line 423-451 |
| "Import path is raw_import_records" | Should be `data_import.core` | ✅ **CONFIRMED** - Correct import found |

### The Real Problem
The linkage code exists but uses a **separate AsyncSession** (line 770), creating a transaction isolation issue. This explains why the database shows no linkage despite the code existing!

---

## Updated Implementation Plan

### Phase 1: Fix Transaction Boundaries (PRIORITY)
**Goal:** Make existing linkage code actually work

#### 1.1 Fix Session Management in AssetInventoryExecutor
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

**Problem:** Line 770 creates new session: `async with AsyncSessionLocal() as session:`
**Solution:** Pass existing session from orchestrator

```python
# Line 758: Accept db session as parameter
async def _link_assets_to_raw_records(
    self, 
    created_assets: List,
    asset_data_list: List[Dict[str, Any]],
    db_session: AsyncSession  # NEW: Use passed session
):
    """Link created assets back to their raw import records"""
    from datetime import datetime
    from sqlalchemy import update
    from app.models.data_import.core import RawImportRecord  # CORRECT import
    
    try:
        # Remove line 770: async with AsyncSessionLocal() as session:
        # Use db_session parameter instead
        
        linked_count = 0
        for i, (asset, asset_data) in enumerate(zip(created_assets, asset_data_list)):
            raw_record_id = asset_data.get("raw_import_record_id")
            
            if raw_record_id:
                update_stmt = (
                    update(RawImportRecord)
                    .where(RawImportRecord.id == raw_record_id)
                    .values(
                        asset_id=asset.id,
                        is_processed=True,
                        processed_at=datetime.utcnow(),
                        processing_notes=f"Linked to asset: {asset.name} (ID: {asset.id})",
                    )
                )
                await db_session.execute(update_stmt)  # Use passed session
                linked_count += 1
                
        # Remove line 801: await session.commit() - Let orchestrator handle commit
        logger.info(f"✅ Linked {linked_count} assets to raw records (pending commit)")
        
    except Exception as e:
        logger.error(f"❌ Failed to link assets to raw records: {e}")
        raise  # Let orchestrator handle rollback
```

#### 1.2 Update AssetCommands to Not Auto-Commit
**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`

```python
# Line 158: Remove auto-commit
# if created_assets:
#     await self.db.commit()  # REMOVE - Let orchestrator commit

# Add new method for transactional creation
async def create_assets_from_discovery_no_commit(
    self,
    discovery_flow_id: uuid.UUID,
    asset_data_list: List[Dict[str, Any]],
    discovered_in_phase: str = "inventory",
) -> List[Asset]:
    """Create assets without committing (for transaction control)"""
    # Same as create_assets_from_discovery but without commit
    # Let calling layer handle transaction boundaries
```

#### 1.3 Orchestrator Handles Single Transaction
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

```python
# Line 207: Update _persist_assets_to_database
async def _persist_assets_to_database(self, results: Dict[str, Any]):
    """Persist discovered assets in single transaction"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Create assets (no commit yet)
            created_assets = await asset_manager.create_assets_from_discovery_no_commit(
                discovery_flow_id=discovery_flow_id,
                asset_data_list=asset_data_list
            )
            
            # 2. Link to raw records (same session, no commit)
            await self._link_assets_to_raw_records(
                created_assets, 
                asset_data_list,
                db  # Pass the session
            )
            
            # 3. Single commit for everything
            await db.commit()
            logger.info("✅ Assets and linkages committed atomically")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Transaction rolled back: {e}")
            raise
```

---

### Phase 2: Add Missing Asset Fields
**Goal:** Ensure assets store all linkage data

#### 2.1 Add Missing Fields During Creation
**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`
**Line 102-148:** Add to Asset creation:

```python
asset = Asset(
    # ... existing fields ...
    discovery_flow_id=discovery_flow_id,  # Already there
    master_flow_id=master_flow_id,  # Already there
    raw_import_records_id=asset_data.get("raw_import_record_id"),  # NEW
    field_mappings_used=asset_data.get("field_mappings"),  # NEW
    # ...
)
```

#### 2.2 Pass Field Mappings from Executor
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`
**Line 396:** Add field mappings to asset_data:

```python
asset_data = {
    "name": asset_name,
    "type": self._determine_asset_type(asset),
    "raw_import_record_id": asset.get("raw_import_record_id"),  # Already there
    "field_mappings": self.state.field_mappings,  # NEW: Add field mappings
    # ...
}
```

---

### Phase 3: Fix Frontend Display (Immediate User Value)
**Goal:** Show all assets regardless of flow selection

#### 3.1 Make FlowId Optional for Queries
**File:** `/frontend/src/components/discovery/inventory/InventoryContent.tsx`

```typescript
// Line 150: Make query work without flowId
enabled: !!client && !!engagement,  // Remove flowId requirement

// Line 92: Make flowId optional in API call
const response = await apiCall(
  `/unified-discovery/assets?page=1&page_size=100${
    flowId ? `&flow_id=${flowId}` : ''
  }`
);

// Add toggle for flow-specific vs all assets view
const [showAllAssets, setShowAllAssets] = useState(true);
```

---

### Phase 4: Standardize ID Usage
**Goal:** Clear up confusion between flow IDs

#### 4.1 Document and Enforce ID Meanings
```sql
-- Add FK constraint to clarify relationship
ALTER TABLE migration.assets 
ADD CONSTRAINT fk_assets_discovery_flow 
FOREIGN KEY (discovery_flow_id) 
REFERENCES migration.discovery_flows(id);

-- Document in code
-- assets.discovery_flow_id → discovery_flows.id (PK)
-- assets.master_flow_id → crewai_flow_state_extensions.flow_id
-- assets.flow_id → LEGACY, being deprecated
```

#### 4.2 Update Any Incorrect Joins
Search and fix any code joining on `discovery_flows.flow_id` instead of `discovery_flows.id`

---

### Phase 5: Add Monitoring
**Goal:** Ensure changes work and catch regressions

#### 5.1 Wiring Health Check Endpoint
**File:** `/backend/app/api/v1/endpoints/health/wiring_health.py`

```python
from sqlalchemy import select, func
from app.models.asset import Asset
from app.models.data_import.core import RawImportRecord  # Correct import

@router.get("/health/wiring")
async def check_wiring_health(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Check database wiring health with tenant scoping"""
    
    # Assets missing discovery_flow_id
    missing_flow = await db.execute(
        select(func.count(Asset.id))
        .where(
            Asset.discovery_flow_id.is_(None),
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
            Asset.discovery_method == "flow_based"
        )
    )
    
    # Raw records missing asset_id
    missing_asset = await db.execute(
        select(func.count(RawImportRecord.id))
        .where(
            RawImportRecord.asset_id.is_(None),
            RawImportRecord.is_processed == False,
            RawImportRecord.client_account_id == context.client_account_id,
            RawImportRecord.engagement_id == context.engagement_id
        )
    )
    
    # Assets missing raw_import_records_id
    missing_raw = await db.execute(
        select(func.count(Asset.id))
        .where(
            Asset.raw_import_records_id.is_(None),
            Asset.discovery_method == "flow_based",
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id
        )
    )
    
    issues = {
        "assets_missing_discovery_flow_id": missing_flow.scalar() or 0,
        "raw_records_missing_asset_id": missing_asset.scalar() or 0,
        "assets_missing_raw_import_id": missing_raw.scalar() or 0
    }
    
    all_zero = all(v == 0 for v in issues.values())
    
    return {
        **issues,
        "health_status": "healthy" if all_zero else "unhealthy",
        "tenant": {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id)
        }
    }
```

---

### Phase 6: Store Cleansed Data
**Goal:** Persist cleansing results

#### 6.1 Update Cleansing Executor
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`

Add method to persist cleansed data:
```python
async def _persist_cleansed_data(self, cleansed_records: Dict):
    """Store cleansed data in raw_import_records"""
    from app.models.data_import.core import RawImportRecord
    
    for record_id, cleansed_data in cleansed_records.items():
        stmt = (
            update(RawImportRecord)
            .where(RawImportRecord.id == record_id)
            .values(cleansed_data=cleansed_data)
        )
        await self.db.execute(stmt)
```

---

## Critical Success Factors

### Transaction Discipline
- **Single transaction** for: Create assets → Link raw records → Update flow state
- **No nested commits** in repository methods
- **Session reuse** instead of creating new sessions

### Correct Imports
- `from app.models.data_import.core import RawImportRecord` ✅
- NOT `from app.models.raw_import_records import RawImportRecord` ❌

### ID Standardization
- `assets.discovery_flow_id` → `discovery_flows.id` (PK)
- `assets.master_flow_id` → `crewai_flow_state_extensions.flow_id`
- `assets.flow_id` → DEPRECATED

---

## Timeline (Revised)

| Priority | Phase | Risk | Impact |
|----------|-------|------|--------|
| 1 | Fix Transactions | Medium | **CRITICAL** - Makes existing code work |
| 2 | Frontend Display | Low | High - Immediate user value |
| 3 | Add Missing Fields | Low | Medium - Better audit trail |
| 4 | Standardize IDs | Low | Medium - Prevents confusion |
| 5 | Add Monitoring | Low | High - Catches issues |
| 6 | Store Cleansed Data | Low | Medium - Complete audit trail |

---

## Why The Code Wasn't Working

The root cause is now clear:
1. **Transaction isolation** - Linkage uses separate session, changes not visible
2. **Silent failures** - Exceptions caught but not re-raised
3. **Seed data predates fixes** - All 29 assets created before linkage code existed
4. **Multiple creation paths** - Some bypass the wired path entirely

This plan fixes the real issues while preserving the existing (correct) implementation.