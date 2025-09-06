# Discovery Flow Wiring Implementation Plan

## Executive Summary
Based on my analysis and GPT5's feedback, I've validated the current state of the discovery flow wiring. While GPT5 claims some connections exist in code, **my database inspection shows these connections are NOT working in practice**. This implementation plan addresses both perspectives and provides a comprehensive path to fix all wiring issues.

---

## Validation of GPT5's Claims vs Reality

### What GPT5 Claims vs What I Found

| GPT5 Claim | My Finding | Reality |
|------------|------------|---------|
| "Asset→Flow linkage exists in code" | Code exists BUT data shows 0/29 assets have `discovery_flow_id` set | **Partially True** - Code exists but not executing |
| "Import→Asset linkage exists in code" | No code found that sets `raw_import_records.asset_id` | **FALSE** - No implementation found |
| "AssetInventoryExecutor sets both IDs" | Found the executor, it sets `discovery_flow_id` and `master_flow_id` | **TRUE** - But assets in DB predate this code |
| "Fallback path does it too" | Fallback is disabled with RuntimeError | **FALSE** - Fallback explicitly disabled |
| "AssetCommands.create_assets_from_discovery" | Found it, does set both flow IDs (lines 139-140) | **TRUE** - Implementation exists |

### Root Cause Analysis
1. **All 29 assets are seed data from Sept 3** - Created before the wiring code was implemented
2. **No assets have been created through discovery flow** - The wired code hasn't been executed
3. **The code exists but isn't being used** - Assets are created through other paths
4. **No raw_import_records → asset linkage** - This is completely missing

---

## Implementation Plan

### Phase 1: Quick Wins (Day 1)
**Goal:** Fix critical missing links with minimal risk

#### 1.1 Add Bidirectional Asset-Import Linkage
**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`
**Changes:**
```python
# Line 99: Add raw_import_records_id to asset creation
asset = Asset(
    # ... existing fields ...
    raw_import_records_id=asset_data.get("raw_import_record_id"),  # NEW
    field_mappings_used=asset_data.get("field_mappings"),  # NEW
    # ...
)

# After line 169: Update raw_import_records with asset_id
if asset_data.get("raw_import_record_id"):
    await self._link_raw_import_to_asset(
        asset_data["raw_import_record_id"], 
        asset.id
    )
```

#### 1.2 Implement Raw Import Record Linking
**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`
**Add Method:**
```python
async def _link_raw_import_to_asset(
    self, 
    raw_import_record_id: uuid.UUID, 
    asset_id: uuid.UUID
) -> None:
    """Link raw import record to created asset"""
    from app.models.raw_import_records import RawImportRecord
    
    stmt = (
        update(RawImportRecord)
        .where(RawImportRecord.id == raw_import_record_id)
        .values(
            asset_id=asset_id,
            is_processed=True,
            processed_at=datetime.utcnow(),
            processing_notes=f"Asset created: {asset_id}"
        )
    )
    await self.db.execute(stmt)
```

#### 1.3 Fix Frontend Inventory Display
**File:** `/frontend/src/components/discovery/inventory/InventoryContent.tsx`
**Change Line 150:**
```typescript
// FROM:
enabled: !!client && !!engagement && !!flowId,

// TO:
enabled: !!client && !!engagement,  // Remove flowId requirement
```

**Add query parameter:**
```typescript
// Line 92: Make flowId optional in query
const response = await apiCall(
  `/unified-discovery/assets?page=1&page_size=100${
    flowId ? `&flow_id=${flowId}` : ''
  }`
);
```

---

### Phase 2: Standardization (Day 2)
**Goal:** Fix identifier confusion and ensure consistency

#### 2.1 Standardize Flow ID References
**Issue:** Confusion between `discovery_flows.id` vs `discovery_flows.flow_id`

**Action:** 
- Use `discovery_flows.id` (PK) for `assets.discovery_flow_id`
- Use `crewai_flow_state_extensions.flow_id` for `assets.master_flow_id`
- Document this clearly in code comments

#### 2.2 Persist Cleansed Data
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`
**Add:**
```python
# After cleansing completes, update raw_import_records
for record_id, cleansed_data in cleansed_records.items():
    await self._update_raw_import_cleansed_data(
        record_id, 
        cleansed_data
    )
```

#### 2.3 Store Field Mappings Used
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`
**Line 396: Add field mappings to asset_data:**
```python
asset_data = {
    "name": asset_name,
    "type": self._determine_asset_type(asset),
    "raw_import_record_id": asset.get("raw_import_record_id"),
    "field_mappings": self.state.field_mappings,  # NEW
    # ...
}
```

---

### Phase 3: Monitoring & Validation (Day 3)
**Goal:** Add visibility and ensure changes work

