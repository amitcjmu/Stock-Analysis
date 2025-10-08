# ⚠️ DANGEROUS SCRIPTS - PRODUCTION WARNING

## Scripts That Can Cause Data Loss

The following scripts **MUST NEVER** be run in production or any environment with real data:

### 1. `clean_all_demo_data.py`
**Danger Level**: 🔴 **CRITICAL - DELETES ALL DATA**

**What it does**:
- Deletes ALL data for client_account_id `'11111111-1111-1111-1111-111111111111'`
- Deletes: assets, discovery_flows, data_imports, raw_import_records, collection_flows, and more
- **NO CONFIRMATION** prompt
- **NO UNDO** capability

**Incident History**:
- **Oct 7, 2025**: Wiped 37 assets, all discovery flows, and import data
- Caused production data loss

**When to use**:
- ONLY in local development with seeded demo data
- NEVER in staging or production
- NEVER if you're using the demo client ID for real work

**Prevention**:
- Script has been renamed to `.DANGEROUS_clean_all_demo_data.py.disabled`
- If you must use it, read the confirmation prompt carefully

---

### 2. `clean_all_demo_data_fixed.py`
**Danger Level**: 🔴 **CRITICAL - DELETES ALL DATA**

Same as above but with fixed transaction handling. Still dangerous.

---

## How to Safely Clean Data

### For Local Development
```bash
# 1. Backup first
docker exec migration_postgres pg_dump -U postgres migration_db > backup.sql

# 2. Verify you're on local
docker exec migration_backend python -c "import os; print(os.getenv('ENVIRONMENT'))"

# 3. Only then run cleanup if needed
docker exec migration_backend python scripts/clean_all_demo_data.py
```

### For Production
**DO NOT clean data in production.** Use soft deletes or archival instead.

---

## Safeguards Added

1. ✅ Scripts renamed with `.DANGEROUS_` prefix
2. ✅ Added confirmation prompts requiring typing "DELETE MY DATA"
3. ✅ Added environment checks (refuses to run if ENVIRONMENT != 'local')
4. ✅ Added this documentation
5. ✅ Updated CLAUDE.md with warning
6. ✅ Created pre-execution checklist

---

## If You Accidentally Run a Dangerous Script

1. **IMMEDIATELY** stop the script (Ctrl+C)
2. Check database damage:
   ```sql
   SELECT COUNT(*) FROM migration.assets;
   SELECT COUNT(*) FROM migration.discovery_flows;
   SELECT COUNT(*) FROM migration.data_imports;
   ```
3. Restore from backup if available
4. Check if source data files exist for re-import
5. Document the incident in DATA_LOSS_TRIAGE_REPORT.md

---

**Last Updated**: Oct 8, 2025
**Incident**: Data loss on Oct 7, 2025
