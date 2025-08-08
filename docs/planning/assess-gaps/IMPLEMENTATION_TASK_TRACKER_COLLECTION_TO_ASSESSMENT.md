## Implementation Task Tracker: Discovery → Collection (Gated) → Assessment

Date: 2025-08-08

Purpose: Step-by-step, reviewable task list to implement the consolidated plan with minimal-risk edits first. Each task includes dependencies, files, acceptance criteria, and testing notes.

Legend: [P] Priority, [R] Risk, [Effort] S/M/L, Status (TBD/In-Progress/Done)

### Phase A — Safety checks and preconditions
1. A1 Verify DB schema and migrations [P1][R-Low][Effort-S]
   - Files/Areas: Alembic history; tables `collection_flows`, `collection_data_gaps`, `collection_questionnaire_responses`, `adaptive_questionnaires` (with `collection_flow_id` column).
   - Steps: Run DB introspection (within container) to confirm columns, FKs, and indexes exist per models.
   - Acceptance: All required tables/columns present; FK to `collection_flows` validated; no blocking drift.
   - Tests: Smoke query via backend session; no code changes.

2. A2 Confirm Collection flow endpoints are callable [P1][R-Low][Effort-S]
   - Files: `backend/app/api/v1/endpoints/collection.py`
   - Steps: Exercise `POST /collection/flows`, `GET /collection/flows/{id}`, `GET /collection/flows/{id}/questionnaires` with a seeded engagement.
   - Acceptance: 200 responses; flow creation links to master flow; no 5xx.

3. A3 Confirm Assessment endpoints and repository wiring [P1][R-Low][Effort-S]
   - Files: `backend/app/api/v1/endpoints/assessment_flow.py`, `backend/app/repositories/assessment_flow_repository.py`
   - Steps: Call `POST /assessment-flow/initialize` (with fake app IDs) and ensure validation errors surface if not ready.
   - Acceptance: Endpoint routes, repo instantiation ok; background tasks simulate without error.

### Phase B — Write-back of Collection responses to Assets
4. B1 Implement apply_resolved_gaps_to_assets helper [P0][R-Med][Effort-M]
   - Files: `backend/app/services/flow_configs/collection_handlers.py` (new helper near response_processing) and possibly a new small module if preferred.
   - Steps: Map `collection_questionnaire_responses` (for resolved gaps) to `Asset` fields (whitelist: environment, business_criticality, owner, compliance, performance_baseline, etc.). Write provenance into `asset.metadata` (e.g., source: collection, questionnaire_id, confidence).
   - Acceptance: Batch updates succeed; only whitelisted fields updated; provenance recorded.
   - Tests: Unit test for mapping; integration test with a sample Collection flow.

5. B2 Invoke write-back after response_processing [P0][R-Low][Effort-S]
   - Files: `backend/app/services/flow_configs/collection_handlers.py`
   - Steps: At end of `response_processing`, call the new helper; handle transactions safely; log summary.
   - Acceptance: Submitting questionnaire results updates corresponding Assets.

6. B3 Compute and set assessment_readiness per asset [P0][R-Med][Effort-M]
   - Files: Same as B1; possibly `backend/app/models/asset.py` if new column/enum needed (verify existing readiness field usage).
   - Steps: Define readiness criteria (minimum required fields + validation); flip `asset.assessment_readiness='ready'` when met; increment `CollectionFlow.apps_ready_for_assessment`.
   - Acceptance: Ready flag set only when criteria met; count reflects assets ready.
   - Tests: Unit for readiness logic; integration to confirm flips on submission.

### Phase C — Orchestration gating before Assessment
7. C1 Add readiness gate using DataFlowValidator [P0][R-Med][Effort-M]
   - Files: `backend/app/services/integration/smart_workflow_orchestrator.py` (or MFO hook), `backend/app/services/integration/data_flow_validator.py`
   - Steps: Before initiating Assessment, run validator for engagement; block if thresholds < configured minimums.
   - Acceptance: Attempts to start Assessment return actionable info when not ready and suggest/auto-start Collection.
   - Tests: Integration test: Discovery complete but missing fields → gate triggers; with Collection completed → allowed.

