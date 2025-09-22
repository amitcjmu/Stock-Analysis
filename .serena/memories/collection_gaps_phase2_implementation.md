# Collection Gaps Phase 2 Implementation Learnings

## Insight 1: Asset-Agnostic Collection Architecture
**Problem**: Data Integration page shows only dummy data, collection flow requires application selection first
**Solution**: Implement conflicts table with JSON-first approach before full EAV
**Code**:
```sql
CREATE TABLE migration.asset_field_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES migration.assets(id),
    client_account_id UUID NOT NULL,  -- UUID not INTEGER
    engagement_id UUID NOT NULL,       -- UUID not INTEGER
    field_name VARCHAR(255) NOT NULL,
    conflicting_values JSONB NOT NULL,
    resolution_status VARCHAR(50) DEFAULT 'pending'
        CHECK (resolution_status IN ('pending','auto_resolved','manual_resolved')),
    CONSTRAINT uq_conflict_asset_field_tenant
        UNIQUE (asset_id, field_name, client_account_id, engagement_id)
);
```
**Usage**: When enabling collection for ANY asset type without application dependency

## Insight 2: Router Registration Critical Path
**Problem**: Collection Gaps endpoints not reachable despite being implemented
**Solution**: Register ALL routers in router_imports.py and router_registry.py
**Code**:
```python
# router_imports.py
if COLLECTION_GAPS_AVAILABLE:
    from app.api.v1.endpoints.collection_gaps import (
        collection_flows,
        assets,
        vendor_products,
        maintenance_windows,
        governance
    )

# router_registry.py
router.include_router(
    collection_flows.router,
    prefix="/collection",
    tags=["collection"]
)
```
**Usage**: Without registration, endpoints exist but aren't reachable

## Insight 3: Asset Model Import Path
**Problem**: Import errors with Asset model
**Solution**: Use correct import path from modular structure
**Code**:
```python
# WRONG
from app.models.assets import Asset  # Module doesn't exist

# CORRECT
from app.models.asset import Asset  # Correct module path
# OR
from app.models import Asset  # If re-exported
```
**Usage**: Asset model exists at app/models/asset/models.py in modular structure

## Insight 4: Transaction Pattern Fix
**Problem**: "A transaction is already begun on this Session" errors
**Solution**: Remove nested transactions, use repository commit pattern
**Code**:
```python
# WRONG - Nested transaction
async with db.begin():
    result = await repo.create_window(commit=False)

# CORRECT - Repository manages transaction
result = await repo.create_window(commit=True)
```
**Usage**: For simple operations, let repository handle transactions

## Insight 5: Frontend Mock Data Replacement
**Problem**: DataIntegration.tsx contains 100+ lines of hardcoded mock conflicts
**Solution**: Replace with real API calls to conflicts endpoint
**Code**:
```typescript
// Remove mock data lines 50-152
const { data: conflicts } = useQuery({
  queryKey: ['asset-conflicts', assetId],
  queryFn: () => collectionFlowService.getAssetConflicts(assetId),
  enabled: !!assetId
});
```
**Usage**: Always fetch real data instead of using mock in production UI
