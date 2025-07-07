# Discovery Flow Data Integrity Fix Implementation Plan

## Overview

This document provides a step-by-step implementation plan to fix the critical data integrity issues identified in the discovery flow data architecture analysis.

## Critical Issues Summary

1. **Missing Foreign Keys**: `data_imports.master_flow_id` and `raw_import_records.master_flow_id` are ALL NULL
2. **Broken Relationships**: No proper linkage between data imports and discovery flows
3. **Orphaned Data**: Records exist in isolation without proper flow orchestration tracking
4. **Process Gaps**: Flow creation doesn't establish required relationships

## Fix Implementation Plan

### Phase 1: Database Schema Fixes (2-3 days)

#### 1.1 Fix Foreign Key References

**Problem**: Foreign keys reference `crewai_flow_state_extensions.id` instead of `crewai_flow_state_extensions.flow_id`

**Files to Update**:
- `backend/app/models/data_import/core.py`
- `backend/app/models/discovery_flow.py`

**Changes Required**:

```python
# File: backend/app/models/data_import/core.py

class DataImport(Base):
    # BEFORE: 
    # master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.id", ondelete="CASCADE"), nullable=True)
    
    # AFTER:
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="CASCADE"), nullable=True)
    
    # ADD: Relationship mapping
    master_flow = relationship("CrewAIFlowStateExtensions", foreign_keys=[master_flow_id])

class RawImportRecord(Base):
    # BEFORE:
    # master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.id"), nullable=True)
    
    # AFTER:
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.flow_id"), nullable=True)
    
    # ADD: Relationship mapping
    master_flow = relationship("CrewAIFlowStateExtensions", foreign_keys=[master_flow_id])
```

```python
# File: backend/app/models/discovery_flow.py

class DiscoveryFlow(Base):
    # BEFORE:
    # master_flow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # AFTER: Make it required and properly linked
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("crewai_flow_state_extensions.flow_id"), nullable=False, index=True)
    
    # ADD: Relationship mapping
    master_flow = relationship("CrewAIFlowStateExtensions", foreign_keys=[master_flow_id])
```

#### 1.2 Create Database Migration

**File**: `backend/alembic/versions/YYYYMMDD_fix_master_flow_relationships.py`

```python
"""Fix master flow relationships

Revision ID: fix_master_flow_fk
Revises: [previous_revision]
Create Date: [current_date]
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'fix_master_flow_fk'
down_revision = '[previous_revision]'
branch_labels = None
depends_on = None

def upgrade():
    # Drop existing foreign key constraints
    op.drop_constraint('data_imports_master_flow_id_fkey', 'data_imports', type_='foreignkey')
    op.drop_constraint('raw_import_records_master_flow_id_fkey', 'raw_import_records', type_='foreignkey')
    
    # Add corrected foreign key constraints
    op.create_foreign_key(
        'data_imports_master_flow_id_fkey',
        'data_imports', 'crewai_flow_state_extensions',
        ['master_flow_id'], ['flow_id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'raw_import_records_master_flow_id_fkey', 
        'raw_import_records', 'crewai_flow_state_extensions',
        ['master_flow_id'], ['flow_id']
    )
    
    # Make discovery_flows.master_flow_id required
    op.alter_column('discovery_flows', 'master_flow_id', nullable=False)
    op.create_foreign_key(
        'discovery_flows_master_flow_id_fkey',
        'discovery_flows', 'crewai_flow_state_extensions', 
        ['master_flow_id'], ['flow_id']
    )

def downgrade():
    # Reverse the changes
    op.drop_constraint('discovery_flows_master_flow_id_fkey', 'discovery_flows', type_='foreignkey')
    op.alter_column('discovery_flows', 'master_flow_id', nullable=True)
    
    op.drop_constraint('raw_import_records_master_flow_id_fkey', 'raw_import_records', type_='foreignkey') 
    op.drop_constraint('data_imports_master_flow_id_fkey', 'data_imports', type_='foreignkey')
    
    # Restore original constraints (pointing to .id instead of .flow_id)
    op.create_foreign_key(
        'data_imports_master_flow_id_fkey',
        'data_imports', 'crewai_flow_state_extensions',
        ['master_flow_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'raw_import_records_master_flow_id_fkey',
        'raw_import_records', 'crewai_flow_state_extensions', 
        ['master_flow_id'], ['id']
    )
```

### Phase 2: Process Flow Fixes (3-5 days)

#### 2.1 Fix Data Import Handler

**File**: `backend/app/api/v1/endpoints/data_import/handlers/import_storage_handler.py`

**Function**: `_trigger_discovery_flow`

**Current Problem**: Creates master flow but doesn't link data import back to it.

**Fix**:

