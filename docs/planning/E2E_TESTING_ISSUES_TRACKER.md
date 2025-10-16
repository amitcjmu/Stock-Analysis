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
**Status**: 🔴 OPEN
**Severity**: CRITICAL
**Component**: Phase Routing Architecture

**Problem**:
- Backend uses phase names that don't correspond to frontend routes
- Flow progresses through phases that have no UI pages
- **MAJOR ARCHITECTURAL MISMATCH** between backend phase flow and frontend route structure

**Backend Phases** (from `assessment_flow_config.py`):
1. `readiness_assessment` (aliased: `initialization`, `architecture_minimums`)
2. `complexity_analysis` ❌ **NO ROUTE**
3. `dependency_analysis` ❌ **NO ROUTE**
4. `tech_debt_assessment` ✅ Maps to `/tech-debt`
5. `risk_assessment` ❌ **NO ROUTE**
6. `recommendation_generation` ✅ Possibly maps to `/summary` or `/app-on-page`

**Frontend Routes** (from `src/pages/assessment/[flowId]/`):
1. `/architecture` ❌ **NO BACKEND PHASE**
2. `/tech-debt` ✅ Maps to `tech_debt_assessment`
3. `/sixr-review` ❌ **NO BACKEND PHASE**
4. `/app-on-page` ❌ **NO BACKEND PHASE**
5. `/summary` ✅ Possibly maps to `recommendation_generation`

**Current State**:
- Backend progressed to `complexity_analysis` (phase 2 of 6)
- No frontend route exists for this phase
- Cannot test phases 2, 3, 5 through UI (no routes)
- Architecture standards page exists but backend has no corresponding phase

**Impact**:
- **BLOCKS ALL TESTING** of assessment flow phases
- Users cannot navigate through flow after initial creation
- Backend and frontend were developed with different phase models
- Requires either:
  1. Add missing frontend routes for backend phases, OR
  2. Change backend phases to match frontend routes, OR
  3. Add phase-to-route mapping layer

**Files to Review**:
- `backend/app/services/flow_configs/assessment_flow_config.py:61-68` - Backend phases
- `backend/app/services/flow_configs/phase_aliases.py:29-41` - Phase aliases
- `src/pages/assessment/[flowId]/*.tsx` - Frontend routes

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
**Critical Issues Fixed**: 1
**Critical Issues Open**: 2 (Issue #2: Data Loading, Issue #4: Phase Routing)
**Low Priority Issues**: 1 (Issue #3: Log Noise)
**Test Phases Completed**: 0 / 5 (0%)
**Overall Progress**: **BLOCKED** - Cannot test any phases due to frontend data loading failure and phase routing mismatch

---

## Next Actions

### ⚠️ CRITICAL BLOCKERS - MUST FIX BEFORE TESTING CAN CONTINUE

**Both critical issues MUST be resolved to enable ANY assessment flow testing:**

1. **Issue #2 (Frontend Data Loading)** - HIGHEST PRIORITY
   - **Impact**: Zero application data displayed on ANY page
   - **Investigation**: Check `useAssessmentFlow` hook and API endpoint
   - **Recommendation**: Use `nextjs-ui-architect` agent to diagnose and fix

2. **Issue #4 (Phase Routing Mismatch)** - HIGH PRIORITY
   - **Impact**: Cannot navigate to 3 out of 6 backend phases (no routes exist)
   - **Investigation**: Align backend phases with frontend routes OR create missing routes
   - **Recommendation**: Use `python-crewai-fastapi-expert` agent for backend changes OR `nextjs-ui-architect` for frontend routes

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
