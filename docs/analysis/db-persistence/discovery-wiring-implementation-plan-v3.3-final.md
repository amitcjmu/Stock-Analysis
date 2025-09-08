# Discovery Flow Wiring Implementation Plan v3.3 - Final Production Refinements
*Final corrections and safety measures before execution*

## Critical Corrections

### 1. Model Name Correction - MUST FIX
**Issue:** Model is `CrewAIFlowStateExtensions` (plural), not singular

```python
# WRONG
from app.models.crewai_flow_state_extension import CrewAIFlowStateExtension

# CORRECT
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
```

**File:** `/backend/app/repositories/discovery_flow_repository/commands/asset_commands.py`

```python
async def _get_master_flow_id(self, discovery_flow_id: uuid.UUID) -> Optional[uuid.UUID]:
    """Get master flow ID from discovery flow"""
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions  # PLURAL
    
    # Get discovery flow
    result = await self.db.execute(
        select(DiscoveryFlow.flow_id)
        .where(DiscoveryFlow.id == discovery_flow_id)
    )
    flow_id = result.scalar_one_or_none()
    
    if not flow_id:
        logger.warning(f"No flow_id found for discovery_flow_id: {discovery_flow_id}")
        return None
    
    # Get master flow ID from extension - table name is plural
    result = await self.db.execute(
        select(CrewAIFlowStateExtensions.flow_id)  # PLURAL
        .where(CrewAIFlowStateExtensions.flow_id == flow_id)  # PLURAL
    )
    master_flow_id = result.scalar_one_or_none()
    
    return master_flow_id
```

---

## SQLAlchemy 2.0 Style Corrections

### 2. Proper EXISTS Correlated Subquery
**File:** `/backend/app/api/v1/endpoints/health/wiring_health.py`

```python
from sqlalchemy import exists, select

# SQLAlchemy 2.0 strict style
assets_with_orphan_raw_ref = await db.execute(
    select(func.count(Asset.id))
    .where(
        *base_filter,
        Asset.raw_import_records_id.isnot(None),
        ~exists(
            select(1).where(
                RawImportRecord.id == Asset.raw_import_records_id,
                RawImportRecord.client_account_id == context.client_account_id
            )
        )
    )
)

raw_with_orphan_asset_ref = await db.execute(
    select(func.count(RawImportRecord.id))
    .where(
        RawImportRecord.client_account_id == context.client_account_id,
        RawImportRecord.engagement_id == context.engagement_id,
        RawImportRecord.asset_id.isnot(None),
        ~exists(
            select(1).where(
                Asset.id == RawImportRecord.asset_id,
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id
            )
        )
    )
)
```

---

## Production-Safe Index Creation

### 3. Concurrent Index Creation
**File:** `/backend/alembic/versions/[next]_add_wiring_performance_indexes.py`

```python
"""Add performance indexes for discovery wiring queries - CONCURRENT"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Must use autocommit for CONCURRENT index creation
    with op.get_context().autocommit_block():
        # Assets table indexes - CREATE CONCURRENTLY
        op.create_index(
            'idx_assets_tenant_discovery',
            'assets',
            ['client_account_id', 'engagement_id', 'discovery_method', 'discovery_flow_id'],
            schema='migration',
            postgresql_using='btree',
            postgresql_concurrently=True  # Non-blocking
        )
        
        op.create_index(
            'idx_assets_tenant_raw_import',
            'assets',
            ['client_account_id', 'engagement_id', 'raw_import_records_id'],
            schema='migration',
            postgresql_using='btree',
            postgresql_concurrently=True
        )
        
        # Raw import records indexes - CREATE CONCURRENTLY
        op.create_index(
            'idx_raw_import_tenant_processed',
            'raw_import_records',
            ['client_account_id', 'engagement_id', 'is_processed', 'asset_id'],
            schema='migration',
            postgresql_using='btree',
            postgresql_concurrently=True
        )
        
        op.create_index(
            'idx_raw_import_tenant_id',
            'raw_import_records',
            ['client_account_id', 'engagement_id', 'id'],
            schema='migration',
            postgresql_using='btree',
            postgresql_concurrently=True
        )
    
    print("✅ Indexes created concurrently without blocking writes")

def downgrade():
    # Drops are fast, no need for concurrent
    op.drop_index('idx_assets_tenant_discovery', schema='migration')
    op.drop_index('idx_assets_tenant_raw_import', schema='migration')
    op.drop_index('idx_raw_import_tenant_processed', schema='migration')
    op.drop_index('idx_raw_import_tenant_id', schema='migration')
```

---

## Backfill Safety

### 4. Prevent Overwriting Existing Links
**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

