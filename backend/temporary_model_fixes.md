# Temporary Model Fixes for Database Schema Mismatch

## Issue
The SQLAlchemy models have been updated with new field names, but the database migrations haven't been applied yet. This causes a mismatch between what the code expects and what's actually in the database.

## Temporary Fixes Applied

### 1. RawImportRecord Model (app/models/data_import/core.py)
- Changed `record_index` back to `row_number` to match current database schema
- The model still has `is_processed` and `is_valid` fields which exist in the database

### 2. Import Storage Handler (app/api/v1/endpoints/data_import/handlers/import_storage_handler.py)
- Using `row_number` instead of `record_index`
- Including `is_processed=False` and `is_valid=True` when creating records
- Using existing field names: `filename`, `file_size`, `mime_type`
- Using `match_type` instead of `mapping_type` for ImportFieldMapping

### 3. DiscoveryFlow Model (app/models/discovery_flow.py)
- Database has deprecated columns that need to be included in model:
  - `learning_scope` (VARCHAR(50))
  - `memory_isolation_level` (VARCHAR(20))
  - `assessment_ready` (BOOLEAN)
  - `phase_state` (JSONB)
  - `agent_state` (JSONB)
- Database is missing columns that model expects (commented out):
  - `flow_type`, `current_phase`, `phases_completed`
  - `crew_outputs`, `field_mappings`, `discovered_assets`
  - `dependencies`, `tech_debt_analysis`

## Next Steps
Once the database migrations are applied:
1. Revert the model back to use `record_index`
2. Update the code to use the new field names
3. Remove deprecated columns from database
4. Add missing columns to database
5. Remove this temporary fix file

## Migration Required
The following migration needs to be applied to align the database with the models:
- Rename `row_number` to `record_index` in `raw_import_records` table
- Drop deprecated columns from `discovery_flows` table
- Add missing columns to `discovery_flows` table
- Apply other field renames as defined in the migration files