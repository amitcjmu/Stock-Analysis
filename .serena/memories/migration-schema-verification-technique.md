# Migration Debugging - Schema Verification First

**Problem**: Migration referenced `flow_id` column that didn't exist in `assessment_flows` table

**Root Cause**: Assumed column existed based on naming patterns from other tables

**Solution**: Always verify actual schema before writing migration SQL

**Commands**:
```bash
# 1. Find the SQLAlchemy model
find backend -name "*assessment_flow*.py" | grep models

# 2. Read the actual model definition to verify columns
# Check Column() definitions, NOT assumptions

# 3. Verify:
#    - Actual column names (id vs flow_id vs master_flow_id)
#    - Column types (JSONB vs Array affects SQL functions)
#    - Foreign key references (must match actual PKs)
```

**Pattern**: SQLAlchemy model = source of truth, not assumptions

**Verification Checklist for Migrations**:
1. ✅ Read SQLAlchemy model to confirm column names
2. ✅ Check column types (JSONB vs Array, UUID vs String)
3. ✅ Verify foreign key references match actual primary keys
4. ✅ Don't assume naming patterns from other tables apply
5. ✅ Test SELECT queries before adding to migration

**Common Mistakes**:
- ❌ Assuming `table_flows` has `flow_id` (might be `id` + `master_flow_id`)
- ❌ Using array functions on JSONB columns
- ❌ Referencing columns from old/deprecated table versions

**Reference**: Fixed in migration 121_backfill_assessment_source_collection.py (removed non-existent `af.flow_id`)
