# Data Cleansing Recommendation Migration Guide

This guide explains how to migrate from deterministic recommendation IDs to stable database primary keys.

## Overview

The recommendation persistence model has been refactored to use stable database primary keys instead of deterministic IDs based on recommendation content. This prevents breaking links to user actions when recommendation content changes.

## Migration Steps

### 1. Run the Database Migration

The migration creates the `data_cleansing_recommendations` table:

```bash
# Using Docker (recommended)
docker-compose exec backend python -m alembic upgrade head

# Or using local environment
cd backend
python -m alembic upgrade head
```

**Migration File**: `backend/alembic/versions/127_add_data_cleansing_recommendations_table.py`

### 2. Verify Table Creation

Check that the table was created successfully:

```sql
-- Connect to your database
\c your_database

-- Check if table exists
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'migration'
AND table_name = 'data_cleansing_recommendations';

-- Check table structure
\d migration.data_cleansing_recommendations
```

### 3. Migrate Existing JSONB Actions to Table (Required)

**IMPORTANT**: Per ADR-012, child flows store operational decisions. The current implementation uses dual storage:
- **Preferred**: `data_cleansing_recommendations` table (stable, queryable)
- **Fallback**: `discovery_flows.crewai_state_data.data_cleansing_results.recommendation_actions` (JSONB)

To consolidate into a single source of truth, migrate existing JSONB actions to the table:

```bash
# Step 1: Dry run first to see what would be migrated
cd backend
python scripts/migrate_recommendation_actions_to_table.py --dry-run

# Step 2: Run the actual migration
python scripts/migrate_recommendation_actions_to_table.py

# Step 3: (Optional) Clean up JSONB data after verifying migration
python scripts/migrate_recommendation_actions_to_table.py --cleanup-jsonb
```

**What the script does**:
1. Finds all flows with `recommendation_actions` in JSONB storage
2. For each action, locates the corresponding recommendation in the database table
3. Updates the table record with action data (status, notes, applied_by_user_id, applied_at)
4. Optionally removes JSONB data after successful migration

**When to run**:
- **After deploying the table migration** (step 1)
- **Before removing JSONB fallback code** (if simplifying to table-only storage)
- **As part of production deployment** to consolidate existing data

**Note**: Actions for legacy recommendations (deterministic IDs) that don't exist in the table will remain in JSONB. These will be migrated automatically when recommendations are recreated in the table.

### 4. Test the Endpoints

Run the test script to verify everything works:

```bash
python scripts/test_recommendation_endpoints.py
```

Or test manually:

```bash
# Get recommendations for a flow
curl -X GET "http://localhost:8000/api/v1/flows/{flow_id}/data-cleansing" \
  -H "Authorization: Bearer {token}"

# Apply a recommendation
curl -X PATCH "http://localhost:8000/api/v1/flows/{flow_id}/data-cleansing/recommendations/{recommendation_id}" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"action": "apply", "notes": "Test application"}'
```

## What Changed

### Before (Deterministic IDs)
- Recommendations used deterministic UUIDs based on `category` and `title`
- If recommendation content changed, the ID changed
- Actions were stored in `crewai_state_data.recommendation_actions`
- Links to user actions could break when content changed

### After (Stable Primary Keys)
- Recommendations use stable UUID primary keys
- IDs remain constant even when content changes
- Actions are stored directly in the database table
- Links to user actions are preserved

## Database Schema

The new table includes:

- **Primary Key**: `id` (UUID) - Stable identifier
- **Foreign Key**: `flow_id` - Links to discovery flow
- **Content Fields**: `category`, `title`, `description`, `priority`, `impact`, `effort_estimate`, `fields_affected`
- **Action Fields**: `status`, `action_notes`, `applied_by_user_id`, `applied_at`
- **Audit Fields**: `client_account_id`, `engagement_id`, `created_at`, `updated_at`

## Dual Storage Pattern & Migration Strategy

### Current State (Dual Storage)

The implementation currently supports **dual storage** for backward compatibility:

1. **Primary Storage**: `data_cleansing_recommendations` table
   - Used for all new recommendations
   - Preferred storage location per ADR-012

