# Alembic Migration JSONB Column Handling

**Problem**: Migration failed with "column af.flow_id does not exist" and "function array_length(jsonb, integer) does not exist"

**Solution**: JSONB columns require different functions than PostgreSQL arrays
- Use `jsonb_array_length()` instead of `array_length()`
- Use `jsonb_array_elements_text()` instead of `unnest()`
- Check actual table schema before assuming column existence

**Code**:
```python
# ❌ WRONG - Treats JSONB as array
CONTINUE WHEN assessment_record.selected_asset_ids IS NULL
           OR array_length(assessment_record.selected_asset_ids, 1) = 0
WHERE cfa.asset_id = ANY(SELECT unnest(assessment_record.selected_asset_ids)::uuid)

# ✅ CORRECT - JSONB functions
CONTINUE WHEN assessment_record.selected_asset_ids IS NULL
           OR jsonb_array_length(assessment_record.selected_asset_ids) = 0
WHERE cfa.asset_id IN (SELECT (jsonb_array_elements_text(assessment_record.selected_asset_ids))::uuid)
```

**Usage**: Always verify SQLAlchemy model schema before writing migrations. Use `Column(JSONB, ...)` → JSONB functions, not array functions.

**Reference**: Fixed in migration 121_backfill_assessment_source_collection.py
