# Single Agent Database Consolidation Plan

## Executive Summary

This plan consolidates the database schema from parallel V3/original tables to a single, clean schema. The work will be completed by a single AI coding agent over 5-6 days, eliminating V3 tables while preserving the architectural design including master_flow_id orchestration and all asset mapping fields.

## Key Objectives

1. **Remove V3 table redundancy** - No v3_* tables in final schema
2. **Preserve architectural patterns** - Keep master_flow_id for multi-phase orchestration
3. **Maintain data mapping capability** - Preserve all asset fields for import mapping
4. **Single migration approach** - One Alembic migration to build from scratch
5. **Multi-tenant isolation** - Use client_account_id/engagement_id, remove is_mock

## Architecture Understanding

### Multi-Phase Orchestration Design
```
Master Flow (CrewAIFlowStateExtension)
    ├── Discovery Phase (data_imports → discovery_flows → assets)
    ├── Assessment Phase (assessments → sixr_analyses)
    ├── Planning Phase (migration_waves → wave_plans)
    └── Execution Phase (future implementation)
```

### Critical Fields to Preserve
- `master_flow_id` - Ties all phases together (NOT NULL after phase 1)
- Asset infrastructure fields - Mapping targets for various import sources
- JSON fields in discovery_flows - For CrewAI state management

## Detailed Task Tracker

### Day 1: Database Schema & Migration
**Goal**: Create comprehensive Alembic migration for entire schema

#### Task 1.1: Create Consolidated Schema Migration
**File**: `backend/alembic/versions/001_consolidated_schema.py`

```python
"""
Comprehensive database schema consolidation
Revision ID: 001_consolidated
Create Date: 2025-01-30
"""

def upgrade():
    # 1. Create enum types
    op.execute("CREATE TYPE asset_type AS ENUM ('server', 'application', 'database', 'network', 'storage')")
    op.execute("CREATE TYPE flow_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE import_status AS ENUM ('pending', 'processing', 'completed', 'failed')")
    
    # 2. Create core multi-tenant tables
    op.create_table('client_accounts', ...)
    op.create_table('engagements', ...)
    op.create_table('users', ...)
    
    # 3. Create master orchestration table
    op.create_table('crewai_flow_state_extensions',
        sa.Column('flow_id', UUID, primary_key=True),
        sa.Column('flow_type', sa.String),
        sa.Column('master_state', JSON),
        # ... other fields
    )
    
    # 4. Create discovery phase tables (consolidated)
    op.create_table('data_imports',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('master_flow_id', UUID, sa.ForeignKey('crewai_flow_state_extensions.flow_id')),
        sa.Column('filename', sa.String, nullable=False),  # NOT source_filename
        sa.Column('file_size', sa.Integer),  # NOT file_size_bytes
        sa.Column('mime_type', sa.String),  # NOT file_type
        sa.Column('source_system', sa.String),
        sa.Column('error_message', sa.String),
        sa.Column('error_details', JSON),
        # NO is_mock field
    )
    
    # 5. Create discovery_flows with hybrid approach
    op.create_table('discovery_flows',
        # Boolean flags (keep for backward compatibility)
        sa.Column('data_validation_completed', sa.Boolean, default=False),
        sa.Column('field_mapping_completed', sa.Boolean, default=False),
        # ... other boolean flags
        
        # JSON fields for CrewAI state
        sa.Column('current_phase', sa.String),
        sa.Column('phases_completed', JSON, default=list),
        sa.Column('crew_outputs', JSON, default=dict),
        sa.Column('field_mappings', JSON),
        sa.Column('discovered_assets', JSON),
    )
    
    # 6. Create assets table with ALL fields preserved
    op.create_table('assets',
        # Orchestration fields
        sa.Column('master_flow_id', UUID),
        sa.Column('discovery_flow_id', UUID),
        
        # Infrastructure fields (for mapping) - KEEP ALL
        sa.Column('hostname', sa.String),
        sa.Column('ip_address', sa.String),
        sa.Column('operating_system', sa.String),
        sa.Column('cpu_cores', sa.Integer),
        sa.Column('memory_gb', sa.Float),
        # ... all 60+ fields except is_mock
    )
    
    # 7. DO NOT CREATE these tables:
    # - v3_data_imports, v3_discovery_flows, v3_field_mappings, v3_raw_import_records
    # - workflow_states, discovery_assets, mapping_learning_patterns
    # - data_quality_issues, workflow_progress, import_processing_steps

def downgrade():
    # Drop all tables in reverse order
```

