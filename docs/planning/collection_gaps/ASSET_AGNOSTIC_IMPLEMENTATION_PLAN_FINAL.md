# Asset-Agnostic Collection Implementation Plan - FINAL
## Based on GPT5 Reviews and Verified Code Evidence

## Executive Summary

After two rounds of GPT5 review and thorough codebase verification:
- **Asset model EXISTS** at `app/models/asset/models.py` - import correction needed
- **Tenant IDs are UUIDs** not integers - confirmed in governance.py
- **Completeness endpoints EXIST** at `/flows/{flow_id}/completeness` - already implemented
- **JSON fields confirmed** - `custom_attributes` and `technical_details` exist
- **8 modular gap tools exist** - better than monolithic approach

## Verified Corrections from GPT5

### ✅ CONFIRMED - Must Fix:
1. **Asset import path**: Use `from app.models.asset import Asset` (NOT `from app.models.assets`)
2. **Tenant IDs are UUIDs**: `client_account_id` and `engagement_id` are UUID type (verified in governance.py line 35-46)
3. **Router registration needed**: Must add to `router_imports.py` and `router_registry.py`
4. **Mock data replacement**: DataIntegration.tsx lines 50-152 contain hardcoded conflicts

### ❌ INCORRECT - Already Exists:
1. **Completeness endpoints**: Already exist at `/flows/{flow_id}/completeness` (GET) and `/flows/{flow_id}/completeness/refresh` (POST)
2. **Gap analysis tools**: 8 modular tools exist, not missing

## GPT5 Final Review Clarifications

### ✅ Confirmed Correct:
1. **Completeness endpoints exist** in `collection_gaps/collection_flows/handlers.py`
   - Must verify router registration in `router_imports.py` and `router_registry.py`
2. **Asset import path**: `from app.models.asset import Asset` or `from app.models import Asset`
3. **UUID tenant IDs**: Correct throughout new schemas
4. **Three asset endpoints**: Under `/api/v1/collection/assets/*` with tenant scoping

### ⚠️ Must Verify:
1. **Router Registration**: Check ALL collection_gaps routers are registered:
   - collection_flows
   - assets (new)
   - maintenance_windows
   - vendor_products
   - governance

## Implementation Plan - Week 1 Sprint

### Day 1-2: Database & Backend Foundation

#### 1. Create Conflicts Table Migration
```sql
-- File: /backend/alembic/versions/074_add_asset_field_conflicts.py
CREATE TABLE IF NOT EXISTS migration.asset_field_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
    client_account_id UUID NOT NULL,  -- UUID confirmed
    engagement_id UUID NOT NULL,      -- UUID confirmed
    field_name VARCHAR(255) NOT NULL,
    conflicting_values JSONB NOT NULL,  -- [{value, source, timestamp, confidence}]
    resolution_status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (resolution_status IN ('pending', 'auto_resolved', 'manual_resolved')),
    resolved_value TEXT,
    resolved_by UUID,
    resolution_rationale TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_conflict_asset_field_tenant
        UNIQUE (asset_id, field_name, client_account_id, engagement_id)
);

CREATE INDEX idx_conflicts_asset_field ON migration.asset_field_conflicts (asset_id, field_name);
CREATE INDEX idx_conflicts_tenant ON migration.asset_field_conflicts (client_account_id, engagement_id);
```

