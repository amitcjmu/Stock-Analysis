# Gap Inheritance and Writeback Issue Diagnosis

## Date: December 2025

## Problem Statement
When creating a new collection flow for an asset (WebApp-03) that had already provided ALL questionnaire answers, the heuristic gap scanner still showed 14 gaps. Expected behavior: resolved gaps should not be recreated (gap inheritance).

## Root Cause Analysis

### The Writeback Chain
1. **Gap Resolution**: `resolve_data_gaps()` marks gaps as "resolved" and populates `resolved_value` ✅ WORKS
2. **Writeback Trigger**: `apply_asset_writeback()` is called with `gaps_resolved` count ✅ CALLED
3. **Asset Update**: `apply_resolved_gaps_to_assets()` should write values to Asset columns ❌ FAILED SILENTLY

### Why Writeback Failed
The `apply_asset_writeback()` function in `collection_crud_helpers.py` has error handling that **swallows exceptions**:

```python
except Exception as e:
    logger.error(f"❌ Asset write-back failed: {e}", exc_info=True)
    # Don't fail the entire operation if write-back fails ← SILENTLY SWALLOWED
```

This means:
- If `apply_resolved_gaps_to_assets()` throws an exception
- The error is logged but NOT re-raised
- Questionnaire submission completes successfully
- Asset columns remain NULL
- Next gap scan finds NULL columns → recreates gaps

### Two-Layer Protection (Both Required)
1. **Writeback Layer**: `apply_resolved_gaps_to_assets()` populates Asset columns from `resolved_value`
   - Maps gap field_name → Asset column (via ASSET_FIELD_WHITELIST)
   - Executes SQL UPDATE on Asset model

2. **Gap Inheritance Layer**: `_get_resolved_fields_for_assets()` in `persistence.py`
   - Checks `collection_data_gaps` for `resolution_status='resolved'`
   - Returns set of (asset_id, field_name) already resolved
   - `persist_gaps_with_dedup()` skips creating gaps for resolved fields

### Verification Results
After manually running `apply_resolved_gaps_to_assets()`:
- Asset columns populated: os_version, storage_gb, operating_system, etc. ✅
- Gap scanner finds 9 gaps instead of 14 ✅
- Remaining gaps are application/enrichment/jsonb layers (not column-level)

## Technical Details

### Field Name Mapping
- Questionnaire responses use composite format: `{asset_id}__{field_name}`
- Gaps use simple format: `field_name`
- `_find_gap_for_field()` Strategy 3 handles composite ID extraction

### Files Involved
- `backend/app/api/v1/endpoints/collection_crud_helpers.py`: `apply_asset_writeback()`, `resolve_data_gaps()`
- `backend/app/services/flow_configs/collection_handlers/asset_handlers.py`: `apply_resolved_gaps_to_assets()`
- `backend/app/services/collection/gap_scanner/persistence.py`: `_get_resolved_fields_for_assets()`, `persist_gaps_with_dedup()`

## Recommendations
1. Consider re-raising exceptions from writeback to fail fast
2. Add diagnostic logging (DONE) to trace writeback flow
3. Consider retry logic for transient failures
4. Document the two-layer protection in ADR
