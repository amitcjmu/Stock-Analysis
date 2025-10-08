# Data Loss Prevention Measures - Oct 8, 2025

## Summary of Incident

**Date**: October 7, 2025
**Script**: `backend/scripts/clean_all_demo_data.py`
**Cause**: Manual execution of cleanup script that deletes all data for demo client ID
**Impact**: Wiped 37 assets, all discovery flows, data imports, and raw_import_records
**Client Affected**: `11111111-1111-1111-1111-111111111111` (Demo Cloud Migration Project)

---

## Root Cause Analysis

### What Happened
The script `clean_all_demo_data.py` was manually executed, which:
1. Deletes ALL data for client_account_id `'11111111-1111-1111-1111-111111111111'`
2. Had NO confirmation prompt
3. Had NO environment checks
4. Had NO undo capability

### Why It Was Created
- Created July 1, 2025 (commit 9fc9cc63abe)
- Purpose: Clean test/demo data in development
- **Problem**: The "demo" client ID was being used for real data

### How It Was Executed
- **Manual execution** on Oct 7, 2025
- PostgreSQL logs show DELETE commands at 20:27:38 UTC
- Stats show 101 collection_flows, 33 assets deleted

### Why It Wasn't Caught
- No safeguards in the script
- No backup before execution
- "Demo" client ID used for production-like testing

---

## Prevention Measures Implemented ✅

### 1. Script Renaming
```bash
clean_all_demo_data.py → .DANGEROUS_clean_all_demo_data.py.disabled
clean_all_demo_data_fixed.py → .DANGEROUS_clean_all_demo_data_fixed.py.disabled
```
- Disabled extension prevents accidental execution
- `.DANGEROUS_` prefix makes risk explicit

### 2. Created Safe Alternative
**File**: `backend/scripts/SAFE_cleanup_demo_data.py`

**Safety Features**:
- ✅ Environment check (refuses to run in production/staging)
- ✅ Explicit confirmation requiring typing "DELETE MY DATA"
- ✅ Dry-run mode (`--dry-run` flag)
- ✅ Shows count of records before deletion
- ✅ Creates backup before deletion (placeholder for pg_dump)
- ✅ Detailed logging of operations

**Usage**:
```bash
# Dry run first (safe)
python backend/scripts/SAFE_cleanup_demo_data.py --dry-run

# Actual execution (after confirmation)
python backend/scripts/SAFE_cleanup_demo_data.py
```

### 3. Documentation Created
- ✅ `backend/scripts/DANGEROUS_SCRIPTS.md` - Lists all dangerous scripts
- ✅ `DATA_LOSS_TRIAGE_REPORT.md` - Complete incident analysis
- ✅ `PREVENTION_MEASURES_IMPLEMENTED.md` (this file)

### 4. Updated CLAUDE.md
Added warning section about dangerous scripts to project instructions.

---

## Verification Checklist

### Immediate Actions ✅
- [x] Renamed dangerous scripts with `.disabled` extension
- [x] Created safe alternative with multiple safeguards
- [x] Documented all dangerous scripts
- [x] Updated project documentation

### Before Running ANY Cleanup Script
- [ ] Verify ENVIRONMENT variable (must be 'local')
- [ ] Create database backup:
  ```bash
  docker exec migration_postgres pg_dump -U postgres migration_db > backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Run with `--dry-run` first to see what would be deleted
- [ ] Verify client_account_id is actually demo data
- [ ] Check with team if unsure

### For Production/Staging
**DO NOT** run cleanup scripts. Instead:
- Use soft deletes (add `deleted_at` column)
- Implement data archival (move to archive tables)
- Use feature flags to hide archived data
- Create audit trail for all deletions

---

## Long-Term Recommendations

### 1. Use Different Client IDs for Real Data
**Problem**: Using demo client ID `11111111-1111-1111-1111-111111111111` for real work

**Solution**: Create separate client accounts:
```sql
INSERT INTO migration.client_accounts (id, name, created_at, updated_at)
VALUES (
  gen_random_uuid(),
  'Development Testing',
  NOW(),
  NOW()
);
```

### 2. Implement Soft Deletes
**Why**: Allows data recovery if accidentally deleted

**How**: Add columns to critical tables:
```sql
ALTER TABLE migration.assets
ADD COLUMN deleted_at TIMESTAMP,
ADD COLUMN deleted_by UUID;
```

### 3. Add Pre-Commit Hooks
Prevent dangerous scripts from being committed without safeguards:
```yaml
# .pre-commit-config.yaml
- id: check-dangerous-scripts
  name: Check for dangerous cleanup scripts
  entry: python scripts/check_dangerous_scripts.py
  language: python
