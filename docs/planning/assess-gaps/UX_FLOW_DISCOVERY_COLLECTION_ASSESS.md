### Discovery → Collection → Assess UX flow (code-grounded)

This document maps the practical analyst journey in the current codebase and proposes small, surgical improvements to get from CMDB-import Discovery to 6R Assess with the fewest clicks and least friction.

### Current realities in code
- Master Flow Orchestrator (MFO) is the source of truth for all flows (`backend/app/api/v1/flows.py`, `app/services/master_flow_orchestrator/*`).
- Discovery is hybrid. Some legacy pages still call older endpoints, but the intent is to drive flows via MFO.
- Collection endpoints exist and already integrate with MFO and the DataFlowValidator (`backend/app/api/v1/endpoints/collection.py`). Readiness summary is exposed at `GET /api/v1/collection/flows/{flow_id}/readiness`.
- Assessment exists as pages and a hook (`src/pages/assessment/*`, `src/hooks/useAssessmentFlow`), plus a CrewAI implementation (`backend/app/services/crewai_flows/unified_assessment_flow.py`) and service (`unified_assessment_flow_service.py`). The UI must initialize the assessment flow before visiting deep pages like Tech Debt.

### Primary user journeys
1) Guided path (recommended)
   - User completes CMDB import and runs Discovery Inventory + Dependencies.
   - On “Continue”, navigation goes to `/collection/progress?flowId={discoveryMasterFlowId}` (already wired in `useDependencyNavigation`).
   - The Progress page auto-polls readiness via `GET /api/v1/collection/flows/{id}/readiness` and shows an “Assessment Readiness” summary.
   - When thresholds pass, show a prominent “Start AI-powered assessment” button. Clicking initializes assessment with ready apps and navigates to Assess Overview.

2) Jump-in from Assess
   - Visiting `/assess/overview` checks readiness by calling the same readiness endpoint for the active Collection flow (by engagement).
   - If below threshold, render a banner: “Intelligent gap analysis in progress”. Provide link back to `/collection/progress?flowId=...`; disable deep Assess pages.
   - If threshold met, render an enabled “Initialize Assessment” call-to-action.

3) Resume from Dashboard
   - The Dashboard’s “Active Flows” card lists Discovery and Collection flows. Selecting a running Collection flow routes to `/collection/progress?flowId=...` and the same gating applies.

### Route map (frontend)
- Discovery
  - `/discovery/dependencies` → on continue → `/collection/progress?flowId={flow_id}`
- Collection
  - `/collection/progress?flowId={collection_or_discovery_flow_id}`
  - Auto-refresh readiness summary and show CTA to Assessment when ready
  - Show progress indicators that separate "AI analyzing gaps" vs. "manual input required"
- Assess
  - `/assess/overview` (safe page, no SSE) — checks readiness and offers CTAs
  - `/assessment/initialize` (or unified action from Overview) — creates assessment flow
  - `/assessment/{flowId}/architecture`, `/assessment/{flowId}/tech-debt`, etc. — only after initialization

Backend contracts used
- Ensure-or-create Collection flow for engagement (proposed):
  - `POST /api/v1/collection/flows/ensure` → { collection_flow_id }
  - Behavior: if an active flow exists for the engagement, return it; else create via MFO and link to the discovery flow in metadata.
- Readiness summary (existing):
  - `GET /api/v1/collection/flows/{flow_id}/readiness` → { apps_ready_for_assessment, phase_scores, quality/confidence, issue_counts }
- Initialize Assessment with ready apps (existing pattern):
  - `POST /api/v1/assessment-flow/initialize` payload = list of app ids that have `assessment_readiness='ready'`

### State transitions (high-level)
1) Discovery (completed inventory + dependencies) → MFO marks discovery done for the engagement
2) Collection flow ensured for engagement (create if missing)
3) Collection runs ADCS phases; resolved gaps write back to `Asset`, including `assessment_readiness`
4) DataFlowValidator computes scores and returns readiness summary
5) When threshold met, Assessment becomes enabled
6) Initialize Assessment with ready apps → navigate to Assess Overview (toast: “AI has identified readiness for assessment”)

### Error handling and fallbacks
- Assess deep routes must never initialize or subscribe unless `flowId` is present and valid; otherwise redirect to `/assess/overview`.
- Readiness endpoint failures should not white-screen the UI; render partial data and continue polling with backoff.
- Collection write-backs are tenant-scoped and batched; failures go to a DB-backed failure journal with replay.

### Feature flags
- `FEATURES.COLLECTION.WRITE_BACK_ENABLED`
- `FEATURES.ASSESSMENT.UNIFIED_FLOW_ENABLED`
- `FEATURES.UI.ASSESS_GATING_ENABLED`

### Small, high-impact UX improvements
- On `/collection/progress`, replace mock “time spent/remaining” with real timestamps from flow state; hide if unknown.
- On `/assess/overview`, show a single Next Step: “Start Assessment” (enabled when ready) or “Complete Collection” (link back).
- In sidebar, keep “Tech Debt” only under Assess and guard by initialized assessment flow.
 - Copy should frame Collection as “intelligent enrichment” to reduce perceived extra work.


