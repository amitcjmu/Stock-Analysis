# Soft Delete Pattern for Asset Inventory

**Date**: January 2025  
**Context**: Need reversible deletion for asset cleanup  
**Issue**: #912

## Problem

Users need to remove assets from active inventory view without permanently deleting them. Use cases:
- Remove test/duplicate assets during cleanup
- Undo accidental deletions
- Maintain complete historical audit trail
- Comply with data retention requirements

## Solution: Soft Delete Pattern

**Core Concept**: Mark records as deleted instead of removing from database

### Database Schema
```sql
-- Add to assets table
ALTER TABLE migration.assets 
ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL,
ADD COLUMN deleted_by UUID DEFAULT NULL;

-- Index for active assets (most common query)
CREATE INDEX idx_assets_active 
    ON migration.assets(client_account_id, engagement_id) 
    WHERE deleted_at IS NULL;

-- Index for trash view
CREATE INDEX idx_assets_deleted 
    ON migration.assets(deleted_at DESC) 
    WHERE deleted_at IS NOT NULL;
```

### State Transitions
```
Active (deleted_at = NULL)
    ↓ soft_delete()
Deleted (deleted_at = timestamp)
    ↓ restore()
Active (deleted_at = NULL)
```

## Backend Implementation

### Model Changes
```python
# backend/app/models/asset.py
class Asset(Base):
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP, nullable=True, default=None
    )
    deleted_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None
    )
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    @property
    def is_active(self) -> bool:
        return self.deleted_at is None
```

### Service Layer
```python
# backend/app/services/asset_service/soft_delete.py
class AssetSoftDeleteService:
    async def soft_delete_asset(self, asset_id: UUID, deleted_by: UUID) -> Asset:
        """Mark asset as deleted"""
        asset = await self._get_asset(asset_id)
        asset.deleted_at = datetime.utcnow()
        asset.deleted_by = deleted_by
        await self.db.commit()
        return asset
    
    async def restore_asset(self, asset_id: UUID, restored_by: UUID) -> Asset:
        """Restore soft-deleted asset"""
        asset = await self._get_deleted_asset(asset_id)
        asset.deleted_at = None
        asset.deleted_by = None
        asset.updated_by = restored_by
        await self.db.commit()
        return asset
```

### Repository Pattern
```python
# backend/app/repositories/asset_repository.py
class AssetRepository:
    async def get_all(self, include_deleted: bool = False) -> List[Asset]:
        stmt = select(Asset).where(
            Asset.client_account_id == self.client_account_id,
            Asset.engagement_id == self.engagement_id
        )
        
        # Default: exclude soft-deleted
        if not include_deleted:
            stmt = stmt.where(Asset.deleted_at.is_(None))
        
        return await self.db.execute(stmt).scalars().all()
```

### API Endpoints
```
DELETE /api/v1/assets/{asset_id}          → Soft delete
POST   /api/v1/assets/{asset_id}/restore  → Restore
DELETE /api/v1/assets/bulk-delete         → Bulk soft delete
GET    /api/v1/assets/trash               → Get deleted assets
```

## Frontend Implementation

### UI Components

**Inventory View (Active Assets)**:
```
┌─────────────────────────────────────────┐
│ [View Trash]                   [Export] │
├─────────────────────────────────────────┤
│ Asset Inventory (245 active)            │
│ ☐ | Name    | Type | Actions           │
│ ☐ | Prod-01 | DB   | [🗑️ Delete]       │
└─────────────────────────────────────────┘
```

**Trash View (Deleted Assets)**:
```
┌─────────────────────────────────────────┐
│ [Back to Inventory]                     │
├─────────────────────────────────────────┤
│ Trash (15 deleted)                      │
│ ☐ | Name    | Deleted    | Actions     │
│ ☐ | Test-01 | 2 days ago | [↺ Restore] │
└─────────────────────────────────────────┘
```

### React Hook Pattern
```typescript
// src/hooks/discovery/useAssetSoftDelete.ts
export const useAssetSoftDelete = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const softDeleteMutation = useMutation({
    mutationFn: async (assetId: string) => {
      const confirmed = await confirm('Delete? Can restore later.');
      if (!confirmed) throw new Error('Cancelled');
      return await assetService.softDeleteAsset(assetId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['assets']);
      toast({ title: 'Deleted. View Trash to restore.' });
    }
  });

  const restoreMutation = useMutation({
    mutationFn: async (assetId: string) => {
      return await assetService.restoreAsset(assetId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['assets']);
      toast({ title: 'Asset restored' });
    }
  });

  return { softDelete, restore };
};
```

## Key Design Decisions

### 1. Partial Index for Performance
```sql
-- Only index active assets (most common query)
CREATE INDEX idx_assets_active 
    ON migration.assets(client_account_id, engagement_id) 
    WHERE deleted_at IS NULL;
```

**Why**: 95% of queries filter for active assets. Partial index reduces size and improves query speed.

### 2. Default Exclude Deleted
```python
async def get_all(self, include_deleted: bool = False):
    # Default: exclude deleted
```

**Why**: Prevents accidentally exposing deleted data. Requires explicit opt-in to see trash.

### 3. Soft Delete vs Hard Delete
- **Soft Delete**: Default for user actions (reversible)
- **Hard Delete**: Admin-only, after retention period (permanent)

### 4. Tenant Scoping
```python
# Always scope by tenant
stmt = stmt.where(
    Asset.client_account_id == self.client_account_id,
    Asset.engagement_id == self.engagement_id
)
```

