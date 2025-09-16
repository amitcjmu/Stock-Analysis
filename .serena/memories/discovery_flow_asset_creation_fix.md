# Discovery Flow Asset Creation Fix

## Problem: CSV Records Not Creating New Assets
**Issue**: Discovery flow only showing 34 existing assets, new CSV uploads not creating additional assets
**Root Cause**: Data cleansing phase filtering out records with `is_valid != True`

## Solution: Remove is_valid Filter
**File**: `/backend/app/services/crewai_flows/handlers/phase_executors/data_cleansing_executor.py`
**Line**: ~250

### Code Fix:
```python
# BEFORE - Blocking records
query = (
    select(RawImportRecord)
    .where(RawImportRecord.data_import_id == data_import_id)
    .where(RawImportRecord.is_valid is True)  # THIS WAS THE PROBLEM
)

# AFTER - Process all records
query = (
    select(RawImportRecord)
    .where(RawImportRecord.data_import_id == data_import_id)
    # Removed: .where(RawImportRecord.is_valid is True)
)
```

## Key Learning
The `is_valid` field should NOT be used as a hard filter preventing data flow. Validation should happen during processing, not block the entire pipeline. Raw import records may not be marked as valid during initial import but are still valid data that needs processing.

## Verification
After fix, check logs for:
- "📊 Found X raw import records" (should match CSV row count)
- "✅ Successfully persisted X cleansed records"
- New assets appearing in inventory beyond the initial 34

## Related Tables
- `raw_import_records` - Stores uploaded CSV data
- `discovery_flows` - Tracks flow state
- `assets` - Final asset storage
- `data_imports` - Import metadata

## Commands
```bash
# Restart backend after fix
docker restart migration_backend

# Check logs for record processing
docker logs migration_backend | grep "raw import records"
```
