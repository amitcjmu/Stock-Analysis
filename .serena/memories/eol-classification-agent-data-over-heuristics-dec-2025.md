# EOL Classification: Use Agent-Enriched Data, Not Regex Heuristics

**Date**: December 2025
**PR**: #1266 - Compliance API EOL Classification Fix

## Problem

The compliance API was using regex heuristics to guess `product_type` for EOL lookups:

```python
# ❌ WRONG - Regex-based classification
tech_lower = tech.lower()
if any(re.search(rf"\b{os_name}\b", tech_lower) for os_name in ["windows", "linux", ...]):
    product_type = "os"
elif any(re.search(rf"\b{db_name}\b", tech_lower) for db_name in ["sql server", "oracle", ...]):
    product_type = "database"
else:
    product_type = "runtime"
```

This is incorrect because the architecture already has proper structures:
- `Asset.asset_type` field stores classification (server, database, etc.)
- `AssetEOLAssessment` model stores per-asset EOL data populated by agents

## Solution

Use existing agent-enriched data in priority order:

```python
# ✅ CORRECT - Use agent data first
async def _get_eol_status_for_assets(db, asset_ids, client_account_id, engagement_id):
    # Step 1: Query AssetEOLAssessment records (agent-populated)
    eol_stmt = select(AssetEOLAssessment).where(
        AssetEOLAssessment.asset_id.in_(valid_asset_ids),
        AssetEOLAssessment.client_account_id == client_account_id,
        AssetEOLAssessment.engagement_id == engagement_id,
    )

    # Step 2: Use Asset.asset_type for classification (not regex)
    def _get_product_type_from_asset_type(asset_type: Optional[str]) -> str:
        asset_type_lower = (asset_type or "").lower()
        if asset_type_lower == "database":
            return "database"
        elif asset_type_lower in ("server", "virtual_machine", "vm"):
            return "os"
        return "runtime"

    # Step 3: Only fall back to EOLLifecycleService for unassessed items
```

## Key Files

- `backend/app/api/v1/master_flows/assessment/info_endpoints/compliance_queries/eol_utils.py` - New modular file
- `backend/app/models/asset/specialized.py` - Contains `AssetEOLAssessment` model
- `backend/app/models/asset/models.py` - Contains `Asset.asset_type` field

## Pattern: Prefer Agent Data Over Heuristics

When building classification or enrichment features:

1. **Check existing models first** - Are there agent-populated tables?
2. **Use typed metadata** - `Asset.asset_type` > regex on `asset.name`
3. **Fall back gracefully** - Only use heuristics for truly unknown items
4. **Document deprecations** - Keep legacy functions with clear deprecation notes

## Usage Context

Apply this pattern whenever you need to classify or enrich data that agents already populate. The system has multiple enrichment agents that populate specialized tables - use that data instead of re-inventing classification logic.
