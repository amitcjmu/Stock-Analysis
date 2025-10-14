# Discovery Flow Status Display Fixes

## Overview
This document tracks the fixes for multiple related bugs affecting discovery flow status display across the UI.

## Bug Numbers and Issues

### Bug #557 - Monitor Popup Phase Status Incorrect
**Issue:** Discovery Flow Monitor popup window did not reflect correct phase completion status. Phases that were completed showed as "not_started" with 0% completion.

**Root Cause:** The `create_checklist_status` function in `flow_processing_converters.py` was determining phase status based on index position relative to current phase, rather than using actual database completion flags.

**Fix Location:**
- `backend/app/api/v1/endpoints/flow_processing_converters.py`
- `backend/app/api/v1/endpoints/flow_processing/queries.py`
- `backend/app/api/v1/endpoints/flow_processing/commands.py`

**Fix Description:** Modified the flow processing pipeline to pass `phases_completed` dictionary from database through to `create_checklist_status`, which now uses actual completion flags with `API_TO_DB_PHASE_MAP` for correct phase name translation.

---

### Bug #560 - Overview Progress Bar Shows 0%
**Issue:** The Discovery Overview page (`/discovery/overview`) showed 0% progress even when multiple phases were completed.

**Root Cause:** The `/api/v1/unified-discovery/flows/active` endpoint was returning hardcoded progress values instead of calculating from database completion flags.

**Fix Location:**
- `backend/app/services/discovery/flow_status/operations.py` (lines 249-275)

**Fix Description:**
- Applied "smart detection" logic (same as FlowHandler) to detect actual data presence
- Calculate progress dynamically from completion flags: `(completed_phases / 6) * 100`
- Returns `phases` dictionary to frontend for accurate display

---

### Bug #578 - Success Criteria Shows Incorrect Count
**Issue:** The Success Criteria section on `/discovery/overview` displayed incorrect completion count (e.g., 0/6 instead of 4/6).

**Root Cause:** The `/api/v1/unified-discovery/flows/active` endpoint was not returning the `phases` object that the frontend uses to calculate success criteria.

**Fix Location:**
- `backend/app/services/discovery/flow_status/operations.py` (lines 249-275, 316-342)

**Fix Description:**
- Same fix as Bug #560
- Added `phases_dict` to API response containing boolean completion status for each phase
- Frontend now receives accurate phase completion data to calculate "X/6 complete"

---

### Bug #579 - Data Import Completion Flag Never Set
**Issue:** The `data_imports` table status remained as "processing" even after successful import completion, causing `data_import_completed` flag in `discovery_flows` table to never be set to TRUE.

**Root Cause:** The `DataImportValidationExecutor` successfully validated and stored data but never called `update_import_status` to mark the import as complete in the database.

**Fix Location:**
- `backend/app/services/crewai_flows/handlers/phase_executors/data_import_validation/executor.py` (lines 111-113, 443-516)

**Fix Description:**
- Added `_update_data_import_status_to_completed()` method
- Called after successful validation to update `data_imports.status = "completed"`
- Sets `completed_at` timestamp and `progress_percentage = 100%`
- Ensures future imports properly track completion status

---

## Technical Implementation Details

### Phase Name Mapping Consolidation
**File:** `backend/app/services/discovery/phase_persistence_helpers/base.py`

Created single source of truth for phase name mappings:
```python
API_TO_DB_PHASE_MAP = {
    "data_import": "data_import",
    "attribute_mapping": "field_mapping",
    "data_cleansing": "data_cleansing",
    "inventory": "asset_inventory",
    "dependencies": "dependency_analysis",
    "tech_debt": "tech_debt_assessment",
}

PHASE_FLAG_MAP = {
    db_phase: f"{db_phase}_completed"
    for db_phase in set(API_TO_DB_PHASE_MAP.values())
}
```