```python
async def _trigger_discovery_flow(
    data_import_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    file_data: List[Dict[str, Any]],
    context: RequestContext
) -> Optional[str]:
    """
    Trigger Discovery Flow through MasterFlowOrchestrator with proper data linking.
    
    FIXED: Now properly links DataImport and RawImportRecord to master flow.
    """
    try:
        logger.info(f"🚀 Triggering Discovery Flow via MasterFlowOrchestrator for import {data_import_id}")
        
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        from app.core.database import AsyncSessionLocal
        from app.models.data_import.core import DataImport, RawImportRecord
        from sqlalchemy import update
        import uuid as uuid_module
        
        async with AsyncSessionLocal() as db:
            # Initialize Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(db, context)
            
            # Create flow through orchestrator
            flow_result = await orchestrator.create_flow(
                flow_type="discovery",
                flow_name=f"Discovery Import {data_import_id}",
                configuration={
                    "source": "data_import",
                    "import_id": data_import_id,
                    "filename": f"import_{data_import_id}",
                    "import_timestamp": datetime.utcnow().isoformat()
                },
                initial_state={
                    "raw_data": file_data,
                    "data_import_id": data_import_id
                }
            )
            
            # Extract flow_id from result tuple
            if isinstance(flow_result, tuple) and len(flow_result) >= 1:
                flow_id = flow_result[0]
                flow_uuid = uuid_module.UUID(flow_id)
                data_import_uuid = uuid_module.UUID(data_import_id)
                
                logger.info(f"✅ Discovery flow created: {flow_id}")
                
                # CRITICAL FIX: Link data import to master flow
                logger.info(f"🔗 Linking DataImport {data_import_id} to master flow {flow_id}")
                
                # Update data import with master flow ID
                await db.execute(
                    update(DataImport)
                    .where(DataImport.id == data_import_uuid)
                    .values(master_flow_id=flow_uuid)
                )
                
                # Update all raw import records with master flow ID
                logger.info(f"🔗 Linking RawImportRecords to master flow {flow_id}")
                result = await db.execute(
                    update(RawImportRecord)
                    .where(RawImportRecord.data_import_id == data_import_uuid)
                    .values(master_flow_id=flow_uuid)
                )
                
                logger.info(f"🔗 Updated {result.rowcount} raw import records with master flow ID")
                
                # Commit the linking updates
                await db.commit()
                
                logger.info(f"✅ Successfully linked data import and records to master flow {flow_id}")
                return flow_id
            else:
                logger.error(f"❌ Unexpected flow creation result: {flow_result}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Discovery Flow trigger failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None
```

#### 2.2 Fix Master Flow Orchestrator Discovery Flow Creation

**File**: `backend/app/services/master_flow_orchestrator.py`

**Function**: `create_flow` (discovery flow section)

**Current Problem**: Creates CrewAI flow but doesn't ensure DiscoveryFlow record is properly linked.

**Fix**: Update the discovery flow creation section around line 177:

```python
# In create_flow method, discovery flow section (around line 176)
if flow_type == "discovery":
    logger.info(f"🚀 [FIX] Kicking off CrewAI Discovery Flow for {flow_id}")
    
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
        
        # Create CrewAI service
        crewai_service = CrewAIFlowService(self.db)
        
        # Prepare raw data from initial state
        raw_data = initial_state.get("raw_data", []) if initial_state else []
        
        # Create the UnifiedDiscoveryFlow instance
        # CRITICAL: Pass master_flow_id to ensure proper linking
        flow_metadata = configuration or {}
        flow_metadata['master_flow_id'] = flow_id
        
        discovery_flow = create_unified_discovery_flow(
            flow_id=flow_id,
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            user_id=self.context.user_id or "system",
            raw_data=raw_data,
            metadata=flow_metadata,
            crewai_service=crewai_service,
            context=self.context,
            master_flow_id=flow_id  # ADD: Pass master flow ID for linking
        )
        
        # Rest of the discovery flow logic...
        
    except Exception as e:
        logger.error(f"❌ [FIX] Failed to start CrewAI Discovery Flow: {e}")
```

#### 2.3 Update UnifiedDiscoveryFlow Creation

**File**: `backend/app/services/crewai_flows/unified_discovery_flow.py`

**Function**: `create_unified_discovery_flow`

**Fix**: Ensure DiscoveryFlow record is created with proper master_flow_id:

