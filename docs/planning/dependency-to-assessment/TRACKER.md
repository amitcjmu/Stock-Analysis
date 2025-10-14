### Dependency Mapping → Assessment: Implementation Tracker

**Status**: PIVOT TO ROLLBACK + REFACTOR (2025-10-13)

Status legend: ☐ pending · ▶ in_progress · ✅ completed · ✖ cancelled

---

### Milestones

- M1: Enum Unification (CRITICAL) - ✅ COMPLETED
- M2: Phase + DB Schema - ✖ CANCELLED (Redundant with existing schema)
- M3: Backend Service + Endpoints - ✖ CANCELLED (Will use existing deduplication service)
- M4: Frontend Page + Routing - ✖ CANCELLED (Will use existing ApplicationDeduplicationManager)
- M5: Tests + E2E - ☐ PENDING (Will test rollback + refactor)
- **M6: Rollback Redundant Code - ▶ IN_PROGRESS**
- **M7: Refactor Using Existing Infrastructure - ☐ PENDING**

---

### Original Task Board (CANCELLED)

| ID | Task | Owner | Status | Notes |
|---|---|---|---|---|
| T-01 | Unify AssessmentPhase enums across backend/frontend | Backend | ✅ completed | **KEEP** - Good work, single source of truth established |
| T-02 | Add ASSET_APPLICATION_RESOLUTION to canonical enum | Backend | ✖ cancelled | Will REMOVE this phase - not needed |
| T-03 | Alembic migration: asset_application_mappings | Backend | ✖ cancelled | Redundant - `collection_flow_applications` already exists |
| T-04 | Implement AssetResolutionService | Backend | ✖ cancelled | Redundant - `ApplicationDeduplicationService` already exists |
| T-05 | Add API endpoints for resolution list/map/complete | Backend | ✖ cancelled | Will replace with 2 small collection endpoints |
| T-06 | Update master flow applications to use mappings | Backend | ✖ cancelled | Will adjust to use existing `collection_flow_applications` |
| T-07 | Frontend: add phase type, routes, progress | Frontend | ✖ cancelled | Will remove phase additions |
| T-08 | Build `/assessment/[flowId]/asset-resolution` page | Frontend | ✖ cancelled | Redundant - `ApplicationDeduplicationManager` already exists |
| T-09 | Update `useAssessmentFlow` gating + API | Frontend | ✖ cancelled | Will use banner instead of phase |
| T-10 | Banner on 6R pages showing asset→app mapping | Frontend | ✖ cancelled | Will build simpler banner wrapper |
| T-11 | Backend unit + API tests | QA | ✖ cancelled | Will write new tests for refactored endpoints |
| T-12 | Frontend integration + E2E path | QA | ✖ cancelled | Will test rollback + refactor workflow |
| T-13 | Docs & CHANGELOG update | PM | ✖ cancelled | Will document rollback + refactor instead |

---

### Rollback Task Board (NEW)

| ID | Task | Owner | Status | Start | ETA | Notes |
|---|---|---|---|---|---|---|
| R-01 | Roll back migration 091 (alembic downgrade -1) | Backend | ☐ pending | | | Removes asset_application_mappings table |
| R-02 | Delete AssetResolutionService (320 lines) | Backend | ☐ pending | | | File: app/services/assessment_flow_service/core/asset_resolution_service.py |
| R-03 | Delete asset resolution API endpoints (407 lines) | Backend | ☐ pending | | | File: app/api/v1/endpoints/assessment_flow/asset_resolution.py |
| R-04 | Delete frontend asset resolution page (400 lines) | Frontend | ☐ pending | | | File: src/pages/assessment/[flowId]/asset-resolution.tsx |
| R-05 | Remove ASSET_APPLICATION_RESOLUTION from enum | Backend | ☐ pending | | | File: app/models/assessment_flow_state.py |
| R-06 | Remove phase from assessment_flow_utils.py | Backend | ☐ pending | | | Remove from sequence and progress map |
| R-07 | Remove asset_resolution router import | Backend | ☐ pending | | | File: app/api/v1/endpoints/assessment_flow_router.py |
| R-08 | Remove ASSET_RESOLUTION API tag | Backend | ☐ pending | | | File: app/api/v1/api_tags.py |
| R-09 | Remove phase from frontend types | Frontend | ☐ pending | | | File: src/hooks/useAssessmentFlow/types.ts |
| R-10 | Remove 3 asset resolution API methods | Frontend | ☐ pending | | | File: src/hooks/useAssessmentFlow/api.ts |
| R-11 | Remove phase handling from useAssessmentFlow hook | Frontend | ☐ pending | | | File: src/hooks/useAssessmentFlow/useAssessmentFlow.ts |
| R-12 | Remove phase route from flowRoutes | Frontend | ☐ pending | | | File: src/config/flowRoutes.ts |
| R-13 | Remove phase config from AssessmentFlowLayout | Frontend | ☐ pending | | | File: src/components/assessment/AssessmentFlowLayout.tsx |
| R-14 | Verify database rollback successful | Backend | ☐ pending | | | Query: `\dt migration.asset_application_mappings` |
| R-15 | Verify frontend build passes after removals | Frontend | ☐ pending | | | Run: `npm run build` |

