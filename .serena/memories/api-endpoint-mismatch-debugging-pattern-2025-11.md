# API Endpoint Mismatch Debugging Pattern

## Problem
Frontend API calls returned 404 errors because URLs didn't match backend route definitions.

## Root Cause
Frontend developer (nextjs-ui-architect agent) made assumptions about endpoint structure without verifying backend implementation.

### Incorrect Frontend
```typescript
// ❌ WRONG - Assumed structure
const endpoint = `${API_CONFIG.ENDPOINTS.DISCOVERY.ASSETS}/${asset_id}/field`;
body: JSON.stringify({ field_name, field_value })

const endpoint = `/assets/bulk-field-update`;
body: JSON.stringify({ asset_ids, field_name, field_value })
```

### Actual Backend
```python
# ✅ Correct backend routes
@router.patch("/{asset_id}/fields/{field_name}")  # field_name in URL
async def update_asset_field(
    asset_id: UUID,
    field_name: str,
    request: AssetFieldUpdateRequest  # { value: Any }
)

@router.patch("/bulk-update")  # NOT /bulk-field-update
async def bulk_update(
    request: BulkAssetUpdateRequest  # { updates: [...] }
)
```

## Detection Method

**Qodo Bot Security Review** caught this:
```
⚪ API route mismatch
Frontend endpoints don't match backend API, risking 404 errors
```

## Fix Pattern
```typescript
// ✅ CORRECT - Match backend exactly
static async updateAssetField(
  asset_id: number,
  field_name: string,
  field_value: any
): Promise<Asset> {
  // field_name goes in URL path, not body
  const endpoint = `${BASE}/${asset_id}/fields/${field_name}`;
  return await apiCall(endpoint, {
    method: 'PATCH',
    body: JSON.stringify({ value: field_value })  // Just 'value'
  });
}

static async bulkUpdateAssetField(
  asset_ids: number[],
  field_name: string,
  field_value: any
): Promise<{ updated_count: number }> {
  const endpoint = `${BASE}/bulk-update`;  // Exact backend route
  return await apiCall(endpoint, {
    method: 'PATCH',
    body: JSON.stringify({
      updates: asset_ids.map(id => ({
        asset_id: id,
        field_name,
        value: field_value
      }))
    })
  });
}
```

## Prevention Checklist

### For Agent Prompts
```markdown
**Critical Requirements:**
- Match EXACT backend endpoint paths from router files
- Verify request body schema from Pydantic models
- Use field names EXACTLY as defined in schemas
- Check router_registry.py for URL prefixes
```

### Manual Verification
```bash
# 1. Check backend routes
grep -r "@router" backend/app/api/v1/endpoints/asset_editing.py

# 2. Check frontend calls
grep -r "updateAssetField" src/lib/api/

# 3. Test with curl
curl -X PATCH "http://localhost:8000/api/v1/assets/{id}/fields/cpu_cores" \
  -H "Content-Type: application/json" \
  -d '{"value": 8}'
```

## When This Occurs
✅ Multi-agent implementations (backend + frontend)
✅ New API endpoint creation
✅ Bulk operation endpoints
✅ Path parameters in URLs

## Resolution Time
- Detection: Immediate (Qodo Bot review)
- Fix: 5 minutes (2 files changed)
- Validation: 2 minutes (curl test)
