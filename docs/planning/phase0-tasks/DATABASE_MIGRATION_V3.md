# Phase 0 - Database Migration to V3

## Critical Priority Task
**This must be completed BEFORE Phase 2 to prevent further data bifurcation**

## Context
The Phase 1 remediation created V3 tables alongside existing tables, causing:
- Two parallel data systems
- Data split between original and V3 tables
- Risk of inconsistency
- Confusion about source of truth

## Migration Strategy: Move to V3

### Why V3?
1. Frontend already built for V3 APIs
2. Cleaner, simpler design
3. JSON-centric for flexibility
4. Better suited for AI/CrewAI patterns

## Task 1: Data Migration Scripts

### Create Migration Script
**File**: `backend/migrations/versions/migrate_to_v3_tables.py`

```python
"""Migrate data from original tables to V3 tables

Revision ID: migrate_to_v3_001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

def upgrade():
    """Migrate all data to V3 tables"""
    
    conn = op.get_bind()
    
    # 1. Migrate data_imports -> v3_data_imports
    print("Migrating data_imports to v3_data_imports...")
    conn.execute(text("""
        INSERT INTO v3_data_imports (
            id, client_account_id, engagement_id, filename, 
            file_size, mime_type, source_system, status,
            total_records, processed_records, failed_records,
            created_at, updated_at, completed_at,
            error_message, error_details
        )
        SELECT 
            id, client_account_id, engagement_id, filename,
            file_size, mime_type, source_system,
            CASE 
                WHEN status = 'completed' THEN 'completed'::importstatus
                WHEN status = 'failed' THEN 'failed'::importstatus
                WHEN status = 'processing' THEN 'processing'::importstatus
                ELSE 'pending'::importstatus
            END as status,
            total_records, processed_records, 0 as failed_records,
            created_at, updated_at, completed_at,
            error_message, NULL as error_details
        FROM data_imports
        WHERE NOT EXISTS (
            SELECT 1 FROM v3_data_imports v3 WHERE v3.id = data_imports.id
        );
    """))
    
    # 2. Migrate discovery_flows -> v3_discovery_flows
    print("Migrating discovery_flows to v3_discovery_flows...")
    conn.execute(text("""
        INSERT INTO v3_discovery_flows (
            id, client_account_id, engagement_id, flow_name,
            flow_type, data_import_id, status, current_phase,
            phases_completed, progress_percentage, flow_state,
            created_at, updated_at, started_at, completed_at
        )
        SELECT 
            id, client_account_id, engagement_id, 
            'Discovery Flow ' || COALESCE(import_name, 'Unknown'),
            'unified_discovery', data_import_id,
            CASE
                WHEN status = 'completed' THEN 'completed'::flowstatus
                WHEN status = 'failed' THEN 'failed'::flowstatus
                WHEN status = 'running' THEN 'running'::flowstatus
                ELSE 'initializing'::flowstatus
            END as status,
            CASE
                WHEN tech_debt_assessment_completed THEN 'completed'
                WHEN dependency_analysis_completed THEN 'technical_debt'
                WHEN asset_inventory_completed THEN 'dependency_analysis'
                WHEN data_cleansing_completed THEN 'asset_inventory'
                WHEN field_mapping_completed THEN 'data_cleansing'
                WHEN data_validation_completed THEN 'field_mapping'
                ELSE 'data_validation'
            END as current_phase,
            ARRAY[]::text[] as phases_completed,
            CASE
                WHEN status = 'completed' THEN 100.0
                WHEN tech_debt_assessment_completed THEN 90.0
                WHEN dependency_analysis_completed THEN 75.0
                WHEN asset_inventory_completed THEN 60.0
                WHEN data_cleansing_completed THEN 45.0
                WHEN field_mapping_completed THEN 30.0
                WHEN data_validation_completed THEN 15.0
                ELSE 0.0
            END as progress_percentage,
            COALESCE(crew_outputs, '{}'::json) as flow_state,
            created_at, updated_at, started_at, completed_at
        FROM discovery_flows
        WHERE NOT EXISTS (
            SELECT 1 FROM v3_discovery_flows v3 WHERE v3.id = discovery_flows.id
        );
    """))
    
    # 3. Migrate import_field_mappings -> v3_field_mappings
    print("Migrating import_field_mappings to v3_field_mappings...")
    conn.execute(text("""
        INSERT INTO v3_field_mappings (
            id, data_import_id, client_account_id,
            source_field, target_field, confidence_score,
            match_type, suggested_by, status,
            approved_by, approved_at, transformation_rules,
            created_at, updated_at
        )
        SELECT 
            id, data_import_id, client_account_id,
            source_field, target_field, 
            COALESCE(confidence_score, 0.5),
            COALESCE(mapping_type, 'fuzzy'),
            'ai_agent',
            CASE
                WHEN is_approved = true THEN 'approved'::mappingstatus
                WHEN is_approved = false THEN 'rejected'::mappingstatus
                ELSE 'suggested'::mappingstatus
            END as status,
            approved_by, approved_at,
            validation_rules as transformation_rules,
            created_at, updated_at
        FROM import_field_mappings
        WHERE NOT EXISTS (
            SELECT 1 FROM v3_field_mappings v3 WHERE v3.id = import_field_mappings.id
        );
    """))
    
    # 4. Migrate raw_import_records -> v3_raw_import_records
    print("Migrating raw_import_records to v3_raw_import_records...")
    conn.execute(text("""
        INSERT INTO v3_raw_import_records (
            id, data_import_id, record_index, raw_data,
            is_processed, is_valid, validation_errors,
            cleansed_data, created_at, processed_at
        )
        SELECT 
            id, data_import_id, record_number, raw_data,
            is_processed, is_valid, validation_errors,
            processed_data as cleansed_data,
            created_at, processed_at
        FROM raw_import_records
        WHERE NOT EXISTS (
            SELECT 1 FROM v3_raw_import_records v3 WHERE v3.id = raw_import_records.id
        );
    """))
    
    # 5. Update sequences
    print("Updating sequences...")
    # Update any sequences if needed
    
    print("Migration completed successfully!")

def downgrade():
    """Emergency rollback - restore from backup instead"""
    print("To rollback: restore from backup")
    # Don't delete data in downgrade - too risky
```