#### 2. Add Three Asset Endpoints
```python
# File: /backend/app/api/v1/endpoints/collection_gaps/assets.py

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.core.feature_flags import require_feature
from app.models.asset import Asset  # CORRECT IMPORT PATH
from app.models.collection_flow import CollectionFlow
from app.models.asset_field_conflicts import AssetFieldConflict

router = APIRouter(prefix="/assets")

@router.post("/start")
@require_feature("collection.gaps.v1")
async def start_asset_collection(
    scope: str,  # "tenant" | "engagement" | "asset"
    scope_id: str,
    asset_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Start collection for any asset type without requiring application."""
    # Store scope in collection_flows.flow_metadata
    flow = CollectionFlow(
        flow_metadata={
            "scope": scope,
            "scope_id": scope_id,
            "asset_type": asset_type
        },
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id
    )
    db.add(flow)
    await db.commit()
    return {"flow_id": str(flow.id), "status": "started"}

@router.get("/{asset_id}/conflicts")
@require_feature("collection.gaps.v1")
async def get_asset_conflicts(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Get real conflicts from asset_field_conflicts table."""
    conflicts = await db.execute(
        select(AssetFieldConflict)
        .where(AssetFieldConflict.asset_id == asset_id)
        .where(AssetFieldConflict.client_account_id == context.client_account_id)
        .where(AssetFieldConflict.engagement_id == context.engagement_id)
    )
    return conflicts.scalars().all()

@router.post("/{asset_id}/conflicts/resolve")
@require_feature("collection.gaps.v1")
async def resolve_asset_conflict(
    asset_id: str,
    field_name: str,
    resolution: ConflictResolution,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """Resolve a specific field conflict."""
    conflict = await db.execute(
        select(AssetFieldConflict)
        .where(AssetFieldConflict.asset_id == asset_id)
        .where(AssetFieldConflict.field_name == field_name)
        .where(AssetFieldConflict.client_account_id == context.client_account_id)
    )
    conflict = conflict.scalar_one_or_none()

    if not conflict:
        raise HTTPException(404, "Conflict not found")

    conflict.resolution_status = "manual_resolved"
    conflict.resolved_value = resolution.value
    conflict.resolved_by = context.user_id
    conflict.resolution_rationale = resolution.rationale

    await db.commit()
    return {"status": "resolved"}
```

#### 3. Register ALL Collection Gaps Routers
```python
# File: /backend/app/api/v1/router_imports.py
# Verify ALL collection_gaps routers are imported
COLLECTION_GAPS_AVAILABLE = True
if COLLECTION_GAPS_AVAILABLE:
    from app.api.v1.endpoints.collection_gaps import (
        collection_flows,
        assets,  # NEW
        vendor_products,
        maintenance_windows,
        governance
    )

# File: /backend/app/api/v1/router_registry.py
# Register ALL collection_gaps routers
if COLLECTION_GAPS_AVAILABLE:
    # Collection flows (includes completeness endpoints)
    router.include_router(
        collection_flows.router,
        prefix="/collection",
        tags=["collection"]
    )

    # NEW: Asset-agnostic endpoints
    router.include_router(
        assets.router,
        prefix="/collection",
        tags=["collection-assets"]
    )

    # Vendor products
    router.include_router(
        vendor_products.router,
        prefix="/collection",
        tags=["collection-vendor"]
    )

    # Maintenance windows
    router.include_router(
        maintenance_windows.router,
        prefix="/collection",
        tags=["collection-maintenance"]
    )

    # Governance
    router.include_router(
        governance.router,
        prefix="/collection",
        tags=["collection-governance"]
    )
```

