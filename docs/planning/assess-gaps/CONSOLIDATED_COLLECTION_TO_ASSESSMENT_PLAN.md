## Consolidated Discovery → Collection → Assessment Integration Plan

Date: 2025-08-08

### Purpose
Create a practical, code-grounded plan to insert the Collection Flow as an intelligent gating step between Discovery and Assessment, leveraging what already exists in the codebase and aligning with the phased approach from the gap-analysis and implementation plan documents.

### Scope and current-state verification (code-based)
- **Collection models (exist, DB-backed):**
  - `backend/app/models/collection_flow.py` includes `CollectionFlow`, `CollectionGapAnalysis`, `AdaptiveQuestionnaire`, plus in-memory `CollectionFlowState` and enums.
  - `backend/app/models/collection_data_gap.py` and `backend/app/models/collection_questionnaire_response.py` exist for gaps and responses.
  - Alembic migration adds `collection_flow_id` to `adaptive_questionnaires`: `backend/alembic/versions/009_add_collection_flow_id_to_questionnaires.py`.
- **Collection API (exists):**
  - `backend/app/api/v1/endpoints/collection.py` provides endpoints to create flows, get status/details, list gaps, list questionnaires, submit responses, resume, and cleanup. It invokes the `MasterFlowOrchestrator` to start/resume flows.
- **Collection CrewAI flow (exists, functional skeleton):**
  - `backend/app/services/crewai_flows/unified_collection_flow.py` and its `unified_collection_flow_modules/phase_handlers/*` implement platform detection, automated collection, gap analysis, questionnaire generation, manual collection, validation, and finalization hooks.
  - `flow_utilities.save_questionnaires_to_db` persists adaptive questionnaires with `collection_flow_id`.
  - `collection_handlers.response_processing` updates `collection_questionnaire_responses` and marks gaps resolved.
- **Assessment API (exists; some background tasks simulated):**
  - `backend/app/api/v1/endpoints/assessment_flow.py` supports initialize/resume/status, architecture, components, tech debt, 6R decisions, app-on-page, report, and finalization. It relies on `AssessmentFlowRepository` and conditionally on `DiscoveryFlowIntegration` for readiness checks. Background task bodies simulate flow execution (placeholders), but endpoints and repository wiring are present.
- **Assessment flow service (partially implemented):**
  - `backend/app/services/crewai_flows/unified_assessment_flow.py` exists, but the loader `_load_selected_applications` has a placeholder comment. API doesn’t currently call this class in background tasks.
- **Gating and validation (exists, not fully enforced):**
  - `backend/app/services/integration/data_flow_validator.py` validates end-to-end data quality across phases.
  - Orchestration has readiness checks scaffolding, but hard gating into Assessment based on Collection completion is not fully wired.

### Key gap to close now
- Missing write-back: Resolved questionnaire responses and gap resolutions are not mapped back to `Asset` records and do not flip `assessment_readiness` per application. Consequently, Assessment cannot reliably consume “ready” inputs.
- Assessment loader placeholder: The Assessment flow does not yet fetch curated, ready applications enriched by Collection and Discovery outcomes.

### Immediate plan (1–2 sprints) – fast bridge to value
1) Apply resolved Collection data back to assets and set readiness
   - Add a helper: `apply_resolved_gaps_to_assets(db: AsyncSession, flow_id: str)` to map `collection_questionnaire_responses` and resolved `collection_data_gaps` to concrete `Asset` fields (e.g., environment, business_criticality, owner, compliance flags), persisting provenance in `asset.metadata`.
   - Invoke this helper at the end of `response_processing` in `backend/app/services/flow_configs/collection_handlers.py`.
   - Compute per-asset assessment prerequisites; flip `asset.assessment_readiness` to "ready" when minimum fields are present and validated. Increment `CollectionFlow.apps_ready_for_assessment` accordingly.

2) Enforce gating into Assessment in orchestration
   - Before starting Assessment, run `DataFlowValidator.validate_end_to_end_data_flow(engagement_id)` and ensure:
     - Required collection fields are present for selected apps
     - Discovery enrichment thresholds (e.g., dependency coverage) meet minimums
   - If thresholds fail, auto-create a Collection flow via `MasterFlowOrchestrator` for the engagement, return a PAUSED state with guidance and links to questionnaires.

