# CMDB Testing Scripts

Operational scripts for testing and verifying CMDB fields population.

## Scripts

### 1. `backfill_all_cmdb_fields.py` (Comprehensive)
**Purpose:** Backfill ALL ~60+ CMDB fields from cleansed_data to existing assets

**Usage:**
```bash
# Dry run (preview changes)
docker exec migration_backend python /app/backend/scripts/cmdb_testing/backfill_all_cmdb_fields.py <flow_id> --dry-run

# Execute backfill
docker exec migration_backend python /app/backend/scripts/cmdb_testing/backfill_all_cmdb_fields.py <flow_id>
```

**Coverage:** All CMDB fields (existing + 24 new from PR #833)

---

### 2. `backfill_cmdb_fields.py` (Quick)
**Purpose:** Backfill only the 24 NEW CMDB fields from PR #833

**Usage:**
```bash
docker exec migration_backend python /app/backend/scripts/cmdb_testing/backfill_cmdb_fields.py <flow_id>
```

**Coverage:** Only the 24 new fields

---

### 3. `check_cmdb_data.py`
**Purpose:** Detailed inspection of CMDB data population

**Usage:**
```bash
docker exec migration_backend python /app/backend/scripts/cmdb_testing/check_cmdb_data.py <flow_id>
```

**Output:** Detailed report showing field population, child table records, sample data

---

### 4. `quick_check_cmdb.sh`
**Purpose:** Fast verification of CMDB data

**Usage:**
```bash
./backend/scripts/cmdb_testing/quick_check_cmdb.sh <flow_id>
```

**Output:** Quick summary of assets count, field coverage, child tables

---

### 5. `create_field_mapping_template.sql`
**Purpose:** Pre-create field mappings for future imports (skip UI mapping step)

**Usage:**
1. Edit file and replace placeholders with your UUIDs
2. Run: `docker exec migration_postgres psql -U postgres -d migration_db -f /path/to/script.sql`

**Benefit:** Future CSV imports auto-apply field mappings - no manual UI mapping needed!

---

## When to Use

### During Development/Testing
Use **backfill scripts** instead of manual UI field mapping (saves 15-20 minutes per test)

### For Verification
Use **check scripts** to verify CMDB data is populated correctly

### For Production Imports
Use **field mapping template** to standardize mappings across imports

---

## Example Workflow

```bash
# 1. Import CSV via UI (upload only, skip field mapping)

# 2. Backfill CMDB data from cleansed_data
docker exec migration_backend python /app/backend/scripts/cmdb_testing/backfill_all_cmdb_fields.py <flow_id>

# 3. Verify results
./backend/scripts/cmdb_testing/quick_check_cmdb.sh <flow_id>

# 4. Test in UI
# All CMDB fields should now be visible!
```

---

## Note on Pre-commit Hooks

These are **operational scripts**, not production code. Some intentionally exceed line limits for readability.

**Exception approved for:**
- File length (>400 lines for comprehensive logic)
- Complexity (detailed data transformation)
- Print formatting (operational output)
