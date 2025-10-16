# Development Database Cleanup: When NOT to Use Migrations

## Problem
Test data created during development contains errors (e.g., duplicate asset IDs before deduplication fix). Should this require a migration for cleanup?

## Decision: NO Migration Needed for Development Data

### When to Use Direct SQL Cleanup
✅ **Use direct deletion** when:
1. Data created **during active development** (not production)
2. Data contains **test artifacts** from pre-fix code
3. Only **local development environment** affected
4. Data has **no production equivalent**
5. Cleanup is **environment-specific**, not code-driven

### When to Use Alembic Migration
❌ **Use migration** when:
1. Schema changes required (columns, tables, constraints)
2. Data transformation needed across **all environments**
3. Production data affected
4. Cleanup logic must be **reproducible** in staging/prod
5. Code change caused **persistent data corruption**

## Implementation Pattern

### Step 1: Identify Affected Records
```sql
-- Check for duplicate asset data
SELECT
    af.flow_id,
    af.application_asset_groups,
    jsonb_array_length(af.application_asset_groups) as group_count,
    (SELECT COUNT(*)
     FROM jsonb_array_elements(af.application_asset_groups) AS app_group,
          jsonb_array_elements(app_group->'asset_ids') AS asset_id
    ) as total_asset_refs
FROM migration.assessment_flows af
WHERE af.client_account_id = 1 AND af.engagement_id = 1;

-- Expected: group_count should match unique asset count
-- If total_asset_refs > group_count, duplicates exist
```

### Step 2: Delete Bad Test Data
```sql
-- Delete from child table first (foreign key constraints)
DELETE FROM migration.assessment_flows
WHERE flow_id = 'bad-flow-uuid-here'
  AND client_account_id = 1
  AND engagement_id = 1;

-- Delete from master flow table
DELETE FROM migration.crewai_flow_state_extensions
WHERE flow_id = 'bad-flow-uuid-here'
  AND client_account_id = 1
  AND engagement_id = 1;
```

### Step 3: Verify Cleanup
```sql
-- Check remaining flows are clean
SELECT
    flow_id,
    jsonb_array_length(application_asset_groups) as groups,
    created_at
FROM migration.assessment_flows
WHERE client_account_id = 1 AND engagement_id = 1
ORDER BY created_at DESC;
```

## Docker Exec Pattern

```bash
# Access database container
docker exec -it migration_postgres psql -U postgres -d migration_db

# Run cleanup queries
migration_db=# BEGIN;
migration_db=# DELETE FROM migration.assessment_flows WHERE flow_id = '...';
migration_db=# DELETE FROM migration.crewai_flow_state_extensions WHERE flow_id = '...';
migration_db=# COMMIT;

# Verify
migration_db=# SELECT COUNT(*) FROM migration.assessment_flows;
```

## Real-World Example (October 16, 2025)

**Context**: Assessment Architecture PR #600 - Fixed duplicate asset IDs bug

**Issue**: 1 flow created before fix had 15 duplicate entries (same asset_id repeated 16 times)

**Solution**:
1. Identified affected flow: `SELECT * FROM migration.assessment_flows WHERE ...`
2. Deleted flow: `DELETE FROM migration.assessment_flows WHERE flow_id = '...'`
3. Deleted master: `DELETE FROM migration.crewai_flow_state_extensions WHERE flow_id = '...'`
4. Verified: Remaining 4 flows clean with no duplicates

**Why No Migration**:
- Bug fixed in code (commit 3ea18cb)
- Only development environment affected
- Test data, not production data
- Future flows will be created correctly

## Decision Checklist

Before writing a migration for data cleanup, ask:

| Question | Yes → Migration | No → Direct SQL |
|----------|-----------------|-----------------|
| Will this affect production? | ✅ | ❌ |
| Is this a schema change? | ✅ | ❌ |
| Must cleanup be reproducible? | ✅ | ❌ |
| Is data corruption ongoing? | ✅ | ❌ |
| Only dev test data affected? | ❌ | ✅ |

## Related Patterns
- **Alembic idempotent migrations**: Use for schema changes
- **Data integrity patterns**: Use for production data fixes
- **Test data management**: Keep dev data ephemeral

## Anti-Patterns to Avoid
❌ **Don't create migrations for**:
- One-time dev data cleanup
- Test data artifacts
- Local environment issues
- Bugs already fixed in code

✅ **Do create migrations for**:
- Schema evolution
- Production data transformations
- Cross-environment consistency
- Data integrity enforcement

## Files Referenced
- `backend/alembic/versions/` - Migration directory
- `backend/app/services/assessment/application_resolver.py:162-170` - Bug fix
- Commit: `3ea18cb` - Deduplication fix