**Why**: Prevent cross-tenant data leakage in trash view.

## Confirmation UX Patterns

### Delete Confirmation
```typescript
const confirmed = await confirm(
  'Delete this asset? You can restore it later from Trash.'
);
```

**Why**: "Can restore later" reduces anxiety about deletion.

### Bulk Delete Confirmation
```typescript
const confirmed = await confirm(
  `Delete ${count} assets? You can restore them later.`
);
```

**Why**: Shows impact (count) and reminds of reversibility.

## Query Performance

### Active Assets Query (Optimized)
```sql
SELECT * FROM migration.assets
WHERE client_account_id = ? 
  AND engagement_id = ? 
  AND deleted_at IS NULL  -- Uses partial index
ORDER BY name;
```

**Index Used**: `idx_assets_active` (partial index)

### Trash Query
```sql
SELECT * FROM migration.assets
WHERE client_account_id = ? 
  AND engagement_id = ? 
  AND deleted_at IS NOT NULL  -- Uses partial index
ORDER BY deleted_at DESC;  -- Most recent first
```

**Index Used**: `idx_assets_deleted` (partial index)

## Cascading Considerations

**Question**: What happens to dependencies when asset is soft deleted?

**Options**:
1. **Keep Dependencies** (Recommended for MVP):
   - Dependencies remain in database
   - Queries filter out deleted assets
   - Restoring asset restores dependencies automatically

2. **Cascade Soft Delete** (Future Enhancement):
   - Soft delete all dependencies when parent deleted
   - Restore all dependencies when parent restored
   - More complex but cleaner

**Current Decision**: Option 1 (Keep Dependencies)

## Audit Trail Integration

### Change Log Entry
```python
# Log deletion to asset_field_change_log
await log_change(
    asset_id=asset_id,
    field_name="deleted_at",
    old_value=None,
    new_value=deleted_at.isoformat(),
    changed_by=deleted_by
)
```

### Query Deletion History
```sql
SELECT asset_id, deleted_at, deleted_by, 
       changed_at, changed_by
FROM migration.asset_field_change_log
WHERE field_name = 'deleted_at'
  AND new_value IS NOT NULL
ORDER BY changed_at DESC;
```

## Testing Strategy

### Unit Tests
```python
async def test_soft_delete_asset():
    asset = await service.create_asset(data)
    assert asset.is_active
    
    deleted = await service.soft_delete_asset(asset.id, user_id)
    assert deleted.is_deleted
    assert deleted.deleted_by == user_id
    
    restored = await service.restore_asset(asset.id, user_id)
    assert restored.is_active
```

### Integration Tests
```python
async def test_soft_delete_hides_from_list():
    asset1 = await service.create_asset(data1)
    asset2 = await service.create_asset(data2)
    
    # Both visible initially
    assets = await repo.get_all()
    assert len(assets) == 2
    
    # Soft delete one
    await service.soft_delete_asset(asset1.id, user_id)
    
    # Only one visible
    assets = await repo.get_all()
    assert len(assets) == 1
    assert assets[0].id == asset2.id
    
    # Both visible with include_deleted=True
    all_assets = await repo.get_all(include_deleted=True)
    assert len(all_assets) == 2
```

### E2E Tests
```typescript
test('soft delete and restore workflow', async ({ page }) => {
  // Navigate to inventory
  await page.goto('/discovery/inventory');
  
  // Delete asset
  await page.click('[data-asset="prod-db-01"] [data-action="delete"]');
  await page.click('[data-confirm="delete"]');
  
  // Verify removed from list
  await expect(page.locator('[data-asset="prod-db-01"]')).not.toBeVisible();
  
  // View trash
  await page.click('[data-action="view-trash"]');
  await expect(page.locator('[data-asset="prod-db-01"]')).toBeVisible();
  
  // Restore asset
  await page.click('[data-asset="prod-db-01"] [data-action="restore"]');
  
  // Return to inventory
  await page.click('[data-action="back-to-inventory"]');
  await expect(page.locator('[data-asset="prod-db-01"]')).toBeVisible();
});
```

## Future Enhancements

### 1. Permanent Delete (Admin Only)
```python
async def hard_delete_asset(self, asset_id: UUID, admin_id: UUID):
    """Permanently delete (admin only, after retention period)"""
    # Verify admin permissions
    # Check retention policy (e.g., >90 days in trash)
    # Delete from database
```

### 2. Auto-Purge Trash
```python
async def purge_old_deleted_assets(retention_days: int = 90):
    """Auto-delete assets in trash older than retention period"""
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    stmt = delete(Asset).where(
        Asset.deleted_at < cutoff
    )
    await db.execute(stmt)
```

### 3. Deletion Reason
```python
class Asset(Base):
    deletion_reason: Mapped[Optional[str]] = mapped_column(Text)
```

## Related Patterns

- **Repository Pattern**: Encapsulates data access with filtering
- **Optimistic Updates**: Frontend pattern for immediate UI feedback
- **Confirmation Modals**: UX pattern for destructive actions
- **Audit Trail**: Track all state changes for compliance

## References

- Issue #912 - Implementation tracking
- Issue #911 - AI Grid Editing (related bulk actions)
- `backend/app/services/asset_service/soft_delete.py` - Service implementation
- `backend/alembic/versions/094_add_soft_delete_to_assets.py` - Migration
