# Data Loss Incident Investigation Methodology

**Date**: October 2025
**Context**: Investigation of Oct 7, 2025 data loss incident where 37 assets, all discovery flows, and import data were deleted

## Investigation Workflow

### 1. Verify Data Loss Scope
```sql
-- Check current state of critical tables
SELECT COUNT(*) FROM migration.assets;
SELECT COUNT(*) FROM migration.discovery_flows;
SELECT COUNT(*) FROM migration.data_imports;
SELECT COUNT(*) FROM migration.raw_import_records;
```

### 2. Check Recent Migrations for Destructive Operations
```bash
# Review recent migration files for DROP, DELETE, or CASCADE
ls -la backend/alembic/versions/ | tail -n 5
grep -i "drop\|delete\|cascade" backend/alembic/versions/0XX_*.py
```

### 3. Analyze PostgreSQL Logs for DELETE Commands
```bash
# Check PostgreSQL logs for deletion timestamps
docker logs migration_postgres 2>&1 | grep -i "delete from"
```

**Key Pattern**: Look for timestamp clusters indicating bulk deletions

### 4. Use pg_stat_user_tables for Deletion Statistics
```sql
-- Check deletion statistics per table
SELECT
    schemaname,
    relname,
    n_tup_del as deletes,
    n_live_tup as live_rows
FROM pg_stat_user_tables
WHERE schemaname = 'migration'
ORDER BY n_tup_del DESC;
```

**Critical Insight**: This shows ACTUAL deletion counts even if database now empty

### 5. Search for Cleanup Scripts
```bash
# Find potential cleanup/delete scripts
find backend/scripts -name "*clean*" -o -name "*delete*" -o -name "*purge*"
grep -r "DELETE FROM" backend/scripts/
```

### 6. Check Git History for Script Creation
```bash
# Find when suspicious script was created
git log --all --oneline --date=short --format="%h %ad %s" -- backend/scripts/clean_all_demo_data.py
git show <commit_hash>:backend/scripts/clean_all_demo_data.py
```

### 7. Verify Script Not in Automation
```bash
# Check if script runs automatically
grep -r "clean_all_demo_data" backend/entrypoint.sh
grep -r "clean_all_demo_data" .github/workflows/
grep -r "clean_all_demo_data" docker-compose*.yml
```

## Root Cause Patterns

**Common Causes:**
1. Manual execution of cleanup scripts (Oct 7 incident)
2. Automated scripts with incorrect scoping
3. Migration rollbacks with CASCADE
4. Foreign key cascading deletes

## Prevention Measures

### Disable Dangerous Scripts
```bash
# Rename with .disabled extension
mv script.py .DANGEROUS_script.py.disabled
```

### Create Safe Alternatives with 5-Layer Protection
See `multi_layered_script_safety_pattern_2025_10` memory

## Recovery Options

1. **Recent Backup**: Restore from pg_dump
2. **Source Data**: Re-import from original CSV/Excel files
3. **PostgreSQL WAL**: Point-in-time recovery (if enabled)
4. **Log Reconstruction**: Parse backend logs for import operations

## Key Learnings

- pg_stat_user_tables retains deletion counts even after data gone
- PostgreSQL logs show exact deletion timestamps
- Git history reveals when dangerous scripts were introduced
- Always check automation before assuming manual execution
