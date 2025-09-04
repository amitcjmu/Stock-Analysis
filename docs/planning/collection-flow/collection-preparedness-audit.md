# Collection→Assessment Preparedness Audit (Senior Architecture Review)

## Executive Summary

Overall, the Collection Flow now persists the key artifacts needed to prepare applications for Assessment, but there are critical gaps preventing reliable handoff:
- Collection questionnaires and responses are saved, and models are tenant‑scoped.
- A dedicated transition endpoint exists and creates Assessment flows from selected apps.
- However, manual questionnaire submissions do not resolve gaps or trigger asset write‑back, so Assessment may not see updated attributes. Also, some endpoints lack full tenant scoping, and dependency write‑back is incomplete.

Net: Without closing these gaps, some applications will enter Assessment with missing context (owner, environment, dependencies), degrading 6R quality.

## What We Reviewed (code‑grounded)

- Models and DB
  - `backend/app/models/collection_flow.py`
    - `CollectionFlow`, `CollectionDataGap`, `AdaptiveQuestionnaire` relationships to responses and assets
  - `backend/app/models/collection_questionnaire_response.py`
  - `backend/app/models/asset.py`, `AssetDependency`
  - `backend/app/models/assessment_flow/core_models.py`
- Collection Flow endpoints and handlers
  - `backend/app/api/v1/endpoints/collection_crud_create_commands.py`
  - `backend/app/api/v1/endpoints/collection_crud_questionnaires.py`
  - `backend/app/api/v1/endpoints/collection_questionnaires.py`
  - `backend/app/api/v1/endpoints/collection_crud_update_commands.py`
  - `backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/questionnaire_generation_handler.py`
  - `backend/app/services/flow_configs/collection_handlers/{questionnaire_handlers.py,asset_handlers.py,base.py}`
- Transition and Assess consumption
  - `backend/app/api/v1/endpoints/collection_transition.py`
  - `backend/app/services/collection_transition_service.py`
  - `backend/app/api/v1/endpoints/sixr_analysis_modular/services/analysis_service.py` (reads from `Asset`)

## Data Flow Overview

1) Discovery → Collection
- `DiscoveryToCollectionBridge` seeds `CollectionFlow.collection_config.selected_application_ids`.
- Collection phases identify gaps and generate adaptive questionnaires. `AdaptiveQuestionnaire.collection_flow_id` links instances to a flow.

2) Questionnaire responses persistence
- API: `POST /collection/flows/{flow_id}/questionnaires/{questionnaire_id}/responses`
- Persists one `CollectionQuestionnaireResponse` per field, optionally linked to `asset_id` if `form_metadata.application_id` is supplied.

3) Gap resolution and write‑back
- Agent‑driven path: `questionnaire_handlers.response_processing` updates `CollectionDataGap.resolution_status='resolved'` and then calls `asset_handlers.apply_resolved_gaps_to_assets`, which whitelists select fields and sets `assessment_readiness` when minimums exist.
- Manual API path: responses are saved, but gaps are not marked resolved and write‑back is not triggered.

4) Transition to Assessment
- `POST /collection/flows/{flow_id}/transition-to-assessment` validates readiness via agent, then creates an `AssessmentFlow` using `selected_application_ids` from `CollectionFlow.collection_config` and stores handoff metadata.

5) Assessment consumption
- Assessment 6R analysis reads actual application data from `Asset` and related structures, not from raw questionnaire responses. Therefore, write‑back must populate `Asset` for Assess to have complete inputs.

## Findings

- Collection persistence is in place
  - `AdaptiveQuestionnaire` is persisted with `collection_flow_id` and multi‑tenant fields.
  - `CollectionQuestionnaireResponse` links to `collection_flow_id`, optionally to `asset_id`.

- Transition endpoint and service are implemented
  - Readiness is agent‑driven (no hardcoded thresholds), then Assessment flow is created with app scope.

- Assessment reads from `Asset`
  - 6R analysis service queries `Asset` to build real application context for decisions.

## Critical Gaps (blockers for reliable handoff)

- Manual submissions don’t resolve gaps or update assets
  - `submit_questionnaire_response` creates responses but does not set `gap_id` or update `CollectionDataGap.resolution_status`. The write‑back pipeline (`asset_handlers.apply_resolved_gaps_to_assets`) relies on resolved gaps joined to responses, so it never runs for manual path.
  - Impact: Asset fields (owner, environment, department, criticality, technology_stack, application_name) remain stale; `assessment_readiness` often stays `not_ready`.

- Incomplete tenant scoping on read path
  - `get_adaptive_questionnaires` filters by `engagement_id` but not `client_account_id` when loading the flow; this violates tenant isolation rules.

- Questionnaire completion metadata not updated
  - `AdaptiveQuestionnaire.completion_status`/`responses_collected` are not updated during manual submissions; downstream UX and gating can misrepresent progress.

- Dependency write‑back is missing
  - Collected dependency information (if any) is not mapped into `AssetDependency` or `Asset.dependencies` JSON. Assessment loses critical dependency context for realistic 6R and wave planning.

