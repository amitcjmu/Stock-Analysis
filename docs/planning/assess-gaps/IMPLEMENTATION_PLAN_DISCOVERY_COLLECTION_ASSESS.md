### Implementation Plan: Discovery → Collection → Assess bridge (UX + backend)

Objectives
- Make the post-Discovery path unambiguous: users land in Collection Progress with a valid flow id.
- Replace mock metrics with real data and readiness gating.
- Enable one-click transition to Assessment when minimums are met.
 - Clearly position the step as intelligent automation, not extra manual work.

Key tasks
1) Ensure-or-create Collection Flow API (backend)
   - Endpoint: POST /api/v1/collection/flows/ensure
   - Input: none (tenant context headers used)
   - Behavior: find active collection flow for engagement; if missing, create via MFO; return collection_flow_id
   - Use within `useDependencyNavigation` and in Assess Overview.

2) Collection Progress: remove mock metrics (frontend)
   - Replace time spent/remaining with values from collection_flow state
   - If unavailable, hide the chips; do not show placeholders
   - Keep readiness polling with backoff and partial rendering on errors

3) Assess Overview: unified entry (frontend)
   - On mount, call ensure-or-create to get collection_flow_id
   - Fetch readiness; if thresholds fail, show banner with button back to Collection Progress
   - If thresholds pass, enable “Start Assessment” → POST /api/v1/assessment-flow/initialize with ready app ids → navigate to `/assessment/{flowId}/architecture`

4) Guard deep Assess routes (frontend)
   - If `flowId` missing/invalid or SSE not ready, redirect to `/assess/overview`
   - Remove direct links in sidebar to deep routes unless an assessment flow is active

5) DataFlowValidator extension (backend)
   - Add: architecture_minimums_present, missing_fields, readiness_score
   - Derive from Asset fields updated by Collection write-backs
   - Expose in readiness response

6) Failure journal (backend)
   - Record write-back failures and readiness computation errors with replay support

7) Indexing (DB)
   - Add indexes on assets: (client_account_id, engagement_id, assessment_readiness), discovery_status

8) UX copy and indicators (frontend)
   - Collection Progress banner: "Intelligent gap analysis in progress"; describe that AI is enriching data automatically
   - Auto-transition toast: "AI has identified readiness for assessment"
   - CTA labels: "Start AI-powered assessment"
   - Progress indicators distinguish "AI analyzing gaps" vs. "manual input required" sections

9) Business metrics & monitoring (backend + frontend)
   - Track median time from Discovery completion → Assessment initialization
   - Questionnaire completion rate and abandonment points
   - Assessment success rate (completion without manual corrections)
   - Operational alerts: readiness poll failures, performance degradation on readiness query, high abandonment

10) Customer validation (process)
   - Schedule 2–3 validation sessions after Phase 0; collect feedback on messaging and flow friction
   - Feed insights into copy/threshold tweaks

11) AI enablement (Phase 1, behind flags)
   - Enable existing gap analysis and questionnaire generator agents
   - Include confidence scores and surfaced insights in readiness response
   - Adaptive questionnaire generation based on detected gaps

Feature flags
- FEATURES.UI.ASSESS_GATING_ENABLED
- FEATURES.COLLECTION.WRITE_BACK_ENABLED
- FEATURES.ASSESSMENT.UNIFIED_FLOW_ENABLED

Success criteria
- After Dependencies, users land on Collection Progress with valid data
- Readiness summary renders without 500-looping; mock metrics removed
- From Assess Overview, “Start Assessment” initializes flow only when ready
- Deep Assess pages never throw initialization errors
 - Business outcomes visible: time-to-assessment < 2 days (median); questionnaire completion ≥ 80%; assessment success ≥ 95%


