# TEST REPORT: Dependencies Column - Critical Rendering Bug

**Test Date**: 2025-11-06
**Tester**: QA Playwright Testing Agent
**Test URL**: http://localhost:8081/discovery/inventory
**Browser**: Playwright Chrome
**Test Objective**: Verify count-based dependencies multi-select feature

---

## EXECUTIVE SUMMARY

**CRITICAL BUG FOUND**: The Dependencies column is completely non-functional due to a rendering bug. The column is configured in the code, appears as "enabled" in the column selector UI, and logs confirmation that it's being set up with the custom multi-select editor, but **NEVER RENDERS** in the AG Grid table.

**Impact**: **BLOCKER** - Cannot test any part of the dependencies feature as the column doesn't exist in the visible table.

**Status**: ❌ **FAILED** - Test cannot proceed

---

## BUG DETAILS

### Bug #1: Dependencies Column Not Rendering (CRITICAL)

**Severity**: Critical
**Priority**: P0 (Blocker)
**Component**: AG Grid Asset Table
**File**: `/src/components/discovery/inventory/components/AssetTable/AGGridAssetTable.tsx`

#### Evidence

1. **Column Configuration Exists** (Lines 315-324):
```typescript
} else if (column === 'dependencies' || column === 'dependents') {
  // CC FIX: Custom multi-select editor for dependencies
  colDef.cellRenderer = DependencyCellRenderer;
  colDef.cellEditor = DependencyCellEditor;
  colDef.cellEditorPopup = true;
  colDef.cellEditorParams = {
    updateField,
  };
  colDef.width = 250;
}
```

2. **Column Selector Shows "Checked"**:
   - UI shows Dependencies toggle as enabled
   - Screenshot: `02_dependencies_column_missing.png`

3. **Console Logs Confirm Setup**:
```
✅ Column "dependencies" marked as editable with multi-select editor
```

4. **AG Grid State Includes Column**:
```json
{
  "colId": "dependencies",
  "width": 250,
  "hide": false,
  "pinned": null
}
```

