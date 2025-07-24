# Database Migration Guide - AI Modernize Migration Platform

## Table of Contents
1. [Overview](#overview)
2. [Alembic Migration System](#alembic-migration-system)
3. [Migration Strategy](#migration-strategy)
4. [Initialization Process](#initialization-process)
5. [Test Data Seeding](#test-data-seeding)
6. [Migration Best Practices](#migration-best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

## Overview

This guide provides comprehensive documentation for database migrations and initialization procedures for the AI Modernize Migration Platform. The system uses Alembic for version control of database schema changes and includes automated test data seeding for development environments.

### Key Principles
- **Single Schema**: All tables exist in the `migration` schema
- **Atomic Migrations**: Each migration is self-contained and reversible
- **Multi-Tenant**: Test data uses dedicated tenant IDs, not boolean flags
- **Idempotent**: Migrations can be run multiple times safely

## Alembic Migration System

### Configuration

The Alembic configuration is located at `/backend/alembic.ini` with the following key settings:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88
```

### Environment Configuration

The `/backend/alembic/env.py` file configures the migration environment:

```python
from alembic import context
from sqlalchemy import pool
from app.core.database import Base
from app.core.config import settings

# Import all models to ensure they're registered
from app.models import *

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="migration",
        include_schemas=True
    )

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        connection.execute("SET search_path TO migration")
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            version_table_schema="migration",
            include_schemas=True
        )
```

## Migration Strategy

### Consolidated Schema Approach

Based on the analysis, we're implementing a consolidated migration strategy:

1. **Single Comprehensive Migration**: Create one migration that builds the entire schema from scratch
2. **No V3 Tables**: Eliminate parallel table systems
3. **Preserve Architecture**: Maintain master_flow_id orchestration pattern
4. **Multi-Tenant Design**: Remove is_mock fields in favor of tenant isolation

### Migration File Structure

```
/backend/alembic/versions/
├── 001_consolidated_schema.py      # Complete schema creation
├── 002_initial_indexes.py          # Performance indexes
├── 003_row_level_security.py      # RLS policies for multi-tenancy
├── 004_test_data_seed.py          # Development test data
└── 005_production_constraints.py   # Additional constraints
```

## Initialization Process

### Step 1: Database Creation

```bash
# Create database and migration schema
psql -U postgres -c "CREATE DATABASE migration_db;"
psql -U postgres -d migration_db -c "CREATE SCHEMA IF NOT EXISTS migration;"
psql -U postgres -d migration_db -c "CREATE EXTENSION IF NOT EXISTS pgvector;"
```

### Step 2: Run Migrations

```bash
# Initialize Alembic (first time only)
cd backend
alembic init alembic

# Create the consolidated migration
alembic revision --autogenerate -m "Consolidated schema creation"

# Run all migrations
alembic upgrade head

# Verify migration status
alembic current
alembic history
```

### Step 3: Validate Schema

```python
# Run validation script
python scripts/validate_schema.py
```

## Test Data Seeding

### Test Tenant Strategy

Instead of using `is_mock` fields, we use dedicated test tenants:

```python
# Test tenant constants
TEST_TENANT_1 = "11111111-1111-1111-1111-111111111111"  # TechCorp Solutions
TEST_TENANT_2 = "22222222-2222-2222-2222-222222222222"  # Global Retail Inc

# Test engagement IDs
TEST_ENGAGEMENT_1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # Cloud Migration 2025
TEST_ENGAGEMENT_2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # App Modernization Q1
```

### Seed Script Structure

Create `/backend/scripts/seed_test_data.py`:

```python
import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import (
    ClientAccount, User, Engagement, 
    CrewAIFlowStateExtension, DiscoveryFlow,
    DataImport, Asset, ImportFieldMapping
)

async def seed_test_data(db: AsyncSession):
    """Seed comprehensive test data for development."""
    
    # 1. Create test client accounts
    client1 = ClientAccount(
        id=UUID(TEST_TENANT_1),
        name="TechCorp Solutions",
        slug="techcorp",
        description="Test technology company",
        industry="Technology",
        company_size="1000-5000",
        subscription_tier="enterprise",
        settings={
            "features": ["advanced_discovery", "ai_assessment"],
            "api_access": True
        },
        agent_preferences={
            "discovery_depth": "comprehensive",
            "automation_level": "full",
            "risk_tolerance": "moderate"
        }
    )
    
    client2 = ClientAccount(
        id=UUID(TEST_TENANT_2),
        name="Global Retail Inc",
        slug="globalretail",
        description="Test retail company",
        industry="Retail",
        company_size="5000+",
        subscription_tier="standard"
    )
    
    db.add_all([client1, client2])
    
    # 2. Create test users
    users = [
        User(
            auth0_user_id="auth0|test_admin_001",
            email="admin@techcorp.com",
            full_name="Test Admin",
            is_active=True
        ),
        User(
            auth0_user_id="auth0|test_analyst_001",
            email="analyst@techcorp.com",
            full_name="Test Analyst",
            is_active=True
        )
    ]
    db.add_all(users)
    await db.flush()
    
    # 3. Create test engagements
    engagement1 = Engagement(
        id=UUID(TEST_ENGAGEMENT_1),
        client_account_id=UUID(TEST_TENANT_1),
        name="Cloud Migration 2025",
        description="Migrate legacy applications to AWS",
        engagement_type="migration",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=180)).date(),
        status="active",
        target_applications=15,
        estimated_complexity="high",
        created_by=users[0].id
    )
    
    engagement2 = Engagement(
        id=UUID(TEST_ENGAGEMENT_2),
        client_account_id=UUID(TEST_TENANT_2),
        name="App Modernization Q1",
        description="Modernize e-commerce platform",
        engagement_type="modernization",
        status="planning"
    )
    
    db.add_all([engagement1, engagement2])
    await db.flush()
    
    # 4. Create master flow orchestration
    master_flow = CrewAIFlowStateExtension(
        flow_id=UUID("33333333-3333-3333-3333-333333333333"),
        flow_type="full_migration",
        client_account_id=UUID(TEST_TENANT_1),
        engagement_id=UUID(TEST_ENGAGEMENT_1),
        display_name="Full Migration Workflow",
        description="Complete migration from discovery to execution",
        current_phase="discovery",
        phase_history=["initialization", "discovery"],
        crew_ai_state={
            "agents": ["discovery_agent", "assessment_agent"],
            "current_task": "environment_scanning"
        }
    )
    db.add(master_flow)
    await db.flush()
    
    # 5. Create discovery flow with master linkage
    discovery_flow = DiscoveryFlow(
        flow_id=UUID("44444444-4444-4444-4444-444444444444"),
        master_flow_id=master_flow.flow_id,  # Link to master
        client_account_id=UUID(TEST_TENANT_1),
        engagement_id=UUID(TEST_ENGAGEMENT_1),
        user_id=users[0].id,
        discovery_type="automated",
        target_platforms=["vmware", "aws", "applications"],
        status="in_progress",
        phases={
            "initialization": {"status": "completed", "completed_at": "2025-01-20T10:00:00Z"},
            "agent_loading": {"status": "completed", "completed_at": "2025-01-20T10:05:00Z"},
            "environment_scanning": {"status": "in_progress", "started_at": "2025-01-20T10:10:00Z"},
            "data_collection": {"status": "pending"},
            "analysis": {"status": "pending"},
            "reporting": {"status": "pending"}
        },
        discovered_assets_count=0,
        created_at=datetime.now()
    )
    db.add(discovery_flow)
    await db.flush()
    
    # 6. Create data import with realistic data
    data_import = DataImport(
        client_account_id=UUID(TEST_TENANT_1),
        engagement_id=UUID(TEST_ENGAGEMENT_1),
        master_flow_id=master_flow.flow_id,  # Link to master
        import_name="VMware vCenter Export",
        import_type="vmware_vcenter",
        filename="vcenter_export_20250120.csv",
        file_size=15728640,  # 15MB
        mime_type="text/csv",
        source_system="VMware vCenter 7.0",
        status="completed",
        progress_percentage=100.0,
        total_records=1250,
        processed_records=1250,
        failed_records=0,
        started_at=datetime.now() - timedelta(hours=2),
        completed_at=datetime.now() - timedelta(hours=1),
        imported_by=users[0].id
    )
    db.add(data_import)
    await db.flush()
    
    # 7. Create sample assets with varied data
    assets = []
    for i in range(50):
        asset = Asset(
            client_account_id=UUID(TEST_TENANT_1),
            engagement_id=UUID(TEST_ENGAGEMENT_1),
            master_flow_id=master_flow.flow_id,  # Link to master
            discovery_flow_id=discovery_flow.id,
            
            # Core identification
            asset_name=f"vm-prod-{i:03d}",
            asset_type="server" if i < 30 else "application",
            asset_subtype="virtual_machine" if i < 30 else "web_application",
            
            # Infrastructure details (some fields populated, some null)
            hostname=f"vm-prod-{i:03d}.techcorp.local" if i < 30 else None,
            ip_address=f"10.100.1.{100 + i}" if i < 30 else None,
            os_type="linux" if i % 2 == 0 else "windows" if i < 30 else None,
            os_version="Ubuntu 20.04" if i % 2 == 0 else "Windows Server 2019" if i < 30 else None,
            
            # Resources (populated for servers)
            cpu_cores=4 if i < 30 else None,
            memory_gb=16.0 if i < 30 else None,
            storage_gb=500.0 if i < 30 else None,
            
            # Business context
            environment="production" if i < 20 else "staging" if i < 40 else "development",
            business_unit="Engineering" if i % 3 == 0 else "Sales" if i % 3 == 1 else "Operations",
            business_criticality="critical" if i < 10 else "high" if i < 30 else "medium",
            
            # Application details (populated for applications)
            application_name=f"App-{i:03d}" if i >= 30 else None,
            technology_stack=["Java", "Spring Boot", "PostgreSQL"] if i >= 30 else None,
            
            # Migration planning
            six_r_strategy="rehost" if i < 20 else "replatform" if i < 35 else "refactor",
            migration_complexity="low" if i < 10 else "medium" if i < 35 else "high",
            migration_priority=1 if i < 10 else 2 if i < 30 else 3,
            migration_wave=1 if i < 20 else 2 if i < 40 else 3,
            
            # Metrics (some populated)
            cpu_utilization_percent=float(30 + (i % 50)) if i < 30 else None,
            memory_utilization_percent=float(40 + (i % 40)) if i < 30 else None,
            
            # Quality scores
            completeness_score=0.85 if i < 20 else 0.70 if i < 40 else 0.60,
            confidence_score=0.90 if i < 30 else 0.75,
            
            created_at=datetime.now() - timedelta(hours=1)
        )
        assets.append(asset)
    
    db.add_all(assets)
    await db.flush()
    
    # 8. Create field mappings for the import
    field_mappings = [
        ImportFieldMapping(
            data_import_id=data_import.id,
            client_account_id=UUID(TEST_TENANT_1),
            master_flow_id=master_flow.flow_id,
            source_field="VM Name",
            target_field="asset_name",
            match_type="exact",
            confidence_score=1.0,
            status="approved",
            suggested_by="discovery_agent",
            approved_by=users[0].id,
            approved_at=datetime.now()
        ),
        ImportFieldMapping(
            data_import_id=data_import.id,
            client_account_id=UUID(TEST_TENANT_1),
            master_flow_id=master_flow.flow_id,
            source_field="IP Address",
            target_field="ip_address",
            match_type="exact",
            confidence_score=1.0,
            status="approved",
            transformation_rules={"format": "validate_ipv4"}
        ),
        ImportFieldMapping(
            data_import_id=data_import.id,
            client_account_id=UUID(TEST_TENANT_1),
            master_flow_id=master_flow.flow_id,
            source_field="Operating System",
            target_field="os_type",
            match_type="fuzzy",
            confidence_score=0.85,
            status="suggested",
            transformation_rules={
                "mapping": {
                    "Windows Server*": "windows",
                    "Ubuntu*": "linux",
                    "Red Hat*": "linux"
                }
            }
        )
    ]
    
    db.add_all(field_mappings)
    await db.commit()
    
    print("✅ Test data seeded successfully!")
    print(f"  - 2 Client Accounts")
    print(f"  - 2 Users")
    print(f"  - 2 Engagements")
    print(f"  - 1 Master Flow")
    print(f"  - 1 Discovery Flow")
    print(f"  - 1 Data Import")
    print(f"  - 50 Assets")
    print(f"  - 3 Field Mappings")

# Command-line execution
if __name__ == "__main__":
    asyncio.run(seed_test_data())
```

### Running Test Data Seeding

```bash
# Development environment only
cd backend
python scripts/seed_test_data.py

# Or as part of initialization
make init-dev-db
```

## Migration Best Practices

### 1. Migration Naming Convention

```
001_initial_schema.py
002_add_indexes.py
003_update_constraints.py
```

- Use 3-digit prefixes for ordering
- Descriptive names indicating the change
- Keep migrations focused on single concerns

### 2. Safe Migration Patterns

```python
def upgrade():
    # Check if table exists before creating
    if not op.get_bind().dialect.has_table(op.get_bind(), 'table_name'):
        op.create_table('table_name', ...)
    
    # Check if column exists before adding
    inspector = Inspector.from_engine(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('table_name')]
    if 'new_column' not in columns:
        op.add_column('table_name', sa.Column('new_column', sa.String))
    
    # Safe enum creation
    enum_type = sa.Enum('value1', 'value2', name='my_enum')
    enum_type.create(op.get_bind(), checkfirst=True)
```

### 3. Data Migration Patterns

```python
def upgrade():
    # Add new column with default
    op.add_column('assets', 
        sa.Column('migration_status', sa.String, server_default='pending')
    )
    
    # Backfill data
    op.execute("""
        UPDATE assets 
        SET migration_status = CASE 
            WHEN six_r_strategy IS NOT NULL THEN 'analyzed'
            ELSE 'pending'
        END
    """)
    
    # Remove default
    op.alter_column('assets', 'migration_status', server_default=None)
```

### 4. Performance Considerations

```python
def upgrade():
    # Create indexes concurrently in production
    op.execute("SET statement_timeout = 0")
    op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_assets_master_flow_id ON assets(master_flow_id)")
    
    # Batch large updates
    op.execute("""
        UPDATE assets 
        SET updated_at = NOW() 
        WHERE id IN (
            SELECT id FROM assets 
            WHERE updated_at IS NULL 
            LIMIT 1000
        )
    """)
```

### 5. Row-Level Security Implementation

```python
# File: 003_row_level_security.py
def upgrade():
    # Enable RLS on all tenant-scoped tables
    tables = [
        'assets', 'discovery_flows', 'data_imports', 
        'import_field_mappings', 'assessments', 'agent_learning_patterns'
    ]
    
    for table in tables:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        
        # Create policy for application role
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            FOR ALL TO application_role
            USING (client_account_id = current_setting('app.client_id')::uuid)
        """)
        
        # Create policy for superuser (bypass RLS)
        op.execute(f"""
            CREATE POLICY {table}_superuser ON {table}
            FOR ALL TO postgres
            USING (true)
        """)
    
    # Grant usage to application role
    op.execute("GRANT USAGE ON SCHEMA migration TO application_role")
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA migration TO application_role")

def downgrade():
    # Disable RLS if needed
    tables = ['assets', 'discovery_flows', 'data_imports', ...]
    for table in tables:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Migration Fails Due to Existing Objects

```bash
# Error: relation "assets" already exists

# Solution: Check and clean up
psql -d migration_db -c "DROP TABLE IF EXISTS migration.assets CASCADE;"

# Or use conditional creation in migration
if not op.get_bind().dialect.has_table(op.get_bind(), 'assets', schema='migration'):
    op.create_table('assets', ...)
```

#### 2. Foreign Key Constraint Violations

```bash
# Error: insert or update on table "assets" violates foreign key constraint

# Solution: Check data integrity
SELECT * FROM assets WHERE client_account_id NOT IN (SELECT id FROM client_accounts);

# Fix orphaned records
DELETE FROM assets WHERE client_account_id NOT IN (SELECT id FROM client_accounts);
```

#### 3. Schema Mismatch

```bash
# Compare database with models
alembic revision --autogenerate -m "detect_changes"

# Review generated migration
# If changes detected, review and apply
```

#### 4. Enum Type Conflicts

```python
# In migration, handle existing enums
from sqlalchemy.dialects.postgresql import ENUM

def upgrade():
    # Check if enum exists
    op.execute("DO $$ BEGIN CREATE TYPE asset_type AS ENUM ('server', 'application', 'database'); EXCEPTION WHEN duplicate_object THEN null; END $$")
```

### Debugging Commands

```bash
# Show current migration version
alembic current

# Show migration history
alembic history --verbose

# Show SQL without executing
alembic upgrade head --sql

# Stamp database with specific version (careful!)
alembic stamp head
```

## Rollback Procedures

### 1. Immediate Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001_initial_schema

# Rollback all migrations (careful!)
alembic downgrade base
```

### 2. Emergency Recovery

```bash
# 1. Stop application
systemctl stop migration-app

# 2. Create backup of current state
pg_dump -U postgres -d migration_db > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Restore from previous backup
psql -U postgres -d migration_db < last_known_good_backup.sql

# 4. Reset Alembic version
alembic stamp <last_good_revision>

# 5. Restart application
systemctl start migration-app
```

### 3. Partial Rollback

For rolling back specific changes while keeping others:

```python
# Create compensating migration
def downgrade():
    # Reverse specific changes
    op.drop_column('assets', 'new_problematic_column')
    
    # But keep other changes intact
    # Don't touch successfully migrated data
```

## Production Deployment Checklist

### Pre-Deployment

- [ ] Test migrations on staging environment
- [ ] Create full database backup
- [ ] Review migration SQL with `alembic upgrade head --sql`
- [ ] Check for blocking queries or locks
- [ ] Notify team of maintenance window

### Deployment

- [ ] Enable maintenance mode
- [ ] Run migrations with timeout monitoring
- [ ] Validate schema changes
- [ ] Run smoke tests
- [ ] Monitor error logs

### Post-Deployment

- [ ] Verify all migrations applied
- [ ] Check application functionality
- [ ] Monitor performance metrics
- [ ] Keep backup for 72 hours
- [ ] Document any issues encountered

## Environment-Specific Configuration

### Development

```python
# .env.development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/migration_dev
ALEMBIC_CONFIG=alembic-dev.ini
AUTO_MIGRATE=true
SEED_TEST_DATA=true
```

### Staging

```python
# .env.staging
DATABASE_URL=postgresql://user:pass@staging-db:5432/migration_staging
ALEMBIC_CONFIG=alembic.ini
AUTO_MIGRATE=true
SEED_TEST_DATA=false
```

### Production

```python
# .env.production
DATABASE_URL=postgresql://user:pass@prod-db:5432/migration_prod
ALEMBIC_CONFIG=alembic.ini
AUTO_MIGRATE=false  # Manual migrations only
SEED_TEST_DATA=false
```

## Continuous Integration

### GitHub Actions Migration Check

```yaml
name: Database Migration Check

on: [push, pull_request]

jobs:
  migration-check:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Create test database
        env:
          PGPASSWORD: postgres
        run: |
          psql -h localhost -U postgres -c "CREATE DATABASE test_migration;"
          psql -h localhost -U postgres -d test_migration -c "CREATE SCHEMA migration;"
          
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_migration
        run: |
          cd backend
          alembic upgrade head
          
      - name: Check for uncommitted migrations
        run: |
          cd backend
          alembic revision --autogenerate -m "check_changes"
          git diff --exit-code
```

---

*Database Migration Guide for AI Modernize Migration Platform - January 2025*