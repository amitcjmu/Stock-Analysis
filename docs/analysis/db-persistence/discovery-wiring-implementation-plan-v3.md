# Discovery Flow Wiring Implementation Plan v3
*Final version incorporating GPT5's feedback and critical analysis*

## Executive Summary
The root cause is **transaction isolation from separate sessions**. The linkage code exists but uses `AsyncSessionLocal()` creating a new session, causing changes to be invisible to the main transaction. This plan fixes the session management while adding missing fields and monitoring.

---

## Critical Analysis of GPT5's Feedback

### What I Agree With ✅
1. **Transaction design using `async with db.begin()`** - Cleaner than manual commit/rollback
2. **Leave existing methods intact** - Add no-commit variants to avoid breaking changes
3. **Compact field mapping storage** - Store hash/reference instead of full JSON blob
4. **Schema verification** - All tables confirmed in `migration` schema, FKs are safe
5. **Health endpoint auth** - Should require authentication
6. **Batch updates for performance** - Important for large volumes

### What I Disagree With / Need Clarification ⚠️
1. **"self.db doesn't exist"** - Need to verify cleansing executor structure
2. **Session propagation everywhere** - May be overkill for read operations
3. **Partial unique index** - Could cause issues with legitimate duplicates

### My Additional Insights 💡
1. **Why only 29 seed assets** - They predate ALL the wiring code
2. **Frontend fix is critical** - Users can't see any assets currently
3. **Monitoring before changes** - Establish baseline metrics first

---

## Final Implementation Plan

### Phase 0: Establish Baseline (Day 0 - IMMEDIATE)
**Goal:** Know exactly what's broken before fixing

#### 0.1 Deploy Health Check First
```python
# /backend/app/api/v1/endpoints/health/wiring_health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.context import RequestContext, get_request_context
from app.core.security import require_admin_or_tenant_user
from app.models.asset import Asset
from app.models.data_import.core import RawImportRecord

router = APIRouter()

@router.get("/health/wiring")
@require_admin_or_tenant_user  # GPT5's auth suggestion
async def check_wiring_health(
    detail: bool = False,  # GPT5's drilldown suggestion
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Baseline wiring health check with optional detail"""
    
    # All queries tenant-scoped as GPT5 emphasized
    base_filter = [
        Asset.client_account_id == context.client_account_id,
        Asset.engagement_id == context.engagement_id
    ]
    
    # Count issues
    missing_discovery_flow = await db.execute(
        select(func.count(Asset.id))
        .where(*base_filter, Asset.discovery_flow_id.is_(None))
    )
    
    missing_master_flow = await db.execute(
        select(func.count(Asset.id))
        .where(*base_filter, Asset.master_flow_id.is_(None))
    )
    
    # Use == False not is False (GPT5's SQLAlchemy note)
    unprocessed_raw = await db.execute(
        select(func.count(RawImportRecord.id))
        .where(
            RawImportRecord.client_account_id == context.client_account_id,
            RawImportRecord.engagement_id == context.engagement_id,
            RawImportRecord.is_processed == False,
            RawImportRecord.asset_id.is_(None)
        )
    )
    
    issues = {
        "assets_missing_discovery_flow_id": missing_discovery_flow.scalar() or 0,
        "assets_missing_master_flow_id": missing_master_flow.scalar() or 0,
        "raw_records_unprocessed_no_asset": unprocessed_raw.scalar() or 0
    }
    
    # GPT5's detail mode for triage
    if detail and any(issues.values()):
        sample_ids = {}
        if issues["assets_missing_discovery_flow_id"] > 0:
            samples = await db.execute(
                select(Asset.id).where(*base_filter, Asset.discovery_flow_id.is_(None)).limit(5)
            )
            sample_ids["sample_assets_missing_flow"] = [str(r[0]) for r in samples]
    else:
        sample_ids = None
    
    all_healthy = all(v == 0 for v in issues.values())
    
    return {
        **issues,
        "health_status": "healthy" if all_healthy else "unhealthy",
        "tenant": {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id)
        },
        "samples": sample_ids
    }
```

---

### Phase 1: Fix Transaction Boundaries (Priority 1)
**Goal:** Make existing linkage code work with proper session management

