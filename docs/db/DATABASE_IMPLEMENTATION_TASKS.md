# Database Implementation Tasks - AI Modernize Migration Platform

## Table of Contents
1. [Overview](#overview)
2. [Implementation Phases](#implementation-phases)
3. [Phase 1: Database Consolidation](#phase-1-database-consolidation)
4. [Phase 2: Schema Implementation](#phase-2-schema-implementation)
5. [Phase 3: Model Layer Updates](#phase-3-model-layer-updates)
6. [Phase 4: Application Integration](#phase-4-application-integration)
7. [Phase 5: Testing & Validation](#phase-5-testing--validation)
8. [Phase 6: Deployment](#phase-6-deployment)
9. [Task Tracking Template](#task-tracking-template)
10. [Success Metrics](#success-metrics)

## Overview

This document provides a detailed task breakdown for implementing the consolidated database schema design. Each task includes specific deliverables, acceptance criteria, and implementation notes.

### Project Goals
- Consolidate V3 and original tables into a single schema
- Implement master flow orchestration architecture
- Remove deprecated fields and tables
- Establish multi-tenant test data patterns
- Ensure zero data loss during migration

### Timeline
- **Total Duration**: 10-12 days
- **Team Size**: 1-2 developers
- **Environment Coverage**: Development → Staging → Production

## Implementation Phases

### Phase Overview
1. **Database Consolidation** (2-3 days): Merge V3 tables, remove deprecated tables
2. **Schema Implementation** (2 days): Create consolidated Alembic migrations
3. **Model Layer Updates** (2 days): Update SQLAlchemy models and repositories
4. **Application Integration** (2 days): Update services, APIs, and frontend
5. **Testing & Validation** (1-2 days): Comprehensive testing suite
6. **Deployment** (1 day): Staged rollout to all environments

## Phase 1: Database Consolidation

### Task 1.1: Analyze Current State
**Priority**: Critical  
**Duration**: 4 hours  
**Dependencies**: None

**Actions**:
```sql
-- Generate current state report
SELECT 
    t.table_name,
    COUNT(c.column_name) as column_count,
    pg_size_pretty(pg_total_relation_size(t.table_schema||'.'||t.table_name)) as size,
    obj_description(pgc.oid) as comment
FROM information_schema.tables t
LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
LEFT JOIN pg_class pgc ON pgc.relname = t.table_name
WHERE t.table_schema = 'migration'
GROUP BY t.table_name, t.table_schema, pgc.oid
ORDER BY t.table_name;

-- Check V3 table usage
SELECT 
    'v3_data_imports' as table_name, COUNT(*) as record_count 
FROM v3_data_imports
UNION ALL
SELECT 'v3_discovery_flows', COUNT(*) FROM v3_discovery_flows
UNION ALL
SELECT 'v3_field_mappings', COUNT(*) FROM v3_field_mappings
UNION ALL
SELECT 'v3_raw_import_records', COUNT(*) FROM v3_raw_import_records;
```

**Deliverables**:
- [ ] Current state analysis document
- [ ] V3 data migration requirements
- [ ] Risk assessment for each table

### Task 1.2: Create Backup Strategy
**Priority**: Critical  
**Duration**: 2 hours  
**Dependencies**: Task 1.1

**Actions**:
```bash
#!/bin/bash
# backup_strategy.sh

# Full database backup
pg_dump -U postgres -d migration_db -F custom -f migration_backup_$(date +%Y%m%d_%H%M%S).dump

# Table-specific backups
tables=(
    "data_imports" "discovery_flows" "assets" "import_field_mappings"
    "v3_data_imports" "v3_discovery_flows" "v3_field_mappings"
)

for table in "${tables[@]}"; do
    pg_dump -U postgres -d migration_db -t migration.$table -f backup_${table}_$(date +%Y%m%d).sql
done

# Create restore verification script
cat > verify_restore.sh << 'EOF'
#!/bin/bash
# Test restore on separate database
createdb test_restore
pg_restore -U postgres -d test_restore migration_backup_*.dump
# Run integrity checks
psql -d test_restore -f validate_restore.sql
dropdb test_restore
EOF
```

**Deliverables**:
- [ ] Backup scripts created and tested
- [ ] Restore procedures documented
- [ ] Backup storage location secured

### Task 1.3: Migrate V3 Data
**Priority**: High  
**Duration**: 4 hours  
**Dependencies**: Task 1.2

**Actions**:
```python
# migrate_v3_data.py
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate_v3_data():
    async with engine.begin() as conn:
        # 1. Migrate v3_data_imports
        await conn.execute(text("""
            INSERT INTO data_imports (
                id, client_account_id, engagement_id, master_flow_id,
                filename, file_size, mime_type, source_system,
                status, import_name, import_type, description,
                error_message, error_details, progress_percentage,
                total_records, processed_records, failed_records,
                imported_by, created_at, updated_at, started_at, completed_at
            )
            SELECT 
                id, client_account_id, engagement_id, master_flow_id,
                source_filename, file_size_bytes, file_type, source_system,
                status, import_name, import_type, description,
                error_message, error_details, progress_percentage,
                total_records, processed_records, failed_records,
                user_id, created_at, updated_at, started_at, completed_at
            FROM v3_data_imports
            WHERE NOT EXISTS (
                SELECT 1 FROM data_imports WHERE id = v3_data_imports.id
            )
        """))
        
        # 2. Migrate v3_discovery_flows
        await conn.execute(text("""
            INSERT INTO discovery_flows (
                id, flow_id, master_flow_id, client_account_id, engagement_id,
                data_import_id, user_id, status, progress_percentage,
                flow_type, current_phase, phases_completed, flow_state,
                error_message, error_phase, error_details,
                created_at, updated_at, started_at, completed_at
            )
            SELECT 
                id, flow_id, master_flow_id, client_account_id, engagement_id,
                data_import_id, user_id, status, progress_percentage,
                flow_type, current_phase, phases_completed, flow_state,
                error_message, error_phase, error_details,
                created_at, updated_at, started_at, completed_at
            FROM v3_discovery_flows
            WHERE NOT EXISTS (
                SELECT 1 FROM discovery_flows WHERE id = v3_discovery_flows.id
            )
        """))
        
        # 3. Migrate v3_field_mappings
        await conn.execute(text("""
            INSERT INTO import_field_mappings (
                id, data_import_id, client_account_id, master_flow_id,
                source_field, target_field, match_type, confidence_score,
                status, suggested_by, approved_by, approved_at,
                transformation_rules, is_validated,
                created_at, updated_at
            )
            SELECT 
                id, data_import_id, client_account_id, master_flow_id,
                source_field, target_field, mapping_type, confidence_score,
                CASE 
                    WHEN is_approved THEN 'approved'
                    WHEN is_rejected THEN 'rejected'
                    ELSE 'suggested'
                END as status,
                ai_model_version, approved_by, approved_at,
                transformation_logic, is_validated,
                created_at, updated_at
            FROM v3_field_mappings
            WHERE NOT EXISTS (
                SELECT 1 FROM import_field_mappings WHERE id = v3_field_mappings.id
            )
        """))
        
        print("✅ V3 data migration completed")

if __name__ == "__main__":
    asyncio.run(migrate_v3_data())
```

**Deliverables**:
- [ ] V3 data successfully migrated
- [ ] Migration verification report
- [ ] No data loss confirmed

### Task 1.4: Delete Deprecated Tables
**Priority**: Medium  
**Duration**: 2 hours  
**Dependencies**: Task 1.3

**Actions**:
```sql
-- Drop deprecated tables (after backup)
DROP TABLE IF EXISTS workflow_states CASCADE;
DROP TABLE IF EXISTS discovery_assets CASCADE;
DROP TABLE IF EXISTS mapping_learning_patterns CASCADE;
DROP TABLE IF EXISTS data_quality_issues CASCADE;
DROP TABLE IF EXISTS workflow_progress CASCADE;
DROP TABLE IF EXISTS import_processing_steps CASCADE;

-- Drop V3 tables (after migration verified)
DROP TABLE IF EXISTS v3_raw_import_records CASCADE;
DROP TABLE IF EXISTS v3_field_mappings CASCADE;
DROP TABLE IF EXISTS v3_discovery_flows CASCADE;
DROP TABLE IF EXISTS v3_data_imports CASCADE;

-- Clean up any orphaned sequences
DROP SEQUENCE IF EXISTS workflow_states_id_seq;
DROP SEQUENCE IF EXISTS discovery_assets_id_seq;
-- ... etc
```

**Deliverables**:
- [ ] Deprecated tables removed
- [ ] V3 tables removed
- [ ] Database size reduction documented

## Phase 2: Schema Implementation

### Task 2.1: Create Consolidated Migration
**Priority**: Critical  
**Duration**: 6 hours  
**Dependencies**: Phase 1 complete

**File**: `/backend/alembic/versions/001_consolidated_schema.py`

```python
"""Consolidated database schema
Revision ID: 001_consolidated
Create Date: 2025-01-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Set search path
    op.execute("SET search_path TO migration")
    
    # Create enum types
    op.execute("""
        CREATE TYPE IF NOT EXISTS asset_type AS ENUM (
            'server', 'application', 'database', 'network', 'storage'
        )
    """)
    
    op.execute("""
        CREATE TYPE IF NOT EXISTS flow_status AS ENUM (
            'initialized', 'in_progress', 'completed', 'failed', 'cancelled'
        )
    """)
    
    # Core tables
    op.create_table('client_accounts',
        sa.Column('id', postgresql.UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('industry', sa.String(100)),
        sa.Column('company_size', sa.String(50)),
        sa.Column('headquarters_location', sa.String(255)),
        sa.Column('primary_contact_name', sa.String(255)),
        sa.Column('primary_contact_email', sa.String(255)),
        sa.Column('primary_contact_phone', sa.String(50)),
        sa.Column('subscription_tier', sa.String(50), server_default='standard'),
        sa.Column('max_users', sa.Integer),
        sa.Column('max_engagements', sa.Integer),
        sa.Column('storage_quota_gb', sa.Integer),
        sa.Column('api_quota_monthly', sa.Integer),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('branding', postgresql.JSONB, server_default='{}'),
        sa.Column('agent_preferences', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true')
    )
    
    # Continue with all tables...
```

**Deliverables**:
- [ ] Complete migration file created
- [ ] All 43 tables defined
- [ ] Proper constraints and indexes

### Task 2.2: Create Index Migration
**Priority**: High  
**Duration**: 2 hours  
**Dependencies**: Task 2.1

**File**: `/backend/alembic/versions/002_performance_indexes.py`

```python
"""Add performance indexes
Revision ID: 002_indexes
Revises: 001_consolidated
"""

def upgrade():
    # Multi-tenant indexes
    op.create_index('ix_assets_client_account_id', 'assets', ['client_account_id'])
    op.create_index('ix_assets_engagement_id', 'assets', ['engagement_id'])
    
    # Master flow indexes
    op.create_index('ix_assets_master_flow_id', 'assets', ['master_flow_id'])
    op.create_index('ix_discovery_flows_master_flow_id', 'discovery_flows', ['master_flow_id'])
    
    # Search indexes
    op.create_index('ix_assets_asset_type', 'assets', ['asset_type'])
    op.create_index('ix_assets_environment', 'assets', ['environment'])
    op.create_index('ix_assets_six_r_strategy', 'assets', ['six_r_strategy'])
    
    # Composite indexes
    op.create_index('ix_assets_client_engagement', 'assets', ['client_account_id', 'engagement_id'])
    
    # JSONB GIN indexes
    op.execute("CREATE INDEX ix_assets_technology_stack ON assets USING GIN (technology_stack)")
    op.execute("CREATE INDEX ix_discovery_flows_phases ON discovery_flows USING GIN (phases)")
```

**Deliverables**:
- [ ] Performance indexes created
- [ ] JSONB indexes implemented
- [ ] Query performance validated

### Task 2.3: Create Validation Scripts
**Priority**: Medium  
**Duration**: 3 hours  
**Dependencies**: Task 2.2

**File**: `/backend/scripts/validate_consolidated_schema.py`

```python
import asyncio
from sqlalchemy import inspect, text
from app.core.database import engine

async def validate_schema():
    """Validate the consolidated schema implementation."""
    
    async with engine.connect() as conn:
        inspector = inspect(conn)
        
        # 1. Check no V3 tables exist
        tables = inspector.get_table_names(schema='migration')
        v3_tables = [t for t in tables if t.startswith('v3_')]
        assert len(v3_tables) == 0, f"V3 tables still exist: {v3_tables}"
        
        # 2. Check required tables exist
        required_tables = [
            'client_accounts', 'users', 'engagements',
            'crewai_flow_state_extensions', 'discovery_flows',
            'assets', 'data_imports', 'import_field_mappings'
        ]
        
        for table in required_tables:
            assert table in tables, f"Required table missing: {table}"
        
        # 3. Check removed tables don't exist
        removed_tables = [
            'workflow_states', 'discovery_assets', 
            'mapping_learning_patterns', 'data_quality_issues'
        ]
        
        for table in removed_tables:
            assert table not in tables, f"Deprecated table still exists: {table}"
        
        # 4. Validate master_flow_id columns
        for table in ['discovery_flows', 'assets', 'data_imports']:
            columns = [col['name'] for col in inspector.get_columns(table, schema='migration')]
            assert 'master_flow_id' in columns, f"master_flow_id missing from {table}"
        
        # 5. Check no is_mock fields
        for table in tables:
            columns = [col['name'] for col in inspector.get_columns(table, schema='migration')]
            assert 'is_mock' not in columns, f"is_mock field still exists in {table}"
        
        print("✅ Schema validation passed!")
        
        # 6. Generate validation report
        report = {
            'total_tables': len(tables),
            'indexes': {},
            'constraints': {},
            'field_mappings': {}
        }
        
        for table in required_tables:
            indexes = inspector.get_indexes(table, schema='migration')
            report['indexes'][table] = len(indexes)
            
            constraints = inspector.get_foreign_keys(table, schema='migration')
            report['constraints'][table] = len(constraints)
        
        return report

if __name__ == "__main__":
    report = asyncio.run(validate_schema())
    print(f"Validation Report: {report}")
```

**Deliverables**:
- [ ] Schema validation script
- [ ] Validation report generated
- [ ] All checks passing

## Phase 3: Model Layer Updates

### Task 3.1: Update Base Models
**Priority**: Critical  
**Duration**: 4 hours  
**Dependencies**: Phase 2 complete

**Actions**:
1. Update `/backend/app/models/data_import.py`:
   - Rename fields: source_filename → filename
   - Add: error_message, error_details, source_system
   - Remove: is_mock, file_hash, import_config

2. Update `/backend/app/models/discovery_flow.py`:
   - Add JSON fields: current_phase, phases_completed, flow_state
   - Keep boolean flags for compatibility
   - Remove: is_mock, assessment_package

3. Update `/backend/app/models/asset.py`:
   - Keep ALL infrastructure fields
   - Ensure master_flow_id linkage
   - Remove: is_mock, raw_data (move to separate table if needed)

**Deliverables**:
- [ ] All models updated
- [ ] Type hints corrected
- [ ] Relationships defined

### Task 3.2: Update Repository Layer
**Priority**: High  
**Duration**: 4 hours  
**Dependencies**: Task 3.1

**Updates Required**:
```python
# data_import_repository.py
class DataImportRepository:
    def create_import(self, data: dict):
        # Handle field renames
        if 'source_filename' in data:
            data['filename'] = data.pop('source_filename')
        if 'file_size_bytes' in data:
            data['file_size'] = data.pop('file_size_bytes')
        
        # Remove deprecated fields
        for field in ['is_mock', 'file_hash', 'import_config']:
            data.pop(field, None)
        
        return super().create(data)

# discovery_flow_repository.py
class DiscoveryFlowRepository:
    def update_phase(self, flow_id: UUID, phase: str, status: str):
        # Update both boolean flag and JSON state
        updates = {
            f"{phase}_completed": status == "completed",
            "current_phase": phase,
            "phases_completed": func.array_append(
                DiscoveryFlow.phases_completed, phase
            )
        }
        return self.update(flow_id, updates)
```

**Deliverables**:
- [ ] Repository methods updated
- [ ] Field mapping logic implemented
- [ ] Backward compatibility maintained

### Task 3.3: Remove V3 Model Files
**Priority**: Medium  
**Duration**: 1 hour  
**Dependencies**: Task 3.2

**Actions**:
```bash
# Remove V3 directory
rm -rf backend/app/models/v3/

# Update imports in __init__.py
# Remove all V3 model imports
```

**Deliverables**:
- [ ] V3 models removed
- [ ] Import statements cleaned
- [ ] No broken imports

## Phase 4: Application Integration

### Task 4.1: Update Service Layer
**Priority**: Critical  
**Duration**: 4 hours  
**Dependencies**: Phase 3 complete

**Service Updates**:
```python
# unified_discovery_flow.py
class UnifiedDiscoveryFlow:
    async def initialize_flow(self, context: FlowContext):
        # Create master flow first
        master_flow = await self.create_master_flow(context)
        
        # Create discovery flow with linkage
        discovery_flow = await self.create_discovery_flow(
            context, 
            master_flow_id=master_flow.flow_id
        )
        
        # Initialize with proper orchestration
        return {
            'master_flow_id': master_flow.flow_id,
            'discovery_flow_id': discovery_flow.id
        }
```

**Deliverables**:
- [ ] Service methods updated
- [ ] Master flow creation implemented
- [ ] Error handling enhanced

### Task 4.2: Update API Endpoints
**Priority**: High  
**Duration**: 3 hours  
**Dependencies**: Task 4.1

**API Updates**:
```python
# data_import_routes.py
@router.post("/imports")
async def create_import(
    import_data: DataImportCreate,
    master_flow_id: Optional[UUID] = None
):
    # Handle field mappings
    data = import_data.dict()
    if 'source_filename' in data:
        data['filename'] = data.pop('source_filename')
    
    # Add master flow linkage
    if master_flow_id:
        data['master_flow_id'] = master_flow_id
    
    return await service.create_import(data)
```

**Deliverables**:
- [ ] API routes updated
- [ ] Request/response models aligned
- [ ] OpenAPI schema regenerated

### Task 4.3: Update Frontend Integration
**Priority**: High  
**Duration**: 4 hours  
**Dependencies**: Task 4.2

**Frontend Updates**:
```typescript
// types/api.ts
export interface DataImport {
  id: string;
  filename: string;  // was source_filename
  file_size?: number;  // was file_size_bytes
  mime_type?: string;  // was file_type
  master_flow_id?: string;
  source_system?: string;
  error_message?: string;
  error_details?: Record<string, any>;
  // Remove: is_mock
}

// Update API client
const createImport = async (data: CreateImportRequest) => {
  // Map old field names if needed
  const payload = {
    ...data,
    filename: data.source_filename || data.filename,
    file_size: data.file_size_bytes || data.file_size
  };
  
  return api.post('/v3/imports', payload);
};
```

**Deliverables**:
- [ ] TypeScript interfaces updated
- [ ] API client methods updated
- [ ] Component props aligned

## Phase 5: Testing & Validation

### Task 5.1: Create Integration Tests
**Priority**: Critical  
**Duration**: 4 hours  
**Dependencies**: Phase 4 complete

**Test Suite**: `/backend/tests/integration/test_db_consolidation.py`

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

class TestDatabaseConsolidation:
    async def test_no_v3_tables(self, db: AsyncSession):
        """Ensure V3 tables are removed."""
        result = await db.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'migration' AND table_name LIKE 'v3_%'"
        )
        v3_tables = result.fetchall()
        assert len(v3_tables) == 0
    
    async def test_master_flow_linkage(self, db: AsyncSession):
        """Test master flow orchestration."""
        # Create master flow
        master_flow = await create_master_flow(db)
        
        # Create linked discovery flow
        discovery_flow = await create_discovery_flow(
            db, master_flow_id=master_flow.flow_id
        )
        
        # Verify linkage
        assert discovery_flow.master_flow_id == master_flow.flow_id
    
    async def test_field_migrations(self, db: AsyncSession):
        """Test field name compatibility."""
        # Test with old field names
        data = {
            'source_filename': 'test.csv',
            'file_size_bytes': 1024
        }
        
        import_record = await create_import_with_legacy_fields(db, data)
        assert import_record.filename == 'test.csv'
        assert import_record.file_size == 1024
    
    async def test_no_is_mock_fields(self, db: AsyncSession):
        """Ensure is_mock is removed."""
        inspector = inspect(db.bind)
        for table in inspector.get_table_names(schema='migration'):
            columns = [c['name'] for c in inspector.get_columns(table, schema='migration')]
            assert 'is_mock' not in columns
```

**Deliverables**:
- [ ] Integration test suite
- [ ] All tests passing
- [ ] Coverage report > 80%

### Task 5.2: Create E2E Tests
**Priority**: High  
**Duration**: 3 hours  
**Dependencies**: Task 5.1

**Test Suite**: `/backend/tests/e2e/test_full_discovery_flow.py`

```python
class TestFullDiscoveryFlow:
    async def test_complete_discovery_workflow(self):
        """Test full discovery workflow with new schema."""
        # 1. Create engagement
        engagement = await create_test_engagement()
        
        # 2. Initialize master flow
        master_flow = await initialize_master_flow(engagement.id)
        
        # 3. Upload data file
        import_result = await upload_test_file(
            'test_data.csv',
            master_flow_id=master_flow.flow_id
        )
        
        # 4. Start discovery
        discovery_flow = await start_discovery(
            import_result.id,
            master_flow_id=master_flow.flow_id
        )
        
        # 5. Verify assets created with linkage
        assets = await get_assets_by_master_flow(master_flow.flow_id)
        assert len(assets) > 0
        assert all(a.master_flow_id == master_flow.flow_id for a in assets)
```

**Deliverables**:
- [ ] E2E test scenarios
- [ ] Workflow validation
- [ ] Performance benchmarks

### Task 5.3: Performance Testing
**Priority**: Medium  
**Duration**: 2 hours  
**Dependencies**: Task 5.2

**Test Suite**: `/backend/tests/performance/test_query_performance.py`

```python
class TestQueryPerformance:
    async def test_multi_tenant_query_performance(self, db: AsyncSession):
        """Test query performance with tenant filtering."""
        # Create test data
        client_id = await create_test_client()
        await create_bulk_assets(client_id, count=10000)
        
        # Test query performance
        start_time = time.time()
        
        result = await db.execute(
            select(Asset)
            .where(Asset.client_account_id == client_id)
            .where(Asset.environment == 'production')
            .limit(100)
        )
        
        query_time = time.time() - start_time
        assert query_time < 0.1  # Should be under 100ms
    
    async def test_master_flow_join_performance(self):
        """Test performance of master flow joins."""
        # Test complex join query
        query = """
            SELECT a.*, df.status, cf.flow_type
            FROM assets a
            JOIN discovery_flows df ON a.discovery_flow_id = df.id
            JOIN crewai_flow_state_extensions cf ON a.master_flow_id = cf.flow_id
            WHERE a.client_account_id = :client_id
            AND a.master_flow_id IS NOT NULL
            LIMIT 100
        """
        
        # Should use indexes efficiently
        explain = await db.execute(f"EXPLAIN ANALYZE {query}")
        # Verify index usage
```

**Deliverables**:
- [ ] Performance test suite
- [ ] Query benchmarks documented
- [ ] Optimization recommendations

## Phase 6: Deployment

### Task 6.1: Staging Deployment
**Priority**: Critical  
**Duration**: 4 hours  
**Dependencies**: Phase 5 complete

**Deployment Steps**:
```bash
#!/bin/bash
# deploy_staging.sh

# 1. Backup staging database
pg_dump -h staging-db -U postgres -d migration_staging > staging_backup_$(date +%Y%m%d).sql

# 2. Deploy code
git checkout main
git pull origin main

# 3. Run migrations
cd backend
alembic upgrade head

# 4. Validate deployment
python scripts/validate_consolidated_schema.py

# 5. Run smoke tests
pytest tests/integration/test_db_consolidation.py -v

# 6. Monitor for 2 hours
```

**Deliverables**:
- [ ] Staging deployment successful
- [ ] Validation passes
- [ ] No errors in logs

### Task 6.2: Production Deployment
**Priority**: Critical  
**Duration**: 4 hours  
**Dependencies**: Task 6.1 + 24hr staging validation

**Production Checklist**:
- [ ] Staging stable for 24 hours
- [ ] Full production backup created
- [ ] Maintenance window scheduled
- [ ] Rollback plan prepared
- [ ] Team notified

**Deployment Script**:
```bash
#!/bin/bash
# deploy_production.sh

# Enable maintenance mode
kubectl scale deployment backend --replicas=0

# Backup production
pg_dump -h prod-db -U postgres -d migration_prod > prod_backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
alembic upgrade head

# Validate
python scripts/validate_consolidated_schema.py

# Deploy new code
kubectl set image deployment/backend backend=backend:latest

# Scale up gradually
kubectl scale deployment backend --replicas=1
sleep 60
kubectl scale deployment backend --replicas=3

# Monitor
kubectl logs -f deployment/backend
```

**Deliverables**:
- [ ] Production deployment complete
- [ ] All services operational
- [ ] Performance metrics normal

### Task 6.3: Post-Deployment Validation
**Priority**: High  
**Duration**: 2 hours  
**Dependencies**: Task 6.2

**Validation Steps**:
1. Run all validation scripts
2. Check application functionality
3. Monitor error rates
4. Verify data integrity
5. Test all critical workflows

**Monitoring Dashboard**:
```sql
-- Real-time health check
CREATE VIEW deployment_health AS
SELECT 
    'table_count' as metric,
    COUNT(*) as value
FROM information_schema.tables
WHERE table_schema = 'migration'
UNION ALL
SELECT 
    'active_flows',
    COUNT(*)
FROM crewai_flow_state_extensions
WHERE flow_status IN ('active', 'processing')
UNION ALL
SELECT 
    'recent_errors',
    COUNT(*)
FROM discovery_flows
WHERE error_message IS NOT NULL
AND created_at > NOW() - INTERVAL '1 hour';
```

**Deliverables**:
- [ ] Health metrics dashboard
- [ ] Validation report
- [ ] Sign-off from stakeholders

## Task Tracking Template

Use this template for tracking individual tasks:

```markdown
### Task ID: [PHASE.TASK]
**Title**: [Task Title]
**Status**: [ ] Not Started | [ ] In Progress | [ ] Complete | [ ] Blocked
**Assignee**: [Name]
**Priority**: Critical | High | Medium | Low
**Duration**: [Estimated hours]
**Started**: [Date/Time]
**Completed**: [Date/Time]

**Dependencies**:
- [ ] [Dependency 1]
- [ ] [Dependency 2]

**Acceptance Criteria**:
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Notes**:
[Any additional notes or blockers]

**Verification**:
- [ ] Code reviewed
- [ ] Tests passing
- [ ] Documentation updated
```

## Success Metrics

### Technical Metrics
- **Schema Consolidation**: 100% - No V3 tables remain
- **Data Integrity**: 100% - No data loss during migration
- **Test Coverage**: >80% - Comprehensive test suite
- **Performance**: <5% degradation - Query performance maintained

### Business Metrics
- **Downtime**: <15 minutes - Minimal service interruption
- **Error Rate**: <0.1% - Post-deployment error rate
- **User Impact**: None - Seamless transition
- **Rollback Time**: <30 minutes - If needed

### Quality Gates
Each phase must meet these criteria before proceeding:

1. **Phase 1**: All data migrated, backups verified
2. **Phase 2**: Schema validation passing, migrations tested
3. **Phase 3**: All models updated, no import errors
4. **Phase 4**: APIs functional, frontend integrated
5. **Phase 5**: All tests passing, performance validated
6. **Phase 6**: Staging stable, production monitored

## Risk Mitigation

### High-Risk Areas
1. **Data Migration**: V3 to consolidated tables
   - Mitigation: Comprehensive backups, validation scripts
   
2. **Field Renames**: Breaking API changes
   - Mitigation: Backward compatibility layer
   
3. **Master Flow Implementation**: New orchestration pattern
   - Mitigation: Gradual rollout, feature flag

### Rollback Procedures
```bash
# Quick rollback script
#!/bin/bash
if [ "$1" == "emergency" ]; then
    # Stop all services
    kubectl scale deployment backend --replicas=0
    
    # Restore database
    pg_restore -h $DB_HOST -U postgres -d migration_db < last_good_backup.sql
    
    # Deploy previous version
    kubectl set image deployment/backend backend=backend:previous
    
    # Scale up
    kubectl scale deployment backend --replicas=3
fi
```

## Communication Plan

### Stakeholder Updates
- **Daily**: Slack update on progress
- **Phase Complete**: Email summary to team
- **Blockers**: Immediate escalation
- **Deployment**: 24hr advance notice

### Documentation Updates
- Update README with schema changes
- Update API documentation
- Create migration guide for developers
- Archive old documentation

---

*Database Implementation Tasks for AI Modernize Migration Platform - January 2025*