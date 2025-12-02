# Bug Fix Session: Asset Inventory Issues (December 2025)

**Issues Fixed**: #1075, #1190, #1191
**PR**: #1192

## Insight 1: Soft-Delete Filter Consistency

**Problem**: Soft-deleted assets appeared in grid but failed updates (404 errors)

**Root Cause**: Asset listing queries missing `deleted_at IS NULL` filter while update service correctly filters them out.

**Solution**: Add filter to ALL asset listing queries:
```python
# backend/app/services/unified_discovery_handlers/asset_list_handler.py
base_query = select(Asset).where(
    and_(
        Asset.client_account_id == self.context.client_account_id,
        Asset.engagement_id == self.context.engagement_id,
        Asset.deleted_at.is_(None),  # CRITICAL: Always exclude soft-deleted
    )
)
```

**Files**: `asset_list_handler.py`, `pagination.py`

---

## Insight 2: UUID Type Mismatch (Frontend vs Backend)

**Problem**: Asset deletion returned 404 even for valid assets

**Root Cause**: Frontend `Asset.id: number` but backend uses UUID (string). Type coercion failed silently.

**Solution**: Change all asset ID types to `string`:
```typescript
// src/types/asset.ts
export interface Asset {
  id: string;  // UUID from backend - NOT number!
}

// src/lib/api/assets.ts
static async softDeleteAsset(asset_id: string): Promise<void> {
  // asset_id is string (UUID), not number
}
```

**Files**: `asset.ts`, `assets.ts`, `useAssetSoftDelete.ts`

---

## Insight 3: useMemo for Context Headers

**Problem**: Qodo review flagged potential infinite re-render loop

**Root Cause**: `getAuthHeaders()` creates new object each render, causing `useApplicationsWithContext` to re-fetch.

**Solution**: Memoize the headers:
```typescript
// src/pages/assess/Treatment.tsx
const contextHeaders = useMemo(() => getAuthHeaders(), [getAuthHeaders]);
const { applications } = useApplicationsWithContext(contextHeaders);
```

---

## Insight 4: JSON.stringify for Pydantic Bodies

**Problem**: PATCH request for asset field update returned 422 error

**Root Cause**: Body passed as object, not JSON string. FastAPI/Pydantic requires serialized JSON.

**Solution**: Always stringify body:
```typescript
// src/lib/api/assets.ts
return await apiCall(endpoint, {
  method: 'PATCH',
  body: JSON.stringify({ value: field_value })  // NOT: body: { value }
});
```

---

## Insight 5: execute_phase Method Requirement

**Problem**: Discovery flow failed with `AttributeError: 'DiscoveryChildFlowService' has no attribute 'execute_phase'`

**Root Cause**: MFO lifecycle_commands calls `execute_phase()` on child services, but Discovery didn't implement it.

**Solution**: Add `execute_phase` method to child flow service:
```python
# backend/app/services/child_flow_services/discovery.py
async def execute_phase(
    self,
    flow_id: str,
    phase_name: str,
    phase_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Required by MFO lifecycle_commands"""
    child_flow = await self.get_by_master_flow_id(flow_id)
    if not child_flow:
        raise ValueError(f"Discovery flow not found for master flow {flow_id}")

    # Route to phase handlers based on phase_name
    if phase_name == "data_import":
        return {"status": "awaiting_user_input", "phase": phase_name}
    elif phase_name == "asset_inventory":
        approved_ids = (phase_input or {}).get("approved_asset_ids", [])
        if approved_ids:
            return {"status": "success", "phase": phase_name, "assets_processed": len(approved_ids)}
        return {"status": "awaiting_user_input", "phase": phase_name}
    # ... other phases
```

---

## Quick Reference: Common Asset Inventory Bugs

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| 404 on asset update | Missing soft-delete filter | Add `deleted_at.is_(None)` to listing query |
| 404 on asset delete | ID type mismatch | Change `Asset.id` from `number` to `string` |
| 422 on PATCH | Body not stringified | Use `JSON.stringify()` |
| execute_phase error | Missing method | Add to child flow service |
| Infinite re-renders | Unmemoized headers | Wrap in `useMemo()` |
