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

### 3. Migrate Existing Data (Optional)

If you have existing `recommendation_actions` stored in `crewai_state_data`, you can migrate them:

```bash
# Dry run first to see what would be migrated
python scripts/migrate_recommendation_actions.py --dry-run

# Run the actual migration
python scripts/migrate_recommendation_actions.py
```

**Note**: This script only updates existing recommendations in the database. New recommendations will be created automatically when analysis runs.

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

## Backward Compatibility

The new implementation:
- ✅ Automatically creates recommendations in the database when analysis runs
- ✅ Loads existing recommendations from the database
- ✅ Maintains the same API interface
- ✅ Preserves action status and audit trail

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

## Support

For issues or questions:
1. Check the application logs
2. Review the migration file: `backend/alembic/versions/127_add_data_cleansing_recommendations_table.py`
3. Review the model: `backend/app/models/data_cleansing.py`
4. Review the API endpoints: `backend/app/api/v1/endpoints/data_cleansing/`