```python
def create_unified_discovery_flow(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    raw_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    crewai_service,
    context: RequestContext,
    master_flow_id: Optional[str] = None  # ADD: Accept master flow ID
) -> UnifiedDiscoveryFlow:
    """Create UnifiedDiscoveryFlow with proper master flow linking."""
    
    # Ensure master_flow_id is set (should be same as flow_id for discovery flows)
    if not master_flow_id:
        master_flow_id = flow_id
    
    # When creating DiscoveryFlow record, ensure master_flow_id is set
    # This should happen in the flow initialization or data_import_phase
    
    return UnifiedDiscoveryFlow(
        # ... existing parameters
        master_flow_id=master_flow_id  # ADD: Pass through for later use
    )
```

### Phase 3: Data Migration Fixes (2-3 days)

#### 3.1 Backfill Missing Relationships

**File**: `backend/scripts/fix_orphaned_data_imports.py`

```python
#!/usr/bin/env python3
"""
Fix orphaned data imports by linking them to existing master flows.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_
from app.core.database import AsyncSessionLocal
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

async def fix_orphaned_data_imports():
    """Fix orphaned data imports by linking to master flows."""
    
    async with AsyncSessionLocal() as db:
        # Find data imports without master flow ID
        orphaned_imports = await db.execute(
            select(DataImport).where(DataImport.master_flow_id.is_(None))
        )
        
        orphaned_count = 0
        fixed_count = 0
        
        for data_import in orphaned_imports.scalars():
            orphaned_count += 1
            
            # Try to find matching master flow created around same time
            time_window = timedelta(hours=2)  # 2-hour window
            
            matching_flows = await db.execute(
                select(CrewAIFlowStateExtensions).where(
                    and_(
                        CrewAIFlowStateExtensions.flow_type == "discovery",
                        CrewAIFlowStateExtensions.client_account_id == data_import.client_account_id,
                        CrewAIFlowStateExtensions.engagement_id == data_import.engagement_id,
                        CrewAIFlowStateExtensions.created_at >= data_import.created_at - time_window,
                        CrewAIFlowStateExtensions.created_at <= data_import.created_at + time_window
                    )
                ).order_by(
                    # Find closest by time
                    (CrewAIFlowStateExtensions.created_at - data_import.created_at).abs()
                ).limit(1)
            )
            
            matching_flow = matching_flows.scalar_one_or_none()
            
            if matching_flow:
                print(f"🔗 Linking DataImport {data_import.id} to flow {matching_flow.flow_id}")
                
                # Update data import
                await db.execute(
                    update(DataImport)
                    .where(DataImport.id == data_import.id)
                    .values(master_flow_id=matching_flow.flow_id)
                )
                
                # Update related raw import records
                await db.execute(
                    update(RawImportRecord)
                    .where(RawImportRecord.data_import_id == data_import.id)
                    .values(master_flow_id=matching_flow.flow_id)
                )
                
                fixed_count += 1
            else:
                print(f"⚠️ No matching master flow found for DataImport {data_import.id}")
        
        await db.commit()
        
        print(f"✅ Fixed {fixed_count} out of {orphaned_count} orphaned data imports")

if __name__ == "__main__":
    asyncio.run(fix_orphaned_data_imports())
```

#### 3.2 Validate Data Integrity

**File**: `backend/scripts/validate_flow_relationships.py`

```python
#!/usr/bin/env python3
"""
Validate that all flow relationships are properly established.
"""

import asyncio
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal

async def validate_flow_relationships():
    """Validate all flow relationships are properly established."""
    
    async with AsyncSessionLocal() as db:
        print("🔍 Validating flow relationships...")
        
        # Check for orphaned data imports
        orphaned_imports = await db.execute(
            text("SELECT COUNT(*) FROM data_imports WHERE master_flow_id IS NULL")
        )
        orphaned_import_count = orphaned_imports.scalar()
        
        # Check for orphaned raw import records  
        orphaned_records = await db.execute(
            text("SELECT COUNT(*) FROM raw_import_records WHERE master_flow_id IS NULL")
        )
        orphaned_record_count = orphaned_records.scalar()
        
        # Check for orphaned discovery flows
        orphaned_discovery = await db.execute(
            text("SELECT COUNT(*) FROM discovery_flows WHERE master_flow_id IS NULL")
        )
        orphaned_discovery_count = orphaned_discovery.scalar()
        
        # Check for valid relationships
        valid_relationships = await db.execute(
            text("""
                SELECT 
                    cfe.flow_id,
                    COUNT(di.id) as data_import_count,
                    COUNT(rir.id) as raw_record_count,
                    COUNT(df.id) as discovery_flow_count
                FROM crewai_flow_state_extensions cfe
                LEFT JOIN data_imports di ON di.master_flow_id = cfe.flow_id
                LEFT JOIN raw_import_records rir ON rir.master_flow_id = cfe.flow_id  
                LEFT JOIN discovery_flows df ON df.master_flow_id = cfe.flow_id
                WHERE cfe.flow_type = 'discovery'
                GROUP BY cfe.flow_id
                HAVING COUNT(di.id) > 0 OR COUNT(rir.id) > 0 OR COUNT(df.id) > 0
            """)
        )
        
        valid_count = len(valid_relationships.fetchall())
        
        print(f"📊 Validation Results:")
        print(f"   Orphaned DataImports: {orphaned_import_count}")
        print(f"   Orphaned RawImportRecords: {orphaned_record_count}")
        print(f"   Orphaned DiscoveryFlows: {orphaned_discovery_count}")
        print(f"   Master flows with linked data: {valid_count}")
        
        if orphaned_import_count == 0 and orphaned_record_count == 0 and orphaned_discovery_count == 0:
            print("✅ All flow relationships are properly established!")
            return True
        else:
            print("❌ Data integrity issues found!")
            return False

if __name__ == "__main__":
    asyncio.run(validate_flow_relationships())
```