**Deliverables**:
- [ ] Complete migration file with all tables
- [ ] Proper foreign key constraints
- [ ] Multi-tenant indexes on all tables
- [ ] No V3 tables created

#### Task 1.2: Create Schema Validation Script
**File**: `backend/scripts/validate_schema.py`

```python
def validate_schema():
    # Check no V3 tables exist
    v3_tables = [t for t in inspector.get_table_names() if t.startswith('v3_')]
    assert len(v3_tables) == 0, f"V3 tables found: {v3_tables}"
    
    # Check required tables exist
    required_tables = [
        'data_imports', 'discovery_flows', 'assets',
        'import_field_mappings', 'raw_import_records'
    ]
    
    # Check removed tables don't exist
    removed_tables = [
        'workflow_states', 'discovery_assets', 
        'mapping_learning_patterns', 'data_quality_issues'
    ]
```

#### Task 1.3: Create Test Data Seeding Script
**File**: `backend/scripts/seed_test_data.py`

```python
async def seed_test_data():
    # Create 2 test tenants
    # Create realistic discovery flows
    # Create sample assets with infrastructure data
    # No is_mock fields anywhere
```

### Day 2: Model Layer Updates
**Goal**: Update all SQLAlchemy models to match new schema

#### Task 2.1: Remove V3 Model Files
**Action**: Delete entire `backend/app/models/v3/` directory

#### Task 2.2: Update Core Models
**Files to update**:
- `backend/app/models/data_import.py`
  - Rename: source_filename → filename
  - Rename: file_size_bytes → file_size  
  - Rename: file_type → mime_type
  - Add: error_message, error_details, source_system
  - Remove: is_mock, file_hash, import_config

- `backend/app/models/discovery_flow.py`
  - Keep: All boolean completion flags
  - Add: JSON fields (current_phase, phases_completed, crew_outputs)
  - Add: Error handling fields
  - Remove: is_mock, assessment_package, flow_description

- `backend/app/models/import_field_mapping.py`
  - Rename: mapping_type → match_type
  - Add: transformation_rules (replaces validation_rules)
  - Remove: validation_rules, user_feedback, sample_values

- `backend/app/models/asset.py`
  - Keep: ALL infrastructure and business fields
  - Keep: master_flow_id orchestration
  - Remove: is_mock, raw_data, field_mappings_used

#### Task 2.3: Remove Deprecated Models
**Files to delete**:
- `workflow_state.py`
- `discovery_asset.py`
- `mapping_learning_pattern.py`
- `data_quality_issue.py`
- `workflow_progress.py`
- `import_processing_step.py`

#### Task 2.4: Update Model Registry
**File**: `backend/app/models/__init__.py`
- Remove all V3 imports
- Remove deprecated model imports
- Update __all__ list

### Day 3: Repository & Service Updates
**Goal**: Update V3 repositories and services to use consolidated schema

#### Task 3.1: Update V3 Repositories to Use Consolidated Tables
**Action**: Update V3 repositories to reference consolidated tables (not v3_ prefixed tables)

#### Task 3.2: Update Repository Classes

**DataImportRepository**:
```python
async def create_import(self, import_data: dict):
    # Handle field renames
    if 'source_filename' in import_data:
        import_data['filename'] = import_data.pop('source_filename')
    # Remove deprecated fields
    import_data.pop('is_mock', None)
```

**DiscoveryFlowRepository**:
```python
async def update_phase_completion(self, flow_id, phase, completed=True):
    # Update both boolean flag and JSON state
    # Maintain hybrid approach for compatibility
```

**AssetRepository**:
```python
async def create_from_discovery(self, discovery_data, flow_id, master_flow_id):
    # Preserve all infrastructure fields
    # Link to master flow for orchestration
```

#### Task 3.3: Update V3 Service Layer
- Update V3 services to use consolidated models and field names
- Handle field migrations in service methods (filename, file_size, etc.)
- Implement error handling with new fields
- Ensure V3 services work with consolidated schema

### Day 4: API & Frontend Integration
**Goal**: Update all API endpoints and frontend code

#### Task 4.1: Update V3 API Endpoints
**Directory**: `backend/app/api/v3/`

- Handle field name changes in request/response
- Remove mock-related endpoints
- Add master_flow_id support
- Implement backward compatibility where needed

#### Task 4.2: Update TypeScript Interfaces
**File**: `frontend/src/types/api.ts`

