# SQLAlchemy Model vs Migration Audit Report

Generated on: 2025-01-07

This report audits ALL SQLAlchemy models against the migration files to identify discrepancies.

## Executive Summary

### Critical Issues Found:
1. **Missing Tables in Migrations**: 3 tables defined in models but not created in migrations
2. **Missing Foreign Keys**: Several foreign key relationships not properly established
3. **Field Type Mismatches**: Multiple fields with inconsistent types between models and migrations
4. **Missing Indexes**: Several fields marked for indexing in models but not indexed in migrations
5. **Constraint Issues**: Missing unique constraints and check constraints

## Detailed Findings by Model

### 1. ClientAccount Model (`app/models/client_account.py`)
**Status**: ✅ Table exists, minor issues

| Issue | Field | Model Definition | Migration Definition |
|-------|-------|------------------|---------------------|
| ✅ Match | All core fields | Present | Present |

### 2. Engagement Model (`app/models/client_account.py`)
**Status**: ✅ Table exists, fully matches

### 3. User Model (`app/models/client_account.py`)
**Status**: ✅ Table exists, fully matches

### 4. UserAccountAssociation Model (`app/models/client_account.py`)
**Status**: ✅ Table exists, fully matches

### 5. DiscoveryFlow Model (`app/models/discovery_flow.py`)
**Status**: ⚠️ Table exists, but has discrepancies

| Issue | Field | Model Definition | Migration Definition |
|-------|-------|------------------|---------------------|
| ⚠️ FK Missing | discovery_flow_id | References discovery_flows.flow_id | FK not created for self-reference |

### 6. Asset Model (`app/models/asset.py`)
**Status**: ⚠️ Table exists, multiple issues