#### 1.1 Add No-Commit Variant (GPT5's suggestion to avoid breaking changes)
**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`

```python
# Add new method, keep existing one intact
async def create_assets_from_discovery_no_commit(
    self,
    discovery_flow_id: uuid.UUID,
    asset_data_list: List[Dict[str, Any]],
    discovered_in_phase: str = "inventory",
) -> List[Asset]:
    """
    Create assets without committing - for transaction control.
    Same as create_assets_from_discovery but no commit.
    """
    created_assets = []
    
    # Get master_flow_id (existing code)
    master_flow_id = await self._get_master_flow_id(discovery_flow_id)
    
    for asset_data in asset_data_list:
        # NEW: Add missing fields per GPT5 and my analysis
        asset = Asset(
            # ... existing fields ...
            discovery_flow_id=discovery_flow_id,
            master_flow_id=master_flow_id,
            raw_import_records_id=asset_data.get("raw_import_record_id"),  # NEW
            field_mappings_used=asset_data.get("field_mappings_hash"),  # NEW: Use hash per GPT5
            source_phase=discovered_in_phase,  # NEW: Track provenance
            current_phase=discovered_in_phase,  # NEW: Lifecycle tracking
            # ...
        )
        self.db.add(asset)
        created_assets.append(asset)
    
    # NO COMMIT HERE - caller handles transaction
    if created_assets:
        await self.db.flush()  # Get IDs but don't commit
        for asset in created_assets:
            await self.db.refresh(asset)
    
    return created_assets
```

#### 1.2 Fix Session Management with db.begin() (GPT5's cleaner approach)
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

```python
async def _persist_assets_to_database(self, results: Dict[str, Any]):
    """Persist assets atomically using db.begin() per GPT5"""
    from app.core.database import AsyncSessionLocal
    from app.models.data_import.core import RawImportRecord
    from sqlalchemy import update
    import hashlib
    import json
    
    # Use db.begin() for automatic rollback on exception (GPT5's suggestion)
    async with AsyncSessionLocal() as db:
        async with db.begin():  # Automatic commit/rollback
            try:
                # Prepare field mappings hash (GPT5's compact storage)
                field_mappings = getattr(self.state, 'field_mappings', {})
                mappings_hash = hashlib.md5(
                    json.dumps(field_mappings, sort_keys=True).encode()
                ).hexdigest()
                
                # Add hash to all asset data
                for asset_data in asset_data_list:
                    asset_data['field_mappings_hash'] = mappings_hash
                
                # 1. Create assets without commit
                created_assets = await asset_manager.create_assets_from_discovery_no_commit(
                    discovery_flow_id=discovery_flow_id,
                    asset_data_list=asset_data_list
                )
                
                # 2. Link raw records in same transaction
                for asset, asset_data in zip(created_assets, asset_data_list):
                    raw_record_id = asset_data.get("raw_import_record_id")
                    if raw_record_id:
                        stmt = (
                            update(RawImportRecord)
                            .where(RawImportRecord.id == raw_record_id)
                            .values(
                                asset_id=asset.id,
                                is_processed=True,
                                processed_at=datetime.utcnow(),
                                processing_notes=f"Linked to asset: {asset.name}"
                            )
                        )
                        await db.execute(stmt)
                
                # Transaction commits automatically on context exit
                logger.info(f"✅ Atomically created {len(created_assets)} assets with linkages")
                
            except Exception as e:
                # Transaction rolls back automatically
                logger.error(f"❌ Asset persistence failed, rolled back: {e}")
                raise
```

---

### Phase 2: Frontend Fix (Priority 2 - Immediate User Value)
**Goal:** Users can see assets immediately

#### 2.1 Make FlowId Optional with Toggle (GPT5's refinement)
**File:** `/frontend/src/components/discovery/inventory/InventoryContent.tsx`

```typescript
// Add state for view mode
const [viewMode, setViewMode] = useState<'all' | 'flow'>('all');

// Line 150: Enable query regardless of flowId
enabled: !!client && !!engagement,

// Line 92: Conditional API call based on mode
const response = await apiCall(
  `/unified-discovery/assets?page=1&page_size=100${
    viewMode === 'flow' && flowId ? `&flow_id=${flowId}` : ''
  }`
);

// Add toggle UI
<ToggleGroup value={viewMode} onValueChange={setViewMode}>
  <ToggleGroupItem value="all">All Assets</ToggleGroupItem>
  <ToggleGroupItem value="flow" disabled={!flowId}>Current Flow Only</ToggleGroupItem>
</ToggleGroup>
```

---

### Phase 3: Persist Cleansed Data (Priority 3)
**Goal:** Complete audit trail

#### 3.1 Fix Cleansing Executor Session (GPT5's note about self.db)
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`

