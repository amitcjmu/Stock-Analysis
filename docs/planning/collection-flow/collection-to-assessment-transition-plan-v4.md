# Collection to Assessment Transition - Remediation Plan v4

## Executive Summary

This plan removes any dependency on legacy placeholder phases ("platform_detection", "automated_collection") and makes the Collection flow explicitly questionnaire-driven for gap filling:

- Start Collection at gap analysis by default
- Generate adaptive questionnaires only for missing attributes (gaps)
- Seamlessly progress users through manual collection → readiness check → transition to Assessment
- Eliminate the infinite loop by fixing Progress → Adaptive Forms continuation and gating logic

No new databases or endpoints are required beyond what v2 already delivered. Most fixes are UI wiring plus small, low‑risk backend defaults.

## Current Pain Points

- Continue on Progress only navigates, doesn’t actually resume or fetch questionnaires
- Adaptive Forms blocks when other incomplete flows exist, even when continuing the selected flow
- 422 "no_applications_selected" breaks the UX instead of surfacing the app selection UI
- Completed flows sometimes bounce between pages instead of cleanly transitioning to Assessment

## Target Behavior (User Journey)

1) User clicks Continue on a Collection flow in Progress
2) System resumes the flow and immediately fetches questionnaires for that flow
3) If questionnaires exist → auto-navigate to `/collection/adaptive-forms?flowId={id}`
4) If 422 `no_applications_selected` → show inline application selection UI, then reattempt fetch
5) When Collection is complete and readiness passes → call transition endpoint and navigate to `/assessment/{assessment_flow_id}/architecture`

## Scope and Non-Goals

- In-scope: UI logic fixes, default start phase = gap analysis, readiness checks, transition UX
- Out-of-scope: Implementing platform detection or automated collection (kept as future phases/placeholders)
- No additional migrations; reuse v2 migration (assessment linkage)

## Backend Changes (Small, Safe)

1) Default start phase: gap analysis
- Files to modify:
  - `backend/app/api/v1/endpoints/collection_crud_commands.py` - `create_collection_flow` function
  - `backend/app/services/collection_flow/collection_flow_state_service.py` - `create_flow` method
- On flow creation, set:
  - `current_phase = 'gap_analysis'`
  - `status = CollectionFlowStatus.GAP_ANALYSIS` (snake_case value)
  - Append to `phase_state.phase_history` with a proper entry for gap analysis
- Gap analysis runs AFTER applications are selected (not on flow create)
- Gap analysis is agent-driven and async (10-45s for small sets)
- Rationale: Avoid placeholder phases; match questionnaire-first UX

2) Application selection endpoint
- File: `backend/app/api/v1/endpoints/collection_crud_commands.py`
- Endpoint: `POST /api/v1/collection/flows/{flow_id}/applications`
- Payload: `{ "selected_application_ids": [...] }`
- After selection, trigger gap analysis automatically
- Return 202 Accepted with polling location or status

3) Readiness endpoint with thresholds
- File: `backend/app/api/v1/endpoints/collection_crud_queries.py`
- Ensure `GET /api/v1/collection/flows/{flow_id}/readiness` composes data from `GapAnalysisSummaryService` and agent decisioning
- Return stable, typed fields with server-side thresholds:
  - Default thresholds: `apps_ready_for_assessment > 0`, `collection_quality_score >= 60`, `confidence_score >= 50`
  - Eventually read from engagement preferences when wired
  - Include `missing_requirements` array for clear feedback

4) Gap analysis re-run endpoint
- File: `backend/app/api/v1/endpoints/collection_crud_commands.py`
- Endpoint: `POST /api/v1/collection/flows/{flow_id}/rerun-gap-analysis`
- Re-computes gap summary and regenerates questionnaires
- Returns 202 Accepted with estimated completion time

5) Transition endpoint (from v2)
- File: `backend/app/api/v1/endpoints/collection_transition.py` (already implemented)
- No changes required; ensure proper error codes and snake_case payloads
- On partial failure (assessment created but UI fails), log both flow IDs for recovery

## Frontend Changes (Primary Remediation)

1) Progress → Continue actually resumes and routes
- File: `src/components/collection/progress/FlowDetailsCard.tsx`
- In `handleContinue`:
  - Call `await collectionFlowApi.continueFlow(flow.id)`
  - Then call `await collectionFlowApi.getFlowQuestionnaires(flow.id)`
    - If length > 0 → `navigate(`/collection/adaptive-forms?flowId=${flow.id}`)`
    - If 422 `no_applications_selected` → open app selection UI (inline or modal) and retry fetch after selection
    - Else → render a persistent inline banner "Preparing your questionnaire… This can take up to ~1–2 minutes. We'll open it automatically." with spinner and "Try again" button
    - Poll questionnaires: 2s intervals for first 30s, then 5s intervals up to 90s total
    - After 30s, update message to "Still preparing... This is taking longer than expected." with retry option
    - Auto-navigate when questionnaires arrive or show timeout error panel after 90s with "Try again" and "Return to Progress" actions

