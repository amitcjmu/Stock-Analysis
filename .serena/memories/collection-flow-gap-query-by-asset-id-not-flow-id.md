# Collection Flow Gap Query Pattern: Asset ID vs Flow ID

**Date**: December 2025
**Issue**: #1269 - Collection flow incorrectly marked COMPLETED after gap analysis

## Critical Insight

**Gaps are per-ASSET, not per-FLOW.** When querying gaps for auto-progression or questionnaire generation, always use `asset_id`, NOT `collection_flow_id`.

## Problem

The unique constraint `uq_gaps_dedup` is:
```sql
(collection_flow_id, field_name, gap_type, asset_id)
```

This means:
- Each new collection flow creates **NEW** gap records (even for the same asset)
- Old gaps remain under their original flow ID
- Querying by `collection_flow_id` for a new flow returns 0 gaps → false finalization

## Root Cause Code

```python
# ❌ WRONG - Returns 0 for new flows, even when gaps exist for the assets
pending_gaps_result = await self.db.execute(
    select(func.count(CollectionDataGap.id)).where(
        CollectionDataGap.collection_flow_id == child_flow.id,  # BUG!
        CollectionDataGap.resolution_status == "pending",
    )
)
```

## Solution Pattern

```python
# ✅ CORRECT - Query by asset IDs
selected_asset_ids = (phase_input or {}).get("selected_asset_ids", [])

# Convert to UUIDs
asset_uuids = [UUID(aid) if isinstance(aid, str) else aid for aid in selected_asset_ids]

# Query gaps by asset_id
if asset_uuids:
    pending_gaps_result = await self.db.execute(
        select(func.count(CollectionDataGap.id)).where(
            CollectionDataGap.asset_id.in_(asset_uuids),
            CollectionDataGap.resolution_status == "pending",
        )
    )
else:
    # Fallback to collection_flow_id (may return 0 for new flows)
    pass
```

## Persist Asset IDs for Future Phases

```python
# In gap_analysis phase, store selected_asset_ids to flow_metadata
if selected_asset_ids:
    current_metadata = child_flow.flow_metadata or {}
    current_metadata["selected_asset_ids"] = selected_asset_ids
    child_flow.flow_metadata = current_metadata
    await db.commit()
```

Then in later phases:
```python
# Try phase_input first, fall back to flow_metadata
selected_asset_ids = (phase_input or {}).get("selected_asset_ids", [])
if not selected_asset_ids and child_flow.flow_metadata:
    selected_asset_ids = child_flow.flow_metadata.get("selected_asset_ids", [])
```

## When to Apply

- Auto-progression decisions after gap analysis
- Questionnaire generation gap queries
- Manual collection phase gap counts
- Any code checking "pending gaps" for a collection flow

## Related ADRs

- ADR-034: Asset-Centric Questionnaire Deduplication
- ADR-037: Intelligent Gap Detection and Questionnaire Generation

## Files Changed

- `backend/app/services/child_flow_services/collection/service.py`
  - `_execute_gap_analysis_phase`: Lines 207-232 (auto-progression query)
  - `_execute_questionnaire_generation`: Lines 304-326 (questionnaire gap query)
