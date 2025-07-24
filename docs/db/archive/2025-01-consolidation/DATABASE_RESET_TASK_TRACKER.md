# Database Reset and Seeding Task Tracker

## Overview
This tracker monitors the execution of the Database Reset and Comprehensive Seeding Plan. Each task has clear acceptance criteria and dependencies.

## Task Status Legend
- [ ] Not Started
- [🔄] In Progress
- [✅] Completed
- [❌] Blocked
- [⚠️] Needs Review

---

## Day 1: Database Reset and Migration (8 hours)

### Morning Session: Database Cleanup (4 hours)

#### Task 1.1: Backup and Documentation (1 hour)
- [ ] **1.1.1** Export current demo data from all tables
  - Command: `docker exec migration_postgres pg_dump -U postgres -d migration_db > backup_before_reset_$(date +%Y%m%d_%H%M%S).sql`
  - Store in: `backend/backups/`
  
- [ ] **1.1.2** Document current schema state
  - Export all table definitions
  - Save migration history: `docker exec migration_backend alembic history > migration_history_backup.txt`
  
- [ ] **1.1.3** Identify any custom data worth preserving
  - Review data_imports for reusable test files
  - Note any particularly good test scenarios

#### Task 1.2: Complete Database Reset (1 hour)
- [ ] **1.2.1** Stop all services
  ```bash
  docker-compose down
  ```

- [ ] **1.2.2** Drop and recreate database
  ```bash
  docker exec migration_postgres psql -U postgres -c "DROP DATABASE IF EXISTS migration_db;"
  docker exec migration_postgres psql -U postgres -c "CREATE DATABASE migration_db;"
  ```

- [ ] **1.2.3** Clear alembic version table
  ```bash
  docker exec migration_postgres psql -U postgres -d migration_db -c "DROP TABLE IF EXISTS alembic_version;"
  ```

- [ ] **1.2.4** Archive old migrations
  ```bash
  mkdir -p backend/alembic/versions/archived_$(date +%Y%m%d)
  mv backend/alembic/versions/*.py backend/alembic/versions/archived_$(date +%Y%m%d)/
  ```

#### Task 1.3: Model Alignment (2 hours)
- [ ] **1.3.1** Fix DiscoveryFlow model
  - Remove references to deprecated columns
  - Ensure all JSON columns are properly defined
  - Update to_dict() method
  
- [ ] **1.3.2** Verify DataImport model
  - Confirm field names match plan (filename, file_size, mime_type)
  - Remove any is_mock references
  
- [ ] **1.3.3** Check RawImportRecord model
  - Ensure uses record_index (not row_number)
  - Verify cleansed_data field name
  
- [ ] **1.3.4** Review all other models
  - Remove any remaining is_mock fields
  - Verify all relationships are correct
  - Check default values

### Afternoon Session: Clean Migration Creation (4 hours)

#### Task 1.4: Create Comprehensive Initial Migration (2 hours)
- [ ] **1.4.1** Generate new migration file
  ```bash
  docker exec migration_backend alembic revision -m "initial_clean_schema"
  ```

- [ ] **1.4.2** Define all enum types
  - asset_type_enum
  - flow_status_enum
  - import_status_enum
  - sixr_strategy_enum
  
- [ ] **1.4.3** Create core tables in correct order
  - client_accounts
  - engagements  
  - users
  - crewai_flow_state_extensions
  
- [ ] **1.4.4** Create discovery flow tables
  - discovery_flows (with correct schema)
  - data_imports
  - raw_import_records
  - import_field_mappings
  
- [ ] **1.4.5** Create asset tables
  - assets
  - asset_dependencies
  - assessments
  - migration_waves

#### Task 1.5: Migration Validation (1 hour)
- [ ] **1.5.1** Run migration locally
  ```bash
  docker exec migration_backend alembic upgrade head
  ```

- [ ] **1.5.2** Verify all tables created correctly
  - Check column names match models
  - Verify no deprecated columns exist
  - Confirm all indexes created
  
- [ ] **1.5.3** Test model compatibility
  - Import all models successfully
  - Create test records via SQLAlchemy
  - Verify no column mismatch errors

