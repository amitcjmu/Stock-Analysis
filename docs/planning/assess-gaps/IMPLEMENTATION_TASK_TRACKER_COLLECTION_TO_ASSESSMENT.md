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
4. B1 Implement apply_resolved_gaps_to_assets helper [P0][R-High][Effort-M]
   - Files: `backend/app/services/flow_configs/collection_handlers.py` (new helper near response_processing) and possibly a new small module if preferred.
   - Steps: Map `collection_questionnaire_responses` (for resolved gaps) to `Asset` fields (whitelist: environment, business_criticality, owner, compliance, performance_baseline, etc.). Write provenance into `asset.metadata` (e.g., source: collection, questionnaire_id, confidence).
   - Acceptance:
     - Batched, async updates with bounded chunk size (e.g., 200–500 assets per batch) and transactional safety
     - Only whitelisted fields updated; provenance recorded in `asset.metadata`
     - Audit logging for each batch (who/when/what changed) behind a feature flag
     - Feature flag to disable write-backs quickly if issues detected
   - Tests: Unit test for mapping; integration test with a sample Collection flow; verify audit log entries when enabled.

5. B2 Invoke write-back after response_processing [P0][R-Low][Effort-S]
   - Files: `backend/app/services/flow_configs/collection_handlers.py`
   - Steps: At end of `response_processing`, call the new helper; handle transactions safely; log summary.
   - Acceptance:
     - Submitting questionnaire results updates corresponding Assets
     - Transaction boundaries clear; failures roll back the batch cleanly and emit structured error events

6. B3 Compute and set assessment_readiness per asset [P0][R-Med][Effort-M]
   - Files: Same as B1; possibly `backend/app/models/asset.py` if new column/enum needed (verify existing readiness field usage).
   - Steps: Define readiness criteria (minimum required fields + validation); flip `asset.assessment_readiness='ready'` when met; increment `CollectionFlow.apps_ready_for_assessment`.
   - Acceptance:
     - Ready flag set only when criteria met; count reflects assets ready
     - Readiness queries avoid N+1; use prefetching and filtered, indexed lookups
     - Basic performance guardrails documented (expected durations and thresholds)
   - Tests: Unit for readiness logic; integration to confirm flips on submission.

### Phase C — Orchestration gating before Assessment
7. C1 Add readiness gate using DataFlowValidator [P0][R-High][Effort-M]
   - Files: `backend/app/services/integration/smart_workflow_orchestrator.py` (or MFO hook), `backend/app/services/integration/data_flow_validator.py`
   - Steps: Before initiating Assessment, run validator for engagement; block if thresholds < configured minimums.
   - Acceptance: Attempts to start Assessment return actionable info when not ready and suggest/auto-start Collection.
   - Tests: Integration test: Discovery complete but missing fields → gate triggers; with Collection completed → allowed.

8. C2 Auto-create or resume Collection when gate fails [P1][R-Low][Effort-S]
   - Files: Orchestrator + `collection.py` (if needed for convenience call).
   - Steps: If gate fails, create a Collection flow (or resume active) via `MasterFlowOrchestrator` and pause navigation to Assessment.
   - Acceptance: Seamless path to questionnaires without manual setup.

9. C3 Enforce access control and authorization checks [P0][R-High][Effort-S]
   - Files: Orchestrator checks; `collection.py` and `assessment_flow.py` where gating is invoked.
   - Steps: Ensure only authorized roles can trigger write-backs, gating transitions, and asset updates; reuse RBAC utilities.
   - Acceptance: Unauthorized attempts are rejected with 403; audit log entry created.

10. C4 Failure journal (DB-backed) and replay for failed resume/gating [P1][R-Med][Effort-M]
   - Files: Orchestrator; simple repository + table for failure journal.
   - Steps: On repeated failures (retry exhausted), persist payload and error to a DB table; provide an admin endpoint to list and replay entries; expose counts in monitoring endpoint.
   - Acceptance: No silent drops; operators can inspect and replay without full messaging/DLQ infrastructure.