## Task 2: Update Model References

### Global Model Aliasing
**File**: `backend/app/models/__init__.py`

```python
"""
Unified model imports - pointing to V3 tables
"""

# Import V3 models with original names for compatibility
from app.models.v3 import (
    V3DataImport as DataImport,
    V3DiscoveryFlow as DiscoveryFlow,
    V3FieldMapping as FieldMapping,
    V3RawImportRecord as RawImportRecord,
    ImportStatus,
    FlowStatus,
    MappingStatus
)

# Keep other models as-is
from app.models.base import Base
from app.models.client import Client
from app.models.engagement import Engagement
from app.models.user import User
from app.models.asset import Asset
from app.models.application import Application
from app.models.dependency import Dependency

# Export all models
__all__ = [
    # V3 models (as primary)
    'DataImport',
    'DiscoveryFlow', 
    'FieldMapping',
    'RawImportRecord',
    'ImportStatus',
    'FlowStatus',
    'MappingStatus',
    
    # Other models
    'Base',
    'Client',
    'Engagement',
    'User',
    'Asset',
    'Application',
    'Dependency'
]

# For backward compatibility during migration
from app.models import data_import as legacy_data_import
from app.models import discovery_flow as legacy_discovery_flow
from app.models import import_field_mapping as legacy_field_mapping
from app.models import raw_import_record as legacy_raw_import_record
```

## Task 3: Update Service Layer

### Update Import Service
**File**: `backend/app/services/data_import/service.py`

```python
# Update to use V3 models and repositories
from app.models import DataImport, ImportStatus  # Now points to V3
from app.repositories.v3.data_import import V3DataImportRepository as DataImportRepository
```

### Update Discovery Flow Service
**File**: `backend/app/services/discovery_flow/service.py`

