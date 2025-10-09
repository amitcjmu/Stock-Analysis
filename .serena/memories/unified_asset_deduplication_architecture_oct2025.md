# Unified Asset Deduplication Architecture (October 2025)

## Problem Solved
- **Multiple deduplication implementations** scattered across codebase (Qodo PR #531)
- **N+1 query problem** with batch asset creation (100 assets = 100+ DB queries)
- **Inconsistent duplicate detection** causing duplicate assets in database
- **No status feedback** on whether asset was created, updated, or already existed

## Solution: Single Source of Truth in AssetService

### File Location
`backend/app/services/asset_service/deduplication.py` (modularized from 567-line service)

### Core Method Signature
```python
async def create_or_update_asset(
    service_instance,
    asset_data: Dict[str, Any],
    flow_id: Optional[str] = None,
    *,
    upsert: bool = False,
    merge_strategy: Literal["enrich", "overwrite"] = "enrich",
) -> Tuple[Asset, Literal["created", "existed", "updated"]]:
    """
    Unified deduplication with hierarchical logic.

    Returns:
        (Asset, status) where status = "created" | "existed" | "updated"
    """
```

## Hierarchical Deduplication (4 Levels)

**ALL scoped by client_account_id + engagement_id (multi-tenant)**

### Priority 1: Name + Asset Type
```python
# Check name + asset_type match
existing = await db.execute(
    select(Asset).where(
        Asset.name == asset_data["name"],
        Asset.asset_type == asset_data["asset_type"],
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id
    )
)
if existing: return (existing, "existed")
```

### Priority 2: Hostname / FQDN / IP
```python
# Check hostname OR fqdn OR ip_address
if hostname := asset_data.get("hostname"):
    existing = await db.execute(
        select(Asset).where(
            Asset.hostname == hostname,
            Asset.client_account_id == client_account_id,
            Asset.engagement_id == engagement_id
        )
    )
    if existing: return (existing, "existed")
```

### Priority 3: Smart Name Normalization
```python
# Normalize: lowercase, remove spaces/dashes
normalized = asset_data["name"].lower().replace(" ", "").replace("-", "")
```

### Priority 4: External/Import IDs
```python
if external_id := asset_data.get("external_id"):
    # Check external system identifier
```

## Merge Strategies

### Enrich (Non-Destructive)
```python
if merge_strategy == "enrich":
    # Only set fields that are currently NULL/empty
    if not existing.operating_system and asset_data.get("operating_system"):
        existing.operating_system = asset_data["operating_system"]
```

### Overwrite (Explicit Replace)
```python
if merge_strategy == "overwrite":
    # Replace all provided fields
    for key, value in asset_data.items():
        setattr(existing, key, value)
```

## Batch Optimization: N+1 Elimination

### Problem
```python
# ❌ OLD: 100 assets = 100+ queries
for asset_data in assets_data:
    existing = await db.execute(select(Asset).where(...))  # Query per asset!
```

### Solution: Single Prefetch Query
```python
async def bulk_create_or_update_assets(
    service_instance,
    assets_data: list[Dict[str, Any]],
    ...
) -> list[Tuple[Asset, Literal["created", "existed", "updated"]]]:
    """Batch-optimized with single prefetch query."""

    # Extract all identifiers
    names = [a["name"] for a in assets_data]
    hostnames = [a.get("hostname") for a in assets_data if a.get("hostname")]

    # SINGLE query with OR conditions
    stmt = select(Asset).where(
        or_(
            Asset.name.in_(names),
            Asset.hostname.in_(hostnames),
            # ... other conditions
        ),
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id
    )
    existing_assets = (await db.execute(stmt)).scalars().all()

    # Build in-memory lookup indexes (O(1) checks)
    name_index = {a.name: a for a in existing_assets}
    hostname_index = {a.hostname: a for a in existing_assets if a.hostname}

    # Process all assets in memory
    results = []
    for asset_data in assets_data:
        if existing := name_index.get(asset_data["name"]):
            results.append((existing, "existed"))
        else:
            new_asset = Asset(**asset_data)
            db.add(new_asset)
            results.append((new_asset, "created"))

    await db.flush()  # Batch commit
    return results
```

**Performance**: 100 assets: 100+ queries → 2 queries (99% reduction)

## Database Indexes

**Migration**: `088_add_asset_dedup_composite_indexes.py`

```sql
-- Priority 1: name + asset_type
CREATE INDEX idx_asset_dedup_name_type_tenant
ON migration.assets (name, asset_type, client_account_id, engagement_id)
WHERE name IS NOT NULL AND asset_type IS NOT NULL;

-- Priority 2: hostname
CREATE INDEX idx_asset_dedup_hostname_tenant
ON migration.assets (hostname, client_account_id, engagement_id)
WHERE hostname IS NOT NULL;

-- Batch prefetch (IN clause optimization)
CREATE INDEX idx_asset_dedup_batch_name_tenant
ON migration.assets (client_account_id, engagement_id, name)
WHERE name IS NOT NULL;
```

## Usage in Tools & Services

### AssetCreationTool (CrewAI)
```python
# Use unified method
asset, status = await asset_service.create_or_update_asset(asset_data)

if status == "created":
    message = f"Asset '{asset.name}' created successfully"
elif status == "existed":
    message = f"Asset '{asset.name}' already exists (duplicate skipped)"
```

### AssetCreationBridgeService
```python
# Use unified method
asset, status = await self.asset_service.create_or_update_asset(
    asset_data, flow_id=str(discovery_flow.flow_id)
)

if status == "created":
    created_assets.append(asset)
elif status == "existed":
    skipped_assets.append({"existing_asset_id": str(asset.id)})
```

## Testing Coverage

**File**: `tests/backend/services/test_asset_service_deduplication.py` (427 lines)

### Test Classes
1. `TestCreateOrUpdateAsset` - Status returns (created/existed/updated)
2. `TestHierarchicalDeduplication` - 4-level priority logic
3. `TestMergeStrategies` - Enrich vs overwrite
4. `TestBulkCreateOrUpdateAssets` - Batch optimization
5. `TestMultiTenantIsolation` - Tenant scoping

## Key Takeaways

1. **Single source of truth** - All dedup logic in AssetService.create_or_update_asset()
2. **Status tuple pattern** - Return (asset, status) for caller decision-making
3. **Batch prefetch** - Single query + in-memory processing for N assets
4. **Multi-tenant scoping** - ALL queries include client_account_id + engagement_id
5. **Composite indexes** - Database-level optimization for dedup queries
