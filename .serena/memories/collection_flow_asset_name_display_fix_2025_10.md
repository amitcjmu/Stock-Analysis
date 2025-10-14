# Collection Flow Asset Name Display Fix - October 2025

## Issue
Questionnaire questions showed UUID prefixes ("Asset df0d34a9") instead of actual asset names ("Admin Dashboard").

## Root Cause
In `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py`, the `_arun` method hardcoded asset names as:
```python
"asset_name": f"Asset {asset_id[:8]}"
```

This appeared in 3 sections:
1. Data quality issues (line 150)
2. Unmapped attributes (line 179)
3. Technical details (line 206)

## Solution Architecture

### 1. Added _get_asset_name() Method
Created async method with priority-based lookup:
```python
async def _get_asset_name(self, asset_id: str, business_context: Dict[str, Any] = None) -> str:
    # Priority order:
    # 1. business_context['asset_names'] dict (passed from caller)
    # 2. Cache from previous lookups
    # 3. Database query (if db_session available)
    # 4. Fallback to UUID prefix (preserves existing behavior)
```

### 2. Modified QuestionnaireGenerationTool
- Added optional `db_session` parameter to `__init__`
- Added `_asset_name_cache` dictionary for performance
- Updated 3 sections to call `await self._get_asset_name(asset_id, business_context)`

### 3. Updated Business Context
In `backend/app/api/v1/endpoints/collection_crud_questionnaires/agents.py`:
```python
# Build asset_names mapping from selected_assets
asset_names = {
    asset["asset_id"]: asset["asset_name"]
    for asset in selected_assets
    if asset.get("asset_id") and asset.get("asset_name")
}

# Pass to tool via business_context
"business_context": {
    "engagement_id": context.engagement_id,
    "client_account_id": context.client_account_id,
    "total_assets": len(selected_assets),
    "assets_with_gaps": len(asset_analysis.get("assets_with_gaps", [])),
    "asset_names": asset_names,  # CRITICAL: Enables proper display
}
```

## Implementation Notes

1. **Backward Compatibility**: Maintains UUID prefix fallback for cases where asset_names not available
2. **Performance**: Uses cache to avoid repeated database queries
3. **Flexibility**: Supports 3 lookup methods (business_context, cache, database)
4. **Logging**: Adds debug logs for troubleshooting asset name resolution

## Related Pattern
This fix complements the pattern in `programmatic_gap_scanner.py` (line 203-217) which joins Asset table to get names for gap records:
```python
stmt = (
    select(CollectionDataGap, Asset.name)
    .join(Asset, CollectionDataGap.asset_id == Asset.id, isouter=True)
    .where(CollectionDataGap.collection_flow_id == flow_uuid)
)
```

## Commit
- Commit: 7d586932b
- Files: generation.py, agents.py
- All pre-commit checks passed

## Testing Verification
After this fix:
- ✅ Questions show: "Please provide technical details for Admin Dashboard"
- ❌ No longer: "Please provide technical details for Asset df0d34a9"