#### Task 1.6: Create Migration Documentation (1 hour)
- [ ] **1.6.1** Document schema decisions
- [ ] **1.6.2** Create ER diagram
- [ ] **1.6.3** List all foreign key relationships
- [ ] **1.6.4** Document multi-tenant strategy

---

## Day 2: Comprehensive Seeding Scripts (8 hours)

### Morning Session: Core Entities and Flows (4 hours)

#### Task 2.1: Setup Seeding Infrastructure (1 hour)
- [ ] **2.1.1** Create seeding script directory structure
  ```bash
  mkdir -p backend/scripts/seed_demo_data
  ```

- [ ] **2.1.2** Create base seeding utilities
  - Database connection helper
  - ID constants (demo client, engagement, etc.)
  - Logging configuration
  
- [ ] **2.1.3** Create data generators
  - Random name generators
  - IP address generators
  - Realistic metric generators

#### Task 2.2: Core Entity Seeding (1 hour)
- [ ] **2.2.1** Create 01_core_entities.py
  - Demo client account
  - Demo engagement
  - 4 demo users with proper RBAC roles:
    - demo@democorp.com (ENGAGEMENT_MANAGER, READ_WRITE)
    - analyst@democorp.com (ANALYST, READ_WRITE)
    - viewer@democorp.com (VIEWER, READ_ONLY)
    - client.admin@democorp.com (CLIENT_ADMIN, ADMIN)
  - User-account associations
  - User profiles with RBAC settings
  
- [ ] **2.2.2** Add supporting entities
  - 2 additional client accounts (for variety)
  - Tags for categorization
  - Role assignments

#### Task 2.3: Discovery Flow Seeding (1 hour)
- [ ] **2.3.1** Create 02_discovery_flows.py
  - 3 completed flows (different phases)
  - 1 in-progress flow (at field mapping stage)
  - 1 failed flow (with error details)
  
- [ ] **2.3.2** Add CrewAI state data
  - Realistic flow_state JSON
  - Agent insights
  - Performance metrics

#### Task 2.4: Data Import Seeding (45 minutes)
- [ ] **2.4.1** Create 03_data_imports.py
  - 3 imports with different sources:
    - CMDB export (CSV, completed)
    - Cloud inventory (JSON, completed)
    - Manual asset list (Excel, in-progress)
  - Realistic file sizes and names
  
- [ ] **2.4.2** Create sample import files
  - Generate actual CSV files
  - Create JSON data structures
  - Store in test_data directory

### Afternoon Session: Assets and Relationships (4 hours)

#### Task 2.5: Raw Import Records (45 minutes)
- [ ] **2.5.1** Create 04_raw_import_records.py
  - 150-200 raw records across 3 imports
  - Mix of valid and invalid records
  - Various data quality issues
  - Enough to generate 60 final assets
  
- [ ] **2.5.2** Add cleansed data
  - Transformation results
  - Validation outcomes
  - Processing timestamps

#### Task 2.6: Field Mapping Seeding (30 minutes)
- [ ] **2.6.1** Create 05_field_mappings.py
  - Mappings for each import
  - Mix of approved/pending/rejected
  - Various confidence scores
  - Transformation rules

#### Task 2.7: Asset Inventory Seeding (1 hour)
- [ ] **2.7.1** Create 06_assets.py
  - 10 Applications (Java, .NET, Python, Legacy)
  - 35 Servers (20 Linux, 15 Windows)
  - 10 Databases (Oracle, SQL Server, PostgreSQL)
  - 5 Network devices (load balancers, firewalls)
  
- [ ] **2.7.2** Add realistic metadata
  - Proper hostnames/IPs
  - Resource specifications
  - Business context
  - Technical owners

#### Task 2.8: Relationships and Dependencies (1 hour)
- [ ] **2.8.1** Create 07_dependencies.py
  - Application-to-server mappings
  - Database dependencies
  - Network relationships
  - Circular dependencies (for testing)
  
- [ ] **2.8.2** Create 08_assessments.py
  - Technical assessments
  - Risk evaluations
  - Performance metrics
  - Security findings

