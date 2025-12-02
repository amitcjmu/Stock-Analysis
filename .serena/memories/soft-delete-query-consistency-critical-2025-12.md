# CRITICAL: Soft-Delete Query Consistency Pattern

**Date**: December 2025
**Issue**: #1075 (AG Grid column update failures)
**Impact**: High - causes 404 errors on valid operations

## The Problem

When implementing soft-delete, the `AssetFieldUpdateService` correctly filters out deleted assets, but listing queries did NOT include the filter. This caused:

1. Deleted assets appear in AG Grid
2. User attempts to edit
3. Update service correctly rejects with 404
4. User sees "Asset not found" for visible asset

## The Golden Rule

**ALL asset listing queries MUST include `deleted_at IS NULL`**

## Files That Need the Filter

Every file that lists assets must include:

```python
Asset.deleted_at.is_(None)  # ALWAYS include
```

### Backend Files (Verified December 2025)

| File | Filter Added |
|------|--------------|
| `asset_list_handler.py` → `list_assets()` | ✅ |
| `asset_list_handler.py` → `get_asset_summary()` | ✅ |
| `pagination.py` → `_get_assets_from_db()` | ✅ |
| `asset_repository.py` → `get_all()` | ✅ (via include_deleted param) |

### When Adding New Asset Queries

**ALWAYS ask**: Does this query return assets to display? If yes, add the filter.

```python
# ✅ CORRECT - excludes soft-deleted
select(Asset).where(
    Asset.client_account_id == context.client_account_id,
    Asset.engagement_id == context.engagement_id,
    Asset.deleted_at.is_(None),  # Don't forget!
)

# ❌ WRONG - will show deleted assets
select(Asset).where(
    Asset.client_account_id == context.client_account_id,
    Asset.engagement_id == context.engagement_id,
    # Missing deleted_at filter!
)
```

## Exception: Trash View

Only the trash view endpoint should explicitly include deleted assets:

```python
# Trash view - explicitly show deleted only
select(Asset).where(
    Asset.client_account_id == context.client_account_id,
    Asset.engagement_id == context.engagement_id,
    Asset.deleted_at.is_not(None),  # Only deleted assets
)
```

## Pre-Commit Check Suggestion

Consider adding a pre-commit hook to warn when `select(Asset)` appears without `deleted_at` filter in the same query.

## Related Memories

- `soft-delete-pattern-asset-inventory-2025-01` - Full soft-delete architecture
- `bug-fix-session-asset-inventory-1075-1190-1191-dec2025` - Implementation details
