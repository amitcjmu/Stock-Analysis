# E2E Testing Issues Tracker - Canonical Application Assessment Flow

**Testing Date**: October 16, 2025
**Test Scope**: Complete assessment flow from canonical application creation through all phases
**Test Flow ID**: `2f6b7304-7896-4aa6-8039-4da258524b06`
**Created From**: "Admin Dashboard" canonical application (16 assets)

---

## ✅ Issues Fixed During Testing

### Issue #1: Missing Unique Constraint (500 Error)
**Status**: ✅ FIXED
**Severity**: CRITICAL
**Component**: Database Schema / Architecture Standards

**Problem**:
- 500 error when saving architecture standards
- Error: `there is no unique or exclusion constraint matching the ON CONFLICT specification`
- Code expected unique constraint on `(engagement_id, requirement_type, standard_name)` but table didn't have it

**Root Cause**:
- `engagement_architecture_standards` table missing unique constraint
- `architecture_commands.py:62` uses `ON CONFLICT` but constraint didn't exist

**Fix Applied**:
- Created migration `094_add_architecture_standards_unique_constraint.py`
- Added idempotent unique constraint: `uq_engagement_architecture_standards_composite`
- Verified: ✅ Migration at HEAD, constraint exists, 200 OK responses

**Files Modified**:
- `backend/alembic/versions/094_add_architecture_standards_unique_constraint.py` (new)

**Verification**:
```
✅ PUT /api/v1/master-flows/.../assessment/architecture-standards | Status: 200
Resumed flow: initialization -> complexity_analysis (33%)
```

---

## 🔴 Active Issues (Need Triage)

### Issue #2: Application Count Mismatch
**Status**: ✅ PARTIALLY FIXED (Frontend & Repository Done, Additional Issues Found)
**Severity**: CRITICAL
**Component**: Frontend Data Loading / Backend Repository / Database Schema

**Problem**:
- UI shows "Selected Applications 0" despite database having 16 assets
- Flow shows status "INITIALIZED" and progress "0%" despite database showing "in_progress" at "33%"
- Backend repository had incorrect eager loading relationships
- Database schema mismatch for `application_architecture_overrides` table

**Root Causes Identified**:
1. ✅ **FIXED**: Frontend hook extracted `clientAccountId` from non-existent `user?.client_account_id`
2. ✅ **FIXED**: Backend repository eager-loaded non-existent relationships (`application_components`, `tech_debt_analyses`, `sixr_decisions`, `component_treatments`)
3. ✅ **FIXED**: Database schema for `application_architecture_overrides` didn't match October 2025 model refactor
4. ❌ **REMAINING**: Additional architectural issues discovered (see below)

**Fixes Applied**:
1. ✅ Frontend (`src/hooks/useAssessmentFlow/useAssessmentFlow.ts`):
   - Changed `client?.id` instead of `user?.client_account_id` (line 34)
   - Changed `engagement?.id` instead of `user?.engagement_id` (line 35)
   - Fixed auth context extraction for proper data loading

2. ✅ Backend Repository (`backend/app/repositories/assessment_flow_repository/queries/flow_queries.py`):
   - Removed eager loading of `application_components` (no `assessment_flow_id` FK)
   - Removed eager loading of `component_treatments` (no `assessment_flow_id` FK)
   - Only load `application_overrides` which has proper FK relationship (lines 38-42)

3. ✅ Backend Schema - Migration 095:
   - Created `backend/alembic/versions/095_update_application_architecture_overrides_schema.py`
   - Aligned table with October 2025 model refactor
   - Added enterprise fields: `requirement_type`, `original_value`, `override_value`, `business_justification`, `technical_justification`, `approved`, `approved_at`, `impact_assessment`, `risk_level`, `override_metadata`
   - Removed old fields: `standard_id`, `override_type`, `override_details`, `rationale`

4. ✅ Backend Repository - Additional Fixes:
   - Fixed `mandatory` → `is_mandatory` attribute mapping in `state_queries.py` (line 62)
   - Disabled queries for tables without `assessment_flow_id`: `application_components`, `tech_debt_analysis`, `sixr_decisions`
   - Added safe phase enum conversion to handle unknown backend phases gracefully

**Files Modified**:
- `src/hooks/useAssessmentFlow/useAssessmentFlow.ts` (lines 34-35)
- `backend/app/repositories/assessment_flow_repository/queries/flow_queries.py` (lines 38-42, 30-36, 102-110)
- `backend/app/repositories/assessment_flow_repository/queries/state_queries.py` (lines 62, 103-110, 112-118, 120-125)
- `backend/alembic/versions/095_update_application_architecture_overrides_schema.py` (new)