2. **Fallback Storage**: `discovery_flows.crewai_state_data.data_cleansing_results.recommendation_actions` (JSONB)
   - Used when recommendation not found in table (legacy flows)
   - Maintains backward compatibility during transition

### Migration Strategy

**Phase 1: Deploy Table Migration** ✅
- Run Alembic migration to create `data_cleansing_recommendations` table
- New recommendations automatically stored in table

**Phase 2: Consolidate Existing Data** (Required)
- Run `migrate_recommendation_actions_to_table.py` to consolidate JSONB → table
- Verifies all existing actions are migrated

**Phase 3: Simplify to Table-Only** (Optional, Recommended)
- After migration completes successfully, remove JSONB fallback code
- Simplifies architecture and eliminates technical debt
- See "Simplifying to Table-Only Storage" section below

### Why This Matters

Per ADR-012, child flows store operational decisions. The dual storage pattern:
- ✅ Maintains backward compatibility during transition
- ⚠️ Creates technical debt with complex fallback logic
- ⚠️ Risk of state divergence (some actions in DB, others in JSONB)
- ⚠️ Requires explicit migration to consolidate data

**Recommendation**: Run the migration script after deploying the table, then simplify to table-only storage.

## Backward Compatibility

The new implementation:
- ✅ Automatically creates recommendations in the database when analysis runs
- ✅ Loads existing recommendations from the database
- ✅ Maintains the same API interface
- ✅ Preserves action status and audit trail
- ✅ Falls back to JSONB for legacy flows (during transition period)

## Troubleshooting

### Migration Fails

If the migration fails, check:
1. Database connection is working
2. Previous migrations have been applied
3. Database user has CREATE TABLE permissions

### Recommendations Not Appearing

If recommendations don't appear after migration:
1. Check that analysis has run for the flow
2. Verify recommendations exist in the database:
   ```sql
   SELECT * FROM migration.data_cleansing_recommendations WHERE flow_id = '{flow_id}';
   ```
3. Check application logs for errors

### Actions Not Persisting

If actions aren't persisting:
1. Verify the endpoint is updating the database table
2. Check that the recommendation ID exists in the database
3. Review application logs for errors

## Rollback

If you need to rollback the migration:

```bash
# Rollback the migration
python -m alembic downgrade -1

# Or rollback to a specific revision
python -m alembic downgrade 126_update_alembic_version_to_new_naming
```

**Note**: Rolling back will drop the `data_cleansing_recommendations` table. Make sure to backup any important data first.

## Simplifying to Table-Only Storage (Post-Migration)

After successfully migrating all JSONB actions to the table, you can simplify the codebase by removing the JSONB fallback logic.

### Benefits
- ✅ Eliminates technical debt
- ✅ Single source of truth (table only)
- ✅ Simpler code paths
- ✅ Better query performance
- ✅ Aligns with ADR-012 architecture

### Steps to Simplify

1. **Verify Migration Complete**:
   ```bash
   # Check for any remaining JSONB actions
   python scripts/migrate_recommendation_actions_to_table.py --dry-run
   # Should show 0 flows with recommendation_actions
   ```

2. **Remove JSONB Fallback Code**:
   - Remove fallback logic in `backend/app/api/v1/endpoints/data_cleansing/operations.py`
   - Remove `recommendation_actions` handling from JSONB storage
   - Update error handling to fail fast if recommendation not found in table

3. **Update Tests**:
   - Remove tests for JSONB fallback behavior
   - Add tests for table-only storage

4. **Deploy**:
   - Deploy simplified code
   - Monitor for any edge cases

**Note**: Keep JSONB fallback during transition period. Only remove after confirming all production data is migrated.

## Support

For issues or questions:
1. Check the application logs
2. Review the migration file: `backend/alembic/versions/127_add_data_cleansing_recommendations_table.py`
3. Review the migration script: `backend/scripts/migrate_recommendation_actions_to_table.py`
4. Review the model: `backend/app/models/data_cleansing.py`
5. Review the API endpoints: `backend/app/api/v1/endpoints/data_cleansing/`
6. Review ADR-012: `docs/adr/012-flow-status-management-separation.md`