- Type fidelity of responses is lossy
  - All manual responses default `response_type='text'` and `question_text=field_id`, losing structure needed for accurate mapping and validation.

- Raw SQL without schema qualification (consistency)
  - `asset_handlers.apply_resolved_gaps_to_assets` uses unqualified table names; prefer schema‑qualified or ORM to avoid search path issues.

## Recommendations (actionable, code‑level)

1) Close the manual‑path write‑back gap (highest priority)
- Enhance `submit_questionnaire_response` to:
  - Accept and store `gap_id` per field when provided by the UI (extend form metadata to include `gap_id_map: {field_id: gap_uuid}`).
  - For fields mapped to gaps, set those gaps to `resolved` when `validation_results.isValid` is true.
  - After commit, invoke `asset_handlers.apply_resolved_gaps_to_assets(db, flow.id, context_dict)` to update `Asset` and set `assessment_readiness`.
- If `gap_id` is not provided, add a safe fallback matcher: join on `(collection_flow_id, field_name == question_id)` when the field clearly corresponds to a known gap.

2) Enforce tenant scoping on reads
- Update `get_adaptive_questionnaires` to also filter by `client_account_id` alongside `engagement_id` when loading `CollectionFlow`.

3) Persist questionnaire completion status
- On successful save, update `AdaptiveQuestionnaire.completion_status` and `responses_collected` for the specific `questionnaire_id` to reflect progress; mark `completed_at` on 100%.

4) Capture and write back dependencies
- Extend response schema to capture dependency entries (application→database, application→server) as structured arrays.
- Add a dependency write‑back step:
  - Create/merge `AssetDependency` rows for new relationships.
  - Maintain `Asset.dependencies` JSON for quick UI, but rely on normalized table for analysis.

5) Preserve response types and labels
- Include `field_type`, `question_text`, and structured values in the UI submission payload so backend stores accurate `response_type` and `question_text`.

6) Normalize SQL and schema usage
- Replace raw SQL in handlers with SQLAlchemy or add explicit `migration.` schema qualification to ensure cross‑environment reliability.

## Data Coverage vs Assessment Needs

- Minimum attributes for 6R readiness
  - Identity: `name`, `application_name`, `environment`
  - Ownership: `business_owner`, `department`
  - Technical: `technology_stack`, `operating_system`
  - Governance/criticality: `criticality` (business and/or technical)
  - Dependencies: application↔database, application↔server (normalized)

- Current coverage
  - Collected and available for write‑back via whitelist today: `environment`, `business_criticality`, `business_owner`, `department`, `application_name`, `technology_stack`.
  - Missing pipeline: dependencies not written back; OS rarely updated from forms; progression to `assessment_readiness='ready'` hinges on whitelist fields being written.

## Suggested UI/API Contract Adjustments

- UI submissions should send:
  - `form_metadata`: `{ form_id, questionnaire_id, application_id, submitted_at, completion_percentage, confidence_score }`
  - `responses`: `{ [field_id]: value }`
  - `gap_id_map`: `{ [field_id]: gap_uuid }` (NEW)
  - `field_types`: `{ [field_id]: 'select' | 'text' | 'multiselect' | ... }` (NEW)
  - `question_texts`: `{ [field_id]: 'Business Owner' }` (NEW)
  - `dependencies`: `[ {from_asset_id, to_asset_id, dependency_type, description} ]` (NEW, optional)

- Backend should:
  - Use `gap_id_map` to set `gap.resolution_status` and enable write‑back.
  - Use `field_types` and `question_texts` to store accurate types and labels.
  - Upsert `AssetDependency` for provided `dependencies`.

## Readiness Gate Logic (post‑fix)

- Collection considers a flow ready for transition when:
  - All critical gaps are resolved OR agent readiness deems sufficient per tenant thresholds.
  - Asset write‑back has executed at least once for affected applications.
  - Optional: `apps_ready_for_assessment` equals number of selected apps, and `assessment_ready=True` on flow.

## Verification Plan

- Unit tests
  - Manual submission resolves gaps and triggers write‑back (assert `Asset` fields updated and `assessment_readiness!='not_ready'`).
  - Tenant scoping enforced on questionnaire retrieval.
  - Dependency upsert on submission.

- Integration tests
  - Discovery→Collection→Manual fill→Transition→Assess, verifying 6R consumes updated `Asset` data.

- E2E tests (Playwright)
  - Adaptive Forms completion updates Progress; CTA transitions to Assess and Assess pages render with populated application data.

## Risks and Mitigations

- Over‑eager write‑back across multiple assets
  - Mitigate by requiring `asset_id` or `application_name` match and scoping by engagement/client.
- Partial submissions leading to inconsistent state
  - Track per‑questionnaire completion and restrict transition until minimums are met or agent approves.

## Conclusion

The architecture is close to the intended agentic, tenant‑scoped handoff. The main blocker is the disconnect between manual questionnaire submissions and the gap‑resolution/write‑back pipeline that Assessment depends on. Implementing the above fixes will make Collection reliably prepare each application for high‑quality Assessment and 6R treatment.
