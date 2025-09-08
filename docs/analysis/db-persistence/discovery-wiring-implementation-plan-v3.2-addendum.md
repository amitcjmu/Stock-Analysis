# Discovery Flow Wiring Implementation Plan v3.2 - Production Refinements
*Final production-ready addendum incorporating GPT5's optimization recommendations*

## Query Optimizations

### 1. Health Check Query Optimization
**Replace IN subqueries with EXISTS for better index usage:**

```python
# /backend/app/api/v1/endpoints/health/wiring_health.py

# BEFORE: Using IN subquery
assets_with_orphan_raw_ref = await db.execute(
    select(func.count(Asset.id))
    .where(
        *base_filter,
        Asset.raw_import_records_id.isnot(None),
        ~Asset.raw_import_records_id.in_(
            select(RawImportRecord.id).where(
                RawImportRecord.client_account_id == context.client_account_id
            )
        )
    )
)

# AFTER: Using EXISTS for better performance
from sqlalchemy import exists

assets_with_orphan_raw_ref = await db.execute(
    select(func.count(Asset.id))
    .where(
        *base_filter,
        Asset.raw_import_records_id.isnot(None),
        ~exists().where(
            RawImportRecord.id == Asset.raw_import_records_id,
            RawImportRecord.client_account_id == context.client_account_id
        )
    )
)

# Similar optimization for raw_with_orphan_asset_ref query
raw_with_orphan_asset_ref = await db.execute(
    select(func.count(RawImportRecord.id))
    .where(
        RawImportRecord.client_account_id == context.client_account_id,
        RawImportRecord.engagement_id == context.engagement_id,
        RawImportRecord.asset_id.isnot(None),
        ~exists().where(
            Asset.id == RawImportRecord.asset_id,
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id
        )
    )
)
```

---

## Database Indexes

### 2. Add Composite Indexes for Performance
**File:** `/backend/alembic/versions/[next]_add_wiring_performance_indexes.py`

```python
"""Add performance indexes for discovery wiring queries"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Assets table indexes
    op.create_index(
        'idx_assets_tenant_discovery',
        'assets',
        ['client_account_id', 'engagement_id', 'discovery_method', 'discovery_flow_id'],
        schema='migration',
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_assets_tenant_raw_import',
        'assets',
        ['client_account_id', 'engagement_id', 'raw_import_records_id'],
        schema='migration',
        postgresql_using='btree'
    )
    
    # Raw import records indexes
    op.create_index(
        'idx_raw_import_tenant_processed',
        'raw_import_records',
        ['client_account_id', 'engagement_id', 'is_processed', 'asset_id'],
        schema='migration',
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_raw_import_tenant_id',
        'raw_import_records',
        ['client_account_id', 'engagement_id', 'id'],
        schema='migration',
        postgresql_using='btree'
    )

def downgrade():
    op.drop_index('idx_assets_tenant_discovery', schema='migration')
    op.drop_index('idx_assets_tenant_raw_import', schema='migration')
    op.drop_index('idx_raw_import_tenant_processed', schema='migration')
    op.drop_index('idx_raw_import_tenant_id', schema='migration')
```

---

## API Enforcement

### 3. Backend Page Size Enforcement
**File:** `/backend/app/api/v1/endpoints/unified_discovery/assets.py`

```python
from fastapi import Query

@router.get("/assets")
async def get_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),  # Enforce max 200
    flow_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Get assets with enforced pagination limits"""
    
    # Additional safety check
    MAX_PAGE_SIZE = 200
    actual_page_size = min(page_size, MAX_PAGE_SIZE)
    
    # Log if limit was enforced
    if page_size > actual_page_size:
        logger.warning(f"Page size {page_size} exceeded max, capped at {MAX_PAGE_SIZE}")
```

---

## Transaction Management

### 4. Chunked Transactions for Large Imports
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

```python
async def _persist_assets_to_database(self, results: Dict[str, Any]):
    """Persist assets with chunked transactions for scale"""
    from app.core.database import AsyncSessionLocal
    
    CHUNK_SIZE = 500  # Configurable based on your DB capacity
    
    asset_data_list = results.get('discovered_assets', [])
    total_created = 0
    
    # Process in chunks to avoid long-lived transactions
    for i in range(0, len(asset_data_list), CHUNK_SIZE):
        chunk = asset_data_list[i:i + CHUNK_SIZE]
        
        async with AsyncSessionLocal() as db:
            async with db.begin():  # Each chunk in its own transaction
                try:
                    # Same logic as before but for this chunk
                    created_assets = await asset_manager.create_assets_from_discovery_no_commit(
                        discovery_flow_id=discovery_flow_id,
                        asset_data_list=chunk
                    )
                    
                    # Batch update raw records for this chunk
                    if len(created_assets) > 10:
                        # ... batch update logic ...
                    else:
                        # ... individual update logic ...
                    
                    total_created += len(created_assets)
                    logger.info(f"✅ Chunk {i//CHUNK_SIZE + 1}: Created {len(created_assets)} assets")
                    
                except Exception as e:
                    logger.error(f"❌ Chunk {i//CHUNK_SIZE + 1} failed: {e}")
                    # Continue with next chunk or raise based on policy
                    raise
    
    logger.info(f"✅ Total: Created {total_created} assets across all chunks")
```

---

## Code Consistency Fixes