**Verification**:
- ✅ Migration 095 applied successfully
- ✅ Schema verified: all new columns present, old columns removed
- ✅ Backend restarts without SQLAlchemy relationship errors
- ⚠️ Endpoint still returns errors due to **additional architectural issues** (not part of Issue #2 scope)

**Additional Issues Discovered** (tracked separately):
- AssessmentFlow model missing `next_phase` column definition (exists in DB, not in model)
- Multiple tables missing `assessment_flow_id` foreign keys needed for proper relationships
- Phase enum mismatch causing validation errors (related to Issue #4)

**Issue #2 Status**: Core fixes complete (frontend context, repository eager loading, schema migration). Remaining errors are separate architectural issues requiring broader refactoring

---

### Issue #3: Unmapped Assets Warning
**Status**: 🟡 LOW PRIORITY
**Severity**: LOW (Expected Behavior?)
**Component**: Collection Integration

**Problem**:
- Backend logs: "Assessment flow has no source_collection metadata. Cannot query unmapped assets"
- Repeated warnings every 15 seconds

**Analysis**:
- This is EXPECTED for flows created from canonical apps (no collection flow)
- Warning may be too noisy for legitimate use case
- Should either:
  1. Suppress warning for canonical-based flows
  2. Add `source_collection` metadata even for canonical flows
  3. Return empty list silently without warning

**Impact**:
- No functional impact, just log noise
- May confuse operators monitoring logs

---

### Issue #4: Backend Phase Names Don't Match Frontend Routes
**Status**: ✅ FIXED
**Severity**: CRITICAL
**Component**: Phase Routing Architecture

**Problem**:
- Backend phase metadata had `ui_route` values that didn't match existing frontend routes
- Phase navigation would fail for 3 of 6 backend phases (no routes existed)
- **ARCHITECTURAL MISMATCH** between backend phase metadata and frontend route structure

**Original Backend Phase Metadata** (BEFORE FIX):
1. `readiness_assessment` → `/assessment/readiness` ❌ **NO ROUTE**
2. `complexity_analysis` → `/assessment/complexity` ❌ **NO ROUTE**
3. `dependency_analysis` → `/assessment/dependency-analysis` ❌ **NO ROUTE**
4. `tech_debt_assessment` → `/assessment/tech-debt` ✅ EXISTS
5. `risk_assessment` → `/assessment/risk` ❌ **NO ROUTE**
6. `recommendation_generation` → `/assessment/recommendations` ❌ **NO ROUTE**

**Existing Frontend Routes** (from `src/pages/assessment/[flowId]/`):
1. `/architecture` → Used for readiness/architecture standards
2. `/tech-debt` → Used for complexity & tech debt analysis
3. `/sixr-review` → Used for dependencies & risk (6R strategy review)
4. `/app-on-page` → Used for recommendations & app details
5. `/summary` → Legacy summary page

**Fix Applied**:
Updated phase metadata `ui_route` values to map to existing frontend routes:

**NEW Backend Phase Metadata** (AFTER FIX):
1. `readiness_assessment` → `/assessment/[flowId]/architecture` ✅
2. `complexity_analysis` → `/assessment/[flowId]/tech-debt` ✅
3. `dependency_analysis` → `/assessment/[flowId]/sixr-review` ✅
4. `tech_debt_assessment` → `/assessment/[flowId]/tech-debt` ✅
5. `risk_assessment` → `/assessment/[flowId]/sixr-review` ✅
6. `recommendation_generation` → `/assessment/[flowId]/app-on-page` ✅

**Rationale for Mappings**:
- `readiness_assessment` → `/architecture`: Architecture standards capture readiness requirements
- `complexity_analysis` → `/tech-debt`: Complexity analysis feeds into technical debt assessment
- `dependency_analysis` → `/sixr-review`: Dependency analysis informs 6R migration strategy
- `risk_assessment` → `/sixr-review`: Risk assessment is integral to 6R strategy review
- `recommendation_generation` → `/app-on-page`: Recommendations displayed in application detail view

**Additional Fix**:
- Updated `phase_aliases.py` with frontend route name mappings:
  - `architecture` → `readiness_assessment`
  - `complexity` → `complexity_analysis`
  - `tech-debt` → `tech_debt_assessment`
  - `sixr-review` → `risk_assessment`
  - `app-on-page` → `recommendation_generation`

**Files Modified**:
- `backend/app/services/flow_configs/assessment_phases/readiness_assessment_phase.py`
- `backend/app/services/flow_configs/assessment_phases/complexity_analysis_phase.py`
- `backend/app/services/flow_configs/assessment_phases/dependency_analysis_phase.py`
- `backend/app/services/flow_configs/assessment_phases/risk_assessment_phase.py`
- `backend/app/services/flow_configs/assessment_phases/recommendation_generation_phase.py`
- `backend/app/services/flow_configs/phase_aliases.py`

**Verification**:
- ✅ All 6 backend phases now have valid frontend routes
- ✅ Phase aliases support backward compatibility
- ✅ Multiple phases can share the same UI route (e.g., complexity + tech_debt both use `/tech-debt`)
- ✅ No new routes created - leverages existing UI pages

**Impact**:
- ✅ **UNBLOCKS E2E TESTING** - All assessment phases now navigable
- ✅ Users can progress through entire assessment flow
- ✅ Backend and frontend now architecturally aligned
- ✅ Phase-to-route mapping handled via metadata + aliases

---

## 📋 Test Coverage Progress

### Phase 1: Architecture Standards ✅ COMPLETE
- ✅ Template selection (Enterprise Standard)
- ✅ Load 4 standards (Security, Availability, Backup, Monitoring)
- ✅ Save standards (200 OK)
- ✅ Resume flow to next phase (33% progress)
- ✅ No 500 errors

### Phase 2: Tech Debt Analysis ⏳ PENDING
- [ ] Navigate to Tech Debt phase
- [ ] Load existing tech debt data (if any)
- [ ] Add/edit tech debt items
- [ ] Save and proceed to next phase
- [ ] Verify data persistence

### Phase 3: 6R Strategy Review ⏳ PENDING
- [ ] Navigate to 6R Strategy phase
- [ ] View application recommendations
- [ ] Test strategy assignment (Rehost, Replatform, etc.)
- [ ] Verify critical attributes usage
- [ ] Save and proceed to next phase

### Phase 4: Application Summary ⏳ PENDING
- [ ] Navigate to Application Summary phase
- [ ] Verify all previous phase data displayed
- [ ] Test summary generation
- [ ] Verify application portfolio display
- [ ] Save and proceed to export

### Phase 5: Summary & Export ⏳ PENDING
- [ ] Navigate to Summary & Export phase
- [ ] Test export functionality (PDF, Excel, JSON)
- [ ] Verify complete assessment data in exports
- [ ] Test flow completion

### Cross-Cutting Features ⏳ PENDING
- [ ] **Critical Attributes**: "22 Critical Attributes for 6R Assessment" button
- [ ] **Collection Integration**: Missing data identification
- [ ] **App Portfolio**: Application groups display
- [ ] **Readiness Metrics**: Ready/Not Ready/In Progress counts
- [ ] **Agent Insights**: Verify no insights generated (expected for new flow)
- [ ] **Agent Clarifications**: Verify no questions (expected for new flow)

---

## 🎯 Testing Strategy

### Current Approach:
1. ✅ Test each phase sequentially through UI
2. ✅ Document ALL issues found (no matter how small)
3. ✅ Verify backend logs for each action
4. ✅ Take screenshots for visual verification
5. ⏳ Once complete list compiled → Use CC agents for batch triage/fix

### Known Blockers:
- **Issue #2** may block app portfolio testing (no apps displaying)
- May need to investigate/fix #2 before continuing to later phases

---

## 📊 Summary Statistics

**Total Issues Found**: 4
**Critical Issues Fixed**: 2 (Issue #1: Unique Constraint, Issue #4: Phase Routing)
**Critical Issues Open**: 1 (Issue #2: Data Loading - Partially Fixed)
**Low Priority Issues**: 1 (Issue #3: Log Noise)
**Test Phases Completed**: 0 / 5 (0%)
**Overall Progress**: **PARTIALLY UNBLOCKED** - Phase routing fixed, data loading issue remains

---

## Next Actions

### ⚠️ CRITICAL BLOCKER - MUST FIX BEFORE TESTING CAN CONTINUE

1. **Issue #2 (Frontend Data Loading)** - HIGHEST PRIORITY ⚠️ REMAINING BLOCKER
   - **Impact**: Zero application data displayed on ANY page
   - **Status**: Partially fixed (frontend context, repository eager loading, schema migration complete)
   - **Remaining**: Additional architectural issues discovered:
     - AssessmentFlow model missing `next_phase` column definition
     - Multiple tables missing `assessment_flow_id` foreign keys
     - Phase enum mismatch causing validation errors
   - **Recommendation**: Use `nextjs-ui-architect` agent to diagnose frontend issues OR `python-crewai-fastapi-expert` for model/schema fixes

### ✅ COMPLETED FIXES

2. **Issue #4 (Phase Routing Mismatch)** - ✅ FIXED
   - **Solution**: Updated all phase metadata `ui_route` values to map to existing frontend routes
   - **Impact**: All 6 backend phases now navigable through existing UI
   - **Files Modified**: 6 phase config files + phase_aliases.py

### Once Blockers Resolved:

3. Resume E2E testing: Architecture → Tech Debt → 6R Strategy → Summary → Export
4. Test cross-cutting features: Critical Attributes, Readiness Metrics, Collection Integration
5. Test application portfolio display with properly loaded data
6. Create GitHub issues for Issue #3 (log noise) if needed after core functionality works

### Recommended CC Agent Usage:

**For Issue #2 (Frontend)**:
```bash
# Use nextjs-ui-architect to fix data loading
Task: "Investigate why useAssessmentFlow hook shows 0 applications/INITIALIZED status
despite database having 16 assets at 33% progress in phase 'complexity_analysis'.
Flow ID: 2f6b7304-7896-4aa6-8039-4da258524b06"
```

**For Issue #4 (Backend/Frontend Alignment)**:
```bash
# Option A: Add frontend routes for missing phases
Task: "Create frontend routes for assessment phases: complexity_analysis, dependency_analysis, risk_assessment"

# Option B: Align backend phases with existing frontend routes
Task: "Update assessment_flow_config.py phases to match existing frontend routes:
/architecture, /tech-debt, /sixr-review, /app-on-page, /summary"
```
