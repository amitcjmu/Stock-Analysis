### Dependency Mapping → Assessment: Implementation Tracker

Status legend: ☐ pending · ▶ in_progress · ✅ completed · ✖ cancelled

---

### Milestones

- M1: Enum Unification (CRITICAL)
- M2: Phase + DB Schema
- M3: Backend Service + Endpoints
- M4: Frontend Page + Routing
- M5: Tests + E2E

---

### Task Board

| ID | Task | Owner | Status | Start | ETA | Notes/Links |
|---|---|---|---|---|---|---|
| T-01 | Unify AssessmentPhase enums across backend/frontend | Backend | ✅ completed | 2025-10-13 | 2025-10-13 | Enum unified, deprecated phases removed |
| T-02 | Add ASSET_APPLICATION_RESOLUTION to canonical enum & sequencing | Backend | ✅ completed | 2025-10-13 | 2025-10-13 | Added to assessment_flow_state.py and utils |
| T-03 | Alembic migration: asset_application_mappings | Backend | ✅ completed | 2025-10-13 | 2025-10-13 | Migration 091 created and applied |
| T-04 | Implement AssetResolutionService (tenant-scoped) | Backend | ✅ completed | 2025-10-13 | 2025-10-13 | Full CRUD with tenant scoping |
| T-05 | Add API endpoints for resolution list/map/complete | Backend | ✅ completed | 2025-10-13 | 2025-10-13 | 3 endpoints under assessment routes |
| T-06 | Update master flow applications to use mappings | Backend | ✅ completed | 2025-10-13 | 2025-10-13 | Resolution check added |
| T-07 | Frontend: add phase type, routes, progress | Frontend | ✅ completed | 2025-10-13 | 2025-10-13 | Types, routes, progress components updated |
| T-08 | Build `/assessment/[flowId]/asset-resolution` page | Frontend | ✅ completed | 2025-10-13 | 2025-10-13 | Full page with polling and validation |
| T-09 | Update `useAssessmentFlow` gating + API | Frontend | ✅ completed | 2025-10-13 | 2025-10-13 | Phase navigation and API calls added |
| T-10 | Banner on 6R pages showing asset→app mapping | Frontend | ✅ completed | 2025-10-13 | 2025-10-13 | Included in AssessmentFlowLayout |
| T-11 | Backend unit + API tests | QA | ▶ in_progress | 2025-10-13 | | Automated via qa-playwright-tester |
| T-12 | Frontend integration + E2E path | QA | ☐ pending | | | Collection→Resolution→6R |
| T-13 | Docs & CHANGELOG update | PM | ☐ pending | | | Version bump and release notes |

---

### Detailed Checklists

#### M1: Enum Unification

- [x] Remove duplicate enum in `backend/app/models/assessment_flow/enums_and_exceptions.py`
- [x] Update imports to canonical enum
- [x] Align `backend/app/api/v1/endpoints/assessment_flow_utils.py` phase sequence
- [x] Update `src/hooks/useAssessmentFlow/types.ts` phases
- [x] Frontend build passes; assessment navigation works

#### M2: Phase + DB Schema

- [x] Add `ASSET_APPLICATION_RESOLUTION` to canonical enum
- [x] Update backend phase sequence/navigation helpers
- [x] Alembic migration created and applied (idempotent; `migration` schema)

#### M3: Backend Service + Endpoints

- [x] `AssetResolutionService` with tenant scoping
- [x] `GET /assessment-flows/{flow_id}/asset-resolution`
- [x] `POST /assessment-flows/{flow_id}/asset-resolution/mappings`
- [x] `POST /assessment-flows/{flow_id}/asset-resolution/complete`
- [x] Master flow applications use mappings after completion

#### M4: Frontend Page + Routing

- [x] Add phase to types and `flowRoutes`
- [x] Progress components include new phase
- [x] New page renders; list unresolved; map/create apps; complete
- [x] `useAssessmentFlow` gating integrated
- [x] Banner present until completion

#### M5: Tests + E2E

- [ ] Backend unit + API tests green
- [ ] Frontend integration tests green
- [ ] E2E: Collection→Assessment Init→Resolution→Architecture Minimums

---

### Acceptance Criteria Snapshot

- After resolution completion, `getAssessmentApplications` returns expected applications for previously failing cases.
- All endpoints enforce tenant headers and audit fields.
- Enum drift eliminated (single source of truth).
- UI clearly guides users through mapping and progression.

---

### References

- See `README.md` in this folder for the full plan and code references.