```python
# Update to use V3 models
from app.models import DiscoveryFlow, FlowStatus  # Now points to V3
from app.repositories.v3.discovery_flow import V3DiscoveryFlowRepository as DiscoveryFlowRepository
```

## Task 4: Testing & Validation

### Validation Script
**File**: `backend/scripts/validate_migration.py`

```python
"""Validate V3 migration success"""

import asyncio
from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal

async def validate_migration():
    """Check data integrity after migration"""
    
    async with AsyncSessionLocal() as session:
        # Check record counts
        checks = [
            ("data_imports", "v3_data_imports"),
            ("discovery_flows", "v3_discovery_flows"),
            ("import_field_mappings", "v3_field_mappings"),
            ("raw_import_records", "v3_raw_import_records")
        ]
        
        for original, v3 in checks:
            orig_count = await session.scalar(
                select(func.count()).select_from(text(original))
            )
            v3_count = await session.scalar(
                select(func.count()).select_from(text(v3))
            )
            
            print(f"{original}: {orig_count} records")
            print(f"{v3}: {v3_count} records")
            
            if orig_count != v3_count:
                print(f"⚠️  WARNING: Count mismatch!")
            else:
                print(f"✅ Counts match!")
            print()

if __name__ == "__main__":
    asyncio.run(validate_migration())
```

## Task 5: Deprecate Original Tables

### Rename Original Tables
**File**: `backend/migrations/versions/deprecate_original_tables.py`

```python
"""Deprecate original tables after successful migration

Revision ID: deprecate_original_001
"""

from alembic import op

def upgrade():
    """Rename original tables with _deprecated suffix"""
    
    # Rename tables
    op.rename_table('data_imports', 'data_imports_deprecated')
    op.rename_table('discovery_flows', 'discovery_flows_deprecated')
    op.rename_table('import_field_mappings', 'import_field_mappings_deprecated')
    op.rename_table('raw_import_records', 'raw_import_records_deprecated')
    
    print("Original tables renamed with _deprecated suffix")
    print("These can be dropped after 30 days if no issues arise")

def downgrade():
    """Restore original table names"""
    op.rename_table('data_imports_deprecated', 'data_imports')
    op.rename_table('discovery_flows_deprecated', 'discovery_flows')
    op.rename_table('import_field_mappings_deprecated', 'import_field_mappings')
    op.rename_table('raw_import_records_deprecated', 'raw_import_records')
```

## Execution Steps

### 1. Backup Database (CRITICAL)
```bash
docker exec -it migration_db pg_dump -U postgres -d migration_db > backup_before_v3_migration.sql
```

### 2. Run Migration
```bash
# Create migration
docker exec -it migration_backend alembic revision -m "migrate_to_v3_tables"

# Run migration
docker exec -it migration_backend alembic upgrade head
```

### 3. Validate Migration
```bash
docker exec -it migration_backend python scripts/validate_migration.py
```

### 4. Update Code References
- Run tests to ensure all services work
- Check API endpoints respond correctly

### 5. Deprecate Original Tables
```bash
# After validation passes
docker exec -it migration_backend alembic revision -m "deprecate_original_tables"
docker exec -it migration_backend alembic upgrade head
```

## Success Criteria
- [ ] All data migrated from original to V3 tables
- [ ] Record counts match between systems
- [ ] All APIs functioning with V3 tables
- [ ] No references to original table names in code
- [ ] Original tables renamed with _deprecated suffix
- [ ] Full backup available for rollback

## Rollback Plan
```bash
# If issues arise:
docker exec -it migration_db psql -U postgres -d migration_db < backup_before_v3_migration.sql

# Then revert code changes
git revert <migration-commit>
```

## Timeline
- Day 1: Create and test migration scripts
- Day 2: Run migration in dev/staging
- Day 3: Production migration and validation
- Day 4: Monitor and fix any issues

## Notes
- This consolidation is REQUIRED before Phase 2
- Keeps V3 API contracts intact
- Provides single source of truth
- Enables clean CrewAI transformation