---

### Refactor Task Board (NEW - Extend Existing)

| ID | Task | Owner | Status | Start | ETA | Notes |
|---|---|---|---|---|---|---|
| F-01 | Create collection_post_completion.py endpoint file | Backend | ☐ pending | | 1h | New file with 2 endpoints |
| F-02 | Add GET /{flow_id}/unmapped-assets endpoint | Backend | ☐ pending | | 1.5h | Query collection_flow_applications where canonical_application_id IS NULL |
| F-03 | Add POST /{flow_id}/link-asset-to-canonical endpoint | Backend | ☐ pending | | 1.5h | Wraps canonical_operations.create_collection_flow_link() |
| F-04 | Update assessment apps derivation logic | Backend | ☐ pending | | 2h | File: app/api/v1/master_flows/master_flows_assessment.py |
| F-05 | Add "pending_resolution" status response | Backend | ☐ pending | | 1h | Return structured hint when unmapped assets exist |
| F-06 | Add tenant scoping validation to all queries | Backend | ☐ pending | | 1h | Ensure client_account_id + engagement_id on all queries |
| F-07 | Create AssetResolutionBanner component | Frontend | ☐ pending | | 2h | New file: src/components/assessment/AssetResolutionBanner.tsx |
| F-08 | Integrate ApplicationDeduplicationManager in modal | Frontend | ☐ pending | | 1.5h | Reuse existing component with new wrapper |
| F-09 | Add banner to AssessmentFlowLayout | Frontend | ☐ pending | | 0.5h | Import and render banner conditionally |
| F-10 | Add collection API client methods | Frontend | ☐ pending | | 1h | Add getUnmappedAssets, linkAssetToCanonical to API client |
| F-11 | Update assessment apps query logic | Frontend | ☐ pending | | 1h | Handle "pending_resolution" response |
| F-12 | Write backend integration tests | QA | ☐ pending | | 2h | Test unmapped query, link creation, assessment derivation |
| F-13 | Write frontend E2E tests | QA | ☐ pending | | 2h | Test banner workflow with Playwright |
| F-14 | Manual E2E testing | QA | ☐ pending | | 1h | Collection → Banner → Resolve → Assessment |
| F-15 | Update planning documentation | PM | ☐ pending | | 0.5h | Mark rollback complete, document refactor approach |
| F-16 | Create Serena memory with lessons learned | PM | ☐ pending | | 0.5h | Document redundancy discovery and prevention |

---

### Detailed Checklists

#### M1: Enum Unification ✅ COMPLETED (KEEP THIS)

- [x] Remove duplicate enum in `backend/app/models/assessment_flow/enums_and_exceptions.py`
- [x] Update imports to canonical enum
- [x] Align `backend/app/api/v1/endpoints/assessment_flow_utils.py` phase sequence
- [x] Update `src/hooks/useAssessmentFlow/types.ts` phases
- [x] Frontend build passes; assessment navigation works

#### M6: Rollback Redundant Code ▶ IN_PROGRESS

**Database**:
- [ ] Run `alembic downgrade -1` to remove migration 091
- [ ] Verify `asset_application_mappings` table no longer exists
- [ ] Confirm `collection_flow_applications` table intact

