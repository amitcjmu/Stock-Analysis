# CMDB Fields Implementation Plan

**Document Purpose:** Comprehensive implementation plan for adding missing CMDB fields to AIForce-Assess platform

**Status:** Draft - Ready for Review  
**Date:** 2025-10-28  
**Related Issues:** #833 (Enhancement), #753 (Demo Dataset)  
**Implementation Approach:** Hybrid Architecture (Explicit Columns + JSONB + New Tables)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Type Analysis](#data-type-analysis)
3. [Architectural Constraints](#architectural-constraints)
4. [System Impact Analysis](#system-impact-analysis)
5. [Implementation Phases](#implementation-phases)
6. [Detailed Implementation Plan](#detailed-implementation-plan)
7. [Testing Strategy](#testing-strategy)
8. [Rollback Plan](#rollback-plan)
9. [Timeline & Effort Estimates](#timeline--effort-estimates)

---

## 1. Executive Summary

### Objective
Extend database schema with 40+ CMDB fields for comprehensive migration planning (Issue #753). Follow hybrid approach from Issue #833 review.

### Implementation Strategy
- **24 explicit columns** → `assets` table (high-query frequency fields)
- **10+ JSONB fields** → Use existing `custom_attributes`/`technical_details` 
- **5 fields rejected** → Already exist in other tables
- **2 new tables** → `asset_eol_assessments`, `asset_contacts` (normalized data)
- **6 columns** → Enhance `asset_dependencies` (network discovery)

### Key Constraints (ADRs)
- **ADR-005**: Database consolidation, migration schema, master flow tracking
- **ADR-009**: Multi-tenant isolation (client_account_id, engagement_id, RLS)
- **ADR-013**: Collection Flow integration, JSONB usage patterns
- **ADR-023**: Collection Flow phase redesign (removed platform_detection, automated_collection)
- **ADR-027**: Universal FlowTypeConfig pattern, PhaseConfig with can_skip/can_pause/dependencies/validators
- **ADR-028**: No phase_state duplication - use master flow only
- **ADR-030**: Adaptive questionnaire architecture, bulk operations

### Timeline
**Target: 1-2 days** - Fast implementation leveraging existing patterns and infrastructure.

---

## 2. Data Type Analysis

### 2.1 Existing Column Data Type Patterns

Based on analysis of `/backend/app/models/asset/models.py` and related enrichment tables:

| Pattern | Data Type | Example Usage | Length Constants |
|---------|-----------|---------------|------------------|
| **Short Strings** | `String(SMALL_STRING_LENGTH)` | Status, enum-like fields | 50 chars |
| **Medium Strings** | `String(MEDIUM_STRING_LENGTH)` | Names, identifiers | 100 chars |
| **Large Strings** | `String(LARGE_STRING_LENGTH)` | Descriptions, URLs | 255 chars |
| **Long Text** | `Text` | Detailed descriptions, rationales | Unlimited |
| **Booleans** | `Boolean` | Flags, yes/no fields | N/A |
| **Integers** | `Integer` | Counts, priorities, RTOs | N/A |
| **Floats** | `Float` | Percentages, costs, scores | N/A |
| **High Precision** | `Float8` (DOUBLE PRECISION) | Utilization metrics, financial data | N/A |
| **Dates** | `Date` | Renewal dates, EOL dates | N/A |
| **Timestamps** | `DateTime(timezone=True)` | Audit timestamps | With timezone |
| **UUIDs** | `PostgresUUID(as_uuid=True)` | Primary/foreign keys | N/A |
| **JSON** | `JSON` | Unstructured data | N/A |
| **JSONB** | `JSONB` | Structured, queryable JSON | N/A (PostgreSQL) |
| **Arrays** | `ARRAY(Text)` | Lists (e.g., compliance_scopes) | N/A |

### 2.2 Recommended Data Types for New Fields

#### Category C: 24 Explicit Column Fields

| Field Name | Recommended Type | Rationale |
|-----------|------------------|-----------|
| `business_unit` | `String(100)` | MEDIUM_STRING_LENGTH, commonly used |
| `vendor` | `String(255)` | LARGE_STRING_LENGTH, may include long vendor names |
| `application_type` | `String(20)` | Enum-like (COTS/Custom/Custom-COTS/Other) |
| `lifecycle` | `String(20)` | Enum-like (Retire/Replace/Retain/Invest) |
| `hosting_model` | `String(20)` | Enum-like (On-prem/Cloud/Hybrid) |
| `database_type` | `String(100)` | MEDIUM_STRING_LENGTH, various DB names |
| `database_version` | `String(50)` | SMALL_STRING_LENGTH, version strings |
| `database_size_gb` | `Float` | Numeric storage size |
| `pii_flag` | `Boolean` | Yes/No flag |
| `has_saas_replacement` | `Boolean` | Yes/No flag |
| `server_role` | `String(20)` | Enum-like (Web/DB/App/Citrix) |
| `security_zone` | `String(50)` | SMALL_STRING_LENGTH, zone names |
| `cpu_utilization_percent_max` | `Float` | Match existing `cpu_utilization_percent` pattern |
| `memory_utilization_percent_max` | `Float` | Match existing `memory_utilization_percent` pattern |
| `storage_free_gb` | `Float` | Numeric storage metric |
| `backup_policy` | `Text` | Long descriptions |
| `asset_tags` | `JSONB` | Array of tags, better than TEXT for querying |
| `annual_cost_estimate` | `Float` | Financial data, match `current_monthly_cost` pattern |
| `proposed_treatmentplan_rationale` | `Text` | Long text justification |
| `risk_level` | `String(20)` | Enum-like (Low/Medium/High/Critical) |
| `tshirt_size` | `String(10)` | Enum-like (S/M/L/XL) |
| `application_data_classification` | `String(50)` | Classification levels |

#### Category B: JSONB Storage Fields (10+ fields)

Store in existing `custom_attributes` or `technical_details` JSONB columns:

```json
{
  "infrastructure": {
    "virtualization_platform": "VMware ESXi 7.0",
    "clustering": true,
    "dr_support": true,
    "data_volume_characteristics": 5000
  },
  "application": {
    "user_load_patterns": "Peak 9AM-5PM EST",
    "complexity": {
      "business_logic": "medium",
      "configuration": "high"
    },
    "migration_readiness": {
      "cloud_readiness": "medium",
      "change_tolerance": "low"
    },
    "tech_debt_flags": true
  }
}
```

#### Category D: New Tables

**1. `asset_eol_assessments` Table:**
```sql
CREATE TABLE migration.asset_eol_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
    technology_component VARCHAR(255) NOT NULL,
    eol_date DATE,
    eol_risk_level VARCHAR(20),  -- low, medium, high, critical
    assessment_notes TEXT,
    remediation_options JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**2. `asset_contacts` Table:**
```sql
CREATE TABLE migration.asset_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
    contact_type VARCHAR(50) NOT NULL,  -- 'business_owner', 'technical_owner', 'architect'
    user_id UUID REFERENCES users(id),  -- If contact is platform user
    email VARCHAR(255),  -- Fallback for non-user contacts
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT contact_identity_check CHECK (user_id IS NOT NULL OR email IS NOT NULL)
);
```

**3. Enhanced `asset_dependencies` Table:**
Add network discovery columns:
```sql
ALTER TABLE migration.asset_dependencies
    ADD COLUMN port INTEGER,
    ADD COLUMN protocol_name VARCHAR(50),
    ADD COLUMN conn_count INTEGER,
    ADD COLUMN bytes_total BIGINT,
    ADD COLUMN first_seen TIMESTAMP WITH TIME ZONE,
    ADD COLUMN last_seen TIMESTAMP WITH TIME ZONE;
```

---

## 3. Architectural Constraints

### 3.1 ADR Compliance Requirements

#### ADR-005: Database Consolidation Architecture
- **Constraint**: Must use `migration` schema
- **Constraint**: All tables must include multi-tenant isolation (`client_account_id`, `engagement_id`)
- **Constraint**: Must reference `master_flow_id` for flow tracking
- **Impact**: All new tables must follow these patterns

#### ADR-009: Multi-Tenant Architecture
- **Constraint**: Row-level security (RLS) policies required
- **Constraint**: All queries must filter by `client_account_id` and `engagement_id`
- **Constraint**: Repository pattern must enforce tenant boundaries
- **Impact**: New columns/tables must integrate with existing RLS policies

#### ADR-013: Adaptive Data Collection Integration
- **Constraint**: Collection Flow uses `custom_attributes` JSONB for questionnaire responses
- **Constraint**: Gap analysis expects specific attribute mapping structures
- **Constraint**: Must not conflict with existing gap detection logic
- **Impact**: JSONB fields must follow collection flow conventions

### 3.2 Naming Conventions

| Convention | Pattern | Example |
|------------|---------|---------|
| **Table Names** | Snake case, plural | `asset_eol_assessments` |
| **Column Names** | Snake case | `database_size_gb` |
| **Enum Names** | PascalCase | `ApplicationType` |
| **Enum Values** | Lower snake case | `on_prem`, `cloud`, `hybrid` |
| **JSONB Keys** | Snake case | `virtualization_platform` |

### 3.3 Indexing Strategy

**Must add indexes for:**
- Enum-like columns used in WHERE clauses
- Foreign key columns
- Multi-tenant isolation columns
- High-cardinality query fields

```sql
CREATE INDEX idx_assets_business_unit ON migration.assets(business_unit);
CREATE INDEX idx_assets_vendor ON migration.assets(vendor);
CREATE INDEX idx_assets_lifecycle ON migration.assets(lifecycle);
CREATE INDEX idx_assets_hosting_model ON migration.assets(hosting_model);
CREATE INDEX idx_assets_server_role ON migration.assets(server_role);
CREATE INDEX idx_assets_pii_flag ON migration.assets(pii_flag);
```

---

## 4. System Impact Analysis

### 4.1 Discovery Flow Impact

**Components Affected:**
1. **Data Import Service** (`backend/app/services/data_import/`)
   - **Impact**: Field mappings must recognize new CSV columns
   - **Action Required**: Update `ImportFieldMapping` to support new target fields
   - **File**: `backend/app/services/data_import/import_storage_handler.py`

2. **Discovery Flow Metadata** (`backend/app/services/discovery_flow_service.py`)
   - **Impact**: `detected_columns` metadata may include new fields
   - **Action Required**: No changes needed (auto-detects columns)

3. **Asset Creation Logic** (`backend/app/services/crewai_flows/unified_discovery_flow/`)
   - **Impact**: Agent must populate new fields from parsed CMDB data
   - **Action Required**: Update asset creation phase to map new columns
   - **File**: Phase executors in discovery flow

### 4.2 Collection Flow Impact

**Components Affected:**
1. **Gap Detection** (`backend/app/services/collection/gap_scanner/`)
   - **Impact**: Critical attributes configuration may need new fields
   - **Action Required**: Update `critical_attributes.py` with new field mappings
   - **File**: `backend/app/services/collection/critical_attributes.py`

2. **Questionnaire Generation** (`backend/app/services/collection/`)
   - **Impact**: New fields may trigger questionnaire questions
   - **Action Required**: Update attribute mappings for database/vendor/lifecycle fields
   - **File**: Questionnaire generators

3. **Enriched Data Queries** (`backend/app/services/collection/gap_scanner/gap_detector.py`)
   - **Impact**: `get_enriched_asset_data()` must include new enrichment tables
   - **Action Required**: Update enrichment queries to JOIN new tables
   - **File**: `gap_detector.py:get_enriched_asset_data()`

### 4.3 Assessment Flow Impact

**Components Affected:**
1. **6R Analysis** (`backend/app/services/assessment/`)
   - **Impact**: New fields provide better context for strategy recommendations
   - **Action Required**: Update 6R decision logic to consider `lifecycle`, `hosting_model`, `has_saas_replacement`
   - **File**: Assessment service decision engines

2. **Application Resolver** (`backend/app/services/assessment/application_resolver.py`)
   - **Impact**: Canonical application matching may use `vendor`, `application_type`
   - **Action Required**: Consider enhancing matching logic
   - **File**: `application_resolver.py`

### 4.4 API Layer Impact

**Components Affected:**
1. **Pydantic Schemas** (`backend/app/schemas/`)
   - **Impact**: Request/response schemas must include new fields
   - **Action Required**: Update AssetCreate, AssetUpdate, AssetResponse schemas
   - **Files**: `backend/app/schemas/asset.py` (or equivalent)

2. **Asset Endpoints** (`backend/app/api/v1/endpoints/`)
   - **Impact**: Asset CRUD operations must handle new fields
   - **Action Required**: Validate enum values, handle JSONB structure
   - **Files**: Asset management endpoints

3. **Filtering/Sorting** (`backend/app/repositories/`)
   - **Impact**: New filterable columns in asset lists
   - **Action Required**: Add filter params for `business_unit`, `vendor`, `lifecycle`, etc.
   - **Files**: Asset repository query methods

### 4.5 Frontend Impact

**Components Affected:**
1. **Asset Detail Views** (`src/pages/`, `src/components/`)
   - **Impact**: Display new fields in asset cards/details
   - **Action Required**: Update TypeScript interfaces and React components
   - **Files**: Asset display components

2. **Filter/Search UI** (`src/components/discovery/inventory/`)
   - **Impact**: New filter options for business_unit, vendor, lifecycle
   - **Action Required**: Add filter UI components
   - **Files**: Inventory filter components

3. **Collection Flow Forms** (`src/components/collection/`)
   - **Impact**: Questionnaire forms may include new fields
   - **Action Required**: Update form schemas and validation
   - **Files**: Adaptive form components

### 4.6 Migration/Rollback Impact

**Database Changes:**
- **Forward Migration**: Add 24 columns, create 2 tables, alter 1 table
- **Backward Migration**: Drop columns/tables (requires data backup)
- **Data Retention**: Use `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL` for non-breaking changes

---

## 5. Implementation Phases

### Phase 1: Database Schema Changes
**Focus:** Alembic migrations, database structure

**Tasks:**
1. Create 3 Alembic migrations (idempotent, schema-qualified)
2. Define new enum types
3. Add indexes
4. Update PostgreSQL RLS policies

**Deliverables:**
- Migration 107: Add 24 explicit columns to `assets` table
- Migration 108: Create 2 new tables (`asset_eol_assessments`, `asset_contacts`)
- Migration 109: Enhance `asset_dependencies` with 6 network discovery columns

### Phase 2: ORM Model Updates
**Focus:** SQLAlchemy models, Python layer

**Tasks:**
1. Create `CMDBFieldsMixin` with 24 new columns
2. Add mixin to `Asset` model
3. Create new model classes for specialized tables
4. Update `AssetDependency` model
5. Define new enum classes
6. Add relationships

**Deliverables:**
- `backend/app/models/asset/cmdb_fields.py`
- `backend/app/models/asset/specialized.py`
- Updated `backend/app/models/asset/enums.py`
- Updated `backend/app/models/asset/relationships.py`

### Phase 3: Repository Pattern Integration
**Focus:** Data access layer, queries

**Tasks:**
1. Update asset repository query methods
2. Add filtering/sorting for new columns
3. Update enrichment data queries
4. Add JSONB path queries for `custom_attributes`
5. Ensure multi-tenant filtering

**Deliverables:**
- Updated repository methods
- Query optimization
- Multi-tenant compliance verification

### Phase 4: Service Layer Updates
**Focus:** Business logic integration

**Tasks:**
1. Update Discovery Flow asset creation logic
2. Update Collection Flow gap detection
3. Update Assessment Flow 6R logic
4. Update field mapping handlers
5. Add validation rules

**Deliverables:**
- Updated discovery flow phase executors
- Updated collection flow critical attributes
- Updated assessment decision logic
- Enhanced field mapping support

### Phase 5: API Layer Updates
**Focus:** Pydantic schemas, endpoints

**Tasks:**
1. Update AssetCreate/AssetUpdate/AssetResponse schemas
2. Add enum validation
3. Update endpoint query parameters
4. Add new filter/sort options
5. Update API documentation

**Deliverables:**
- Updated Pydantic schemas
- Enhanced filtering capabilities
- API docs with new fields

### Phase 6: Frontend Integration
**Focus:** React/TypeScript updates

**Tasks:**
1. Update TypeScript asset interfaces
2. Add new fields to asset display components
3. Update collection flow forms
4. Add filter UI for new fields
5. Update discovery inventory views

**Deliverables:**
- Updated TypeScript types
- Enhanced asset detail views
- New filter components
- Updated collection forms

### Phase 7: Testing & Validation
**Focus:** Comprehensive testing

**Tasks:**
1. Unit tests for new models/repositories
2. Integration tests for data import
3. E2E tests for collection flow
4. Migration testing (up/down)
5. Multi-tenant isolation verification

**Deliverables:**
- Unit test coverage
- Integration test suite
- E2E test scenarios
- Migration validation report

### Phase 8: Documentation & Deployment
**Focus:** Documentation, rollout

**Tasks:**
1. Update schema documentation
2. Create data import guide
3. Update API documentation
4. Create demo dataset with new fields
5. Production deployment plan

**Deliverables:**
- Updated documentation
- Demo dataset (Issue #753)
- Deployment checklist
- Rollback procedures

---

## 6. Detailed Implementation Plan

### 6.1 Phase 1: Database Schema - Migration 107

**File:** `backend/alembic/versions/107_add_cmdb_explicit_fields.py`

**Key Points:**
- Idempotent `IF NOT EXISTS` checks for all 24 columns
- Schema-qualified: `migration.assets`
- Add indexes: business_unit, vendor, lifecycle, hosting_model, server_role, pii_flag
- GIN index for asset_tags JSONB
- Comments on all columns

**Columns to add:** business_unit, vendor, application_type, lifecycle, hosting_model, server_role, security_zone, database_type, database_version, database_size_gb, cpu_utilization_percent_max, memory_utilization_percent_max, storage_free_gb, pii_flag, application_data_classification, has_saas_replacement, risk_level, tshirt_size, proposed_treatmentplan_rationale, annual_cost_estimate, backup_policy, asset_tags


**See Appendix A for full migration code.**

### 6.2 Phase 1: Database Schema - Migration 108

**File:** `backend/alembic/versions/108_create_cmdb_specialized_tables.py`

**Key Points:**
- Create `asset_eol_assessments` table (multi-tenant, EOL tracking)
- Create `asset_contacts` table (normalized contact management)
- Both tables include client_account_id, engagement_id (multi-tenant)
- Foreign keys to assets with CASCADE
- Indexes on asset_id, tenant fields
- Check constraints for enum values

**See Appendix A for full migration code.**

### 6.3 Phase 1: Database Schema - Migration 109

**File:** `backend/alembic/versions/109_enhance_asset_dependencies_network_discovery.py`

**Key Points:**
- Add 6 network discovery columns to `asset_dependencies`
- Columns: port, protocol_name, conn_count, bytes_total, first_seen, last_seen
- Index on last_seen for temporal queries
- Support network flow analysis data

**See Appendix A for full migration code.**

### 6.4 Phase 2: ORM Model Updates

**File:** `backend/app/models/asset/cmdb_fields.py`

**Create CMDBFieldsMixin:**
- Define all 24 columns using SQLAlchemy Column definitions
- Follow existing patterns (String lengths, Float vs Integer)
- Include comments and nullable=True for backward compatibility

**File:** `backend/app/models/asset/specialized.py`

**Create specialized models:**
- `AssetEOLAssessment`: End-of-life assessments
- `AssetContact`: Normalized contact management
- Include TimestampMixin, multi-tenant fields
- Add to_dict() methods for API responses

**File:** `backend/app/models/asset/enums.py`

**Add new enums:**
- ApplicationType (cots, custom, custom_cots, other)
- Lifecycle (retire, replace, retain, invest)
- HostingModel (on_prem, cloud, hybrid, colo)
- ServerRole (web, db, app, citrix, file, email, other)
- RiskLevel (low, medium, high, critical)
- TShirtSize (xs, s, m, l, xl, xxl)

**File:** `backend/app/models/asset/relationships.py`

**Update AssetDependency:**
- Add 6 network discovery columns
- Update __init__.py exports

### 6.5 Phase 3-5: Service, API, Frontend

**Repository Layer:**
- Update asset queries for new filters
- Update enrichment data queries (JOIN new tables)
- Ensure multi-tenant filtering

**Service Layer:**
- Discovery Flow: Update asset creation logic
- Collection Flow: Update critical_attributes.py, gap_detector.py
- Assessment Flow: Update 6R decision logic

**API Layer:**
- Update Pydantic schemas with new fields
- Add enum validation
- Add filter/sort parameters

**Frontend:**
- Update TypeScript interfaces
- Update asset display components
- Add filter UI components
- Update collection forms

**Testing:**
- Unit tests for models
- Integration tests for flows
- E2E tests
- Migration tests

---

## 7. Testing Strategy

**Unit Tests:**
- Asset model with new CMDB fields
- Enum validation
- JSONB field handling
- Repository queries

**Integration Tests:**
- CMDB import with new fields
- Discovery flow processing
- Collection gap detection
- Assessment 6R logic

**Migration Tests:**
- Forward migration (107, 108, 109)
- Idempotency verification
- Backward migration
- Data preservation

**E2E Tests:**
- Full flow: Upload → Discovery → Collection → Assessment
- Frontend displays new fields
- Filters work correctly

---

## 8. Rollback Plan

### Rollback Procedure
```bash
# 1. Backup database FIRST
pg_dump -h localhost -U postgres migration_db > backup_pre_rollback.sql

# 2. Rollback migrations (reverse order)
alembic downgrade 108_create_cmdb_specialized_tables  # Rollback 109
alembic downgrade 107_add_cmdb_explicit_fields  # Rollback 108
alembic downgrade 106_update_existing_tables  # Rollback 107

# 3. Verify and restart
psql -h localhost -U postgres migration_db -c "\d migration.assets"
docker-compose restart backend
```

### ⚠️ WARNING
Rolling back after production use will **LOSE DATA**:
- All new column data deleted
- New tables dropped
- Network discovery metadata lost

**Mitigation:**
- Test thoroughly in staging
- Back up before production deployment
- Consider "soft rollback" (disable features, keep schema)

---

## 10. Appendices

### Appendix A: Complete Migration Code

**Full Alembic migration code with all column definitions, table schemas, and detailed SQL statements is maintained in AI context for implementation phase.**

When implementing:
- Migration 107: 24 explicit columns with idempotent checks
- Migration 108: 2 new tables with full schemas
- Migration 109: 6 network discovery columns

### Appendix B: Field Categorization Summary

**Category A - Rejected (5 fields):**
rto_hours, rpo_minutes, technical_detail, business_owner_email, technical_owner_email

**Category B - JSONB Storage (10+ fields):**
virtualization_platform, clustering, dr_support, data_volume_characteristics, user_load_patterns, business_logic_complexity, configuration_complexity, change_tolerance, cloud_readiness, tech_debt_flags

**Category C - Explicit Columns (24 fields):**
business_unit, vendor, application_type, lifecycle, hosting_model, database_type, database_version, database_size_gb, pii_flag, has_saas_replacement, server_role, security_zone, cpu_utilization_percent_max, memory_utilization_percent_max, storage_free_gb, backup_policy, asset_tags, annual_cost_estimate, proposed_treatmentplan_rationale, risk_level, tshirt_size, application_data_classification

**Category D - New Tables (2 tables):**
asset_eol_assessments, asset_contacts

**Category E - Enhanced Tables (1 table):**
asset_dependencies (+6 network discovery columns)

### Appendix C: JSONB Structure Example

```json
{
  "infrastructure": {
    "virtualization": {
      "platform": "VMware ESXi",
      "version": "7.0",
      "clustering": true,
      "dr_support": true
    },
    "data_volume_characteristics": 5000
  },
  "application": {
    "load_patterns": {
      "user_load_patterns": "Peak 9AM-5PM EST"
    },
    "complexity": {
      "business_logic": "medium",
      "configuration": "high"
    },
    "migration_readiness": {
      "cloud_readiness": "medium",
      "change_tolerance": "low"
    },
    "tech_debt_flags": true
  }
}
```

### Appendix D: Related Documentation

**Issues:**
- #833: Map CMDB related fields (this implementation)
- #753: Create Realistic Demo Dataset

**ADRs:**
- ADR-005: Database Consolidation Architecture
- ADR-009: Multi-Tenant Architecture  
- ADR-013: Adaptive Data Collection Integration
- ADR-023: Collection Flow Phase Redesign
- ADR-028: Eliminate Collection Phase State Duplication
- ADR-030: Adaptive Questionnaire Architecture

---

**END OF IMPLEMENTATION PLAN**

**Document Status:** Concise Reference - Full implementation details available in AI context
