# Collection Gap Resolution Fixes - December 2025

Last Updated: 2025-12-08

## Summary
Fixed critical issues with collection flow gap resolution where questionnaire responses weren't properly closing gaps and gaps reappeared on new flows.

## Issues Fixed

### Issue 1: Field Name Mismatch (Primary Fix)
**Problem**: Only 7 of 22 gaps were resolved because LLM-generated questionnaire field names didn't match gap field names.

**Root Cause**: `SectionQuestionGenerator` (LLM-based) generated field names like `code_quality_metric_level` while gaps had names like `code_quality_metrics`.

**Solution**: Added Strategy 4 to `resolve_data_gaps()` with semantic field mapping:
- File: `backend/app/api/v1/endpoints/collection_crud_helpers.py`
- Added `RESPONSE_TO_GAP_FIELD_MAPPING` dictionary (28 mappings)
- Maps LLM variations to canonical gap field names

**Key Mappings**:
- `code_quality_metric_level` → `code_quality_metrics`
- `documentation_completeness` → `documentation_quality`
- `eol_assessment_status` → `eol_technology_assessment`
- `cpu_cores`, `memory_gb`, `storage_gb` → `cpu_memory_storage_specs`
- `operating_system`, `os_version` → `operating_system_version`

### Issue 2: Prompt Enforcement
**Problem**: LLMs were free to generate any field_id instead of using exact gap field_ids.

**Solution**: Added explicit instruction in prompt builder:
- File: `backend/app/services/collection/gap_analysis/section_question_generator/prompt_builder.py`
- Added: "CRITICAL: field_id MUST match gap field_id exactly!"

### Issue 3: Missing Technical Detail Fields
**Problem**: Gap fields like `code_quality_metrics` weren't in the asset writeback whitelist.

**Solution**: Extended `TECHNICAL_DETAIL_FIELDS` list:
- File: `backend/app/services/flow_configs/collection_handlers/asset_field_whitelist.py`
- Added 12 new technical detail fields for JSONB storage

### Issue 4: Gap Inheritance in Persistence (Duplicate Gaps on New Flows)
**Problem**: Creating a new collection flow for the same asset showed all 22 gaps again instead of 0.

**Root Cause**: Unique constraint `uq_gaps_dedup` includes `collection_flow_id`, so new flows always created new gap records.

**Solution**: Added gap inheritance check in `persist_gaps()`:
- File: `backend/app/services/collection/gap_analysis/gap_persistence.py`
- Before creating gaps, queries for already-resolved gaps for the same asset+field from ANY flow
- Skips creating new gaps for fields that were already resolved

### Issue 5: Multi-Gap-Type Field Resolution (NEW - Dec 2025)
**Problem**: Same field can have MULTIPLE gap records with different `gap_type` values (e.g., `missing_field`, `missing_critical_attribute`, `null_field`). When user answered a question, only ONE gap_type was resolved, leaving others pending.

**Example**:
```
| field_name           | gap_type                   | resolution_status |
|----------------------|----------------------------|-------------------|
| architecture_pattern | missing_field              | pending           |
| architecture_pattern | missing_critical_attribute | resolved          |
```

**Root Cause**: `resolve_data_gaps()` used `gap_index` which only stores ONE gap per field_name (dict overwrites).

**Solution**: Added UPDATE statement to resolve ALL gaps for same (asset_id, field_name):
```python
# In collection_crud_helpers.py, after resolving matched gap:
if gap.asset_id:
    additional_resolved = await db.execute(
        update(CollectionDataGap)
        .where(
            and_(
                CollectionDataGap.asset_id == gap.asset_id,
                CollectionDataGap.field_name == gap.field_name,
                CollectionDataGap.resolution_status == "pending",
                CollectionDataGap.id != gap.id,  # Exclude already-updated gap
            )
        )
        .values(
            resolution_status="resolved",
            resolved_at=datetime.utcnow(),
            resolved_by="manual_submission",
            resolved_value=gap.resolved_value,
        )
    )
```

