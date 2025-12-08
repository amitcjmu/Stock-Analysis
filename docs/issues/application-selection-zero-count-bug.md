# Application Selection Page Shows Zero Application Count on Initial Load

## 🐛 Bug Description

The Application Selection page (`/collection/select-applications`) displays **zero applications** in the asset type count section on initial page load, even though there are **186+ applications** in the database. The count becomes correct only after scrolling through the table, which triggers infinite scroll to load additional pages.

## 📋 Steps to Reproduce

1. Navigate to `/collection/select-applications?flowId=<flow-id>`
2. Observe the asset type count buttons at the top of the page
3. **Initial Load**: Applications count shows **0**
4. Scroll down in the assets table to trigger infinite scroll
5. **After Scrolling**: Applications count updates to the correct number (186)

## 📸 Screenshots

> **Note**: Screenshots will be attached showing:
> - Initial page load with Applications (0) count
> - After scrolling showing Applications (186) count
> - Browser console logs showing pagination behavior

## ✅ Expected Behavior

The asset type count buttons should display the **total count of all assets by type** from the database immediately on page load, regardless of pagination:

- **Applications**: Should show **186** (or actual total)
- **Servers**: Should show correct total count
- **Databases**: Should show correct total count
- **Network Devices**: Should show correct total count

The count section should be **independent of pagination** - it should show totals for all assets, not just the assets loaded in the current page.

## ❌ Actual Behavior

On initial page load:
- **Applications**: Shows **0** ❌
- **Servers**: Shows **47** (incorrect - only counts first page)
- **Databases**: Shows **3** (may be correct by coincidence)

After scrolling (when infinite scroll loads more pages):
- **Applications**: Shows **186** ✅ (correct)
- **Servers**: Shows correct total
- **Databases**: Shows correct total

## 🗄️ Database Verification

**Total Assets by Type:**
```sql
SELECT asset_type, COUNT(*) 
FROM migration.assets 
WHERE client_account_id = 'ee84c985-01fc-43f5-9721-2c2e0261afbd'::uuid 
  AND engagement_id = '83e716bd-6da9-45cc-bbad-675936194eba'::uuid 
  AND deleted_at IS NULL 
GROUP BY asset_type;
```

**Results:**
- `application`: **186** ✅
- `server`: **96** ✅
- `database`: **3** ✅

**Total**: **285 assets**

## 🔧 Technical Details

### Affected Components

**Backend:**
- `backend/app/api/v1/endpoints/asset_inventory/pagination.py`
- Endpoint: `GET /api/v1/asset-inventory/list/paginated`
- The `summary` object in the API response appears to only count assets from the current page

**Frontend:**
- `src/pages/collection/ApplicationSelection/hooks/useApplicationData.ts`
- `src/pages/collection/ApplicationSelection/components/SelectionControls.tsx`
- Asset type count buttons display: `Applications ({assetsByType.APPLICATION.length})`

### API Response Observation

The API response includes:
```json
{
  "assets": [...],  // Current page assets only
  "pagination": {
    "total_items": 285,  // ✅ Correct total
    "current_page": 1,
    "page_size": 50
  },
  "summary": {
    "applications": 0,  // ❌ Wrong: only counts current page
    "servers": 47,      // ❌ Wrong: only counts current page
    "databases": 3      // May be correct by coincidence
  }
}
```

## 📊 Impact

- **Severity**: Medium
- **User Impact**: Confusing UX - users see 0 applications and may think there are none
- **Workaround**: Users can scroll to load more pages, but counts are incorrect on initial load
- **Affected Users**: All users accessing the Application Selection page

## 🔗 Related

- Collection Flow: Application Selection
- Asset Inventory Pagination

## 📝 Additional Notes

- The infinite scroll mechanism works correctly
- The issue only affects the **initial count display**
- Once all pages are loaded via scrolling, counts become accurate
- The asset type count section should be independent of the paginated table below it

---

**Created**: [Date]  
**Reporter**: [Name]  
**Priority**: Medium  
**Labels**: `bug`, `backend`, `frontend`, `collection-flow`, `asset-inventory`

