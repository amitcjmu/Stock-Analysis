## Collection Flow – Adaptive Forms: Root Cause Issues and Fix Plan

### Executive Summary

When a user navigates to Collection → Adaptive Forms and starts a new workload without selecting an application, the system fails to generate any questionnaire. The current wiring between frontend and backend enforces application selection elsewhere, rather than prompting within the adaptive questionnaire. Multiple contract mismatches and fallback gaps prevent a graceful experience.

This report documents the precise issues found across frontend and backend, with concrete file references and a prioritized fix plan to make the flow intelligent even when no application is preselected.

---

### Reproduction (Observed Behavior)

1) Navigate to Collection → Adaptive Forms without `applicationId` in the URL.
2) A collection flow is created and executed.
3) No questionnaires are returned; frontend often redirects to discovery inventory selection or shows a loading/error state. The adaptive form never renders a prompt to choose an application.

---

### Frontend Issues

- Application selection redirect prevents adaptive prompting
  - File: `src/pages/collection/AdaptiveForms.tsx`
  - Logic: `hasApplicationsSelected` detects missing apps and triggers redirect to inventory for NEW flows.
  - Impact: The UI never shows an initial questionnaire that asks the user to select an application.
  - Reference snippet:
```28:438:/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/pages/collection/AdaptiveForms.tsx
// ... existing code ...
if (!hasApps && !isExistingFlowContinuation && !hasProgressed) {
  // Redirect to inventory
  navigate(`/discovery/inventory?collectionFlowId=${activeFlowId}`, { replace: true, ... })
}
// ... existing code ...
```

- Config key mismatch when creating a flow
  - File: `src/hooks/collection/useAdaptiveFormFlow.ts`
  - Creation payload uses `collection_config.application_id`:
```1:633:/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/hooks/collection/useAdaptiveFormFlow.ts
// ... existing code ...
const flowData = {
  automation_tier: 'tier_2',
  collection_config: {
    form_type: 'adaptive_data_collection',
    application_id: applicationId,
    collection_method: 'manual_adaptive_form'
  }
}
// ... existing code ...
```
  - Backend and serializers look for `selected_application_ids` (or equivalent) to consider apps selected. The UI’s `hasApplicationsSelected` also checks `selected_application_ids | applications | application_ids | has_applications`.
  - Result: Even after flow creation, the system considers the flow as having no applications selected.

- Questionnaire fallback logic is incomplete (crashes on empty list)
  - File: `src/hooks/collection/useAdaptiveFormFlow.ts`
  - After timeout with 0 questionnaires, code logs a fallback but still attempts to convert `agentQuestionnaires[0]`, which is undefined.
  - Reference snippet:
```1:633:/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/hooks/collection/useAdaptiveFormFlow.ts
// ... existing code ...
if (agentQuestionnaires.length === 0) {
  console.warn('⚠️ No questionnaires generated after timeout. Using fallback.');
}
// Immediately after, attempts to convert index 0 (undefined):
adaptiveFormData = convertQuestionnairesToFormData(agentQuestionnaires[0], applicationId);
// ... existing code ...
```
  - There is a ready helper `createFallbackFormData()` in `src/utils/collection/formDataTransformation.ts` that is never invoked here.

- Hard redirect on 422 prevents graceful in-page prompting
  - File: `src/services/api/collection-flow.ts`
  - Endpoint `getFlowQuestionnaires()` catches 422 with `error: 'no_applications_selected'` and forces `window.location.href = '/discovery/cmdb-import'`.
  - Impact: The UI cannot show an in-form application selector; the user is kicked to another page.
  - Reference snippet:
```1:370:/Users/chocka/CursorProjects/migrate-ui-orchestrator/src/services/api/collection-flow.ts
// ... existing code ...
if (status === 422 && errorCode === 'no_applications_selected') {
  window.location.href = '/discovery/cmdb-import';
  return new Promise(() => {});
}
// ... existing code ...
```

- Potential type/contract confusion in submit payload (non-blocking)
  - File: `src/services/api/collection-flow.ts`
  - Method types suggest `QuestionnaireResponse[]` while actual call submits a richer object with metadata and validation. Backend accepts any dict, so this works at runtime but is misleading for maintainers.

---

### Backend Issues

- Hard requirement for existing applications blocks questionnaire generation
  - File: `backend/app/api/v1/endpoints/collection_crud_questionnaires.py`
  - If no application assets exist for the engagement, the endpoint raises 422 `no_applications_selected` instead of returning a minimal questionnaire that asks for application selection.
  - Reference snippet:
```1:223:/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend/app/api/v1/endpoints/collection_crud_questionnaires.py
// ... existing code ...
if not has_applications:
  raise HTTPException(
    status_code=422,
    detail={
      'error': 'no_applications_selected',
      'message': 'No applications have been discovered or selected ...'
    },
  )
// ... existing code ...
```
  - This directly contradicts the desired behavior.

- Data shape mismatch when saving generated questionnaires (results lost)
  - File: `backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/questionnaire_generation_handler.py`
    calls generator → returns a list of section-level questionnaire dicts (top-level `questions` array per item).
  - File: `backend/app/services/crewai_flows/unified_collection_flow_modules/flow_utilities.py`
    `save_questionnaires_to_db()` expects nested shape under `questionnaire.metadata`, `questionnaire.sections`, etc. It then extracts `sections` to compute questions, which will be empty for the current generator output.
  - Impact: Saved `AdaptiveQuestionnaire` can end up missing questions or metadata, causing downstream fetches to return incomplete/empty questionnaires.