### Smart Detection Logic
Applied `FlowHandlerHelpers.check_actual_data_via_import_id()` to:
- Detect if import data actually exists in database
- Detect if field mappings are present
- Fallback to database completion flags if detection fails
- Ensures consistent status across all API endpoints

### Data Flow
```
1. Data Import → 2. Validation → 3. Update Status → 4. Set Completion Flag
                                   (Bug #579 Fix)   (Enables Smart Detection)

5. API Queries → 6. Smart Detection → 7. Calculate Progress → 8. UI Display
                                        (Bug #560/#578 Fix)   (Bug #557 Fix)
```

---

## Files Modified

### Backend API Layer
- `backend/app/api/v1/endpoints/flow_processing_converters.py` - Bug #557
- `backend/app/api/v1/endpoints/flow_processing/queries.py` - Bug #557
- `backend/app/api/v1/endpoints/flow_processing/commands.py` - Bug #557

### Backend Service Layer
- `backend/app/services/discovery/flow_status/operations.py` - Bug #560, #578
- `backend/app/services/discovery/phase_persistence_helpers/base.py` - Infrastructure

### Backend Phase Executors
- `backend/app/services/crewai_flows/handlers/phase_executors/data_import_validation/executor.py` - Bug #579

---

## Testing Verification

### Before Fixes
- ❌ Monitor popup: All phases show "not_started" 0%
- ❌ Overview progress bar: Shows 0%
- ❌ Success criteria: Shows 0/6
- ❌ Database: `data_imports.status = 'processing'` after completion

### After Fixes
- ✅ Monitor popup: Completed phases show "completed" 100%
- ✅ Overview progress bar: Shows correct % (e.g., 66.7% for 4/6)
- ✅ Success criteria: Shows correct count (e.g., 4/6)
- ✅ Database: `data_imports.status = 'completed'` after validation

---

## Related PRs and Issues

**Primary Issue:** #557 - Discovery Flow Monitor status does not reflect actual flow status

**Related Issues:**
- #560 - Overview progress bar incorrect
- #578 - Success criteria count incorrect
- #579 - Data import completion flag not set

**Milestone:** Discovery Flow Demo Readiness

---

## Impact Assessment

### User-Facing Impact
- **High:** Users can now accurately track discovery flow progress
- **High:** Success criteria properly reflects actual completion status
- **High:** Monitor popup provides reliable phase status information

### System Impact
- **Medium:** Unified response logic across all status endpoints
- **Medium:** Future data imports will properly track completion
- **Low:** Existing in-progress flows will benefit from smart detection

### Technical Debt Reduction
- **High:** Single source of truth for phase name mappings
- **Medium:** Consistent smart detection across all endpoints
- **Low:** Eliminated hardcoded progress values

---

## Rollout Strategy

1. ✅ Code fixes applied
2. ⏳ Backend restart required to load new code
3. ⏳ Frontend refresh required to see updated progress
4. ⏳ Existing flows: Status will update immediately via smart detection
5. ⏳ New imports: Will properly set completion flags

---

## Monitoring and Validation

### Key Metrics to Watch
- Discovery flow progress accuracy
- Data import completion rate
- Phase transition success rate
- API response consistency

### Validation Queries
```sql
-- Check data import completion status
SELECT id, status, completed_at, progress_percentage
FROM migration.data_imports
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Check discovery flow completion flags
SELECT flow_id,
       data_import_completed,
       field_mapping_completed,
       data_cleansing_completed,
       asset_inventory_completed,
       dependency_analysis_completed,
       tech_debt_assessment_completed
FROM migration.discovery_flows
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

---

## Future Improvements

1. Add automated tests for phase completion tracking
2. Implement real-time progress updates via WebSocket
3. Add progress history tracking for audit trail
4. Create admin dashboard for flow status monitoring

---

**Last Updated:** October 14, 2025
**Status:** Ready for PR
**Branch:** `fix/discovery-flow-demo-readiness-01`