#### 3.1 Create Wiring Health Check Endpoint
**File:** `/backend/app/api/v1/endpoints/health/wiring_health.py`
```python
@router.get("/health/wiring")
async def check_wiring_health(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Check database wiring health"""
    
    # Check assets missing discovery_flow_id
    assets_missing_flow = await db.execute(
        select(count(Asset.id))
        .where(
            Asset.discovery_flow_id.is_(None),
            Asset.client_account_id == context.client_account_id
        )
    )
    
    # Check raw records missing asset_id
    raw_missing_asset = await db.execute(
        select(count(RawImportRecord.id))
        .where(
            RawImportRecord.asset_id.is_(None),
            RawImportRecord.is_processed == False
        )
    )
    
    # Check assets missing raw_import_records_id
    assets_missing_raw = await db.execute(
        select(count(Asset.id))
        .where(
            Asset.raw_import_records_id.is_(None),
            Asset.discovery_method == "flow_based"
        )
    )
    
    return {
        "assets_missing_discovery_flow_id": assets_missing_flow.scalar(),
        "raw_records_missing_asset_id": raw_missing_asset.scalar(),
        "assets_missing_raw_import_id": assets_missing_raw.scalar(),
        "health_status": "healthy" if all_zero else "unhealthy"
    }
```

#### 3.2 Add Integration Test
**File:** `/backend/tests/integration/test_discovery_flow_wiring.py`
```python
async def test_discovery_flow_creates_wired_assets():
    """Test that discovery flow properly wires all connections"""
    
    # 1. Create discovery flow
    # 2. Import data
    # 3. Run field mapping
    # 4. Run data cleansing
    # 5. Run asset inventory
    
    # Verify:
    # - Assets have discovery_flow_id
    # - Assets have master_flow_id
    # - Assets have raw_import_records_id
    # - Raw records have asset_id
    # - Raw records have cleansed_data
    # - Assets have field_mappings_used
```

---

### Phase 4: Data Migration (Day 4)
**Goal:** Fix existing data to match new wiring

#### 4.1 Backfill Script for Existing Assets
**File:** `/backend/scripts/backfill_asset_wiring.py`
```python
"""
Backfill missing connections for existing assets:
1. Link assets to their discovery flows based on flow_id
2. Infer raw_import_records connections
3. Set default field_mappings_used
"""
```

#### 4.2 Mark or Remove Seed Data
```sql
-- Mark seed data
UPDATE migration.assets 
SET custom_attributes = jsonb_set(
    COALESCE(custom_attributes, '{}'::jsonb),
    '{is_seed_data}',
    'true'
)
WHERE created_at::date = '2025-09-03';
```

---

### Phase 5: Enforce Single Path (Day 5)
**Goal:** Prevent future unwired assets

#### 5.1 Deprecate Direct AssetService.create_asset
**File:** `/backend/app/services/asset_service.py`
```python
async def create_asset(self, asset_data: Dict[str, Any]) -> Optional[Asset]:
    """
    DEPRECATED: Use AssetManager.create_assets_from_discovery instead
    """
    if not asset_data.get("discovery_flow_id"):
        logger.warning(
            "⚠️ Creating asset without discovery_flow_id - use AssetManager instead"
        )
        # Optionally: raise ValueError("Assets must be created through discovery flow")
```

#### 5.2 Add Database Constraints
```sql
-- Add check constraint (warning only initially)
ALTER TABLE migration.assets 
ADD CONSTRAINT check_discovery_flow_id 
CHECK (
    discovery_method != 'flow_based' 
    OR discovery_flow_id IS NOT NULL
) NOT VALID;
```

---

## Success Metrics

### Immediate (After Phase 1)
- [ ] Inventory page shows all assets without flowId
- [ ] New assets created have discovery_flow_id
- [ ] New assets created have master_flow_id

### Short-term (After Phase 3)
- [ ] Health check shows 0 unwired assets
- [ ] Integration test passes
- [ ] Raw import records have asset_id after processing

### Long-term (After Phase 5)
- [ ] No new unwired assets created
- [ ] All seed data marked or removed
- [ ] Single creation path enforced

---

## Risk Mitigation

### Low Risk Changes
1. Adding fields that are currently NULL (no data loss)
2. Frontend display fix (graceful degradation)
3. Health check endpoint (read-only)

### Medium Risk Changes
1. Updating raw_import_records (add transaction safety)
2. Backfilling existing data (test on staging first)

### High Risk Changes
1. Enforcing constraints (deploy as NOT VALID first)
2. Deprecating AssetService (provide migration period)

---

## Timeline

| Day | Phase | Risk | Impact |
|-----|-------|------|--------|
| 1 | Quick Wins | Low | High - Fixes display issue |
| 2 | Standardization | Low | Medium - Improves consistency |
| 3 | Monitoring | Low | High - Provides visibility |
| 4 | Data Migration | Medium | Medium - Fixes existing data |
| 5 | Enforcement | High | High - Prevents future issues |

---

## Conclusion

While GPT5 correctly identified that wiring code exists, my analysis shows it's not being executed in practice. This plan addresses both the missing implementation AND ensures the existing code actually runs. The phased approach minimizes risk while providing immediate user value (fixing the inventory display) and long-term system health (enforcing proper wiring).