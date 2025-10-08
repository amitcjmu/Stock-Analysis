# Data Loss Triage Report - Oct 8, 2025

## Summary
Multiple database tables were wiped clean (assets, discovery_flows, data_imports, raw_import_records) while other tables (users, canonical_applications, collection_flows) remained intact.

## Affected Tables

| Table | Expected Rows | Actual Rows | Inserts | Deletes | Status |
|-------|--------------|-------------|---------|---------|--------|
| `assets` | 48 (81-33) | 0 | 81 | 33 | ❌ WIPED |
| `discovery_flows` | 7 (8-1) | 0 | 8 | 1 | ❌ WIPED |
| `data_imports` | 8 | 0 | 8 | 0 | ❌ WIPED |
| `raw_import_records` | 115 | 0 | 115 | 0 | ❌ WIPED |
| `collection_flows` | 42 (143-101) | 2 | 143 | 101 | ⚠️ PARTIAL |
| `users` | 11 | 11 | 11 | 0 | ✅ INTACT |
| `canonical_applications` | 8 | 8 | 8 | 0 | ✅ INTACT |
| `crewai_flow_state_extensions` | 66 (136-70) | 2 | 136 | 70 | ⚠️ PARTIAL |

## Root Cause Analysis

### Finding 1: Manual DELETE Operation (Oct 7, 20:27:38 UTC)
**Evidence**: PostgreSQL log shows attempted DELETE command:
```sql
DELETE FROM migration.collection_flows WHERE status != 'completed';
```
- **Result**: Syntax error (used `\!=` instead of `!=`)
- **Impact**: Command FAILED, but stats show 101 collection_flows were deleted earlier
- **Conclusion**: This was an ATTEMPTED cleanup, but deletions occurred earlier

### Finding 2: Migration 086/087 Execution (Oct 7, 18:22-18:48 UTC)
**Migrations run**:
- `086_fix_collection_flow_status_adr012.py` - Updates CollectionFlowStatus enum
- `087_add_paused_remove_phase_values.py` - Adds 'paused' status

**Key Operations**:
```python
# Line 106 in migration 086:
op.execute("DROP TYPE IF EXISTS migration.collectionflowstatus CASCADE")
```

**Analysis**:
- `DROP TYPE ... CASCADE` drops the enum and ALL dependent objects
- In theory, this should only affect column types, not data
- However, PostgreSQL logs show errors during migration execution
- Stats show last autovacuum on collection_flows at 18:25:35 UTC

### Finding 3: Unexplained Data Removal Pattern
**Critical observation**: Tables with 0 deletes but 0 live rows
- `raw_import_records`: 115 inserts, **0 deletes**, but **0 live rows**
- `data_imports`: 8 inserts, **0 deletes**, but **0 live rows**

**This pattern indicates**:
- Data was NOT deleted via SQL DELETE commands
- Possible causes:
  1. **TRUNCATE** operation (doesn't record deletes in pg_stat)
  2. **Transaction rollback** (but wouldn't explain collection_flows having 101 deletes)
  3. **DROP TABLE + recreate** (but table definitions match)
  4. **Cascading from parent table** (but no CASCADE constraints found)

### Finding 4: Foreign Key Analysis
**Assets table has FK to**:
- `client_accounts(id)` - NO CASCADE
- `engagements(id)` - NO CASCADE
- `raw_import_records(id)` - NO CASCADE

**Discovery_flows has FK to**:
- `data_imports(id)` - NO CASCADE
- `crewai_flow_state_extensions(flow_id)` - **ON DELETE CASCADE** ✅

**Collection_flows children (with ON DELETE CASCADE)**:
- `adaptive_questionnaires`
- `collection_data_gaps`
- `collected_data_inventory`
- `collection_questionnaire_responses`
- `collection_gap_analysis`
- `collection_flow_applications`

## Timeline

```
Oct 7, 18:22:49 - Migration 086 starts, errors on enum conversion
Oct 7, 18:23:28 - Multiple "unsafe use of new value 'running'" errors
Oct 7, 18:25:35 - Autovacuum runs on collection_flows (101 deletes recorded)
Oct 7, 18:28:20 - Large checkpoint: 319 buffers, 66 sync files
Oct 7, 20:27:38 - Manual DELETE attempt (failed due to syntax error)
Oct 7, 20:28:20 - Another large checkpoint: 315 buffers, 210 sync files
Oct 8, 10:37:29 - User discovers assets table is empty
```

## Hypotheses (Ranked by Likelihood)

### 1. **Manual Cleanup Script Execution** (80% confidence)
- Evidence: Failed DELETE command at 20:27, 101 collection_flows deleted
- Theory: Someone ran a cleanup script to remove test data
- Why assets wiped: Script may have included TRUNCATE statements
- Why no DELETE stats: TRUNCATE bypasses DELETE triggers

### 2. **Migration Side Effect** (15% confidence)
- Evidence: DROP TYPE CASCADE during migration 086/087
- Theory: Cascade operation had unintended side effects
- Problem: CASCADE shouldn't remove data, only type dependencies

### 3. **Database Restore from Old Backup** (5% confidence)
- Evidence: Container created Sept 25, still running
- Theory: Database volume was restored to empty state
- Problem: Doesn't explain why some tables have data

## Data Recovery Options

### Option 1: Check Docker Volume Backups
```bash
docker volume ls | grep migration
# Check if volume was recently recreated
```

### Option 2: Check PostgreSQL WAL/Backup Files
```bash
docker exec migration_postgres ls -la /var/lib/postgresql/data/pg_wal/
```

### Option 3: Check Application Backups
- Look for automated backup scripts in codebase
- Check if Railway has point-in-time restore

### Option 4: Reconstruct from Logs
- Parse backend logs for import operations
- Identify source files that were imported
- Re-import data from source

## Recommendations

### Immediate Actions
1. **Do NOT run any more migrations** until root cause is confirmed
2. **Backup current database state** before any recovery attempts
3. **Check if user has source data files** for re-import
4. **Review recent commit history** for cleanup scripts

### Prevention Measures
1. **Add database backup before migrations**:
   ```python
   # In alembic env.py
   def backup_before_upgrade():
       op.execute("SELECT pg_dump('migration_db') INTO '/backups/pre-migration.sql'")
   ```

2. **Add confirmation for destructive operations**:
   - Require explicit confirmation for DELETE/TRUNCATE
   - Add dry-run mode for cleanup scripts

3. **Implement audit logging**:
   - Log all DELETE/TRUNCATE operations to audit table
   - Track who executed destructive operations

4. **Use soft deletes** for critical tables:
   - Add `deleted_at` timestamp instead of hard deletes
   - Implement row-level security for data isolation

## Next Steps

1. **User Action**: Confirm if they have source data files for re-import
2. **Investigation**: Check if cleanup script exists in codebase or git history
3. **Recovery**: Determine best recovery path based on availability of:
   - Source data files
   - Database backups
   - WAL archives

## Files to Review

- `backend/alembic/versions/086_fix_collection_flow_status_adr012.py`
- `backend/alembic/versions/087_add_paused_remove_phase_values.py`
- Any cleanup scripts in `backend/scripts/` or `backend/utils/`
- Git history for Oct 7, 2025

---

**Report Generated**: Oct 8, 2025
**Database Size**: 23 MB
**Containers**: Running since Sept 25-30, 2025
**Current Migration**: 087_add_paused_remove_phase_values