### Phase D — Assessment consumer updates
11. D1 Replace Assessment loader placeholder with ready-app query [P0][R-Med][Effort-M]
   - Files: `backend/app/services/crewai_flows/unified_assessment_flow.py`, `backend/app/services/integrations/discovery_integration.py`
   - Steps: Implement `_load_selected_applications` to pull `assessment_readiness='ready'` apps, including resolved manual fields (join via Collection synthesis if needed).
   - Acceptance: Assessment initializes only with ready apps, containing curated data.
   - Tests: Integration: attempt load with/without ready apps; verify content shape.

12. D2 Wire Assessment API to the improved loader (optional if kept simulated) [P2][R-Low][Effort-S]
   - Files: `assessment_flow.py` background tasks; ensure repository fields align.
   - Steps: If desired now, invoke UnifiedAssessmentFlow; otherwise keep simulation until Phase E.
   - Acceptance: No regression in API; loader available for future enablement.

### Phase E — API enhancements for readiness/quality (read-only)
13. E1 Add readiness/quality summary endpoints (read-only) [P2][R-Low][Effort-S]
   - Files: `backend/app/api/v1/endpoints/collection.py`
   - Steps: Add `GET /flows/{id}/readiness` returning `apps_ready_for_assessment`, validator summary, and last synthesis timestamp.
   - Acceptance: UI can decide routing without additional joins.

### Phase F — Minimal UI routing (optional in this PR if backend-first)
14. F1 Route to Collection when zero ready apps (minimal UX; intelligent-automation messaging) [P2][R-Low][Effort-M]
   - Files: `src/pages/...` flow creation/summary; hooks invoking unified flows.
   - Steps: After Discovery, fetch readiness; if zero, deep-link to questionnaires page with UX copy framing as intelligent automation; on submit, re-check and proceed to Assessment.
   - Acceptance: Simple UX path; no loops; respects unified APIs.

15. F2 Minimal progress indicators and auto-transitions [P1][R-Low][Effort-M]
   - Files: Frontend flow pages and status hooks.
   - Steps: Display phase progress and auto-transition to next step upon readiness; show ETA where applicable.
   - Acceptance:
     - Users see seamless progression with minimal clicks; abandonment risk reduced
     - UX copy explicitly frames step as "automated gap analysis/intelligent enrichment", not an extra chore
     - Progress messaging emphasizes "intelligent enrichment in progress" during automated phases
     - No user action required during automated phases (buttons disabled with clear status), resumes automatically when input needed

16. F3 User journey optimization and testing (after backend gating proves stable) [P3][R-Low][Effort-M]
   - Steps: Conduct small UX test for messaging and routing; measure friction points; refine copy and default paths.
   - Acceptance: Documented improvements; fewer back-and-forth navigations in test sessions.

17. F4 Questionnaire completion rate optimization (after metric baseline) [P3][R-Low][Effort-S]
   - Steps: Introduce shorter sections, save-as-you-go, and suggest answers where confidence is high.
   - Acceptance: Baseline completion rate measured and improved ≥10%.

### Phase G — Testing, validation, and rollout
18. G1 Unit tests for mapping and readiness [P0][R-Low][Effort-S]
   - Files: `tests/backend/...` new tests for write-back & readiness.
   - Acceptance: >90% coverage for new helpers; CI green.

19. G2 Integration tests for gated flow [P0][R-Med][Effort-M]
   - Steps: E2E Discovery → (gate) → Collection → Assessment; assert gate behavior and data propagation.
   - Acceptance: Deterministic pass locally and in CI.

20. G3 Update CHANGELOG and docs [P0][R-Low][Effort-S]

21. G4 Business metrics and ROI tracking (with operational alerts) [P1][R-Low][Effort-S]
   - Files: Monitoring/analytics layer; add counters/ timers.
   - Steps: Track time-to-assessment reduction, % apps entering Assessment without rework, questionnaire completion rates; add operational alerts:
     - Alert thresholds for batch write-back failures and error rate spikes
     - Performance degradation detection for readiness queries and loader latencies
     - User abandonment rate monitoring on Collection steps with automatic flags when above threshold
   - Acceptance: Dashboards/logs expose metrics; alert rules configured and tested; baseline recorded.