5. **Column NEVER Renders**:
   - Visible columns: Name, Asset Type, Environment, Operating System, Location, Actions
   - Dependencies column expected between Business Criticality (#7) and Hostname (#9)
   - Actual: Column skipped entirely in rendering

#### Steps to Reproduce

1. Navigate to http://localhost:8081/discovery/inventory
2. Click on "Inventory" tab
3. Click "Columns" button
4. Observe "Dependencies" is checked/enabled
5. Close columns menu
6. Inspect table headers
7. **BUG**: Dependencies column not visible
8. Try toggling Dependencies off and on
9. **BUG**: Still not visible
10. Refresh page
11. **BUG**: Still not visible even after refresh

#### Expected Behavior

Dependencies column should:
- Appear in the table between Business Criticality and Hostname columns
- Display either "No dependencies" (gray text) or "🔗 X dependencies" (badge)
- Show "Double-click to view/edit" hint
- Be double-clickable to open the multi-select modal

#### Actual Behavior

Dependencies column:
- Does NOT render in the table at all
- Is completely invisible despite being configured
- Prevents any testing of the dependencies feature

#### Screenshots

1. `01_inventory_table_initial.png` - Initial state, no Dependencies column
2. `02_dependencies_column_missing.png` - After enabling, still missing
3. `03_table_scrolled_right_no_dependencies.png` - Scrolled right, column skipped

#### Browser Console Analysis

**No JavaScript errors reported**

Console shows column being configured twice (likely React strict mode):
```
✅ Column "dependencies" marked as editable with multi-select editor
✅ Column "dependencies" marked as editable with multi-select editor
```

But column never appears in DOM.

#### Root Cause Analysis

**Likely Issue**: The `selectedColumns` prop passed to `AGGridAssetTable` does NOT include `'dependencies'` even though the column selector UI shows it as checked.

**Evidence**:
- Line 259 in AGGridAssetTable.tsx: `selectedColumns.forEach((column) => {`
- If `'dependencies'` is not in the `selectedColumns` array, it won't be added to the column definitions
- The column selector UI state and the actual `selectedColumns` prop are out of sync

**Affected Code Path**:
1. User checks "Dependencies" in ColumnSelector component
2. `onToggleColumn('dependencies')` is called
3. Parent component should update `selectedColumns` state
4. AGGridAssetTable receives updated `selectedColumns` prop
5. **BUG HERE**: `selectedColumns` prop doesn't include `'dependencies'`
6. Column definition loop skips dependencies
7. AG Grid renders table without Dependencies column

#### Recommended Fix

**Option 1**: Check ColumnSelector state management
- File: `/src/components/discovery/inventory/components/AssetTable/ColumnSelector.tsx`
- Verify that toggling updates parent state correctly
- Check if there's a filter/allowlist preventing 'dependencies' from being added

**Option 2**: Check parent component's column state
- File: `/src/components/discovery/inventory/components/AssetTable/EnhancedAssetTable.tsx` or index.tsx
- Verify `selectedColumns` state is being updated when column is toggled
- Check if there's a hardcoded list that excludes dependencies

**Option 3**: Check for conditional rendering
- Search for code that might conditionally exclude dependencies column
- Check if there's a feature flag or permission check

#### Impact on Testing

**Cannot test ANY of the following**:
- ❌ Part 1: Initial State (Dependencies cell display)
- ❌ Part 2: Add Dependencies (Modal interaction)
- ❌ Part 3: Verify Persistence (Data saved to database)
- ❌ Part 4: Edit Dependencies (Update existing selections)
- ❌ Part 5: Remove All Dependencies (Clear functionality)

**All test scenarios BLOCKED** until this rendering bug is fixed.

---

## TEST COVERAGE

**Attempted**: 0%
**Completed**: 0%
**Blocked**: 100%

### Test Scenarios (ALL BLOCKED)

| Scenario | Status | Reason |
|----------|--------|--------|
| Initial State Display | ❌ BLOCKED | Column doesn't render |
| Add Dependencies | ❌ BLOCKED | Cannot access cell to double-click |
| Verify Persistence | ❌ BLOCKED | Cannot add data to test persistence |
| Edit Dependencies | ❌ BLOCKED | Column doesn't exist to edit |
| Remove All Dependencies | ❌ BLOCKED | Cannot access cell |
| Count Badge Display | ❌ BLOCKED | Column doesn't render |
| Modal Interaction | ❌ BLOCKED | Cannot open modal without column |
| Database Updates | ❌ BLOCKED | Cannot trigger PATCH without UI |

---

## RECOMMENDATIONS

### Immediate Action Required

1. **Fix the rendering bug** - This is a P0 blocker
2. **Investigate column state management** - Check why selectedColumns doesn't include 'dependencies'
3. **Add debug logging** - Log the selectedColumns array to see what's actually being passed
4. **Review recent changes** - Check if a recent commit broke column visibility
5. **Add integration test** - Ensure column visibility toggling works correctly

### Next Steps After Fix

1. Re-run this test suite with working Dependencies column
2. Verify all 5 test scenarios (Initial, Add, Persist, Edit, Remove)
3. Test count-based display (🔗 X dependencies badge)
4. Verify double-click interaction
5. Test modal functionality
6. Verify database persistence with PATCH requests
7. Confirm no console errors during interactions

---

## ENVIRONMENT

- **Frontend**: Next.js running in Docker on localhost:8081
- **Backend**: FastAPI running in Docker on localhost:8000
- **Database**: PostgreSQL on localhost:5433
- **Browser**: Playwright Chrome (headless mode)
- **OS**: macOS (Darwin 25.1.0)
- **Date**: November 6, 2025

---

## ADDITIONAL NOTES

### Related Files

- **Column Configuration**: `/src/components/discovery/inventory/components/AssetTable/AGGridAssetTable.tsx`
- **Dependencies Renderer**: `/src/components/discovery/inventory/components/AssetTable/DependencyCellRenderer.tsx`
- **Dependencies Editor**: `/src/components/discovery/inventory/components/AssetTable/DependencyCellEditor.tsx`
- **Column Selector**: `/src/components/discovery/inventory/components/AssetTable/ColumnSelector.tsx`

### Console Logs Captured

All console logs show normal operation except the Dependencies column never appears:
```
✅ Column "name" marked as editable with text editor
✅ Column "asset_type" marked as editable with dropdown editor
✅ Column "environment" marked as editable with dropdown editor
✅ Column "operating_system" marked as editable with text editor
✅ Column "location" marked as editable with text editor
✅ Column "business_criticality" marked as editable with dropdown editor
✅ Column "dependencies" marked as editable with multi-select editor  ← LOGGED BUT NOT RENDERED
✅ Column "hostname" marked as editable with text editor
... (more columns)
```

### AG Grid Column State (from localStorage)

The column IS in AG Grid's internal state but doesn't render:
```json
{
  "colId": "dependencies",
  "width": 250,
  "hide": false,  ← Should be visible!
  "pinned": null
}
```

This suggests the column gets added to AG Grid AFTER the initial render but then gets filtered out or hidden by React state management.

---

## CONCLUSION

**This is a critical blocker bug that prevents ANY testing of the dependencies feature.** The column is fully configured in the code with custom renderer and editor components, but fails to render in the UI due to a state management issue between the ColumnSelector component and the AGGridAssetTable component.

**The development team needs to:**
1. Debug why `selectedColumns` prop doesn't include `'dependencies'`
2. Fix the state synchronization between ColumnSelector and parent component
3. Ensure the column renders when toggled on
4. Re-test with QA after fix is deployed

**Test Status**: ❌ **FAILED - CRITICAL BUG - CANNOT PROCEED**
