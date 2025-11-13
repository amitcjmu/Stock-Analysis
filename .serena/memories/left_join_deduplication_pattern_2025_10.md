# LEFT JOIN Deduplication Pattern

## Problem
When using LEFT JOIN with one-to-many relationships, duplicate rows cause incorrect aggregations. Example: Asset with 3 `collection_flow_applications` entries appears 3 times in results, causing "16 assets" to display when only 1 unique asset exists.

## Solution
Track seen entity IDs in a set during aggregation loop to skip duplicates.

## Code Pattern

```python
# In aggregation function (e.g., resolve_assets_to_applications)
app_groups: Dict[str, Dict[str, Any]] = {}

for row in rows:
    app_key = str(row.canonical_application_id) or f"unmapped-{row.asset_id}"

    if app_key not in app_groups:
        app_groups[app_key] = {
            "canonical_application_id": row.canonical_application_id,
            "canonical_application_name": row.canonical_name or "Unknown",
            "assets": [],
            "asset_types": set(),
            "readiness": {"ready": 0, "not_ready": 0, "in_progress": 0},
            "seen_asset_ids": set(),  # ✅ Deduplication tracker
        }

    # ✅ Skip duplicate assets
    if row.asset_id in app_groups[app_key]["seen_asset_ids"]:
        continue

    # ✅ Mark as seen before processing
    app_groups[app_key]["seen_asset_ids"].add(row.asset_id)

    # Now aggregate without duplicates
    app_groups[app_key]["assets"].append({
        "asset_id": row.asset_id,
        "asset_name": row.asset_name,
        "asset_type": row.asset_type,
    })
```

## When to Use
- **Any LEFT JOIN with one-to-many relationships** (assets → dependencies, assets → vulnerabilities, assets → product_links)
- **Grouping queries** where entity may have multiple related records
- **Aggregation functions** counting distinct entities

## Example Scenarios
1. Assets with multiple `AssetDependency` entries
2. Assets with multiple `AssetVulnerabilities` entries
3. Canonical applications with multiple `CollectionFlowApplication` mappings

## Related Files
- `backend/app/services/assessment/application_resolver.py:162-170` (implementation)
- Commit: `3ea18cb` (Assessment Architecture bug fix)

## Why Not SQL DISTINCT?
`SELECT DISTINCT` would remove duplicate rows but lose relationship data. This pattern preserves all relationships while ensuring entity-level uniqueness in aggregations.
