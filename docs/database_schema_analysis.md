# Database Schema Analysis - Asset Model Alignment

## Current Database Schema Analysis

### Overview
- **Table**: `migration.assets`
- **Total Columns**: 74 columns
- **Primary Key**: `id` (integer, auto-increment)
- **Foreign Keys**: `migration_id` → `migrations(id)`
- **Referenced By**: `assessments`, `asset_dependencies`, `workflow_progress`

### Schema Breakdown by Category

#### **Identity Fields**
```sql
id                          | integer                  | not null | PK auto-increment
migration_id                | integer                  | not null | FK to migrations
name                        | character varying(255)   | not null | 
asset_type                  | assettype                | not null | ENUM
asset_id                    | character varying(100)   | nullable |
asset_name                  | character varying(255)   | nullable |
```

#### **Multi-Tenancy Fields** 
```sql
client_account_id           | uuid                     | nullable |
engagement_id               | uuid                     | nullable |
```

#### **Discovery & Source Fields**
```sql
hostname                    | character varying(255)   | nullable |
ip_address                  | character varying(45)    | nullable |
fqdn                        | character varying(255)   | nullable |
environment                 | character varying(50)    | nullable |
datacenter                  | character varying(100)   | nullable |
rack_location               | character varying(50)    | nullable |
availability_zone           | character varying(50)    | nullable |
discovery_method            | character varying(50)    | nullable |
discovery_source            | character varying(100)   | nullable |
source_system               | character varying(100)   | nullable |
source_file                 | character varying(255)   | nullable |
```

#### **Technical Specifications**
```sql
operating_system            | character varying(100)   | nullable |
os_version                  | character varying(50)    | nullable |
cpu_cores                   | integer                  | nullable |
memory_gb                   | double precision         | nullable |
storage_gb                  | double precision         | nullable |
network_interfaces          | json                     | nullable |
intelligent_asset_type      | character varying(100)   | nullable |
hardware_type               | character varying(100)   | nullable |
```

#### **Application Fields**
```sql
description                 | text                     | nullable |
application_id              | character varying(100)   | nullable |
application_version         | character varying(50)    | nullable |
programming_language        | character varying(100)   | nullable |
framework                   | character varying(100)   | nullable |
database_type               | character varying(100)   | nullable |
```

#### **Business & Ownership**
```sql
business_owner              | character varying(100)   | nullable |
technical_owner             | character varying(100)   | nullable |
department                  | character varying(100)   | nullable |
business_criticality        | character varying(20)    | nullable |
```

#### **Migration Strategy & Assessment**
```sql
status                      | assetstatus              | nullable | ENUM
six_r_strategy              | sixrstrategy             | nullable | ENUM  
migration_priority          | integer                  | nullable |
migration_complexity        | character varying(20)    | nullable |
migration_wave              | integer                  | nullable |
sixr_ready                  | character varying(20)    | nullable |
estimated_migration_effort  | character varying(20)    | nullable |
recommended_6r_strategy     | character varying(20)    | nullable |
strategy_confidence         | double precision         | nullable |
strategy_rationale          | text                     | nullable |
```

#### **Dependencies & Relationships**
```sql
dependencies                | json                     | nullable |
dependents                  | json                     | nullable |
```

#### **Risk & Security**
```sql
risk_score                  | double precision         | nullable |
security_classification     | character varying(50)    | nullable |
vulnerability_score         | double precision         | nullable |
security_findings           | json                     | nullable |
compatibility_issues        | json                     | nullable |
```

#### **Cost Analysis**
```sql
current_monthly_cost        | double precision         | nullable |
estimated_cloud_cost        | double precision         | nullable |
cost_optimization_potential | double precision         | nullable |
estimated_monthly_cost      | double precision         | nullable |
license_cost                | double precision         | nullable |
support_cost                | double precision         | nullable |
```

#### **Quality & Performance**
```sql
cloud_readiness_score       | double precision         | nullable |
modernization_complexity    | character varying(20)    | nullable |
tech_debt_score             | double precision         | nullable |
performance_metrics         | json                     | nullable |
completeness_score          | double precision         | nullable |
quality_score               | double precision         | nullable |
```