```typescript
export interface DataImport {
  filename: string;  // was source_filename
  file_size?: number;  // was file_size_bytes
  mime_type?: string;  // was file_type
  master_flow_id?: string;  // new orchestration field
  // Remove: is_mock
}
```

#### Task 4.3: Update React Components
- Update all components using old field names
- Remove any mock-related UI elements
- Add error detail handling

#### Task 4.4: Create API Migration Guide
**File**: `docs/API_MIGRATION_GUIDE.md`
- Document all field renames
- List removed fields
- Provide code examples for migration

### Day 5: Testing & Staging Deployment
**Goal**: Comprehensive testing and staging deployment

#### Task 5.1: Create Test Suites
**Files to create**:
- `backend/tests/integration/test_db_consolidation.py`
- `backend/tests/e2e/test_full_discovery_flow.py`
- `backend/tests/performance/test_db_performance.py`

**Key Test Scenarios**:
```python
def test_no_v3_tables_exist():
    # Ensure complete V3 removal

def test_master_flow_relationships():
    # Verify orchestration works

def test_field_migrations():
    # Old field names handled gracefully

def test_multi_tenant_isolation():
    # No is_mock, proper tenant scoping
```

#### Task 5.2: Create Deployment Scripts
**File**: `scripts/deploy_db_consolidation.sh`
```bash
#!/bin/bash
# 1. Backup current database
# 2. Run consolidation migration
# 3. Validate schema
# 4. Run integration tests
# 5. Seed test data (non-prod)
```

#### Task 5.3: Deploy to Staging
- Deploy to Railway staging environment
- Run full E2E test suite
- Monitor for 4 hours
- Document any issues

### Day 6: Production Deployment
**Goal**: Deploy to all production environments

#### Task 6.1: Production Deployment Checklist
- [ ] All tests passing in staging
- [ ] Backup production database
- [ ] Schedule maintenance window
- [ ] Prepare rollback plan
- [ ] Update monitoring alerts

#### Task 6.2: Execute Production Deployment
1. Deploy to Railway production
2. Deploy to AWS production  
3. Run validation scripts
4. Monitor error rates
5. Check performance metrics

#### Task 6.3: Post-Deployment Validation
- Verify no V3 tables in production
- Check all APIs responding correctly
- Validate multi-tenant isolation
- Confirm master_flow_id relationships

## Critical Implementation Notes

### Field Migration Patterns
```python
# Always handle both old and new field names during transition
field_value = data.get('filename') or data.get('source_filename')

# Remove deprecated fields silently
data.pop('is_mock', None)
data.pop('file_hash', None)
```

### Multi-Tenant Patterns
```python
# Replace is_mock with dedicated test tenant
if testing:
    context.client_account_id = TEST_TENANT_ID
```

### Error Handling Pattern
```python
# Use new error fields consistently
{
    'status': 'failed',
    'error_message': str(error),
    'error_details': {
        'type': type(error).__name__,
        'traceback': traceback.format_exc()
    }
}
```

## Success Criteria

1. **Schema Consolidation**
   - [ ] No V3 tables exist in any environment
   - [ ] Single schema across all environments
   - [ ] All migrations run successfully

2. **Data Integrity**
   - [ ] No data loss during migration
   - [ ] Master flow relationships intact
   - [ ] All asset fields preserved

3. **Application Functionality**
   - [ ] All APIs working correctly
   - [ ] Frontend fully functional
   - [ ] No regression in features

4. **Performance**
   - [ ] No performance degradation
   - [ ] Proper indexes in place
   - [ ] Query performance maintained

5. **Multi-Tenancy**
   - [ ] Proper tenant isolation
   - [ ] No is_mock fields remain
   - [ ] Test data in dedicated tenant

## Rollback Plan

If issues arise:
1. Stop all application traffic
2. Run rollback script to restore backup
3. Restart applications with old code
4. Investigate and fix issues
5. Retry deployment with fixes

## Environment-Specific Notes

### Railway
- Use environment variables for migration flags
- Enable auto-migration on deployment
- Monitor resource usage during migration

### AWS
- Use Step Functions for orchestrated deployment
- Enable CloudWatch alarms
- Use RDS snapshots for backup

### Local Development
- Always use Docker containers
- Test migrations on fresh database
- Use separate test database

## Timeline Summary

- **Day 1**: Schema migration creation
- **Day 2**: Model layer updates  
- **Day 3**: Repository/service updates
- **Day 4**: API/frontend integration
- **Day 5**: Testing & staging deployment
- **Day 6**: Production deployment & monitoring

Total execution time: 6 days with single agent