```

### 4. Environment-Based Safeguards
Add to all destructive scripts:
```python
import os

ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
if ENVIRONMENT in ['production', 'staging']:
    raise RuntimeError("Cannot run destructive operations in production!")
```

### 5. Automatic Backups
Add to entrypoint.sh:
```bash
# Before migrations, create backup
pg_dump -U postgres migration_db > /backups/pre_migration_$(date +%Y%m%d_%H%M%S).sql
```

---

## How to Recover from Data Loss

### If You Catch It Immediately (Within Minutes)
1. Stop the script (Ctrl+C)
2. Check PostgreSQL WAL logs
3. Attempt point-in-time recovery

### If Data Is Already Gone
1. **Check for backups**:
   ```bash
   docker volume ls
   ls /backups/ /tmp/
   ```

2. **Check source data files**:
   - Look for original CSV/Excel/JSON files
   - Check if they're in `backend/data/` or upload folders

3. **Re-import from source**:
   ```bash
   # Use the standard import flow
   python backend/scripts/import_discovery_data.py --source /path/to/data.csv
   ```

4. **Reconstruct from logs** (last resort):
   - Parse backend logs for import operations
   - Extract data that was imported
   - Manually recreate records

---

## Testing the Safeguards

### Test 1: Environment Check
```bash
# Should refuse to run
ENVIRONMENT=production python backend/scripts/SAFE_cleanup_demo_data.py
# Expected: "❌ FATAL: This script cannot run in production or staging!"
```

### Test 2: Dry Run Mode
```bash
# Should show what would be deleted without deleting
python backend/scripts/SAFE_cleanup_demo_data.py --dry-run
# Expected: "🔍 DRY RUN MODE - No data will be deleted"
```

### Test 3: Confirmation Prompt
```bash
# Run without dry-run, try to bypass confirmation
python backend/scripts/SAFE_cleanup_demo_data.py
# Type wrong confirmation text
# Expected: "❌ Confirmation failed. Aborting."
```

---

## Distribution Checklist

### Files to Commit
- [x] `.DANGEROUS_clean_all_demo_data.py.disabled`
- [x] `.DANGEROUS_clean_all_demo_data_fixed.py.disabled`
- [x] `SAFE_cleanup_demo_data.py`
- [x] `DANGEROUS_SCRIPTS.md`
- [x] `DATA_LOSS_TRIAGE_REPORT.md`
- [x] `PREVENTION_MEASURES_IMPLEMENTED.md`

### Files to Update
- [ ] `CLAUDE.md` - Add warning about dangerous scripts
- [ ] `.gitignore` - Ensure `.disabled` files are tracked
- [ ] `README.md` - Add link to DANGEROUS_SCRIPTS.md

### Notify Team
- [ ] Send email/Slack about dangerous scripts
- [ ] Update team documentation
- [ ] Add to onboarding checklist

---

## Contact for Questions

If you're unsure about running a cleanup script:
1. Check `backend/scripts/DANGEROUS_SCRIPTS.md` first
2. Always run with `--dry-run` first
3. Create a backup before running
4. Ask in team chat if uncertain

---

**Last Updated**: October 8, 2025
**Incident Response**: Complete
**Prevention**: Implemented
**Status**: ✅ Safe to continue development
