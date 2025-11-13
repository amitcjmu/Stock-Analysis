# Asset Preview Workflow Implementation (PR #913)

## Overview
Complete implementation of asset preview and approval workflow (Issues #907, #910) with 11 critical bug fixes discovered through iterative QA testing.

## Critical Bug Patterns Fixed

### 1. JSONB Persistence Requires flag_modified()

**Problem**: SQLAlchemy doesn't auto-detect in-place dictionary modifications on JSONB columns.

**Solution**: Always call `flag_modified()` after modifying JSONB data.

```python
from sqlalchemy.orm.attributes import flag_modified

# Modify JSONB column
persistence_data = master_flow.flow_persistence_data or {}
persistence_data["assets_preview"] = serialized_assets
master_flow.flow_persistence_data = persistence_data

# CRITICAL: Mark as modified for SQLAlchemy change tracking
flag_modified(master_flow, "flow_persistence_data")
await db_session.commit()
```

**File**: `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py:258`

### 2. Auto-Continuation Blocked by 'completed' Status

**Problem**: Auto-continuation logic blocked when `status='completed'`, preventing phase progression.

**Root Cause**: Misunderstood that 'completed' means "THIS PHASE done", not "entire flow done".

**Solution**: Only block on 'paused' and 'waiting_for_approval'.

```python
# CRITICAL: 'completed' means THIS PHASE is done, NOT the entire flow
should_auto_continue = result_status not in ["paused", "waiting_for_approval"]

if should_auto_continue and execution_result.get("next_phase"):
    await self.execute_phase(
        flow_id=str(master_flow.flow_id),
        phase_name=execution_result["next_phase"],
        phase_input=next_phase_input,
        validation_overrides=None,
    )
```

**File**: `backend/app/services/master_flow_orchestrator/operations/flow_execution_operations.py:239`

### 3. data_import_id Lost in Auto-Continuation

**Problem**: Auto-continuation passed empty `phase_input={}`, causing asset_inventory to fail.

**Solution**: Retrieve discovery flow and propagate data_import_id.

```python
# Retrieve discovery flow to pass data_import_id
discovery_repo = DiscoveryFlowRepository(self.db, ...)
discovery_flow = await discovery_repo.get_by_flow_id(str(master_flow.flow_id))

next_phase_input = {
    "master_flow_id": str(master_flow.flow_id),
    "client_account_id": str(master_flow.client_account_id),
    "engagement_id": str(master_flow.engagement_id),
}

if discovery_flow and discovery_flow.data_import_id:
    next_phase_input["data_import_id"] = str(discovery_flow.data_import_id)

await self.execute_phase(..., phase_input=next_phase_input, ...)
```

**File**: `backend/app/services/master_flow_orchestrator/operations/flow_execution_operations.py:256-269`

### 4. Phase Transition Routing to Wrong Phase

**Problem**: After data_cleansing, flow went directly to asset_creation, skipping asset_inventory.

**Solution**: Fixed PhaseTransitionAgent to route to asset_inventory.

```python
# Line 253 - Changed from asset_creation to asset_inventory
return AgentDecision(
    action=PhaseAction.PROCEED,
    next_phase="asset_inventory",  # CC FIX: Was "asset_creation"
    confidence=proceed_confidence,
    reasoning="Data cleansing completed. Proceeding to asset inventory for preview.",
)
```

**File**: `backend/app/services/crewai_flows/agents/decision/discovery_decisions.py:253`

### 5. Frontend Field Name Mismatch ('temp_id' vs 'id')

**Problem**: Backend used 'temp_id', frontend expected 'id' for asset tracking.

**Solution**: Align backend to use 'id' field.

```python
# Generate preview data with 'id' field (not 'temp_id')
serialized_assets = []
for i, asset in enumerate(assets_data):
    serialized_asset = serialize_uuids_for_jsonb(asset)
    serialized_asset["id"] = f"asset-{i}"  # Frontend expects 'id'
    serialized_assets.append(serialized_asset)
```

**File**: `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py:249`

### 6. React Query onSuccess Deprecated (v4+)

**Problem**: Assets not displaying despite API success - React Query v4+ deprecated `onSuccess` callback.

**Solution**: Replace with `useEffect` hook watching query data.

```typescript
// Before (deprecated)
useQuery({
  queryFn: getAssetPreview,
  onSuccess: (data) => {
    setEditableAssets(data.assets_preview.map(...));
  }
});

// After (correct)
const { data: previewData } = useQuery({
  queryFn: getAssetPreview,
});

useEffect(() => {
  if (previewData?.assets_preview && editableAssets.length === 0) {
    setEditableAssets(
      previewData.assets_preview.map((asset) => ({
        ...asset,
        isSelected: true,
        validationErrors: {},
      }))
    );
  }
}, [previewData, editableAssets.length]);
```

**File**: `src/components/discovery/AssetCreationPreviewModal.tsx:95-106`

### 7. Missing useEffect Import

**Problem**: Browser error "ReferenceError: useEffect is not defined".

**Solution**: Add useEffect to React imports.

```typescript
// Add useEffect to imports
import React, { useState, useMemo, useEffect } from 'react';
```

**File**: `src/components/discovery/AssetCreationPreviewModal.tsx:17`

## Security Fixes (Qodo Bot Feedback)

### 8. Input Validation Gap in Approve Endpoint

**Problem**: Approve endpoint accepted unbounded payload.

**Solution**: Add Pydantic model with validation.

```python
from pydantic import BaseModel, Field, validator

class ApproveAssetsRequest(BaseModel):
    """Request model for asset approval with validation"""

    approved_asset_ids: List[str] = Field(
        ...,
        min_items=1,
        max_items=1000,
        description="List of asset IDs to approve (max 1000)",
    )

    @validator("approved_asset_ids")
    def validate_asset_ids(cls, v):
        if not all(isinstance(id, str) and id.strip() for id in v):
            raise ValueError("All asset IDs must be non-empty strings")
        return v

@router.post("/{flow_id}/approve")
async def approve_asset_preview(
    flow_id: UUID,
    request: ApproveAssetsRequest = Body(...),  # Pydantic validation
    ...
):
    approved_asset_ids = request.approved_asset_ids
```

**File**: `backend/app/api/v1/endpoints/asset_preview.py:26-41, 119-140`

### 9. Transaction Rollback Not Clearing In-Memory Lists

**Problem**: After database rollback, in-memory lists still contained IDs that were never persisted.

**Solution**: Clear lists on rollback to reflect actual database state.

```python
if errors:
    await self.db.rollback()
    # CC FIX (Qodo Security): Clear lists to reflect actual DB state
    created_assets.clear()
    created_dependencies.clear()
    resolved_count = 0
else:
    await self.db.commit()
    resolved_count = len(request.resolutions)
```

**File**: `backend/app/services/asset_conflict_service.py:79-87`

## Key Architectural Patterns

### Preview Data Storage Pattern

Store transformed assets in `flow_persistence_data` BEFORE database creation:

```python
# 1. Check if preview already exists
persistence_data = master_flow.flow_persistence_data or {}
if persistence_data.get("assets_preview"):
    # Preview exists - wait for approval
    return {"status": "waiting_for_approval"}

# 2. Generate preview data
serialized_assets = []
for i, asset in enumerate(assets_data):
    serialized_asset = serialize_uuids_for_jsonb(asset)
    serialized_asset["id"] = f"asset-{i}"
    serialized_assets.append(serialized_asset)

# 3. Store in JSONB with flag_modified
persistence_data["assets_preview"] = serialized_assets
persistence_data["preview_generated_at"] = datetime.utcnow().isoformat()
master_flow.flow_persistence_data = persistence_data
flag_modified(master_flow, "flow_persistence_data")
await db_session.commit()

# 4. Return paused status
return {"status": "waiting_for_approval", "next_phase": "asset_inventory"}
```

### Approval and Resume Pattern

```python
# 1. User approves assets
persistence_data["approved_asset_ids"] = approved_asset_ids
persistence_data["approval_timestamp"] = datetime.utcnow().isoformat()
persistence_data["approved_by_user_id"] = str(current_user.id)
flag_modified(flow, "flow_persistence_data")
await db.commit()

# 2. Resume flow to create assets
from app.api.v1.endpoints.unified_discovery.flow_control_handlers import resume_flow_handler

await resume_flow_handler(
    flow_id=str(flow_id),
    phase_input=None,
    db=db,
    context=request_context,
    current_user=current_user,
)
```

## Testing Methodology

Used iterative QA testing with Playwright agent:
1. Create discovery flow with 41-record CSV
2. Observe phase transitions and backend logs
3. Verify preview modal displays assets
4. Test approval and asset creation
5. Check database for created assets

**Test Evidence**:
- Flow ID: `3d2bb902-4b36-40eb-8bb7-fb5503fb4e8b`
- Data Import ID: `fde34b5f-8f61-44f6-838d-b1901388af71`
- Test File: `test_40_assets_qa.csv` (41 records)
- Result: All 41 assets displayed, selectable, and created on approval

## When to Use This Pattern

Apply this pattern when:
- ✅ Users need to review data before database persistence
- ✅ Workflow requires approval gates
- ✅ Preview data must survive across phase transitions
- ✅ Need to track approval audit trail

## Common Pitfalls

1. **Forgetting flag_modified()** - JSONB changes won't persist
2. **Blocking on 'completed'** - Prevents phase progression
3. **Not propagating data_import_id** - Breaks context chain
4. **Using deprecated onSuccess** - React Query v4+ requires useEffect
5. **Missing Pydantic validation** - Security vulnerability

## Related Files

**Backend**:
- `backend/app/services/crewai_flows/handlers/phase_executors/asset_inventory_executor/base.py`
- `backend/app/services/master_flow_orchestrator/operations/flow_execution_operations.py`
- `backend/app/services/crewai_flows/agents/decision/discovery_decisions.py`
- `backend/app/api/v1/endpoints/asset_preview.py`
- `backend/app/services/asset_conflict_service.py`

**Frontend**:
- `src/components/discovery/AssetCreationPreviewModal.tsx`
- `src/lib/api/assetPreview.ts`

## PR Details

- **PR Number**: #913
- **Merge Commit**: d2928dcba
- **Issues Resolved**: #907 (Asset Preview), #910 (Conflict Resolution)
- **Files Changed**: 56 total
- **Lines Changed**: +5263, -1062