```python
# In batch update section
if update_data:
    # Batch update with VALUES - ONLY update if asset_id is NULL
    stmt = (
        update(RawImportRecord)
        .where(
            RawImportRecord.id == bindparam('rid'),
            RawImportRecord.asset_id.is_(None)  # Safety: Don't overwrite existing links
        )
        .values(
            asset_id=bindparam('aid'),
            is_processed=True,
            processed_at=datetime.utcnow(),
            processing_notes=bindparam('notes')
        )
    )
    result = await db.execute(stmt, update_data)
    
    # Log if some records were already linked
    if result.rowcount < len(update_data):
        logger.warning(
            f"Skipped {len(update_data) - result.rowcount} already-linked records"
        )

# Small batch: individual updates with same safety
for asset, asset_data in zip(created_assets, asset_data_list):
    if raw_id := asset_data.get("raw_import_record_id"):
        stmt = (
            update(RawImportRecord)
            .where(
                RawImportRecord.id == raw_id,
                RawImportRecord.asset_id.is_(None)  # Safety check
            )
            .values(
                asset_id=asset.id,
                is_processed=True,
                processed_at=datetime.utcnow(),
                processing_notes=f"Linked to: {asset.name}"
            )
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            logger.warning(f"Raw record {raw_id} already linked, skipping")
```

---

## Configurable Chunk Size

### 5. Environment-Based Configuration
**File:** `/backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Asset processing configuration
    ASSET_BATCH_CHUNK_SIZE: int = Field(
        default=500,
        ge=10,
        le=5000,
        description="Number of assets to process per transaction"
    )
    ASSET_CHUNK_RETRY_POLICY: str = Field(
        default="stop",
        regex="^(stop|skip|retry)$",
        description="Policy on chunk failure: stop, skip, or retry"
    )
    ASSET_CHUNK_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max retries per chunk if retry policy enabled"
    )
```

**File:** `/backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor.py`

```python
from app.core.config import get_settings

async def _persist_assets_to_database(self, results: Dict[str, Any]):
    """Persist assets with configurable chunking"""
    settings = get_settings()
    CHUNK_SIZE = settings.ASSET_BATCH_CHUNK_SIZE
    RETRY_POLICY = settings.ASSET_CHUNK_RETRY_POLICY
    MAX_RETRIES = settings.ASSET_CHUNK_MAX_RETRIES
    
    failed_chunks = []
    
    for i in range(0, len(asset_data_list), CHUNK_SIZE):
        chunk = asset_data_list[i:i + CHUNK_SIZE]
        chunk_num = i // CHUNK_SIZE + 1
        retries = 0
        
        while retries <= MAX_RETRIES:
            try:
                async with AsyncSessionLocal() as db:
                    async with db.begin():
                        # ... existing chunk processing logic ...
                        break  # Success, exit retry loop
                        
            except Exception as e:
                retries += 1
                if retries > MAX_RETRIES:
                    logger.error(f"❌ Chunk {chunk_num} failed after {MAX_RETRIES} retries: {e}")
                    
                    if RETRY_POLICY == "stop":
                        raise
                    elif RETRY_POLICY == "skip":
                        failed_chunks.append((chunk_num, i, i + len(chunk)))
                        break  # Skip to next chunk
                    # If "retry", loop continues
                else:
                    logger.warning(f"Chunk {chunk_num} retry {retries}/{MAX_RETRIES}")
                    await asyncio.sleep(retries * 2)  # Exponential backoff
    
    if failed_chunks:
        logger.error(f"Failed chunks for reprocessing: {failed_chunks}")
        # Could write to a reprocess queue or dead letter table
```

---

## Health Endpoint Optimization

### 6. TTL Cache for Health Checks
**File:** `/backend/app/api/v1/endpoints/health/wiring_health.py`

```python
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib

# Simple TTL cache for health metrics
_health_cache = {}
_cache_ttl = timedelta(seconds=30)  # 30 second cache

@router.get("/health/wiring")
async def check_wiring_health(
    detail: bool = False,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user = Depends(get_current_user)
):
    """Enhanced wiring health check with TTL cache"""
    
    # Cache key based on tenant + detail mode
    cache_key = hashlib.md5(
        f"{context.client_account_id}:{context.engagement_id}:{detail}".encode()
    ).hexdigest()
    
    # Check cache
    now = datetime.utcnow()
    if cache_key in _health_cache:
        cached_result, cached_time = _health_cache[cache_key]
        if now - cached_time < _cache_ttl:
            return {**cached_result, "cached": True, "cache_age_seconds": (now - cached_time).seconds}
    
    # ... existing health check logic ...
    
    result = {
        "metrics": issues,
        "health_status": "healthy" if all_healthy else "unhealthy",
        "tenant": {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id)
        },
        "samples": samples if detail else None,
        "cached": False
    }
    
    # Cache the result
    _health_cache[cache_key] = (result, now)
    
    # Cleanup old cache entries periodically
    if len(_health_cache) > 100:
        cutoff = now - _cache_ttl
        _health_cache = {
            k: v for k, v in _health_cache.items() 
            if v[1] > cutoff
        }
    
    return result
```

---

## API Response Metadata

### 7. Page Size Cap Indicator
**File:** `/backend/app/api/v1/endpoints/unified_discovery/assets.py`

