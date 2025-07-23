# PostgreSQL Collation Version Warning Fix

## Issue
You're seeing warnings like:
```
WARNING: database "postgres" has no actual collation version, but a version was recorded
WARNING: database "migration_db" has no actual collation version, but a version was recorded
```

## Explanation
These warnings occur when:
1. PostgreSQL was upgraded
2. The operating system's locale/collation libraries were updated
3. There's a mismatch between the recorded collation version and the actual version

## Impact
- **Development**: Generally harmless, can be ignored
- **Production**: Should be addressed to prevent potential sorting/comparison issues

## Solutions

### Option 1: Refresh Collation Version (Recommended for Development)
```sql
-- Connect to each database and run:
ALTER DATABASE postgres REFRESH COLLATION VERSION;
ALTER DATABASE migration_db REFRESH COLLATION VERSION;
```

### Option 2: Using psql Commands
```bash
# For Docker setup
docker exec -it migration_postgres psql -U postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
docker exec -it migration_postgres psql -U postgres -c "ALTER DATABASE migration_db REFRESH COLLATION VERSION;"

# For local PostgreSQL
psql -U postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
psql -U postgres -c "ALTER DATABASE migration_db REFRESH COLLATION VERSION;"
```

### Option 3: Suppress Warnings (Development Only)
Add to your PostgreSQL configuration:
```
# In postgresql.conf
log_min_messages = error  # This will suppress warnings
```

Or set in your database connection:
```python
# In your database configuration
DATABASE_URL = "postgresql://user:pass@localhost/dbname?options=-c%20client_min_messages%3Derror"
```

## Prevention
When creating new databases, explicitly set the locale:
```sql
CREATE DATABASE migration_db 
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;
```

## Verification
After applying the fix:
```sql
-- Check collation versions
SELECT datname, datcollate, datctype, datcollversion 
FROM pg_database 
WHERE datname IN ('postgres', 'migration_db');
```

## Related Issues
- This often occurs after macOS updates (which update ICU libraries)
- Common in Docker environments when PostgreSQL images are updated
- Can happen when moving databases between different OS versions

## References
- [PostgreSQL Collation Documentation](https://www.postgresql.org/docs/current/collation.html)
- [ALTER DATABASE Documentation](https://www.postgresql.org/docs/current/sql-alterdatabase.html)