**Backend Files to Delete**:
- [ ] `backend/alembic/versions/091_add_asset_application_mappings.py`
- [ ] `backend/app/services/assessment_flow_service/core/asset_resolution_service.py`
- [ ] `backend/app/api/v1/endpoints/assessment_flow/asset_resolution.py`

**Backend Files to Modify** (remove phase, keep enum unification):
- [ ] `backend/app/models/assessment_flow_state.py` - Remove ASSET_APPLICATION_RESOLUTION
- [ ] `backend/app/api/v1/endpoints/assessment_flow_utils.py` - Remove from sequence/progress
- [ ] `backend/app/api/v1/endpoints/assessment_flow_router.py` - Remove router import
- [ ] `backend/app/api/v1/api_tags.py` - Remove ASSET_RESOLUTION tag

**Frontend Files to Delete**:
- [ ] `src/pages/assessment/[flowId]/asset-resolution.tsx`

**Frontend Files to Modify** (remove phase):
- [ ] `src/hooks/useAssessmentFlow/types.ts` - Remove phase from union type
- [ ] `src/hooks/useAssessmentFlow/api.ts` - Remove 3 API methods (getAssetResolutionStatus, createAssetMapping, completeAssetResolution)
- [ ] `src/hooks/useAssessmentFlow/useAssessmentFlow.ts` - Remove phase handling
- [ ] `src/config/flowRoutes.ts` - Remove phase route
- [ ] `src/components/assessment/AssessmentFlowLayout.tsx` - Remove phase config

**Verification**:
- [ ] `docker exec migration_postgres psql -U postgres -d migration_db -c "\dt migration.asset_application_mappings"` returns "Did not find"
- [ ] Backend starts without errors
- [ ] Frontend builds without TypeScript errors
- [ ] No references to `asset_application_mappings` in codebase

#### M7: Refactor Using Existing Infrastructure ☐ PENDING

**Backend: Collection API Extension**:
- [ ] Create `backend/app/api/v1/endpoints/collection_post_completion.py`
- [ ] Implement GET `/{flow_id}/unmapped-assets`
  - Query: `collection_flow_applications WHERE asset_id IS NOT NULL AND canonical_application_id IS NULL`
  - Join with `assets` table for name, type
  - Return: List of unmapped asset details
- [ ] Implement POST `/{flow_id}/link-asset-to-canonical`
  - Accept: `{ asset_id, canonical_application_id }`
  - Call: `canonical_operations.create_collection_flow_link()`
  - Update: Set canonical_application_id, deduplication_method, match_confidence
- [ ] Add tenant scoping to both endpoints (client_account_id, engagement_id)
- [ ] Register router in main application

**Backend: Assessment Apps Derivation**:
- [ ] Modify `backend/app/api/v1/master_flows/master_flows_assessment.py`
- [ ] Update `get_assessment_applications_via_master()`
  - Query `collection_flow_applications` for canonical links
  - Filter: `canonical_application_id IS NOT NULL`
  - If no links: return `{ "status": "pending_resolution", "unmapped_count": X }`
  - If links exist: fetch canonical application details
  - Return: Application list or pending status

**Frontend: Banner Component**:
- [ ] Create `src/components/assessment/AssetResolutionBanner.tsx`
- [ ] Query unmapped assets from collection API
- [ ] Show warning banner if unmapped assets exist
- [ ] "Resolve Assets" button opens modal
- [ ] Modal contains `ApplicationDeduplicationManager` (reused component)
- [ ] On completion: hide modal, refresh assessment applications
- [ ] Banner auto-hides when no unmapped assets

**Frontend: Integration**:
- [ ] Add `<AssetResolutionBanner />` to `AssessmentFlowLayout.tsx`
- [ ] Create collection API client methods (unmapped assets, link to canonical)
- [ ] Handle "pending_resolution" response in assessment apps query
- [ ] Update assessment flow initialization to check for unmapped assets

**Testing**:
- [ ] Backend unit test: unmapped assets query
- [ ] Backend unit test: link asset to canonical
- [ ] Backend integration test: assessment apps derivation
- [ ] Frontend E2E test: banner shows for unmapped assets
- [ ] Frontend E2E test: resolve workflow (open modal, select app, close banner)
- [ ] Manual E2E: Collection → Assessment → Banner → Resolve → Continue