8. C2 Auto-create or resume Collection when gate fails [P1][R-Low][Effort-S]
   - Files: Orchestrator + `collection.py` (if needed for convenience call).
   - Steps: If gate fails, create a Collection flow (or resume active) via `MasterFlowOrchestrator` and pause navigation to Assessment.
   - Acceptance: Seamless path to questionnaires without manual setup.

### Phase D — Assessment consumer updates
9. D1 Replace Assessment loader placeholder with ready-app query [P0][R-Med][Effort-M]
   - Files: `backend/app/services/crewai_flows/unified_assessment_flow.py`, `backend/app/services/integrations/discovery_integration.py`
   - Steps: Implement `_load_selected_applications` to pull `assessment_readiness='ready'` apps, including resolved manual fields (join via Collection synthesis if needed).
   - Acceptance: Assessment initializes only with ready apps, containing curated data.
   - Tests: Integration: attempt load with/without ready apps; verify content shape.

10. D2 Wire Assessment API to the improved loader (optional if kept simulated) [P2][R-Low][Effort-S]
   - Files: `assessment_flow.py` background tasks; ensure repository fields align.
   - Steps: If desired now, invoke UnifiedAssessmentFlow; otherwise keep simulation until Phase E.
   - Acceptance: No regression in API; loader available for future enablement.

### Phase E — API enhancements for readiness/quality (read-only)
11. E1 Add readiness/quality summary endpoints (read-only) [P2][R-Low][Effort-S]
   - Files: `backend/app/api/v1/endpoints/collection.py`
   - Steps: Add `GET /flows/{id}/readiness` returning `apps_ready_for_assessment`, validator summary, and last synthesis timestamp.
   - Acceptance: UI can decide routing without additional joins.

### Phase F — Minimal UI routing (optional in this PR if backend-first)
12. F1 Route to Collection when zero ready apps [P2][R-Low][Effort-S]
   - Files: `src/pages/...` flow creation/summary; hooks invoking unified flows.
   - Steps: After Discovery, fetch readiness; if zero, deep-link to questionnaires page; on submit, re-check and proceed to Assessment.
   - Acceptance: Simple UX path; no loops; respects unified APIs.

### Phase G — Testing, validation, and rollout
13. G1 Unit tests for mapping and readiness [P0][R-Low][Effort-S]
   - Files: `tests/backend/...` new tests for write-back & readiness.
   - Acceptance: >90% coverage for new helpers; CI green.

14. G2 Integration tests for gated flow [P0][R-Med][Effort-M]
   - Steps: E2E Discovery → (gate) → Collection → Assessment; assert gate behavior and data propagation.
   - Acceptance: Deterministic pass locally and in CI.

15. G3 Update CHANGELOG and docs [P0][R-Low][Effort-S]
   - Files: `CHANGELOG.md`, consolidated plan doc updates.
   - Acceptance: Entries include business impact and technical notes.

### Dependencies summary
- B1 → B2 → B3 (sequential)
- C1 depends on B3 (needs readiness flags) and A2/A3
- C2 depends on C1
- D1 depends on B3 and C1 (ensures data available)
- E1/F1 can follow D1 or be parallel once B3 exists
- G-tests after each phase; final E2E after D1/C2

### Rollback/guardrails
- Feature flag the write-back (env var) to disable updates if needed
- Strict whitelist for updatable `Asset` fields; log changes with provenance
- Transactional updates; safe retries on transient errors

### Review checklist (for approval)
- Scope: Immediate focus on B1–B3, C1–C2, D1, G1–G2
- No new controllers; all via `MasterFlowOrchestrator`
- No legacy endpoints used
- Multi-tenant scoping and async DB patterns respected

Status board (initial)
- A1: TBD
- A2: TBD
- A3: TBD
- B1: TBD
- B2: TBD
- B3: TBD
- C1: TBD
- C2: TBD
- D1: TBD
- D2: TBD
- E1: TBD
- F1: TBD
- G1: TBD
- G2: TBD
- G3: TBD