3) Make Assessment consume only curated, ready applications
   - Replace the placeholder loader in `UnifiedAssessmentFlow` to query apps with `assessment_readiness='ready'` using `DiscoveryFlowIntegration.get_applications_ready_for_assessment` and include:
     - Resolved manual fields from `collection_questionnaire_responses`
     - Synthesized `manual_data` and `automated_data` produced by `synthesis_preparation` in Collection handlers.
   - Ensure `AssessmentFlowRepository.create_assessment_flow` stores the selected app IDs, and status endpoints reflect only those.

4) Minimal UI routing
   - After Discovery completion, if zero apps are ready, route users to the Collection questionnaires page for the engagement; after submission, re-check readiness and proceed to Assessment creation.

Deliverables
- Code edits in:
  - `backend/app/services/flow_configs/collection_handlers.py` (new write-back; call site in `response_processing`)
  - `backend/app/services/integration/data_flow_validator.py` (confirm thresholds align to readiness gate)
  - `backend/app/services/integration/smart_workflow_orchestrator.py` or MFO hook (enforce gate / auto-start Collection)
  - `backend/app/services/crewai_flows/unified_assessment_flow.py` (real loader)
  - `backend/app/services/integrations/discovery_integration.py` (ensure ready-app query covers new readiness flag)

Success criteria
- Submitting Collection questionnaires updates `Asset` records; assets display `assessment_readiness='ready'` when prerequisites are met.
- Assessment can initialize only when selected apps are ready; otherwise a Collection flow is started automatically.
- No CRITICAL issues in `DataFlowValidator` for apps entering Assessment.

### Near-term plan (aligns with Phase 2 outcomes; 2–4 sprints)
- Complete synthesis-to-assessment input package
  - Extend `synthesis_preparation` (Collection) to persist a concise “assessment input package” summarizing curated fields, quality, and provenance, retrievable by Assessment.
- Harden adapters and normalization
  - Improve `collection_flow/adapters/*` implementations and rate limiting; ensure `collection_data_normalization` saves consistent normalized schemas.
- API enhancements (do not duplicate controllers)
  - Add read endpoints for readiness, quality score, and summarized synthesis under `collection.py` so the UI can gate navigation without extra joins.

Metrics
- < 2 days from Discovery completion to Assessment-ready state
- ≥ 80% of required fields satisfied before Assessment kickoff
- Validator collection/discovery scores ≥ 0.7 for apps entering Assessment

### Mid-term plan (select Phase 3 items; 4–6 sprints)
- Questionnaire optimization and learning
  - Use `ai_analysis/learning_optimizer` to shorten forms, schedule at optimal times, and raise completion rates.
- Assessment readiness calculator
  - Formalize a readiness score in `DataFlowValidator` with an API endpoint for UI gating and reporting.
- Analytics and reporting
  - Track gap resolution rates, time-to-ready, and handoff success to continuously improve flows.

### Risks and mitigations
- Mapping correctness
  - Start with a conservative whitelist of asset fields; log all write-backs with provenance; provide a rollback path for erroneous writes.
- Orchestration complexity
  - Keep all transitions within `MasterFlowOrchestrator`; avoid legacy endpoints.
- Performance
  - Use async sessions and batched updates; avoid N+1 queries; add indexes if needed on frequently filtered flags (e.g., `assessment_readiness`).

### Acceptance checklist
- [ ] `apply_resolved_gaps_to_assets` implemented and invoked post-response
- [ ] Assets reflect resolved fields and `assessment_readiness`
- [ ] Orchestration blocks Assessment until validator thresholds met
- [ ] Assessment loads only ready apps and includes Collection synthesis data
- [ ] Basic UI route from Discovery to Collection to Assessment based on readiness

### Notes on assumptions validated
- Collection models, endpoints, and flow handlers exist and persist data, including `adaptive_questionnaires` with `collection_flow_id`.
- Assessment endpoints and repository are present; background tasks currently simulate execution, but the flow scaffolding and persistence are in place.
- Gating is not fully enforced today; the plan above adds minimal, targeted edits to enforce it without introducing new competing controllers.