---

### Acceptance Criteria Snapshot (Revised)

**Rollback**:
- ✅ Migration 091 rolled back, table removed
- ✅ All redundant files deleted (3 backend, 1 frontend)
- ✅ All redundant phase references removed (6 backend files, 5 frontend files)
- ✅ Build passes, no TypeScript/import errors
- ✅ ASSET_APPLICATION_RESOLUTION phase removed from enum

**Refactor**:
- ✅ Collection API has 2 new endpoints for unmapped assets/linking
- ✅ Assessment apps endpoint derives from `collection_flow_applications` canonical links
- ✅ Banner component shows if unmapped assets exist
- ✅ Banner reuses existing `ApplicationDeduplicationManager` in modal
- ✅ Banner hides when all assets resolved
- ✅ Multi-tenant scoping enforced on all queries
- ✅ E2E workflow works: Collection → Assessment → Banner → Resolve → Continue

**Code Quality**:
- ✅ Leverages existing infrastructure (1,296 lines of redundant code removed)
- ✅ Reuses battle-tested deduplication service
- ✅ Maintains architectural coherence per ADR-016
- ✅ Zero duplication: one table, one service, one UI component

---

### Effort Tracking

**Original Estimate (Redundant Approach)**: ~25-35 hours
- Backend: 8-12h
- Frontend: 10-14h
- Tests: 3-5h
- Documentation: 2-3h

**Revised Estimate (Rollback + Refactor)**: 13-17 hours
- Rollback: 2-3h
- Backend refactor: 6-8h
- Frontend refactor: 3-4h
- Testing: 2-3h

**Savings**: ~10-18 hours upfront + ongoing maintenance burden eliminated

---

### References

**Analysis**:
- `backend/ASSET_RESOLUTION_REDUNDANCY_ANALYSIS.md` - Full 500-line redundancy analysis

**Existing Infrastructure**:
- `backend/app/models/canonical_applications/collection_flow_app.py` - CollectionFlowApplication model
- `backend/app/services/application_deduplication/canonical_operations.py` - Deduplication service
- `src/components/collection/application-input/ApplicationDeduplicationManager.tsx` - Reusable UI

**Planning Documents**:
- `docs/planning/dependency-to-assessment/README.md` - Rollback + refactor plan

**ADRs**:
- ADR-016: Collection Flow for Intelligent Data Enrichment
- ADR-012: Flow Status Management Separation

**Serena Memories**:
- `collection_flow_phase_status_fixes_2025_10` - Mentioned as "future enhancement"

---

### Lessons Learned

1. **ALWAYS explore existing schema before creating new tables**
   - Use `\d table_name` to inspect existing tables
   - Query `information_schema` for similar tables
   - Check if existing tables can be extended

2. **Read Serena memories BEFORE implementation**
   - May contain context about "future enhancements" vs. urgent needs
   - Provides historical context on architectural decisions

3. **Review ADRs for architectural intent**
   - ADR-016 explicitly designed Collection Flow for data enrichment
   - Creating assessment-specific mapping violated separation of concerns

4. **Search codebase systematically**
   - Use `find`, `grep`, Serena tools to find existing patterns
   - Don't assume functionality doesn't exist

5. **Question planning documents**
   - Treat as starting point, not absolute truth
   - Validate assumptions against actual codebase

6. **Use checklist for new database tables**:
   - [ ] Check existing tables with similar purpose
   - [ ] Read related Serena memories
   - [ ] Review relevant ADRs
   - [ ] Search for existing models/services
   - [ ] Justify why extension isn't possible
   - [ ] Get review before creating schema migration

---

### Next Actions

1. ✅ Planning documents updated (README.md, TRACKER.md)
2. ☐ **AWAIT USER CONFIRMATION** before proceeding with rollback
3. ☐ Execute rollback tasks (R-01 through R-15)
4. ☐ Execute refactor tasks (F-01 through F-16)
5. ☐ Create comprehensive test suite
6. ☐ Update Serena memory with lessons learned
7. ☐ Close PR #577, create new PR with rollback + refactor