```python
@router.get("/assets")
async def get_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    flow_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Get assets with pagination metadata"""
    
    MAX_PAGE_SIZE = 200
    requested_page_size = page_size
    actual_page_size = min(page_size, MAX_PAGE_SIZE)
    
    # ... existing query logic with actual_page_size ...
    
    # Build response with metadata
    response = {
        "data": assets,
        "pagination": {
            "page": page,
            "page_size": actual_page_size,
            "total": total_count,
            "total_pages": (total_count + actual_page_size - 1) // actual_page_size
        },
        "metadata": {
            "page_size_capped": requested_page_size > actual_page_size,
            "max_page_size": MAX_PAGE_SIZE
        }
    }
    
    if requested_page_size > actual_page_size:
        logger.info(
            f"Page size capped: requested={requested_page_size}, actual={actual_page_size}, "
            f"tenant={context.client_account_id}"
        )
    
    return response
```

---

## Comprehensive Testing

### 8. FK Constraint Test
**File:** `/backend/tests/integration/test_fk_constraints.py`

```python
async def test_fk_add_validate_workflow():
    """Test the FK constraint add and validate workflow"""
    
    async with AsyncSessionLocal() as db:
        # 1. Create orphaned asset (no discovery_flow_id)
        asset = Asset(
            client_account_id=test_client_id,
            engagement_id=test_engagement_id,
            name="Orphaned Asset",
            discovery_flow_id=None  # Orphaned
        )
        db.add(asset)
        await db.commit()
        
        # 2. Try to add FK constraint (should succeed with NOT VALID)
        await db.execute("""
            ALTER TABLE migration.assets 
            ADD CONSTRAINT test_fk_assets_discovery_flow 
            FOREIGN KEY (discovery_flow_id) 
            REFERENCES migration.discovery_flows(id)
            NOT VALID
        """)
        await db.commit()
        
        # 3. Verify we can still insert orphaned records
        asset2 = Asset(
            client_account_id=test_client_id,
            engagement_id=test_engagement_id,
            name="Another Orphan",
            discovery_flow_id=None
        )
        db.add(asset2)
        await db.commit()  # Should succeed
        
        # 4. Fix orphaned records
        flow = await create_test_discovery_flow(db)
        await db.execute(
            update(Asset)
            .where(Asset.discovery_flow_id.is_(None))
            .values(discovery_flow_id=flow.id)
        )
        await db.commit()
        
        # 5. Now validate constraint
        await db.execute("""
            ALTER TABLE migration.assets 
            VALIDATE CONSTRAINT test_fk_assets_discovery_flow
        """)
        await db.commit()
        
        # 6. Verify constraint now enforces
        with pytest.raises(IntegrityError):
            bad_asset = Asset(
                client_account_id=test_client_id,
                engagement_id=test_engagement_id,
                name="Bad Asset",
                discovery_flow_id=uuid.uuid4()  # Non-existent flow
            )
            db.add(bad_asset)
            await db.commit()
        
        # Cleanup
        await db.execute("""
            ALTER TABLE migration.assets 
            DROP CONSTRAINT test_fk_assets_discovery_flow
        """)
```

---

## Asset Type Consistency Verification

### 9. Upstream Validation Check
**File:** `/backend/scripts/verify_asset_type_consistency.py`

```python
#!/usr/bin/env python3
"""Verify asset_type is used consistently across codebase"""

import os
import re
from pathlib import Path

def check_asset_type_consistency():
    """Scan for any remaining 'type' field references in asset context"""
    
    backend_dir = Path(__file__).parent.parent
    
    # Patterns to find potential issues
    patterns = [
        (r'asset.*\["type"\]', "Dictionary access with 'type'"),
        (r'asset\.get\("type"', "get() with 'type'"),
        (r'"type":\s*asset', "JSON key 'type' for asset"),
        (r'asset_data\["type"\]', "asset_data with 'type'"),
    ]
    
    issues = []
    
    for py_file in backend_dir.rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue
            
        content = py_file.read_text()
        for pattern, description in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"{py_file}: {description}")
    
    if issues:
        print("⚠️ Found potential 'type' field usage (should be 'asset_type'):")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All asset references use 'asset_type' consistently")
        return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if check_asset_type_consistency() else 1)
```

---

## Summary Checklist

### Must Fix Before Execution:
- [ ] Change `CrewAIFlowStateExtension` → `CrewAIFlowStateExtensions` (plural)
- [ ] Use SQLAlchemy 2.0 style EXISTS with `select(1).where(...)`
- [ ] Add `asset_id IS NULL` check to prevent overwriting links
- [ ] Make chunk size configurable via environment settings

### Performance & Safety:
- [ ] Create indexes with `postgresql_concurrently=True`
- [ ] Add 30-second TTL cache to health endpoint
- [ ] Include metadata about page_size capping in API response
- [ ] Implement retry policy for chunk failures

### Testing:
- [ ] Test health endpoint with detail=true and tenant scoping
- [ ] Test FK constraint add/validate workflow
- [ ] Verify asset_type consistency across codebase

### Documentation:
- [ ] Document environment variables for chunk configuration
- [ ] Note that health endpoint may return cached results
- [ ] Explain page_size_capped metadata field for frontend

This completes all production refinements. The implementation is now ready for execution with all safety measures, performance optimizations, and consistency checks in place.