- Generator not provided `collection_flow_id`
  - File: `questionnaire_generation_handler.py`
  - Calls `self.services.questionnaire_generator.generate_questionnaires(...)` without `collection_flow_id`. The generator logs and packages metadata based on this ID; omitting it reduces traceability and may affect persistence logic if later added.

- Strict skip logic on zero gaps
  - File: `questionnaire_generation_handler.py`
  - If `gaps_identified == 0` or tier is TIER_1, phase returns `None` (skip). For new flows without context, this can preclude generating an initial prompting questionnaire.

---

### Contract and Model Inconsistencies

- Frontend creation payload vs backend expectations
  - Frontend uses `collection_config.application_id`.
  - Backend and serializers use `selected_application_ids` (and UI checks those keys to decide if apps are selected).

- Questionnaire structure across layers
  - Generator returns simplified per-section questionnaire dicts (top-level `questions`).
  - DB save utility expects nested `questionnaire.{metadata, sections, ...}`.
  - API schema `AdaptiveQuestionnaireResponse` expects `questions: List[Dict[str, Any]]` which aligns with a flattened top-level list; saving code should populate this reliably.

---

### Root Causes Mapped to Symptoms

- No questionnaire shown without preselected application
  - Caused by: Frontend redirect (`AdaptiveForms.tsx`) + backend 422 guard + missing fallback usage in hook + config key mismatch preventing system from recognizing app selection.

- Questionnaires never appear after execution
  - Caused by: Saving mismatch in `save_questionnaires_to_db()` (questions extracted from `sections` that don’t exist in the provided shape), resulting in empty/incomplete DB records.

- Infinite waiting / timeout → then crash on conversion
  - Caused by: Attempt to convert `agentQuestionnaires[0]` when list is empty; fallback not actually used.

---

### Recommended Fix Plan (Prioritized)

1) Implement in-form application selection fallback (Backend first)
  - In `collection_crud_questionnaires.get_adaptive_questionnaires()`, when no applications exist, return a minimal `AdaptiveQuestionnaireResponse` with a single section asking the user to choose one or more applications from inventory (backend can populate options from `Asset` records if present, or leave empty and let frontend fetch options).
  - Do not raise 422; instead, set `completion_status: 'pending'` and a clear description.

2) Align frontend creation payload and selected app detection
  - Update `useAdaptiveFormFlow.ts` flow creation to set `selected_application_ids: []` initially (or omit), and ensure subsequent updates when user selects apps in-form.
  - Update `hasApplicationsSelected` to also respect a new `pending_application_selection` marker if we choose to introduce it, avoiding immediate redirects.

3) Fix questionnaire persistence shape
  - Update `save_questionnaires_to_db()` to accept the generator’s current top-level format (`{ id, title, questions, ... }`).
  - Populate `AdaptiveQuestionnaire.questions` directly from the provided `questions` array when `sections` are not present.
  - Populate metadata fields (title, description, version) defensively from either nested `questionnaire.metadata` or top-level keys.

4) Actually use the fallback form on timeout
  - In `useAdaptiveFormFlow.ts`, when `agentQuestionnaires.length === 0` after max attempts, call `createFallbackFormData(applicationId)` instead of indexing `[0]`.
  - Render that fallback form so the user can start by entering basic app details.

5) Remove hard navigation on 422
  - In `collection-flow.ts` API client, replace the forced `window.location.href` with a rejected promise containing a sentinel error code that the page can handle by displaying the in-form application selection questionnaire.

6) Pass `collection_flow_id` to generator
  - Add `collection_flow_id=state.flow_id` in `questionnaire_generation_handler.generate_questionnaires()` calls to improve traceability.

7) Revisit skip logic for zero gaps
  - Allow generation of an initial “bootstrap” questionnaire even if `gaps_identified == 0` so users can supply minimal context (application selection, basic details) to kickstart gap analysis.

---

### Acceptance Criteria for the Fix

- Visiting Adaptive Forms with no `applicationId` and no existing applications shows an in-form selection questionnaire instead of a redirect.
- If generator fails or times out, a fallback form renders with at least “Application Name” and “Application Type,” and submission records the initial context to continue the flow.
- Questionnaires saved in DB have non-empty `questions` and align with `AdaptiveQuestionnaireResponse`.
- Creating a new flow does not immediately redirect; subsequent fetches of questionnaires do not raise 422.

---

### Post-Fix Validation Checklist

- Frontend
  - New flow creation without `applicationId` renders a form that includes application selection.
  - Fallback form renders after timeout with zero questionnaires and submits successfully.
  - No hard redirects occur on `getFlowQuestionnaires`.

- Backend
  - `GET /collection/flows/{flow_id}/questionnaires` returns a minimal questionnaire when no apps exist.
  - Saved `AdaptiveQuestionnaire` rows include populated `questions`.
  - `questionnaire_generation_handler` passes `collection_flow_id` to generator.

---

### References

- Frontend
  - `src/pages/collection/AdaptiveForms.tsx`
  - `src/hooks/collection/useAdaptiveFormFlow.ts`
  - `src/services/api/collection-flow.ts`
  - `src/utils/collection/formDataTransformation.ts`

- Backend
  - `backend/app/api/v1/endpoints/collection_crud_questionnaires.py`
  - `backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/questionnaire_generation_handler.py`
  - `backend/app/services/crewai_flows/unified_collection_flow_modules/flow_utilities.py`
  - `backend/app/services/ai_analysis/questionnaire_generator.py`
  - `backend/app/models/collection_flow.py`
  - `backend/app/api/v1/endpoints/collection.py`