### Issue 6: Gap Inheritance in Questionnaire Generation (NEW - Dec 2025)
**Problem**: `IntelligentGapScanner` finds TRUE gaps but doesn't filter out fields that were already resolved in previous flows. This caused questionnaire to generate 25 questions when only 6 gaps were pending.

**Solution**: Added gap inheritance filtering to `_generate_per_section.py`:
```python
# After IntelligentGapScanner runs, filter by resolved fields:
async def _get_resolved_fields_for_assets(
    asset_ids: List[UUID], db: AsyncSession
) -> dict[str, set[str]]:
    """Get resolved fields for each asset (from ANY previous flow)."""
    resolved_stmt = select(
        CollectionDataGap.asset_id, CollectionDataGap.field_name
    ).where(
        and_(
            CollectionDataGap.asset_id.in_(asset_ids),
            CollectionDataGap.resolution_status == "resolved",
        )
    )
    # Build dict: asset_id -> set of resolved field_names
    ...

def _filter_gaps_by_resolved(
    intelligent_gaps: dict[str, List["IntelligentGap"]],
    resolved_by_asset: dict[str, set[str]],
) -> tuple[dict[str, List["IntelligentGap"]], int]:
    """Filter out gaps for fields already resolved."""
    # Filter by field_id not in resolved_fields
    ...
```

### Issue 7: Chained Normalization Pattern (NEW - Dec 2025)
**Problem**: Field normalization strategies weren't chained - if Strategy 2 (custom_attributes prefix removal) ran, Strategy 3 (composite ID extraction) used original field_name instead of normalized version.

**Solution**: Use single `lookup_field` variable that chains through all strategies:
```python
# Use a single variable to chain normalization steps
lookup_field = field_name

# Strategy 1: Exact match
gap = gap_index.get(lookup_field)

# Strategy 2: Custom_attributes prefix removal
if not gap and lookup_field.startswith("custom_attributes."):
    lookup_field = lookup_field.replace("custom_attributes.", "")
    gap = gap_index.get(lookup_field)

# Strategy 3: Composite ID extraction (asset_id__field_name)
if not gap and "__" in lookup_field:
    parts = lookup_field.split("__", 1)
    if len(parts) == 2:
        extracted_field = parts[1]
        lookup_field = extracted_field  # Chain for next strategy
        gap = gap_index.get(lookup_field)

# Strategy 4: Semantic field mapping
if not gap:
    mapped_field = RESPONSE_TO_GAP_FIELD_MAPPING.get(lookup_field)
    ...
```

## Files Modified

1. `backend/app/api/v1/endpoints/collection_crud_helpers.py`
   - Added `RESPONSE_TO_GAP_FIELD_MAPPING` dictionary
   - Added Strategy 4 (semantic field mapping)
   - Added multi-gap-type resolution UPDATE statement
   - Fixed chained normalization with single `lookup_field` variable

2. `backend/app/api/v1/endpoints/collection_crud_questionnaires/_generate_per_section.py`
   - Added `_get_resolved_fields_for_assets()` function
   - Added `_filter_gaps_by_resolved()` function
   - Filter IntelligentGapScanner results by gap inheritance

3. `backend/app/services/collection/gap_analysis/section_question_generator/prompt_builder.py`
   - Added explicit instruction for LLM to use exact gap field_ids

4. `backend/app/services/flow_configs/collection_handlers/asset_field_whitelist.py`
   - Extended `TECHNICAL_DETAIL_FIELDS` with 12 new fields

5. `backend/app/services/collection/gap_analysis/gap_persistence.py`
   - Added gap inheritance check before creating new gaps

## Key Database Insight

The unique constraint `uq_gaps_dedup` is on `(collection_flow_id, field_name, gap_type, asset_id)`. This means:
- Same field can have MULTIPLE gap records with different gap_types
- Gap resolution must update ALL gap_types for a field, not just one
- New flows will attempt to create new gaps - inheritance check prevents duplicates

## Verification Steps
1. Create collection flow for asset
2. Complete questionnaire
3. Verify ALL gaps marked as resolved (including all gap_types per field)
4. Create NEW collection flow for SAME asset
5. Verify gap grid shows 0 heuristic gaps for already-resolved fields
6. Verify questionnaire generates questions ONLY for remaining gaps