2) Adaptive Forms: unblock valid continuation and fetch on mount
- File: `src/pages/collection/AdaptiveForms.tsx`
- Fix blocking logic to allow continuation when `flowId` in URL matches any `incompleteFlows` entry
- Add `useEffect` to fetch questionnaires when `flowId` changes and page is not loading
- If `getFlowQuestionnaires` throws `code === 'no_applications_selected'`:
  - Render application selection UI inline showing ALL tenant-scoped Application assets
  - Include search/filter by name, environment, criticality
  - Pre-select any already linked to the flow
  - Minimum 1 app required, max 100 for UX (paginate if more)
  - Submit via `POST /api/v1/collection/flows/{id}/applications` with `selected_application_ids`
  - After submission, refetch questionnaires

3) Adaptive Forms state hook improvements
- File: `src/hooks/collection/useAdaptiveFormFlow.ts`
- Ensure questionnaires are fetched on mount if `flowId` exists
- Normalize error handling for 422 to set state that triggers the selection UI, not a hard failure
- Handle async gap analysis (10-45s typical) with polling feedback

4) Completed flows transition with readiness checks
- File: `src/pages/collection/Progress.tsx`
- When `status === 'completed'` or `assessment_ready === true`:
  - Show a persistent CTA panel with a primary action "Start Assessment"
  - On click, call `collectionFlowApi.transitionToAssessment(selectedFlow)` and navigate to `/assessment/{assessment_flow_id}/architecture`
  - If `error === 'not_ready'`:
    - Display missing requirements inline with specific CTAs:
      - "Complete questionnaires" → navigate to adaptive forms
      - "Re-run gap analysis" → call backend endpoint to recompute
    - Use server-provided thresholds (defaults: apps_ready > 0, quality >= 60, confidence >= 50)
  - If assessment flow created but navigation fails:
    - Show success panel with deep link to `/assessment/{flowId}/architecture`
    - Include "Open Assessment" button for recovery
    - Log flow ID for debugging

5) Multiple flow handling
- File: `src/pages/collection/Progress.tsx`
- If multiple incomplete flows exist, show flow selector (list with status/progress)
- User explicitly picks which flow to continue
- Clearly indicate selected flow and scope all actions to that flow
- No "blocked by other flows" message unless policy enforces single-flow limit

6) Persistent feedback instead of toasts-only
- For critical steps (resumed, questionnaires ready, transition success/failure), prefer persistent inline `Alert`/panel in the page layout; keep toasts as supplementary signals

## Data Model / Migrations

- No new migrations required. Reuse v2’s linkage columns (`assessment_flow_id`, `assessment_transition_date`) and continue writing handoff details to `flow_metadata.assessment_handoff`

## Telemetry & Error Handling

### Events to Emit (all tenant-scoped)
- `flow_resumed` - When continueFlow called successfully
- `questionnaires_ready` - When questionnaires fetched successfully
- `questionnaires_polling_timeout` - When polling exceeds 90s
- `application_selection_opened` - When 422 triggers selection UI
- `application_selection_submitted` - When apps selected and submitted
- `gap_analysis_started` - When gap analysis begins after app selection
- `gap_analysis_completed` - When gaps identified and questionnaires generated
- `transition_started` - When transition to assessment initiated
- `transition_succeeded` - When assessment flow created successfully
- `transition_failed` - When transition fails with reason
- `readiness_check_failed` - When not ready for assessment with missing requirements

### Error Handling
- Return structured errors (`error`, `reason`, `missing_requirements`) only; no mock data
- Log safely (no sensitive IDs in plaintext)
- Include correlation IDs for support debugging

## Testing Strategy

Unit
- `FlowDetailsCard.handleContinue` branches: questionnaires present, 422 selection, pending (poll), completed
- `useAdaptiveFormFlow` fetch on mount, 422 handling to selection UI
- Readiness endpoint stability (fields, snake_case)
- Application selection: min 1, max 100, pagination, pre-selection of linked apps
- Polling logic: 2s→30s→5s→90s intervals with proper timeout

Integration/E2E
- Continue a stuck/incomplete flow → auto-navigate to Adaptive Forms when questionnaires ready
- Continue with 422 → application selection UI (search/filter/paginate) → submit → gap analysis (10-45s) → questionnaires → Adaptive Forms
- Multiple flows → flow selector → continue selected flow only
- Completed flow with readiness (apps > 0, quality >= 60, confidence >= 50) → transition → `/assessment/{id}/architecture`
- Completed but not ready → persistent banner with CTAs ("Complete questionnaires", "Re-run gap analysis")
- Partial transition failure → success panel with deep link and "Open Assessment" button
- Polling timeout (90s) → error message with "Try again" button

## Rollout Plan

Phase A (UI wiring) – 1–2 days
- Implement Continue logic, Adaptive Forms gating, questionnaire fetch on mount, 422 selection flow

Phase B (defaults & readiness polish) – 1 day
- Default start at gap analysis on flow creation
- Minor readiness endpoint polish (if needed)

Phase C (staged release) – 1 day
- Feature flag for any risky toggles, deploy, monitor loop elimination and transition success rate

## Success Criteria

- 0 infinite loops between Progress and Adaptive Forms
- 100% of valid Continue actions either auto-navigate to Adaptive Forms or clearly communicate background progress
- 100% of completed, ready flows transition and navigate to Assessment automatically
- No user gets blocked by 422; selection UI always appears when needed

## Future Work (Out of Scope)

- Implement real platform detection and automated collection as agent-driven phases executed via MFO
- When added, keep the questionnaire-first UX intact and treat automated phases as background steps with Progress-only visibility until manual input is required






