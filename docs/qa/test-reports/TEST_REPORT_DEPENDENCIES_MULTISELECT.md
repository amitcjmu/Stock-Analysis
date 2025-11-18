# Test Report: Dependencies Multi-Select Feature
**Date:** 2025-11-06
**Tester:** QA Playwright Agent
**Test Environment:** http://localhost:8081/discovery/inventory
**Branch:** fix/collection-flow-issues-20251106

## Executive Summary
**Status:** ❌ **CRITICAL FAILURE**
The dependencies multi-select feature has a **critical bug** that prevents users from selecting multiple assets as dependencies. The feature exhibits single-select behavior instead of multi-select, making it impossible to complete the intended workflow.

---

## Test Scenario Executed

### Objective
Verify that users can select multiple assets as dependencies from the inventory grid, save them, and see them persist across page refreshes.

### Test Steps
1. ✅ Navigate to inventory page (http://localhost:8081/discovery/inventory)
2. ✅ Locate an asset row with "No dependencies"
3. ✅ Double-click the Dependencies cell to open the modal
4. ✅ Verify modal opens with expected UI elements
5. ❌ **FAILED:** Select 3 different assets from the list
6. ❌ **BLOCKED:** Verify selected assets appear as badges
7. ❌ **BLOCKED:** Verify footer updates to "3 assets selected"
8. ❌ **BLOCKED:** Click Done and verify modal closes
9. ❌ **BLOCKED:** Verify dependencies cell shows 3 asset badges
10. ❌ **BLOCKED:** Verify PATCH request sent to backend
11. ❌ **BLOCKED:** Refresh page and verify persistence

---

## Critical Bug Found

### Bug #1: Single-Select Behavior Instead of Multi-Select

**Severity:** 🔴 **CRITICAL**
**Component:** `/src/components/discovery/inventory/components/AssetTable/DependencyCellEditor.tsx`

#### Observed Behavior
- ❌ Clicking on a checkbox unchecks all previously selected checkboxes
- ❌ Only one asset can be "active" at a time (radio button behavior)
- ❌ Footer always displays "0 assets selected • 133 available"
- ❌ Selected assets badges section never appears
- ❌ No console.log output from DependencyCellEditor despite logging statements in code

#### Expected Behavior
- ✅ Multiple checkboxes should remain checked simultaneously
- ✅ Footer should update to show "N assets selected"
- ✅ Selected assets should appear as removable badges above the list
- ✅ Clicking "Done" should save comma-separated asset IDs

#### Evidence
- **Screenshot 1:** [1_inventory_grid_initial.png] - Initial grid view
- **Screenshot 2:** [2_dependencies_column_visible.png] - Dependencies column visible
- **Screenshot 3:** [3_dependencies_modal_opened.png] - Modal opened successfully
- **Screenshot 4:** [4_BUG_single_select_instead_of_multiselect.png] - Shows both checkboxes unchecked after clicking each one

#### Root Cause Analysis
**Hypothesis:** The state management in the multi-select component is not working correctly. Possible causes:

1. **React State Issue:** The `selectedAssets` state in `DependencyCellEditor.tsx` (line 24) may not be updating properly due to:
   - Type mismatch between `asset.id` (from API) and stored IDs in state
   - Incorrect comparison in `selectedAssets.includes(asset.id)` (line 307)
   - Checkbox `checked` prop not reflecting state correctly

2. **Component Not Re-rendering:** The component may not be re-rendering when state changes, causing:
   - Checkboxes to not visually reflect selection
   - Footer counter to not update
   - Selected badges section to never appear

3. **Event Propagation Issue:** The onClick handler (line 304) and checkbox onCheckedChange (line 308) may be conflicting, causing:
   - Double-toggle behavior (toggle on, then immediate toggle off)
   - Race condition in state updates

#### Technical Details

**Asset ID Type Analysis:**
- Assets are fetched via `/api/v1/unified-discovery/assets` (see console logs)
- Database schema shows `assets.id` is UUID type
- Component supports both `number` and `string` IDs (line 24: `(number | string)[]`)
- The `includes()` comparison may fail if types don't match exactly

**State Management Flow:**
```typescript
// Line 166-172: Toggle function
const toggleAsset = (assetId: number | string) => {
  setSelectedAssets(prev =>
    prev.includes(assetId)
      ? prev.filter(id => id !== assetId)
      : [...prev, assetId]
  );
};
```

**Checkbox Implementation:**
```typescript
// Line 306-309: Dual event handlers (potential issue)
<Checkbox
  checked={selectedAssets.includes(asset.id)}
  onCheckedChange={() => toggleAsset(asset.id)}
/>
```

**Parent Div Click Handler:**
```typescript
// Line 303-305: Wrapping div also has onClick
<div
  onClick={() => toggleAsset(asset.id)}
>
```

**Potential Issue:** Both the div and checkbox trigger `toggleAsset()`, causing a double-toggle effect.

---

## Additional Findings

### Positive Observations
- ✅ Modal opens correctly on double-click
- ✅ Search box is present and functional (autofocus works)
- ✅ Filter buttons (All, Applications, Servers, Databases) render correctly
- ✅ Asset list displays 133 available assets
- ✅ Each asset shows name, type icon, and metadata
- ✅ Cancel and Done buttons are present
- ✅ UI layout and styling are correct
- ✅ No JavaScript errors in console

### Missing Console Output
Despite the code containing numerous `console.log` statements (lines 33-36, 51-52, 59-62, 146-159), **NONE appear in the browser console**. This suggests:
- The component may not be fully mounted/active
- Console logs may be stripped in production build
- Component instance may be different from expected

---

## Test Environment Details

### System Information
- **URL:** http://localhost:8081/discovery/inventory
- **Authenticated User:** chockas@hcltech.com
- **Client:** Democorp (11111111-1111-1111-1111-111111111111)
- **Engagement:** Cloud Migration 2024 (22222222-2222-2222-2222-222222222222)
- **Total Assets:** 134
- **Dependencies Column:** Visible after scrolling grid horizontally

### Database State
```sql
-- Verified no assets currently have dependencies
SELECT id, name, dependencies FROM migration.assets
WHERE dependencies IS NOT NULL;
-- Result: 0 rows
```

### Console Logs Analysis
- ✅ DependencyCellEditor marked as editable
- ✅ Asset API call successful (134 assets loaded)
- ✅ Modal asset fetch initiated (`/assets?page=1&page_size=200`)
- ❌ No logs from DependencyCellEditor component functions
- ❌ No getValue() calls logged
- ❌ No handleClose() calls logged

---

## Recommended Fix

### Immediate Action Required
1. **Fix State Management:**
   ```typescript
   // Remove onClick from parent div to prevent double-toggle
   <div className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded">
     <Checkbox
       checked={selectedAssets.includes(asset.id)}
       onCheckedChange={() => toggleAsset(asset.id)}
     />
     {/* ... rest of content ... */}
   </div>
   ```

2. **Add Type Safety:**
   ```typescript
   // Ensure consistent type comparison
   const toggleAsset = (assetId: number | string) => {
     const stringId = String(assetId); // Normalize to string
     setSelectedAssets(prev =>
       prev.map(String).includes(stringId)
         ? prev.filter(id => String(id) !== stringId)
         : [...prev, assetId]
     );
   };
   ```

3. **Debug Logging:**
   ```typescript
   // Add useEffect to track state changes
   useEffect(() => {
     console.log('[DependencyCellEditor] selectedAssets changed:', selectedAssets);
   }, [selectedAssets]);
   ```

### Verification Steps After Fix
1. Click first checkbox → Verify it stays checked
2. Click second checkbox → Verify both remain checked
3. Click third checkbox → Verify all three remain checked
4. Verify footer shows "3 assets selected • 130 available"
5. Verify selected badges appear with asset names
6. Click X on a badge → Verify it's removed from selection
7. Click Done → Verify cell updates with 3 asset badges
8. Check network tab for PATCH request to `/api/v1/unified-discovery/assets/{id}/fields/dependencies`
9. Refresh page → Verify dependencies persist

---

## Impact Assessment

### User Impact
**Severity:** 🔴 **CRITICAL**
**Affected Users:** ALL users attempting to set asset dependencies
**Business Impact:**
- Users cannot establish dependency relationships between assets
- Migration planning workflow is blocked
- Wave planning cannot account for dependencies
- Risk assessment is incomplete without dependency data

### Workaround
**Status:** ❌ **NO WORKAROUND AVAILABLE**
There is no alternative way to set dependencies through the UI. The only option would be direct database manipulation, which is not acceptable for end users.

---

## Test Artifacts

### Screenshots
1. **1_inventory_grid_initial.png** - Shows inventory grid after login
2. **2_dependencies_column_visible.png** - Dependencies column after horizontal scroll
3. **3_dependencies_modal_opened.png** - Modal successfully opened
4. **4_BUG_single_select_instead_of_multiselect.png** - Bug evidence: both checkboxes unchecked

### Location
All screenshots saved to:
```
/Users/chocka/CursorProjects/migrate-ui-orchestrator/.playwright-mcp/
```

---

## Conclusion

The dependencies multi-select feature **CANNOT be used in its current state**. The critical bug preventing multi-selection must be fixed before this feature can be considered functional. The issue appears to be in the state management and event handling of the DependencyCellEditor component.

**Recommendation:** Block release until this critical bug is resolved and verified through comprehensive testing.

---

## Next Steps

1. ✅ Test report created
2. ⏳ Developer fixes state management issue
3. ⏳ Re-test with same scenario
4. ⏳ Verify backend integration (PATCH request)
5. ⏳ Verify data persistence
6. ⏳ Test edge cases (select all, deselect all, search + select)
7. ⏳ Performance test with large asset lists (>500 assets)

**Test Report Generated By:** Claude Code QA Playwright Testing Agent
**Report Date:** November 6, 2025