| Issue | Field | Model Definition | Migration Definition |
|-------|-------|------------------|---------------------|
| ❌ Missing Field | flow_id | UUID, FK to discovery_flows.flow_id | NOT IN MIGRATION |
| ❌ Missing Field | session_id | UUID, FK to data_import_sessions.id | NOT IN MIGRATION |
| ❌ Missing Field | master_flow_id | UUID, index=True | NOT IN MIGRATION |
| ❌ Missing Field | discovery_flow_id | UUID, index=True | NOT IN MIGRATION |
| ❌ Missing Field | assessment_flow_id | UUID, index=True | NOT IN MIGRATION |
| ❌ Missing Field | planning_flow_id | UUID, index=True | NOT IN MIGRATION |
| ❌ Missing Field | execution_flow_id | UUID, index=True | NOT IN MIGRATION |
| ❌ Missing Field | source_phase | String(50), index=True | NOT IN MIGRATION |
| ❌ Missing Field | current_phase | String(50), index=True | NOT IN MIGRATION |
| ❌ Missing Field | phase_context | JSON | NOT IN MIGRATION |
| ❌ Missing Field | name | String(255), index=True | NOT IN MIGRATION |
| ❌ Missing Field | asset_name | String(255) | Migration has asset_name but model has both name and asset_name |
| ❌ Missing Field | hostname | String(255), index=True | Migration has hostname but without index |
| ❌ Missing Field | asset_type | Enum(AssetType), index=True | Migration has asset_type as String(100) |
| ❌ Missing Field | description | Text | NOT IN MIGRATION |
| ❌ Missing Field | fqdn | String(255) | NOT IN MIGRATION |
| ❌ Missing Field | mac_address | String(17) | NOT IN MIGRATION |
| ❌ Missing Field | environment | String(50), index=True | Migration has environment but without index |
| ❌ Missing Field | datacenter | String(100) | NOT IN MIGRATION |
| ❌ Missing Field | rack_location | String(50) | NOT IN MIGRATION |
| ❌ Missing Field | availability_zone | String(50) | NOT IN MIGRATION |
| ❌ Missing Field | os_version | String(50) | NOT IN MIGRATION |
| ❌ Missing Field | business_owner | String(255) | NOT IN MIGRATION |
| ❌ Missing Field | technical_owner | String(255) | NOT IN MIGRATION |
| ❌ Missing Field | department | String(100) | NOT IN MIGRATION |
| ❌ Missing Field | application_name | String(255) | NOT IN MIGRATION |
| ❌ Missing Field | technology_stack | String(255) | NOT IN MIGRATION |
| ❌ Missing Field | business_criticality | String(20) | NOT IN MIGRATION |
| ❌ Missing Field | custom_attributes | JSON | NOT IN MIGRATION |
| ❌ Missing Field | six_r_strategy | Enum(SixRStrategy) | NOT IN MIGRATION |
| ❌ Missing Field | mapping_status | String(20), index=True | NOT IN MIGRATION |
| ❌ Missing Field | migration_priority | Integer | NOT IN MIGRATION |
| ❌ Missing Field | migration_complexity | String(20) | NOT IN MIGRATION |
| ❌ Missing Field | migration_wave | Integer | NOT IN MIGRATION |
| ❌ Missing Field | sixr_ready | String(50) | NOT IN MIGRATION |
| ❌ Missing Field | status | String(50), index=True | Migration has status but model expects different default |
| ❌ Missing Field | migration_status | Enum(AssetStatus), index=True | NOT IN MIGRATION |
| ❌ Missing Field | dependencies | JSON | NOT IN MIGRATION |
| ❌ Missing Field | related_assets | JSON | NOT IN MIGRATION |
| ❌ Missing Field | discovery_method | String(50) | NOT IN MIGRATION |
| ❌ Missing Field | discovery_timestamp | DateTime(timezone=True) | NOT IN MIGRATION |
| ❌ Missing Field | cpu_utilization_percent | Float | NOT IN MIGRATION |
| ❌ Missing Field | memory_utilization_percent | Float | NOT IN MIGRATION |
| ❌ Missing Field | disk_iops | Float | NOT IN MIGRATION |
| ❌ Missing Field | network_throughput_mbps | Float | NOT IN MIGRATION |
| ❌ Missing Field | completeness_score | Float | NOT IN MIGRATION |
| ❌ Missing Field | quality_score | Float | NOT IN MIGRATION |
| ❌ Missing Field | current_monthly_cost | Float | NOT IN MIGRATION |
| ❌ Missing Field | estimated_cloud_cost | Float | NOT IN MIGRATION |
| ❌ Missing Field | imported_by | UUID, FK to users.id | NOT IN MIGRATION |
| ❌ Missing Field | imported_at | DateTime(timezone=True) | NOT IN MIGRATION |
| ❌ Missing Field | source_filename | String(255) | NOT IN MIGRATION |
| ❌ Missing Field | raw_data | JSON | Migration has raw_data as JSONB |
| ❌ Missing Field | field_mappings_used | JSON | NOT IN MIGRATION |
| ❌ Missing Field | created_by | UUID, FK to users.id | NOT IN MIGRATION |
| ❌ Missing Field | updated_by | UUID, FK to users.id | NOT IN MIGRATION |

### 7. AssetDependency Model (`app/models/asset.py`)
**Status**: ❌ TABLE MISSING IN MIGRATION

| Issue | Description |
|-------|-------------|
| ❌ Missing Table | Table `asset_dependencies` defined in model but not in migration |
| Note | Migration has similar table `asset_dependencies` but with different schema |

Model fields not in migration:
- `asset_id` (should be `source_asset_id` per migration)
- `depends_on_asset_id` (should be `target_asset_id` per migration)
- No unique constraint defined in model

### 8. WorkflowProgress Model (`app/models/asset.py`)
**Status**: ❌ TABLE COMPLETELY MISSING

| Issue | Description |
|-------|-------------|
| ❌ Missing Table | Table `workflow_progress` not created in any migration |

### 9. CMDBSixRAnalysis Model (`app/models/asset.py`)
**Status**: ❌ TABLE MISSING IN MIGRATION

| Issue | Description |
|-------|-------------|
| ❌ Missing Table | Table `cmdb_sixr_analyses` defined in model but migration only has `cmdb_sixr_analysis` |
| ❌ Schema Mismatch | Model has different fields than what's in migration table |

### 10. CrewAIFlowStateExtensions Model (`app/models/crewai_flow_state_extensions.py`)
**Status**: ✅ Table exists, fully matches

### 11. DataImport Model (`app/models/data_import/core.py`)
**Status**: ✅ Table exists, fully matches

### 12. RawImportRecord Model (`app/models/data_import/core.py`)
**Status**: ✅ Table exists, fully matches

