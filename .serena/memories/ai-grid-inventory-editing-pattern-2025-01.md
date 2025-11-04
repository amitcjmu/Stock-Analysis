# AI Grid Pattern: Inline Editing for Asset Inventory

**Date**: January 2025
**Context**: Need to fix AI misclassifications and data gaps after inventory creation
**Issue**: #911

## Problem

Current inventory tab is **read-only** - users cannot correct AI errors without re-importing data.

**Common Issues Requiring Edits**:
- AI misclassifies asset_type (e.g., "SQL Server" as application vs. database)
- Business criticality incorrectly inferred
- Missing fields (operating_system, business_owner)
- Asset names are UUIDs/serial numbers instead of meaningful names

## Solution: Apply AI Grid Pattern

**Reference Implementation**: Data Gaps page already uses AI Grid for inline editing

### AI Grid Features
1. **Inline Editing**: Click cell → Edit → Auto-save
2. **Field Validation**: Type-specific (enum dropdowns, number ranges)
3. **Bulk Updates**: Select rows → Update field for all
4. **Audit Trail**: Track who changed what and when
5. **Optimistic Updates**: UI updates immediately, rolls back on error

## Architecture

### Frontend Components

**Component Hierarchy**:
```
InventoryPage
  ↓
AIGrid (shared component)
  ↓
EditableCell (dropdown | text | number)
  ↓
useAssetInventoryGrid (custom hook)
  ↓
assetService.updateAssetField() (API call)
```

**Key Files**:
- `src/components/shared/AIGrid.tsx` - Reusable editable grid
- `src/hooks/discovery/useAssetInventoryGrid.ts` - Asset-specific logic
- `src/services/api/assetService.ts` - API integration

### Backend Endpoints

**Single Field Update**:
```
PATCH /api/v1/assets/{asset_id}/fields/{field_name}
Body: { "value": "new_value" }
```

**Bulk Field Update**:
```
PATCH /api/v1/assets/bulk-update
Body: {
  "asset_ids": ["uuid1", "uuid2", ...],
  "field_name": "criticality",
  "value": "High"
}
```

### Field Security Model

**Editable Fields** (ALLOWED_EDITABLE_FIELDS):
```python
ALLOWED_EDITABLE_FIELDS = {
    # Core
    "name", "description", "asset_type", "environment",
    # Technical
    "operating_system", "os_version", "cpu_cores", "memory_gb", "storage_gb",
    # Network
    "ip_address", "hostname", "fqdn",
    # Business
    "business_owner", "technical_owner", "department", "criticality",
    # Migration
    "six_r_strategy", "migration_priority", "migration_complexity",
    # CMDB (PR #847)
    "business_unit", "vendor", "application_type", "lifecycle", "server_role"
}
```

**Protected Fields** (NEVER editable):
```python
PROTECTED_FIELDS = {
    "id", "client_account_id", "engagement_id", "flow_id",
    "created_at", "created_by", "discovery_timestamp"
}
```

### Validation Strategy

**Type-Specific Validation**:
```python
def _validate_field_value(field_name: str, value: Any) -> Any:
    if field_name in ["cpu_cores", "memory_gb", "storage_gb"]:
        # Numeric: 0 ≤ value ≤ max_value
        return float(value) if isinstance(value, (int, float)) else None

    elif field_name in ["asset_type", "criticality", "environment"]:
        # Enum: value in allowed_values
        allowed = get_allowed_enum_values(field_name)
        if value not in allowed:
            raise ValueError(f"Invalid {field_name}: {value}")

    elif field_name in ["name", "hostname", "operating_system"]:
        # String: trim whitespace
        return str(value).strip() if value else None

    return value
```

### Audit Trail

**Database Table** (optional enhancement):
```sql
CREATE TABLE migration.asset_field_change_log (
    id UUID PRIMARY KEY,
    asset_id UUID REFERENCES migration.assets(id),
    field_name VARCHAR(100),
    old_value JSONB,
    new_value JSONB,
    changed_by UUID,
    changed_at TIMESTAMP DEFAULT NOW(),
    change_reason TEXT
);
```

**Querying History**:
```sql
-- Get all changes for an asset
SELECT field_name, old_value, new_value, changed_at, changed_by
FROM migration.asset_field_change_log
WHERE asset_id = 'uuid-here'
ORDER BY changed_at DESC;

-- Get all criticality changes
SELECT asset_id, old_value, new_value, changed_at
FROM migration.asset_field_change_log
WHERE field_name = 'criticality'
AND changed_at > NOW() - INTERVAL '30 days';
```

## Implementation Details

### Frontend Hook Pattern

```typescript
// useAssetInventoryGrid.ts
export const useAssetInventoryGrid = () => {
  const { flowId } = useFlowContext();
  const queryClient = useQueryClient();

  // Optimistic update mutation
  const updateAssetMutation = useMutation({
    mutationFn: async ({ assetId, field, value }) => {
      return await assetService.updateAssetField(assetId, field, value);
    },
    onMutate: async ({ assetId, field, value }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(['assets', flowId]);

      // Snapshot previous value
      const previousAssets = queryClient.getQueryData(['assets', flowId]);

      // Optimistically update cache
      queryClient.setQueryData(['assets', flowId], (old) =>
        old.map(asset =>
          asset.id === assetId ? { ...asset, [field]: value } : asset
        )
      );

      // Return rollback context
      return { previousAssets };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['assets', flowId], context.previousAssets);
      toast({ variant: 'destructive', title: 'Update failed' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['assets', flowId]);
      toast({ title: 'Asset updated' });
    }
  });

  return { updateAsset: updateAssetMutation.mutateAsync };
};
```