### Day 3: Conflict Detection Service
```python
# File: /backend/app/services/collection_gaps/conflict_detection_service.py

class ConflictDetectionService:
    """Detects field-level conflicts across multiple data sources."""

    async def detect_conflicts(self, asset_id: str) -> List[AssetFieldConflict]:
        """Aggregate data from multiple sources and detect conflicts."""

        # 1. Get asset with JSON fields
        asset = await self.db.execute(
            select(Asset).where(Asset.id == asset_id)
        )
        asset = asset.scalar_one_or_none()

        # 2. Aggregate from sources
        sources = {}

        # From custom_attributes JSON
        if asset.custom_attributes:
            for field, value in asset.custom_attributes.items():
                sources.setdefault(field, []).append({
                    "value": value,
                    "source": "custom_attributes",
                    "timestamp": asset.updated_at,
                    "confidence": 0.7
                })

        # From technical_details JSON
        if asset.technical_details:
            for field, value in asset.technical_details.items():
                sources.setdefault(field, []).append({
                    "value": value,
                    "source": "technical_details",
                    "timestamp": asset.updated_at,
                    "confidence": 0.8
                })

        # From raw_import_records
        imports = await self.db.execute(
            select(RawImportRecord)
            .where(RawImportRecord.asset_id == asset_id)
        )
        for record in imports.scalars():
            for field, value in record.data.items():
                sources.setdefault(field, []).append({
                    "value": value,
                    "source": f"import:{record.source_file}",
                    "timestamp": record.created_at,
                    "confidence": 0.9
                })

        # 3. Detect conflicts
        conflicts = []
        for field_name, values in sources.items():
            unique_values = set(v["value"] for v in values)
            if len(unique_values) > 1:
                conflict = AssetFieldConflict(
                    asset_id=asset_id,
                    field_name=field_name,
                    conflicting_values=values,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id
                )
                conflicts.append(conflict)

        return conflicts
```

### Day 4-5: Frontend Changes

#### 1. Remove Application Gates
```typescript
// File: /src/components/collection/ScopeSelectionDialog.tsx

interface ScopeSelectionDialogProps {
  onScopeSelect: (scope: 'tenant' | 'engagement' | 'asset', id: string) => void;
  onSkip?: () => void;
}

export const ScopeSelectionDialog: React.FC<ScopeSelectionDialogProps> = ({
  onScopeSelect,
  onSkip
}) => {
  const [scope, setScope] = useState<'tenant' | 'engagement' | 'asset'>('tenant');
  const [selectedAsset, setSelectedAsset] = useState<string>('');

  return (
    <Dialog open={true}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Select Collection Scope</DialogTitle>
          <DialogDescription>
            Choose what to collect data for. You can start with any asset type.
          </DialogDescription>
        </DialogHeader>

        <RadioGroup value={scope} onValueChange={setScope}>
          <RadioGroupItem value="tenant">Entire Tenant</RadioGroupItem>
          <RadioGroupItem value="engagement">Current Engagement</RadioGroupItem>
          <RadioGroupItem value="asset">Specific Asset</RadioGroupItem>
        </RadioGroup>

        {scope === 'asset' && (
          <AssetSelector
            onSelect={setSelectedAsset}
            allowedTypes={['server', 'database', 'device', 'application']}
          />
        )}

        <DialogFooter>
          <Button onClick={onSkip} variant="ghost">Skip</Button>
          <Button
            onClick={() => onScopeSelect(scope, selectedAsset)}
            disabled={scope === 'asset' && !selectedAsset}
          >
            Start Collection
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

#### 2. Replace Mock Data
```typescript
// File: /src/pages/assessment/collection-gaps/data-integration.tsx

// REMOVE lines 50-152 (mockConflicts)

// ADD real data fetching
const { data: conflicts, isLoading } = useQuery({
  queryKey: ['asset-conflicts', assetId],
  queryFn: async () => {
    const response = await fetch(`/api/v1/collection/assets/${assetId}/conflicts`, {
      headers: {
        'X-Client-Account-ID': clientAccountId,
        'X-Engagement-ID': engagementId
      }
    });
    return response.json();
  },
  enabled: !!assetId
});

// Use real conflicts in render
{conflicts?.map((conflict) => (
  <ConflictRow
    key={`${conflict.asset_id}-${conflict.field_name}`}
    conflict={conflict}
    onResolve={handleResolve}
  />
))}
```

#### 3. Collection Gaps Dashboard
```typescript
// File: /src/pages/assessment/collection-gaps/dashboard.tsx