22. G5 Customer validation framework [P1][R-Low][Effort-M]
   - Steps: Identify 2–3 customers for pilot; define feedback loop and acceptance criteria; schedule validation checkpoints.
   - Acceptance: Documented validation results and action items.

23. G6 Assessment success rate tracking [P1][R-Low][Effort-S]
   - Steps: Measure % of Assessment flows completing without manual data correction; correlate improvements to Collection enrichment readiness metrics.
   - Acceptance: Regular report/metric available; target uplift tracked over time.

### Phase H — AI Intelligence Enablement (strategic enhancement behind flags)
24. H1 Enable and integrate existing gap analysis agent [P1][R-Med][Effort-M]
   - Files: `backend/app/services/ai_analysis/gap_analysis_agent.py` (enable in collection flow handlers via feature flag).
   - Acceptance: >80% accuracy on curated sample; can disable via flag if noisy.

25. H2 Enable adaptive questionnaire generation (existing) [P1][R-Med][Effort-M]
   - Files: `backend/app/services/ai_analysis/questionnaire_generator.py`; confirm persistence via `flow_utilities.save_questionnaires_to_db`.
   - Acceptance: Targets top-priority gaps; gated by feature flag.

26. H3 Integrate lightweight confidence scoring [P2][R-Low][Effort-S]
   - Files: Scoring hook; store confidence with responses; factor into readiness thresholds later.
   - Acceptance: Confidence persisted; optional weighting configurable.

27. H4 Enable learning optimizer for incremental improvements [P2][R-Low][Effort-M]
   - Files: `backend/app/services/ai_analysis/learning_optimizer/*`.
   - Acceptance: Evidence of shorter forms/higher completion over time.
   - Files: `CHANGELOG.md`, consolidated plan doc updates.
   - Acceptance: Entries include business impact and technical notes.

### Dependencies summary
- B1 → B2 → B3 (sequential core)
- B4 (indexing) follows B3; privacy/encryption scoping (B5) in parallel with C1; monitoring folded into G4
- C1 depends on B3 (readiness flags) and A2/A3; C2 depends on C1
- C3 depends on existing RBAC; C4 depends on orchestrator retry logic
- D1 depends on B3 and C1; D2 optional
- E1/F1–F4 follow D1; some UX work can begin earlier with mocks
- G1–G5 after corresponding phases; final E2E after D1/C2
- H1–H4 after Phase A–D stabilize (can prototype earlier off-path)

### Rollback/guardrails
- Feature flag the write-back (env var) to disable updates if needed
- Strict whitelist for updatable `Asset` fields; log changes with provenance
- Transactional updates; safe retries on transient errors
 - DLQ for repeated failures; operator replay tools
 - RBAC enforced on sensitive transitions

### Privacy review checklist (for write-backs)
- Inventory fields updated on `Asset`; flag PII/sensitive fields
- Exclude or mask PII where not essential to Assessment readiness
- Document any targeted encryption plan for a small, high-risk subset (phase 2)

### Risk priorities (updated)
1. Data integrity (write-back operations)
2. User adoption and UX (perception of added step)
3. Performance and scalability (batch operations)
4. Security and compliance (sensitive data handling)

### Review checklist (for approval)
- Scope: Immediate focus on B1–B3, C1–C2, D1, G1–G2
- No new controllers; all via `MasterFlowOrchestrator`
- No legacy endpoints used
- Multi-tenant scoping and async DB patterns respected

### Quantitative success metrics
- Time-to-assessment: median < 2 days from Discovery completion
- Questionnaire completion rate: ≥ 80% (improve ≥ 10% vs. baseline post F4/H4)
- Data completeness before Assessment: ≥ 85% for required fields
- Validator scores: Collection/Discovery ≥ 0.7 for apps entering Assessment
- Rework reduction: ≥ 50% fewer manual corrections during Assessment

### Prioritization roadmap (agreed)
- Must-have now: B1–B3, C1–C2, D1, C3, G1–G2, G4
- Should-have next: E1, F1–F2 (minimal), C4 (failure journal), B4 (indexing), G5 (1–2 customer validation sessions)
- Could-have later: D2
- Strategic later (behind flags): H1–H4 enablement/integration

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


