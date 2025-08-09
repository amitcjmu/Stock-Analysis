### Implementation Plan: Discovery → Collection → Assess bridge (UX + backend)

Objectives
- Make the post-Discovery path unambiguous: users land in Collection Progress with a valid flow id.
- Replace mock metrics with real data and readiness gating.
- Enable one-click transition to Assessment when minimums are met.

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

Feature flags
- FEATURES.UI.ASSESS_GATING_ENABLED
- FEATURES.COLLECTION.WRITE_BACK_ENABLED
- FEATURES.ASSESSMENT.UNIFIED_FLOW_ENABLED

Success criteria
- After Dependencies, users land on Collection Progress with valid data
- Readiness summary renders without 500-looping; mock metrics removed
- From Assess Overview, “Start Assessment” initializes flow only when ready
- Deep Assess pages never throw initialization errors