### Backend Service Pattern

```python
# backend/app/services/asset_service/field_updates.py
class AssetFieldUpdateService:
    async def update_asset_field(
        self,
        asset_id: UUID,
        field_name: str,
        new_value: Any,
        updated_by: UUID
    ) -> Asset:
        # 1. Fetch asset with tenant scoping
        asset = await self._get_asset_with_tenant_check(asset_id)

        # 2. Store old value for audit
        old_value = getattr(asset, field_name, None)

        # 3. Validate new value
        validated_value = self._validate_field_value(field_name, new_value)

        # 4. Update field
        setattr(asset, field_name, validated_value)
        asset.updated_at = datetime.utcnow()
        asset.updated_by = updated_by

        # 5. Commit transaction
        await self.db.commit()
        await self.db.refresh(asset)

        # 6. Log audit trail (optional)
        await self._log_field_change(
            asset_id, field_name, old_value, validated_value, updated_by
        )

        return asset
```

### Cell Type Definitions

```typescript
// Column configuration for different cell types
const columns: ColumnDef<Asset>[] = [
  {
    accessorKey: 'name',
    header: 'Asset Name',
    editable: true,
    cellType: 'text',
    validation: { required: true, minLength: 3 }
  },
  {
    accessorKey: 'asset_type',
    header: 'Asset Type',
    editable: true,
    cellType: 'dropdown',
    options: ['server', 'application', 'database', 'network', 'storage', 'other'],
    validation: { required: true }
  },
  {
    accessorKey: 'cpu_cores',
    header: 'CPU Cores',
    editable: true,
    cellType: 'number',
    validation: { min: 0, max: 512 }
  },
  {
    accessorKey: 'criticality',
    header: 'Criticality',
    editable: true,
    cellType: 'dropdown',
    options: ['Low', 'Medium', 'High', 'Critical']
  }
];
```

## UX Design Patterns

### Inline Edit State Machine
```
Idle → Click → Editing → Blur/Enter → Saving → Success/Error → Idle
                  ↓                        ↓
                 Esc → Cancel          Rollback (if error)
```

### Visual Feedback
- **Idle**: Normal cell, hover shows edit icon ✏️
- **Editing**: Input/dropdown with focus
- **Saving**: Spinner icon
- **Success**: Green checkmark ✓ (fades after 2s)
- **Error**: Red border + error message tooltip

### Bulk Edit Modal
```
┌─────────────────────────────────────┐
│ Bulk Update Assets (25 selected)   │
├─────────────────────────────────────┤
│ Field to Update: [Criticality ▼]   │
│ New Value:       [High ▼]           │
├─────────────────────────────────────┤
│ Preview Changes:                    │
│ • Prod-DB-01: Medium → High         │
│ • App-Server: Low → High            │
│ • ...23 more                        │
├─────────────────────────────────────┤
│ [Cancel]              [Update All]  │
└─────────────────────────────────────┘
```

## Testing Strategy

### Unit Tests
```typescript
describe('useAssetInventoryGrid', () => {
  it('updates asset field optimistically', async () => {
    const { result } = renderHook(() => useAssetInventoryGrid());
    await result.current.updateAsset('asset-id', 'criticality', 'High');
    expect(queryClient.getQueryData()).toContainEqual({ criticality: 'High' });
  });

  it('rolls back on error', async () => {
    // Mock API failure
    // Verify cache rollback
  });
});
```

### Integration Tests
```python
async def test_update_asset_field_with_validation():
    # Update cpu_cores to valid value
    response = await client.patch(
        f"/api/v1/assets/{asset_id}/fields/cpu_cores",
        json={"value": 16}
    )
    assert response.status_code == 200

    # Attempt invalid value
    response = await client.patch(
        f"/api/v1/assets/{asset_id}/fields/cpu_cores",
        json={"value": -1}  # Negative cores invalid
    )
    assert response.status_code == 400
```

### E2E Tests (Playwright)
```typescript
test('edit asset criticality inline', async ({ page }) => {
  await page.goto('/discovery/inventory');

  // Click criticality cell
  await page.click('[data-row="0"] [data-field="criticality"]');

  // Select new value
  await page.selectOption('[data-field="criticality"] select', 'High');

  // Verify checkmark appears
  await expect(page.locator('[data-row="0"] .success-icon')).toBeVisible();

  // Verify value persists on reload
  await page.reload();
  await expect(page.locator('[data-row="0"] [data-field="criticality"]')).toHaveText('High');
});
```

## Migration Path

### Phase 1: Core Functionality (MVP)
- Inline editing for text fields (name, description, hostname)
- Dropdown editing for enums (asset_type, criticality, environment)
- Auto-save on blur/Enter
- Basic error handling

### Phase 2: Bulk Operations
- Multi-row selection
- Bulk update modal
- Bulk validation
- Progress indicator for large batches

### Phase 3: Audit Trail
- asset_field_change_log table
- Change history modal per asset
- "Revert change" functionality
- Export audit report

### Phase 4: AI Assistance
- Suggest values based on asset type patterns
- "Fix all asset_type misclassifications" button
- Confidence score for AI suggestions
- Batch accept/reject suggestions

## Related Patterns

- **Optimistic Updates**: Frontend pattern for immediate UI feedback
- **Field Validation**: Backend pattern for type-safe field updates
- **Audit Trail**: Database pattern for change history
- **Multi-tenant Scoping**: Security pattern for data isolation

## References

- Issue #911 - Implementation tracking
- `src/components/shared/AIGrid.tsx` - Reusable grid component
- `backend/app/services/asset_service/field_updates.py` - Field update service
- Data Gaps page - Reference implementation of AI Grid