---

## Day 3: Testing and Validation (8 hours)

### Morning Session: Execution and Verification (4 hours)

#### Task 3.1: Run Complete Seeding (1 hour)
- [ ] **3.1.1** Create run_all_seeds.py master script
- [ ] **3.1.2** Execute full seeding
  ```bash
  docker exec migration_backend python scripts/seed_demo_data/run_all_seeds.py
  ```
- [ ] **3.1.3** Monitor execution time
- [ ] **3.1.4** Check for any errors

#### Task 3.2: Data Validation (1 hour)
- [ ] **3.2.1** Verify record counts
  - Check each table has expected rows
  - Validate foreign key integrity
  - Ensure no orphaned records
  
- [ ] **3.2.2** Test data relationships
  - Navigate from client → engagement → flows → assets
  - Verify all joins work correctly
  - Check multi-tenant isolation

#### Task 3.3: Query Performance Testing (1 hour)
- [ ] **3.3.1** Test complex queries
  - Asset search with filters
  - Discovery flow aggregations
  - Dependency analysis queries
  
- [ ] **3.3.2** Check index usage
  - Run EXPLAIN on key queries
  - Verify indexes are utilized
  - Identify any missing indexes

#### Task 3.4: API Endpoint Testing (1 hour)
- [ ] **3.4.1** Test data retrieval endpoints
  - Discovery flow status
  - Asset inventory
  - Field mappings
  
- [ ] **3.4.2** Test data modification endpoints
  - Approve field mappings
  - Update asset metadata
  - Progress discovery flows

### Afternoon Session: UI Validation (4 hours)

#### Task 3.5: Page-by-Page Testing (2 hours)
- [ ] **3.5.1** Login as demo@democorp.com
- [ ] **3.5.2** Test each UI page:
  - [ ] Dashboard (shows summary data)
  - [ ] Discovery Flows (lists all flows)
  - [ ] CMDB Import (can see previous imports)
  - [ ] Attribute Mapping (has mappings to approve)
  - [ ] Asset Inventory (shows all assets)
  - [ ] Dependency Analysis (displays relationships)
  - [ ] Migration Planning (waves visible)
  - [ ] Analytics (metrics populated)

#### Task 3.6: Workflow Testing (1 hour)
- [ ] **3.6.1** Complete discovery flow workflow
  - Start new import
  - Map fields
  - Review assets
  - Complete flow
  
- [ ] **3.6.2** Test error scenarios
  - View failed import
  - Handle validation errors
  - Recovery procedures

#### Task 3.7: Documentation Updates (1 hour)
- [ ] **3.7.1** Update README with seed commands
- [ ] **3.7.2** Document demo scenarios
- [ ] **3.7.3** Create demo user guide
- [ ] **3.7.4** Update developer setup guide

---

## Validation Checklist

### Schema Validation
- [ ] All models match database schema exactly
- [ ] No deprecated columns exist
- [ ] All required columns present
- [ ] Foreign keys properly defined
- [ ] Indexes created correctly

### Data Validation  
- [ ] Every table has demo data
- [ ] Multi-tenant isolation working
- [ ] No orphaned records
- [ ] Relationships properly linked
- [ ] Realistic data distributions

### Application Validation
- [ ] All pages show data for demo user
- [ ] No empty states (unless intentional)
- [ ] Workflows complete successfully
- [ ] Performance acceptable
- [ ] No console errors

---

## Risk Log

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| Data loss | High | Complete backup before reset | |
| Migration failure | High | Test locally first | |
| Seeding errors | Medium | Incremental seeding with validation | |
| Performance issues | Medium | Monitor query times, add indexes | |
| Missing relationships | Low | Validation scripts | |

---

## Notes Section

### Decisions Made:
- 

### Issues Encountered:
- 

### Future Improvements:
- 

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Tech Lead | | | |
| QA | | | |

---

**Total Tasks**: 65
**Estimated Time**: 24 hours (3 days)
**Priority**: Critical (Blocks proper development)

**Next Review**: End of Day 1