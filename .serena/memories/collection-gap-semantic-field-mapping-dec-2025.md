# Collection Gap Semantic Field Mapping

## Problem (December 2025)
LLM-generated questionnaires used slightly different field names than gap field_ids, causing only 7 of 22 gaps to be resolved after form submission.

## Root Cause
- Gap field_id: `code_quality_metrics`
- LLM-generated question field_id: `code_quality_metric_level`
- No semantic matching was in place

## Solution

### 1. Semantic Field Mapping Dictionary
Location: `backend/app/api/v1/endpoints/collection_crud_helpers.py`

```python
RESPONSE_TO_GAP_FIELD_MAPPING = {
    # Code quality variations
    "code_quality_metric_level": "code_quality_metrics",
    "code_quality": "code_quality_metrics",
    "code_quality_score": "code_quality_metrics",
    # Compliance variations
    "compliance_requirements": "compliance_constraints",
    "compliance_status": "compliance_constraints",
    # ... 28 total mappings
}
```

### 2. Multi-Strategy Field Matching
The `_find_gap_for_field()` function uses 4 strategies:
1. Exact match
2. Custom_attributes prefix removal
3. Composite ID extraction (asset_id__field_name)
4. Semantic mapping (new)

### 3. Gap Inheritance
Location: `backend/app/services/collection/gap_analysis/gap_persistence.py`

Added `_get_resolved_fields()` to query already-resolved gaps across ALL flows, preventing duplicate gaps for the same asset.

## Related Files
- `collection_crud_helpers.py` - RESPONSE_TO_GAP_FIELD_MAPPING dictionary
- `gap_persistence.py` - Gap inheritance logic
- `prompt_builder.py` - LLM instruction to use exact field_ids
- `asset_field_whitelist.py` - TECHNICAL_DETAIL_FIELDS for JSONB storage

## PR Reference
PR #1270: fix(collection): resolve gap-to-response field name mismatch and add gap inheritance