### Phase 4: Testing and Validation (2-4 days)

#### 4.1 End-to-End Test

**File**: `backend/tests/integration/test_discovery_flow_data_integrity.py`

```python
import pytest
import uuid
from app.core.database import AsyncSessionLocal
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

@pytest.mark.asyncio
async def test_complete_discovery_flow_data_linkage():
    """Test that data import creates properly linked discovery flow."""
    
    async with AsyncSessionLocal() as db:
        # 1. Simulate data import upload
        from app.api.v1.endpoints.data_import.handlers.import_storage_handler import _trigger_discovery_flow
        from app.core.context import RequestContext
        
        context = RequestContext(
            client_account_id="test-client-uuid",
            engagement_id="test-engagement-uuid", 
            user_id="test-user"
        )
        
        # Create test data import first
        data_import = DataImport(
            id=uuid.uuid4(),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            import_name="Test Import",
            import_type="cmdb",
            filename="test.csv",
            imported_by=context.user_id,
            status="pending"
        )
        db.add(data_import)
        await db.commit()
        
        # Create raw import records
        raw_records = []
        for i in range(3):
            record = RawImportRecord(
                id=uuid.uuid4(),
                data_import_id=data_import.id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                row_number=i,
                raw_data={"test": f"data_{i}"}
            )
            raw_records.append(record)
            db.add(record)
        
        await db.commit()
        
        # 2. Trigger discovery flow
        flow_id = await _trigger_discovery_flow(
            data_import_id=str(data_import.id),
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,
            file_data=[{"test": "data"}],
            context=context
        )
        
        assert flow_id is not None
        
        # 3. Verify all relationships are established
        
        # Check master flow exists
        master_flow = await db.get(CrewAIFlowStateExtensions, uuid.UUID(flow_id))
        assert master_flow is not None
        assert master_flow.flow_type == "discovery"
        
        # Check data import is linked
        await db.refresh(data_import)
        assert data_import.master_flow_id == uuid.UUID(flow_id)
        
        # Check raw records are linked
        for record in raw_records:
            await db.refresh(record)
            assert record.master_flow_id == uuid.UUID(flow_id)
        
        # Check discovery flow is created and linked (may be created async)
        from sqlalchemy import select
        discovery_flows = await db.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.master_flow_id == uuid.UUID(flow_id))
        )
        discovery_flow = discovery_flows.scalar_one_or_none()
        
        # Discovery flow may be created asynchronously, so this could be None initially
        if discovery_flow:
            assert discovery_flow.master_flow_id == uuid.UUID(flow_id)
        
        print("✅ All data relationships properly established!")
```

## Deployment Checklist

### Pre-deployment
- [ ] Run database backup
- [ ] Test migration on staging environment
- [ ] Validate foreign key constraints
- [ ] Run data integrity validation script

### Deployment Steps
1. [ ] Apply database migration
2. [ ] Deploy code changes
3. [ ] Run data backfill script
4. [ ] Validate all relationships
5. [ ] Monitor for errors

### Post-deployment
- [ ] Run end-to-end tests
- [ ] Verify zero orphaned records
- [ ] Check flow creation/deletion works
- [ ] Monitor database performance

## Success Metrics

- **Zero orphaned records**: All `master_flow_id` fields properly populated
- **Foreign key integrity**: All constraints enforced
- **Flow management**: Create/delete operations work correctly
- **API consistency**: All endpoints return linked data
- **User experience**: No flow state inconsistencies

## Risk Mitigation

1. **Database Constraints**: Use nullable foreign keys initially, then enforce
2. **Backward Compatibility**: Maintain existing API interfaces  
3. **Data Migration**: Incremental backfill with validation
4. **Rollback Plan**: Keep migration downgrade scripts ready

This plan addresses all critical data integrity issues and establishes proper relationships throughout the discovery flow data architecture.