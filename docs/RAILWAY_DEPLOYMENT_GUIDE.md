# Railway Deployment Guide

This guide ensures safe deployment to Railway even if migration histories differ between local development and production.

## Problem Statement

During local development, we may have:
1. Applied migrations manually
2. Marked migrations as applied without actually running them
3. Created merge migrations that don't exist on Railway
4. Modified the database schema directly

This creates a risk where Railway deployments could fail due to:
- Missing migration dependencies
- Schema mismatches
- Foreign key constraint violations
- Index creation conflicts

## Solution: Railway-Safe Migration Strategy

### 1. Pre-Deployment Validation

Run the validation script to check your current database state:

```bash
# Local validation
docker exec migration_backend python railway_migration_check.py

# Or for Railway DATABASE_URL
DATABASE_URL="your_railway_url" python railway_migration_check.py
```

This script will:
- ✅ Check actual schema state vs expected
- ✅ Identify missing columns/indexes/constraints
- ✅ Validate data consistency
- ✅ Provide Railway deployment recommendations

### 2. Railway-Safe Migration

We've created a special migration `railway_safe_schema_sync.py` that:

- **Idempotent**: Safe to run multiple times
- **Defensive**: Checks if changes are needed before applying
- **Comprehensive**: Ensures all critical schema elements exist
- **Forward-only**: Doesn't rely on specific migration history

```bash
# Apply the Railway-safe migration
docker exec migration_backend alembic upgrade railway_safe_schema_sync
```

### 3. Migration History Strategy

#### Option A: Clean Railway Migration (Recommended)

If Railway has a clean database:

1. **Reset local migration history** to match Railway:
   ```bash
   # Check what Railway actually has
   # Then reset local alembic_version table to match
   docker exec migration_postgres psql -U postgres -d migration_db -c "
   DELETE FROM alembic_version;
   INSERT INTO alembic_version (version_num) VALUES ('railway_safe_schema_sync');
   "
   ```

2. **Deploy with clean history**:
   ```bash
   # Railway will run: alembic upgrade head
   # This will apply railway_safe_schema_sync migration
   ```

#### Option B: Migration History Reconciliation

If Railway has partial migration history:

1. **Check Railway's current state**:
   ```sql
   -- On Railway database
   SELECT version_num FROM alembic_version;
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
   ```

2. **Create bridge migration** if needed:
   ```bash
   # Create custom migration to bridge the gap
   alembic revision -m "railway_bridge_migration"
   ```

3. **Mark problematic migrations as applied** on Railway:
   ```sql
   -- If Railway needs to "catch up" to our local state
   INSERT INTO alembic_version (version_num) VALUES 
   ('a1409a6c4f88'),
   ('f410c7d36d82'),
   ('b1cc7d8d2aa1');
   ```

### 4. Deployment Checklist

Before deploying to Railway:

- [ ] ✅ Local validation script passes
- [ ] ✅ All critical columns exist in `crewai_flow_state_extensions`
- [ ] ✅ `assets.flow_id` column exists
- [ ] ✅ Required indexes are created
- [ ] ✅ No orphaned foreign key constraints
- [ ] ✅ Data consistency validated
- [ ] ✅ Railway-safe migration tested locally

### 5. Railway Environment Variables

Ensure these are set on Railway:

```bash
# Required for proper migration execution
DATABASE_URL=postgresql://...
ALEMBIC_CONFIG=/app/alembic.ini

# Optional: Migration debugging
SQLALCHEMY_ECHO=false
ALEMBIC_VERBOSE=true
```

### 6. Post-Deployment Validation

After Railway deployment:

1. **Check migration status**:
   ```bash
   # In Railway console
   alembic current
   alembic history --verbose
   ```

2. **Validate schema**:
   ```bash
   # Run validation script against Railway
   DATABASE_URL="$RAILWAY_DATABASE_URL" python railway_migration_check.py
   ```

3. **Test flow creation**:
   ```bash
   # Test that new flows create properly
   curl -X POST https://your-app.railway.app/api/v3/discovery-flow/flows \
     -H "Content-Type: application/json" \
     -H "X-Client-Account-ID: 11111111-1111-1111-1111-111111111111" \
     -d '{"test": true}'
   ```

### 7. Rollback Strategy

If deployment fails:

1. **Immediate rollback**:
   ```bash
   # Railway automatic rollback to previous deployment
   railway rollback
   ```

2. **Database rollback** (if needed):
   ```sql
   -- Remove problematic migration
   DELETE FROM alembic_version WHERE version_num = 'railway_safe_schema_sync';
   
   -- Drop recently added columns if they cause issues
   ALTER TABLE crewai_flow_state_extensions DROP COLUMN IF EXISTS client_account_id;
   -- etc.
   ```

3. **Schema recreation** (nuclear option):
   ```bash
   # Backup data first!
   pg_dump $DATABASE_URL > backup.sql
   
   # Recreate schema from models
   alembic stamp base
   alembic upgrade head
   
   # Restore data with careful mapping
   ```

## Common Issues and Solutions

### Issue: "Multiple heads detected"
```bash
# Solution: Create merge migration
alembic merge -m "merge_for_railway" head1 head2
```

### Issue: "Column already exists"
```bash
# Railway-safe migration handles this with IF NOT EXISTS checks
# No action needed - migration will skip existing columns
```

### Issue: "Foreign key constraint violation"
```bash
# Check for orphaned records first
SELECT * FROM discovery_flows df 
LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id 
WHERE cse.flow_id IS NULL;

# Run orphan migration to fix
python -m app.services.migration.orphan_flow_migrator
```

### Issue: "Migration timeout on Railway"
```bash
# Railway has deployment timeouts
# Break large migrations into smaller chunks
# Use railway_safe_schema_sync which is optimized for speed
```

## Best Practices for Future Migrations

1. **Always use Railway-safe patterns**:
   ```python
   # Check before adding
   if not check_column_exists(connection, 'table', 'column'):
       op.add_column('table', sa.Column('column', ...))
   ```

2. **Test migrations locally with Railway DB**:
   ```bash
   # Use Railway DB URL for local testing
   DATABASE_URL="$RAILWAY_URL" alembic upgrade head
   ```

3. **Keep migrations small and focused**:
   - One migration per logical change
   - Avoid complex data transformations
   - Use separate migrations for schema and data changes

4. **Document breaking changes**:
   ```python
   """
   BREAKING CHANGE: This migration requires...
   ROLLBACK: Not supported due to...
   RAILWAY SAFE: Yes/No because...
   """
   ```

## Emergency Contacts

If Railway deployment fails:
1. Check Railway logs: `railway logs`
2. Check database logs: Railway dashboard → Database → Logs
3. Contact team with specific error messages
4. Have rollback plan ready

---

**Remember**: Railway deployments are irreversible once database changes are applied. Always validate locally first!