# Discovery Flow Multi-Import Completion Fix

**Issue:** Discovery flow unable to complete after asset_inventory phase, blocking multi-CMDB import workflow
**Root Cause:** Legacy completion checks for phases removed in ADR-027
**Status:** Fixed
**Date:** October 15, 2025

---

## 🐛 Problem Statement

After ADR-027 (PR #585), Discovery flow was restructured to v3.0.0 with only 5 phases:
- data_import
- data_validation
- field_mapping
- data_cleansing
- asset_inventory

**However**, 3 locations still checked for removed phases (`dependency_analysis`, `tech_debt_assessment`):
1. `flow_phase_management.py` - completion check
2. `flow_state_validator.py` - phase dependencies
3. `flow_specs.py` - incomplete phases specification

This prevented flows from auto-completing after asset_inventory, blocking users from importing additional CMDB files.

---

## 🔍 Root Cause Analysis

### Discovery v3.0.0 Phase Scope (per ADR-027)
```python
# backend/app/services/flow_configs/discovery_flow_config.py
phases=[
    get_data_import_phase(),
    get_data_validation_phase(),
    get_field_mapping_phase(),
    get_data_cleansing_phase(),
    get_asset_inventory_phase(),  # ← LAST PHASE
]
```

### Legacy Checks Not Updated
```python
# BEFORE FIX:
required_phases = {
    # ... 4 phases ...
    "dependency_analysis": flow.dependency_analysis_completed,  # ← Ghost requirement!
}
# Result: all_phases_complete = FALSE (always!)
```

---

## 🔧 Technical Solution

### Change 1: Remove Legacy Phase from Completion Check
**File:** `backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py`
**Line:** 261 (removed)

**Before:**
```python
required_phases = {
    "data_import": flow.data_import_completed,
    "field_mapping": flow.field_mapping_completed,
    "data_cleansing": flow.data_cleansing_completed,
    "asset_inventory": flow.asset_inventory_completed,
    "dependency_analysis": flow.dependency_analysis_completed,  # ← REMOVED
}
```

**After:**
```python
required_phases = {
    "data_import": flow.data_import_completed,
    "field_mapping": flow.field_mapping_completed,
    "data_cleansing": flow.data_cleansing_completed,
    "asset_inventory": flow.asset_inventory_completed,
}
```

### Change 2: Update Phase Transition Validator
**File:** `backend/app/core/flow_state_validator.py`
**Line:** 62

**Before:**
```python
"completed": ["tech_debt_analysis"],
```

**After:**
```python
"completed": ["asset_inventory"],  # Per ADR-027: Discovery completes after asset_inventory
```

### Change 3: Update Incomplete Phases Specification
**File:** `backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py`
**Lines:** 49-50 (removed)

**Before:**
```python
return ~and_(
    DiscoveryFlow.data_import_completed is True,
    DiscoveryFlow.field_mapping_completed is True,
    DiscoveryFlow.data_cleansing_completed is True,
    DiscoveryFlow.asset_inventory_completed is True,
    DiscoveryFlow.dependency_analysis_completed is True,  # ← REMOVED
    DiscoveryFlow.tech_debt_assessment_completed is True,  # ← REMOVED
)
```

**After:**
```python
return ~and_(
    DiscoveryFlow.data_import_completed is True,
    DiscoveryFlow.field_mapping_completed is True,
    DiscoveryFlow.data_cleansing_completed is True,
    DiscoveryFlow.asset_inventory_completed is True,
)
```

---

## ✅ Expected Behavior After Fix

**Multi-Import Workflow:**
1. User imports CMDB file #1
2. Discovery flow runs through 5 phases
3. Flow auto-completes after `asset_inventory` ✅
4. User immediately starts new discovery flow for CMDB file #2 ✅
5. Repeat for additional files

**Database Updates:**
- `discovery_flows.status` = "completed"
- `discovery_flows.progress_percentage` = 100.0
- `discovery_flows.completed_at` = timestamp
- `crewai_flow_state_extensions.flow_status` = "completed"

---

## 🧪 Testing Checklist

- [ ] Create discovery flow, complete through asset_inventory
- [ ] Verify flow status = "completed"
- [ ] Verify progress = 100%
- [ ] Verify can start new discovery flow immediately
- [ ] Verify legacy `dependency_analysis_completed` remains FALSE
- [ ] Verify no regression in existing flows
- [ ] Check UI shows completion correctly

---

## 📊 Impact Analysis

**Files Modified:** 3
**Lines Changed:** 6 lines removed/updated
**Time to Implement:** 30 minutes
**Risk Level:** Low (removing legacy checks)

**Backward Compatibility:**
- ✅ Database columns retained
- ✅ Old flows unaffected
- ✅ Assessment flow still has these phases
- ✅ No breaking changes

---

## 🔗 Related Work

**Prerequisite:**
- PR #585 (ADR-027): Universal FlowTypeConfig Migration

**References:**
- ADR-027: Universal flow-type-config pattern
- Migration 091: Phase deprecation comments
- Discovery v3.0.0: 5-phase configuration

---

**Branch:** `fix/discovery-flow-multi-import-completion`
**Related Issue:** Multi-CMDB import workflow requirement
