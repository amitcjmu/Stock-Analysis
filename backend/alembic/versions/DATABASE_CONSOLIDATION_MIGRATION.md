# Database Consolidation Migration

## Overview

This migration (`20250101_database_consolidation.py`) consolidates the entire database schema as part of the platform remediation effort. It combines all necessary schema changes into a single migration that can be applied automatically during deployment.

## Changes Included

### 1. V3 Table Removal
Drops all `v3_` prefixed tables:
- `v3_discovery_flows`
- `v3_data_imports`
- `v3_import_field_mappings`
- `v3_assets`
- `v3_raw_import_records`
- `v3_asset_dependencies`
- `v3_migration_waves`

### 2. Field Renames
Updates field names to follow new conventions:

#### data_imports table:
- `source_filename` → `filename`
- `file_size_bytes` → `file_size`
- `file_type` → `mime_type`

#### discovery_flows table:
- `attribute_mapping_completed` → `field_mapping_completed`
- `inventory_completed` → `asset_inventory_completed`
- `dependencies_completed` → `dependency_analysis_completed`
- `tech_debt_completed` → `tech_debt_assessment_completed`

#### assets table:
- `memory_mb` → `memory_gb`
- `storage_mb` → `storage_gb`

### 3. Deprecated Column Removal
Drops the `is_mock` column from:
- `client_accounts`
- `engagements`
- `users`
- `user_account_associations`
- `data_import_sessions`
- `tags`
- `asset_embeddings`
- `asset_tags`

Also drops other deprecated columns:
- `data_imports.file_hash`
- `data_imports.import_config`
- `data_imports.raw_data`
- `discovery_flows.assessment_package`
- `discovery_flows.flow_description`
- `discovery_flows.user_feedback`
- `import_field_mappings.sample_values`

### 4. New Column Additions
Adds new columns for enhanced state management:

#### discovery_flows table:
- `flow_state` (JSONB) - CrewAI flow state
- `phase_state` (JSONB) - Phase-specific state
- `agent_state` (JSONB) - Agent state tracking
- `error_message` (Text) - Error descriptions
- `error_phase` (String) - Phase where error occurred
- `error_details` (JSON) - Detailed error information

#### data_imports table:
- `source_system` (String) - Track data source system

### 5. Index Creation
Creates multi-tenant and performance indexes:

#### Multi-tenant indexes:
- `idx_data_imports_client_account`
- `idx_data_imports_engagement`
- `idx_discovery_flows_client_account`
- `idx_discovery_flows_engagement`
- `idx_import_field_mappings_client_account`
- `idx_assets_client_account`
- `idx_assets_engagement`

#### Performance indexes:
- `idx_discovery_flows_status`
- `idx_discovery_flows_flow_id`
- `idx_data_imports_status`
- `idx_assets_asset_type`
- `idx_assets_discovery_flow`

### 6. Deprecated Table Removal
Drops tables that are no longer needed:
- `workflow_states`
- `discovery_assets` (consolidated into assets table)
- `mapping_learning_patterns`
- `session_management`
- `discovery_sessions`

## Deployment Instructions

### For Railway/AWS Deployment

1. **Ensure the migration file is in the correct location:**
   ```
   backend/alembic/versions/20250101_database_consolidation.py
   ```

2. **The migration will run automatically during deployment if you have:**
   ```python
   # In your app startup or Docker entrypoint
   alembic upgrade head
   ```

3. **For Railway specifically, add to your start command:**
   ```json
   {
     "start": "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   }
   ```

### For Manual Deployment

1. **Generate the migration with proper revision linking:**
   ```bash
   cd backend
   ./scripts/generate_consolidation_migration.py
   ```

2. **Test the migration (dry run):**
   ```bash
   alembic upgrade head --sql
   ```

3. **Apply the migration:**
   ```bash
   alembic upgrade head
   ```

### For Docker Deployment

Add to your `docker-entrypoint.sh`:
```bash
#!/bin/bash
echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
```

## Rollback Instructions

If you need to rollback:

```bash
# Rollback to previous revision
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade <previous_revision_id>
```

## Safety Features

The migration includes several safety features:

1. **Idempotent Operations**: Uses try/except blocks to handle already-applied changes
2. **Logging**: Comprehensive logging of all operations
3. **Graceful Handling**: Continues even if some operations fail (e.g., column already renamed)
4. **Full Rollback Support**: Complete downgrade() function to reverse all changes

## Verification

After migration, verify the changes:

```sql
-- Check that v3_ tables are gone
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE 'v3_%';

-- Check field renames
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'data_imports' 
AND column_name IN ('filename', 'file_size', 'mime_type');

-- Check is_mock columns are gone
SELECT table_name, column_name 
FROM information_schema.columns 
WHERE column_name = 'is_mock';

-- Check new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'discovery_flows' 
AND column_name IN ('flow_state', 'phase_state', 'agent_state');

-- Check indexes
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('data_imports', 'discovery_flows', 'assets')
AND indexname LIKE 'idx_%';
```

## Troubleshooting

### Migration fails with "column already exists"
The migration is designed to handle this gracefully. Check the logs to ensure other operations completed.

### Migration fails with "table does not exist"
This is expected for v3_ tables or deprecated tables. The migration will continue.

### Application errors after migration
1. Ensure all application code has been updated to use new field names
2. Check that the models no longer reference `is_mock` or other deprecated fields
3. Verify environment variables are set correctly

## Next Steps

After successful migration:
1. Update any remaining code references to old field names
2. Test all critical workflows
3. Monitor application logs for any issues
4. Remove any temporary backward compatibility code after stability is confirmed