### 5. Asset Commands Helper Method
**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`

```python
async def _get_master_flow_id(self, discovery_flow_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Get master flow ID from discovery flow"""
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.crewai_flow_state_extension import CrewAIFlowStateExtension
    
    # Get discovery flow
    result = await self.db.execute(
        select(DiscoveryFlow.flow_id)
        .where(DiscoveryFlow.id == discovery_flow_id)
    )
    flow_id = result.scalar_one_or_none()
    
    if not flow_id:
        logger.warning(f"No flow_id found for discovery_flow_id: {discovery_flow_id}")
        return None
    
    # Get master flow ID from extension
    result = await self.db.execute(
        select(CrewAIFlowStateExtension.flow_id)
        .where(CrewAIFlowStateExtension.flow_id == flow_id)
    )
    master_flow_id = result.scalar_one_or_none()
    
    return master_flow_id
```

### 6. Consistent Field Naming
**Update all occurrences to use `asset_type` consistently:**

```python
# Line 396 in asset_inventory_executor.py
asset_data = {
    "name": asset_name,
    "asset_type": self._determine_asset_type(asset),  # NOT "type"
    "raw_import_record_id": asset.get("raw_import_record_id"),
    "field_mappings": self.state.field_mappings,
    "mappings_version_id": self.state.mappings_version_id if hasattr(self.state, 'mappings_version_id') else None
}

# In asset_commands.py
asset = Asset(
    # ...
    asset_type=asset_data.get("asset_type"),  # Consistent naming
    # ...
)
```

### 7. Import Statements
**Add missing imports where needed:**

```python
# In all files using datetime
from datetime import datetime

# In health check endpoint
from sqlalchemy import exists, select, func, and_
from app.core.security import get_current_user
```

---

## Testing Suite

### 8. Health Endpoint Test
**File:** `/backend/tests/api/test_wiring_health.py`

```python
async def test_health_endpoint_shape_and_scoping():
    """Test health endpoint returns correct shape and respects tenant scoping"""
    
    # Setup test data
    test_client_id = uuid.uuid4()
    test_engagement_id = uuid.uuid4()
    
    # Create assets in different tenants
    await create_test_asset(client_id=test_client_id, engagement_id=test_engagement_id)
    await create_test_asset(client_id=uuid.uuid4(), engagement_id=uuid.uuid4())  # Different tenant
    
    # Test basic response
    response = await client.get(
        "/api/v1/health/wiring",
        headers={"X-Client-Account-Id": str(test_client_id), "X-Engagement-Id": str(test_engagement_id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify shape
    assert "health_status" in data
    assert "metrics" in data
    assert "tenant" in data
    
    # Verify tenant scoping
    assert data["tenant"]["client_account_id"] == str(test_client_id)
    assert data["tenant"]["engagement_id"] == str(test_engagement_id)
    
    # Test detail mode
    response = await client.get(
        "/api/v1/health/wiring?detail=true",
        headers={"X-Client-Account-Id": str(test_client_id), "X-Engagement-Id": str(test_engagement_id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
```

### 9. Bidirectional Link Test
**File:** `/backend/tests/integration/test_asset_raw_linkage.py`

```python
async def test_bidirectional_linkage_in_transaction():
    """Test both sides of the asset-raw linkage in single transaction"""
    
    async with AsyncSessionLocal() as db:
        async with db.begin():
            # Create raw record
            raw_record = RawImportRecord(
                client_account_id=test_client_id,
                engagement_id=test_engagement_id,
                raw_data={"test": "data"}
            )
            db.add(raw_record)
            await db.flush()
            
            # Create asset with linkage
            asset_data = [{
                "name": "Test Asset",
                "asset_type": "SERVER",
                "raw_import_record_id": raw_record.id
            }]
            
            assets = await asset_commands.create_assets_from_discovery_no_commit(
                discovery_flow_id=test_flow_id,
                asset_data_list=asset_data
            )
            
            # Update raw record
            stmt = (
                update(RawImportRecord)
                .where(RawImportRecord.id == raw_record.id)
                .values(asset_id=assets[0].id, is_processed=True)
            )
            await db.execute(stmt)
            
            # Verify both directions IN SAME TRANSACTION
            await db.refresh(assets[0])
            await db.refresh(raw_record)
            
            assert assets[0].raw_import_records_id == raw_record.id
            assert raw_record.asset_id == assets[0].id
            assert raw_record.is_processed == True
```

---

## Migration Rollback Script

### 10. Fast Rollback Script
**File:** `/backend/scripts/rollback_wiring_constraints.py`

```python
#!/usr/bin/env python3
"""Fast rollback script for wiring constraints if issues arise"""

import asyncio
from app.core.database import AsyncSessionLocal

async def rollback_constraints():
    """Remove FK constraints quickly if needed"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Disable validation first (fast)
            await db.execute("""
                ALTER TABLE migration.assets 
                ALTER CONSTRAINT fk_assets_discovery_flow NOT VALID
            """)
            
            # Drop constraint (fast)
            await db.execute("""
                ALTER TABLE migration.assets 
                DROP CONSTRAINT IF EXISTS fk_assets_discovery_flow
            """)
            
            await db.commit()
            print("✅ Constraints rolled back successfully")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Rollback failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(rollback_constraints())
```

---

## Summary of Critical Changes

1. **Query Performance**: Replace IN with EXISTS for orphan checks
2. **Database Indexes**: Add 4 composite indexes for tenant-scoped queries
3. **API Limits**: Enforce max page_size=200 at backend level
4. **Transaction Chunking**: Process large imports in 500-record chunks
5. **Missing Helper**: Add `_get_master_flow_id()` method
6. **Field Consistency**: Use `asset_type` everywhere, not `type`
7. **Import Fixes**: Add datetime and exists imports
8. **Test Coverage**: Add health endpoint and bidirectional link tests
9. **Fast Rollback**: Script ready for quick constraint removal

These refinements ensure the v3.1 plan scales efficiently under production load while maintaining data integrity and providing quick rollback options.