export const CollectionGapsDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Collection Gaps Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Reuse existing component */}
        <CompletenessDashboard />

        {/* Use existing maintenance windows */}
        <Card>
          <CardHeader>
            <CardTitle>Maintenance Windows</CardTitle>
          </CardHeader>
          <CardContent>
            <MaintenanceWindowTable />
          </CardContent>
        </Card>

        {/* New conflicts overview */}
        <Card>
          <CardHeader>
            <CardTitle>Data Conflicts</CardTitle>
          </CardHeader>
          <CardContent>
            <ConflictsOverview />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
```

## Critical Code Fixes Required

### 1. Fix Asset Import
```python
# WRONG
from app.models.assets import Asset  # Module doesn't exist

# CORRECT
from app.models.asset import Asset  # Correct module path
# OR
from app.models import Asset  # If re-exported
```

### 2. Field Type Support
```typescript
// FormField.tsx - Verify both patterns work
case 'date':
case 'date_input':
  return <DatePicker {...props} />;

case 'number':
case 'numeric_input':
  return <NumberInput {...props} />;
```

### 3. Feature Flag Enforcement
```python
# Add to all new endpoints
from app.core.feature_flags import require_feature

@require_feature("collection.gaps.v1")
async def endpoint_handler(...):
    pass
```

## Success Validation Checklist

### Router Registration Verification
- [ ] collection_flows router registered (includes completeness endpoints)
- [ ] assets router registered (NEW)
- [ ] vendor_products router registered
- [ ] maintenance_windows router registered
- [ ] governance router registered
- [ ] All routers under `/api/v1/collection/*` prefix

### Week 1 Deliverables
- [ ] Asset model import corrected to `from app.models.asset import Asset`
- [ ] Conflicts table created with UUID tenant IDs
- [ ] Three asset endpoints added (start/conflicts/resolve) with proper imports
- [ ] ALL routers registered in router_imports.py and router_registry.py
- [ ] Application gates removed with ScopeSelectionDialog
- [ ] Mock data replaced with real API calls
- [ ] Collection Gaps dashboard created mounting existing components
- [ ] Feature flags enforced on all new endpoints

### Acceptance Criteria
- [ ] Can start collection for ANY asset type (not just applications)
- [ ] Real conflicts shown from multiple data sources
- [ ] Conflicts can be resolved through UI
- [ ] Completeness metrics visible (using existing endpoints)
- [ ] Maintenance windows editable (using existing components)
- [ ] All endpoints tenant-scoped with UUID IDs
- [ ] No mock data in production UI

## What We're NOT Doing
- ❌ **NOT creating new completeness endpoints** - they already exist
- ❌ **NOT creating GapAnalysisTool** - 8 modular tools are better
- ❌ **NOT using integer tenant IDs** - verified as UUIDs
- ❌ **NOT deploying full EAV yet** - JSON fields first
- ❌ **NOT enabling pgvector yet** - feature flag for later

## Implementation Order
1. **Hour 1-2**: Create conflicts table migration with UUID IDs
2. **Hour 3-4**: Add three asset endpoints with full imports
3. **Hour 5-6**: Register ALL collection_gaps routers and verify
4. **Hour 7-8**: Build ConflictDetectionService with tenant scoping
5. **Hour 9-10**: Remove application gates in UI
6. **Hour 11-12**: Replace mock data with real API calls
7. **Hour 13-14**: Create Collection Gaps dashboard mounting existing components
8. **Hour 15-16**: Test end-to-end flow with all routers

## GPT5 Implementation Offer

GPT5 has offered to help with:
1. **Verify routes are registered** and add them if missing
2. **Add the conflicts migration** and assets endpoints
3. **Add minimal UI page** mounting completeness, maintenance windows, and conflicts

This would accelerate Phase 1/2 visibility end-to-end.

## Final Notes

This plan incorporates all of GPT5's valid corrections:
- Proper imports and tenant scoping throughout
- UUID tenant IDs confirmed and used
- ALL collection_gaps routers must be registered
- Structured error responses required
- No mock data in production

The implementation is ready to proceed with focus on router registration verification as the critical path item.