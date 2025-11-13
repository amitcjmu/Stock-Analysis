# Asset Inventory Frontend Enhancements (Issues #911 & #912)

## Implementation Summary

This document details the frontend implementation for AI Grid inline editing (#911) and soft delete functionality (#912) for the Asset Inventory feature.

## Files Created/Modified

### 1. API Layer (`/src/lib/api/assets.ts`)

**New Methods Added:**
- `updateAssetField(asset_id, field_name, field_value)` - PATCH with request body
- `bulkUpdateAssetField(asset_ids, field_name, field_value)` - PATCH with request body
- `softDeleteAsset(asset_id)` - DELETE
- `restoreAsset(asset_id)` - POST
- `bulkSoftDelete(asset_ids)` - DELETE with request body
- `getDeletedAssets(flow_id?)` - GET with query params

**Critical Implementation Details:**
- All POST/PUT/PATCH/DELETE methods use request body with `JSON.stringify()`, NOT query parameters
- All field names use `snake_case` (e.g., `asset_id`, `field_name`, NOT `assetId`, `fieldName`)
- Uses `apiCall()` helper from `/src/lib/api/apiClient.ts`

### 2. Type Definitions (`/src/types/asset.ts`)

**New Fields Added to Asset Interface:**
```typescript
// Soft delete fields (Issue #912)
deleted_at?: string;
deleted_by?: string;
is_deleted?: boolean;
```

### 3. Hooks

#### `/src/hooks/discovery/useAssetInventoryGrid.ts`
**Purpose:** Manages AI Grid inline editing with validation

**Key Features:**
- `EDITABLE_COLUMNS` configuration with validation rules
- Column types: `text`, `number`, `dropdown`, `boolean`
- Dropdown options for:
  - Asset Type (SERVER, APPLICATION, DATABASE, etc.)
  - Business Criticality (Critical, High, Medium, Low)
  - Environment (Production, Staging, Development, etc.)
  - 6R Strategy (rehost, replatform, refactor, etc.)
- Field validation:
  - Required fields
  - Min/max values for numbers
  - Regex patterns (e.g., IP address validation)
  - Custom validation functions
- `updateField` mutation with optimistic updates
- `bulkUpdateField` mutation for multi-asset updates
- Toast notifications for success/error

**Usage:**
```typescript
const { editableColumns, updateField, bulkUpdateField, isUpdating, validateFieldValue } = useAssetInventoryGrid();

// Update single field
updateField({ asset_id: 123, field_name: 'environment', field_value: 'Production' });

// Bulk update
bulkUpdateField({ asset_ids: [1, 2, 3], field_name: 'business_criticality', field_value: 'High' });
```

#### `/src/hooks/discovery/useAssetSoftDelete.ts`
**Purpose:** Manages soft delete operations with confirmation dialogs

**Key Features:**
- Soft delete with confirmation
- Restore with confirmation
- Bulk soft delete with confirmation
- Optimistic updates
- Toast notifications
- React Query cache invalidation

**Usage:**
```typescript
const { softDelete, restore, bulkSoftDelete, isDeleting, isRestoring } = useAssetSoftDelete();

// Delete single asset (with confirmation)
softDelete(asset.id, asset.name);

// Restore asset (with confirmation)
restore(asset.id, asset.name);

// Bulk delete (with confirmation)
bulkSoftDelete([1, 2, 3], 3);
```

### 4. Components

#### `/src/components/discovery/inventory/components/AssetTable/EditableCell.tsx`
**Purpose:** Inline editing cell component with validation

**Features:**
- Hover to show edit icon
- Click to edit
- Dropdown for dropdown columns
- Input for text/number columns
- Real-time validation with error messages
- Save on Enter, cancel on Escape
- Visual feedback (checkmarks, errors)
- Auto-focus on edit mode

**Props:**
```typescript
interface EditableCellProps {
  value: any;
  column: EditableColumn;
  onSave: (value: any) => Promise<void>;
  isUpdating: boolean;
}
```

#### `/src/components/discovery/inventory/components/AssetTable/EnhancedAssetTable.tsx`
**Purpose:** Enhanced asset table with inline editing and soft delete

**Features:**
- Inline editing for all editable columns
- Delete button (Trash2 icon) for active assets
- Restore button (RotateCcw icon) for deleted assets
- Visual distinction for trash view (red header, opacity)
- Integration with useAssetInventoryGrid and useAssetSoftDelete hooks
- Preserves all existing table functionality (filters, pagination, etc.)

**New Props:**
```typescript
interface EnhancedAssetTableProps extends AssetTableProps {
  isTrashView?: boolean; // Show as trash view with restore buttons
}
```

#### `/src/components/discovery/inventory/components/AssetTable/index.tsx` (Modified)
**Purpose:** Wrapper component that routes to appropriate table implementation

**Logic:**
- Detects Asset type (number IDs) vs AssetInventory type (string IDs)
- Routes to EnhancedAssetTable for Asset type or when `enableInlineEditing={true}`
- Routes to legacy AssetTable for AssetInventory type
- Maintains backward compatibility

### 5. Integration Example

To use the enhanced asset table with inline editing and soft delete in InventoryContent.tsx:

```typescript
import { AssetTable } from '../components/AssetTable';
import { AssetAPI } from '@/lib/api/assets';
import { useQuery } from '@tanstack/react-query';

// In component:
const [showTrash, setShowTrash] = useState(false);

// Query for active assets
const { data: activeAssets = [] } = useQuery({
  queryKey: ['assets', flowId],
  queryFn: () => AssetAPI.getAssets({ flow_id: flowId }),
  enabled: !showTrash
});

// Query for deleted assets
const { data: deletedAssets = [] } = useQuery({
  queryKey: ['deleted-assets', flowId],
  queryFn: () => AssetAPI.getDeletedAssets(flowId),
  enabled: showTrash
});

// Render
<div>
  <Button onClick={() => setShowTrash(!showTrash)}>
    {showTrash ? 'View Active Assets' : 'View Trash'}
  </Button>

  <AssetTable
    assets={showTrash ? deletedAssets : activeAssets}
    filteredAssets={...}
    selectedAssets={selectedAssets}
    onSelectAsset={handleSelectAsset}
    onSelectAll={handleSelectAll}
    // ... other props
    isTrashView={showTrash}
    enableInlineEditing={true}
  />
</div>
```

## Architecture Decisions

### 1. Request Body vs Query Parameters
Following `/docs/guidelines/API_REQUEST_PATTERNS.md`:
- ✅ **CORRECT**: POST/PUT/PATCH/DELETE use request body with `JSON.stringify()`
- ❌ **WRONG**: Using URLSearchParams for mutations

### 2. Field Naming Convention
Following CLAUDE.md guidelines:
- ✅ **CORRECT**: `snake_case` for all field names (e.g., `asset_id`, `field_name`, `deleted_at`)
- ❌ **WRONG**: camelCase (e.g., `assetId`, `fieldName`, `deletedAt`)

### 3. Optimistic Updates
- TanStack Query `onMutate` for instant UI feedback
- Automatic rollback on error via `invalidateQueries`
- Toast notifications for user confirmation

### 4. Validation Strategy
- Frontend validation for immediate feedback
- Backend validation for security (will be implemented separately)
- Editable column configuration defines validation rules
- Custom validators for complex logic (e.g., IP address format)

### 5. Soft Delete Pattern
- Assets marked with `deleted_at` timestamp
- Separate trash view to prevent accidental data loss
- Restore functionality to recover deleted assets
- Backend implementation will handle permanent deletion after retention period

## Testing Checklist

### Inline Editing (#911)
- [ ] Edit text fields (name, hostname, location)
- [ ] Edit number fields (cpu_cores, memory_gb, storage_gb)
- [ ] Edit dropdown fields (asset_type, environment, business_criticality, six_r_strategy)
- [ ] Validation errors for invalid input (IP address, required fields, min/max)
- [ ] Save on Enter key
- [ ] Cancel on Escape key
- [ ] Optimistic updates work correctly
- [ ] Error rollback on failed save
- [ ] Toast notifications show success/failure
- [ ] Bulk edit updates multiple assets
- [ ] Loading states during save

### Soft Delete (#912)
- [ ] Delete button appears for active assets
- [ ] Confirmation dialog shown before delete
- [ ] Asset disappears from active view after delete
- [ ] Trash toggle button works
- [ ] Trash view shows deleted assets with grayed appearance
- [ ] deleted_at timestamp displayed
- [ ] Restore button appears in trash view
- [ ] Confirmation dialog shown before restore
- [ ] Asset reappears in active view after restore
- [ ] Bulk delete confirmation shows count
- [ ] Bulk delete removes multiple assets
- [ ] Cache invalidation refreshes both active and trash views

## UI Flow

### Edit Flow
1. User hovers over editable cell → Edit icon (pencil) appears
2. User clicks edit icon → Cell enters edit mode with input/dropdown
3. User modifies value → Validation runs in real-time
4. User presses Enter or clicks checkmark → Value saved (optimistic update)
5. Success toast shown → Cell exits edit mode
6. If error → Error toast shown, value reverted, cell stays in edit mode

### Delete Flow
1. User clicks trash icon for an asset → Confirmation dialog appears
2. User confirms → Asset optimistically removed from view
3. Success toast shown → Asset moved to trash
4. If error → Error toast shown, asset reappears in view

### Restore Flow
1. User toggles to trash view → Deleted assets shown with opacity
2. User clicks restore icon (RotateCcw) → Confirmation dialog appears
3. User confirms → Asset disappears from trash
4. Success toast shown → Asset restored to active view
5. If error → Error toast shown, asset stays in trash

## Backend Requirements (To Be Implemented)

The frontend is ready, but backend endpoints need to be implemented:

### Required Endpoints

```python
# PATCH /api/v1/unified-discovery/assets/{asset_id}/field
# Request body: { "field_name": "environment", "field_value": "Production" }
# Response: Updated Asset object

# PATCH /api/v1/unified-discovery/assets/bulk-field-update
# Request body: { "asset_ids": [1, 2, 3], "field_name": "business_criticality", "field_value": "High" }
# Response: { "updated_count": 3 }

# DELETE /api/v1/unified-discovery/assets/{asset_id}
# Soft delete (set deleted_at timestamp)
# Response: 204 No Content

# POST /api/v1/unified-discovery/assets/{asset_id}/restore
# Clear deleted_at timestamp
# Response: Updated Asset object

# DELETE /api/v1/unified-discovery/assets/bulk-delete
# Request body: { "asset_ids": [1, 2, 3] }
# Response: { "deleted_count": 3 }

# GET /api/v1/unified-discovery/assets?deleted=true&flow_id={flow_id}
# Response: AssetListResponse with deleted assets
```

### Database Schema Updates

```sql
-- Add to assets table:
ALTER TABLE migration.assets
ADD COLUMN deleted_at TIMESTAMPTZ,
ADD COLUMN deleted_by VARCHAR(255);

-- Index for trash view queries
CREATE INDEX idx_assets_deleted_at ON migration.assets(deleted_at) WHERE deleted_at IS NOT NULL;
```

## Notes & Recommendations

1. **Validation**: Frontend validation is defensive. Backend MUST also validate all field updates for security.

2. **Permissions**: Backend should verify user has permission to edit/delete assets before processing requests.

3. **Audit Trail**: Consider logging field changes to an `asset_audit_log` table for compliance.

4. **Bulk Operations**: Implement transaction management for bulk operations to ensure atomicity.

5. **Permanent Deletion**: Implement a background job to permanently delete assets after a retention period (e.g., 30 days).

6. **Rate Limiting**: Consider rate limiting for bulk operations to prevent abuse.

7. **Field-Level Permissions**: Future enhancement could restrict editing certain fields based on user role.

8. **Undo/Redo**: Future enhancement could add undo/redo functionality for edits.

## Related Documentation

- `/docs/guidelines/API_REQUEST_PATTERNS.md` - API request patterns
- `/CLAUDE.md` - Project-specific coding standards
- `/docs/analysis/Notes/coding-agent-guide.md` - Implementation patterns
- GitHub Issue #911 - AI Grid Editing for Asset Inventory
- GitHub Issue #912 - Soft Delete for Assets