```python
# Pass session from orchestrator like inventory does
async def execute_with_session(self, crew_input: Dict[str, Any], db: AsyncSession):
    """Execute with passed session for consistency"""
    
    # ... crew execution ...
    
    # Persist cleansed data with passed session
    from app.models.data_import.core import RawImportRecord
    from sqlalchemy import update
    
    for record_id, cleansed_data in results.get('cleansed_records', {}).items():
        stmt = (
            update(RawImportRecord)
            .where(RawImportRecord.id == record_id)
            .values(cleansed_data=cleansed_data)
            # Don't set is_processed here - wait for asset creation
        )
        await db.execute(stmt)
    
    # No commit - let orchestrator handle
    return results
```

---

### Phase 4: Add Integration Test (Priority 4)
**Goal:** Prevent regression

#### 4.1 End-to-End Wiring Test
**File:** `/backend/tests/integration/test_discovery_wiring.py`

```python
async def test_discovery_flow_atomic_wiring():
    """Test atomic transaction for asset creation and linkage"""
    
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # 1. Create test discovery flow
            flow = await create_test_discovery_flow(db)
            
            # 2. Create raw import records
            raw_records = await create_test_raw_records(db, flow.id)
            
            # 3. Execute asset creation with linkage
            asset_manager = AssetManager(db, test_context)
            assets = await asset_manager.create_assets_from_discovery_no_commit(
                discovery_flow_id=flow.id,
                asset_data_list=[
                    {"name": "test", "raw_import_record_id": raw_records[0].id}
                ]
            )
            
            # 4. Verify in same transaction
            assert assets[0].discovery_flow_id == flow.id
            assert assets[0].master_flow_id is not None
            assert assets[0].raw_import_records_id == raw_records[0].id
            
            # 5. Verify linkage
            await db.refresh(raw_records[0])
            assert raw_records[0].asset_id == assets[0].id
            assert raw_records[0].is_processed == True
            
            # Rollback test transaction
            raise Exception("Test rollback")
```

---

### Phase 5: Backfill & Constraints (Priority 5)
**Goal:** Fix existing data and prevent future issues

#### 5.1 Backfill Script
**File:** `/backend/scripts/backfill_discovery_wiring.py`

```python
"""Backfill missing connections with safety checks"""

async def backfill_discovery_flow_ids():
    """Link orphaned assets to their discovery flows"""
    
    # Start with NOT VALID constraint per GPT5
    await db.execute("""
        ALTER TABLE migration.assets 
        ADD CONSTRAINT fk_assets_discovery_flow 
        FOREIGN KEY (discovery_flow_id) 
        REFERENCES migration.discovery_flows(id)
        NOT VALID;
    """)
    
    # Backfill where flow_id exists but discovery_flow_id doesn't
    await db.execute("""
        UPDATE migration.assets a
        SET discovery_flow_id = df.id
        FROM migration.discovery_flows df
        WHERE a.flow_id = df.flow_id
        AND a.discovery_flow_id IS NULL;
    """)
    
    # Validate constraint after backfill
    await db.execute("""
        ALTER TABLE migration.assets 
        VALIDATE CONSTRAINT fk_assets_discovery_flow;
    """)
```

---

## Success Metrics & Timeline

### Immediate Success (Day 0-1)
- [ ] Health endpoint shows current state
- [ ] Frontend shows all 29 assets
- [ ] No new unwired assets created

### Short-term Success (Day 2-3)
- [ ] Integration test passes
- [ ] Cleansed data persisted
- [ ] New assets have all linkages

### Long-term Success (Day 4-5)
- [ ] Backfill completes
- [ ] FK constraints validate
- [ ] Zero unwired assets in health check

---

## Risk Mitigation

### What We're NOT Doing (Per GPT5)
- ❌ Not moving commits into repository layer
- ❌ Not duplicating linkage logic
- ❌ Not breaking existing callers
- ❌ Not adding FKs before backfill

### What We ARE Doing
- ✅ Using `async with db.begin()` for atomicity
- ✅ Adding no-commit variants alongside existing methods
- ✅ Storing compact field mapping hashes
- ✅ Adding auth to health endpoints
- ✅ Using `== False` not `is False` in SQLAlchemy

---

## Conclusion

This plan addresses the real root cause (session isolation) while incorporating GPT5's refinements:
1. **Cleaner transactions** with `db.begin()`
2. **Non-breaking changes** with no-commit variants
3. **Compact storage** for field mappings
4. **Proper auth** on health endpoints
5. **Safe rollout** with NOT VALID constraints

The phased approach delivers immediate user value (frontend fix) while systematically fixing the underlying wiring issues.