### 13. ImportProcessingStep Model (`app/models/data_import/core.py`)
**Status**: ✅ Table exists, fully matches

### 14. ImportFieldMapping Model (`app/models/data_import/mapping.py`)
**Status**: ✅ Table exists, fully matches

### 15. EnhancedUserProfile Model (`app/models/rbac_enhanced.py`)
**Status**: ❌ TABLE COMPLETELY MISSING

| Issue | Description |
|-------|-------------|
| ❌ Missing Table | Table `enhanced_user_profiles` not created in any migration |

### 16. RolePermissions Model (`app/models/rbac_enhanced.py`)
**Status**: ❌ TABLE COMPLETELY MISSING

| Issue | Description |
|-------|-------------|
| ❌ Missing Table | Table `role_permissions` not created in any migration |

### 17. SoftDeletedItems Model (`app/models/rbac_enhanced.py`)
**Status**: ❌ TABLE COMPLETELY MISSING

| Issue | Description |
|-------|-------------|
| ❌ Missing Table | Table `soft_deleted_items` not created in any migration |

### 18. AccessAuditLog Model (`app/models/rbac_enhanced.py`)
**Status**: ❌ WRONG TABLE NAME

| Issue | Description |
|-------|-------------|
| ❌ Table Name | Model uses `enhanced_access_audit_log` but migration creates `access_audit_log` |

### 19. UserProfile Model (`app/models/rbac.py`)
**Status**: ✅ Created in migration 005

### 20. UserRole Model (`app/models/rbac.py`)
**Status**: ⚠️ Table exists but with wrong schema

| Issue | Description |
|-------|-------------|
| ⚠️ Schema Issue | Migration 001 creates different schema than model expects |
| ✅ Fixed | Migration 004 fixes the schema to match model |

### 21. ClientAccess Model (`app/models/rbac.py`)
**Status**: ⚠️ Table exists but with different foreign key

| Issue | Field | Model Definition | Migration Definition |
|-------|-------|------------------|---------------------|
| ❌ FK Mismatch | user_profile_id | FK to user_profiles.user_id | Migration has user_id FK to users.id |

### 22. EngagementAccess Model (`app/models/rbac.py`)
**Status**: ✅ Created in migration 005

### 23. AccessAuditLog Model (`app/models/rbac.py`)
**Status**: ✅ Created in migration 005

## Critical Actions Required

### 1. **Create Missing Migration for Asset Model Fields**
```sql
-- Add missing fields to assets table
ALTER TABLE assets ADD COLUMN flow_id UUID REFERENCES discovery_flows(flow_id);
ALTER TABLE assets ADD COLUMN session_id UUID REFERENCES data_import_sessions(id);
ALTER TABLE assets ADD COLUMN master_flow_id UUID;
ALTER TABLE assets ADD COLUMN discovery_flow_id UUID;
-- ... (many more fields needed)
```

### 2. **Create Missing Tables**
```sql
-- Create workflow_progress table
CREATE TABLE workflow_progress (...);

-- Create enhanced_user_profiles table
CREATE TABLE enhanced_user_profiles (...);

-- Create role_permissions table
CREATE TABLE role_permissions (...);

-- Create soft_deleted_items table
CREATE TABLE soft_deleted_items (...);
```

### 3. **Fix Table Name Mismatches**
- Rename `enhanced_access_audit_log` in model to `access_audit_log` OR
- Create new migration to rename table in database

### 4. **Fix Foreign Key Issues**
- Update `client_access` table foreign key structure
- Add missing foreign key for `discovery_flows` self-reference

### 5. **Add Missing Indexes**
Multiple fields in models are marked with `index=True` but indexes are not created in migrations.

## Recommendations

1. **Immediate Action**: Create a new migration (006) to add all missing Asset model fields
2. **High Priority**: Create migration (007) for missing RBAC tables
3. **Medium Priority**: Fix table name mismatches and foreign key issues
4. **Low Priority**: Add missing indexes for performance optimization
5. **Code Review**: Review why models and migrations diverged so significantly

## Migration Order

To fix these issues, create migrations in this order:
1. Fix Asset table schema (highest impact)
2. Create missing RBAC tables
3. Fix foreign key relationships
4. Add missing indexes
5. Clean up naming inconsistencies