#### **AI Analysis & Recommendations**
```sql
ai_recommendations          | json                     | nullable |
confidence_score            | double precision         | nullable |
ai_confidence_score         | double precision         | nullable |
last_ai_analysis            | timestamp with time zone | nullable |
```

#### **Workflow Status Fields** (Added by our migrations)
```sql
discovery_status            | character varying(50)    | default 'discovered' |
mapping_status              | character varying(50)    | default 'pending'    |
cleanup_status              | character varying(50)    | default 'pending'    |
assessment_readiness        | character varying(50)    | default 'not_ready'  |
```

#### **Audit Fields**
```sql
discovered_at               | timestamp with time zone | default now() |
last_scanned                | timestamp with time zone | nullable |
created_at                  | timestamp with time zone | default now() |
updated_at                  | timestamp with time zone | nullable |
import_batch_id             | character varying(100)   | nullable |
created_by                  | character varying(100)   | nullable |
updated_by                  | character varying(100)   | nullable |
```

#### **Compliance Requirements**
```sql
compliance_requirements     | json                     | nullable |
```

## Asset Model Analysis

### Current Issues with Asset Model

1. **Primary Key Mismatch**: 
   - Model likely expects UUID primary key
   - Database has integer auto-increment primary key

2. **Type Mismatches**:
   - JSON fields in database but model may expect strings
   - ENUM types need proper SQLAlchemy enum definitions
   - Double precision vs Float field types

3. **Missing Field Definitions**:
   - Model may not have all 74 database columns defined
   - Workflow status fields may not be properly mapped

4. **Default Values**:
   - Database has defaults that model doesn't specify
   - May cause insertion issues if model provides explicit None values

## Recommended Fix Strategy

### Option 1: Align Model to Match Database (RECOMMENDED)
**Pros**: 
- Preserves existing data
- Faster to implement
- No additional migrations needed
- Works with existing foreign key relationships

**Cons**: 
- Need to update model significantly
- May require updating other models that reference Asset

### Option 2: Align Database to Match Model
**Pros**: 
- Keeps current model design intact
- May be more "clean" architecturally  

**Cons**: 
- Requires complex data migration
- Risk of data loss
- Breaking change to existing relationships
- Much more time consuming

## Specific Fix Plan (Option 1 - Align Model to Database)

### 1. Create AssetMinimal Model First
- Include only essential fields that definitely work
- Use for testing and validation
- Gradually expand

### 2. Fix Asset Model Field Types
- Change primary key to Integer
- Define proper Enum types for assettype, assetstatus, sixrstrategy
- Use JSON type for JSON fields
- Match all column names and types exactly

### 3. Handle Defaults Properly
- Let database defaults work (don't override with None)
- Remove fields from INSERT if they should use defaults

### 4. Test Incrementally
- Test with minimal fields first
- Add fields gradually
- Validate each step

## Next Steps

1. **Create AssetMinimal model** - Test basic CRUD operations
2. **Create comprehensive Asset model fix** - Align all 74 fields
3. **Update test script** - Validate with real data
4. **Test workflow services** - Ensure integration works
5. **Document field mappings** - For future reference

## Database Schema vs Model Field Mapping

| Database Column | Expected Model Field | Type Match | Notes |
|-----------------|---------------------|------------|-------|
| id | id | ❌ Integer vs UUID | Need to change model to Integer |
| name | name | ✅ VARCHAR(255) | Should work |
| asset_type | asset_type | ❌ ENUM | Need SQLAlchemy Enum definition |
| network_interfaces | network_interfaces | ❌ JSON | Need JSON type, not TEXT |
| dependencies | dependencies | ❌ JSON | Need JSON type, not TEXT |
| client_account_id | client_account_id | ✅ UUID | Should work |
| engagement_id | engagement_id | ✅ UUID | Should work |

*(Full mapping to be completed during fix implementation)*

## Success Criteria

- [ ] Asset model can perform basic CRUD operations without SQL errors
- [ ] All 74 database columns properly mapped in model
- [ ] Type mismatches resolved
- [ ] Default values handled correctly
- [ ] Foreign key relationships working
- [ ] Integration with workflow services functional 