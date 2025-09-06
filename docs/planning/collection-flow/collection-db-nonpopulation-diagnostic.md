# Collection Flow DB Non‑Population Diagnostic (Post‑PR 331)

## Executive Summary

After executing the implementation plan from `collection-preparedness-audit.md`, the following tables remain empty during the Collection flow:
- `migration.collection_gap_analysis`
- `migration.collection_flow_applications`
- `migration.collected_data_inventory`

Root causes identified:
- Phase execution mismatch: the trigger uses `GAP_ANALYSIS` but the configured phase name is `gap_analysis`, preventing MFO from executing the intended phase.
- Missing child flow context: gap summary population depends on `flow_context.collection_flow_id`, which is not set in some executions, so `collection_gap_analysis` is skipped.
- Skipping automated collection: starting the flow at gap analysis bypasses the post‑handler that writes to `collected_data_inventory`.
- Application linking path may not be exercised (or fails silently) when deduplication/canonical creation does not run; verification logging and commits need confirmation.

## Symptoms

- Application selection succeeds and UI navigates to Adaptive Forms, but no rows in:
  - `migration.collection_gap_analysis`
  - `migration.collection_flow_applications`
  - `migration.collected_data_inventory`

## Expected Write Paths (Code‑Grounded)

- Gap analysis summary insertion (writes `collection_gap_analysis`):
```20:206:backend/app/services/gap_analysis_summary_service.py
            # Use atomic transaction pattern
            await self.db.flush()

            logger.info(
                f"Gap analysis summary: {len(critical_gaps)} critical gaps, "
                f"{len(optional_gaps)} optional gaps, "
                f"{completeness_percentage}% complete"
            )

            return gap_summary
```
- Handler invoking summary population (requires `collection_flow_id` in context):
```120:160:backend/app/services/crewai_flows/unified_collection_flow_modules/phase_handlers/gap_analysis_handler.py
# NEW: Populate gap analysis summary table
summary_service = GapAnalysisSummaryService(db)
...
collection_flow_id = getattr(self.flow_context, "collection_flow_id", None)
if collection_flow_id:
    await summary_service.populate_gap_analysis_summary(
        collection_flow_id=collection_flow_id,
        gap_results=state.gap_analysis_results,
        context=context,
    )
    await db.flush()
```
- Collected data inventory write (post‑handler of automated collection):
```68:83:backend/app/services/flow_configs/collection_handlers/data_handlers.py
# Insert into collected_data_inventory
insert_query = """
    INSERT INTO collected_data_inventory
    (id, collection_flow_id, platform, collection_method, raw_data,
     normalized_data, data_type, resource_count, quality_score,
     validation_status, metadata, collected_at)
    VALUES
    (:id, :collection_flow_id, :platform, :collection_method, :raw_data::jsonb,
     :normalized_data::jsonb, :data_type, :resource_count, :quality_score,
     :validation_status, :metadata::jsonb, :collected_at)
"""
await db.execute(insert_query, inventory_data)
await db.commit()
```
- Application selection linking (`collection_flow_applications`):
```65:109:backend/app/services/application_deduplication/canonical_operations.py
# Create new link
new_link = CollectionFlowApplication(
    collection_flow_id=collection_flow_id,
    canonical_application_id=canonical_app.id,
    name_variant_id=variant.id if variant else None,
    application_name=original_name,
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    deduplication_method=(variant.match_method if variant else MatchMethod.EXACT.value),
    match_confidence=variant.match_confidence if variant else 1.0,
)

db.add(new_link)
return new_link
```

## Findings

1) Phase name mismatch blocks gap analysis execution
- Trigger on application selection calls:
```271:274:backend/app/api/v1/endpoints/collection_applications.py
execution_result = await orchestrator.execute_phase(
    flow_id=str(collection_flow.master_flow_id),
    phase_name="GAP_ANALYSIS",
)
```
- Configured phase name is lowercase:
```26:39:backend/app/services/flow_configs/collection_phases/gap_analysis_phase.py
return PhaseConfig(
    name="gap_analysis",
    ...
    pre_handlers=["gap_analysis_preparation"],
    post_handlers=["gap_prioritization"],
)
```
- The execution engine looks up the phase by exact name; mismatch likely results in "Phase not found" and skips handlers/crew.

2) `collection_flow_id` missing in flow context during gap analysis
- `GapAnalysisHandler` requires `self.flow_context.collection_flow_id` to populate `collection_gap_analysis`. If flow context is only master‑flow‑aware and does not set the child collection flow ID, summary insertion is skipped. The handler logs a warning and continues.

3) `collected_data_inventory` is only written by automated collection post‑handler
- Current UX often starts Collection at gap analysis (per plan). Without executing automated collection phase (and its post‑handler `collection_data_normalization`), nothing writes to `collected_data_inventory`.
- There is a `CollectedDataInventoryService`, but it isn’t invoked on app selection or manual submission paths.

4) `collection_flow_applications` link not created in some paths
- The dedup service creates links when it creates a new canonical app or when explicitly asked via `create_collection_flow_link`. The application selection endpoint sets `selected_application_ids` but relies on dedup processing loop to create links; if any earlier validation fails or canonical path isn’t reached, links may not be added.
- The endpoint commits before triggering MFO; but lack of detailed logging for link creation makes silent failures hard to detect.

## Why tables are empty (Cause map)

- `collection_gap_analysis`: Due to phase name mismatch, the gap phase never runs; and even when it runs in other flows, missing `collection_flow_id` in context prevents summary insertion.
- `collected_data_inventory`: Bypassed because automated collection is not executed; normalization handler (the only writer) never runs.
- `collection_flow_applications`: Dedup/linking may not execute successfully or lacks visibility; needs explicit, tenant‑scoped insert with clear logs and commit.

## Remediation Plan

1) Fix phase trigger name
- Change `phase_name` to `"gap_analysis"` when calling MFO in `update_flow_applications`.
- Alternatively, teach `MasterFlowOrchestrator.execute_phase` to case‑normalize or alias known phases.

2) Ensure `collection_flow_id` is available to handlers
- When executing collection phases through MFO, set `flow_context.collection_flow_id` by resolving child record via `master_flow_id → collection_flows.id`.
- Add a fallback in `GapAnalysisHandler` to resolve the collection flow via DB using the master flow ID if `collection_flow_id` is missing.

3) Populate `collected_data_inventory` when starting at gap analysis
- Option A: Run automated collection phase (or its post‑handler) before gap analysis if inventory is empty.
- Option B: On application selection, call `CollectedDataInventoryService.populate_collected_data` with a bootstrap record per selected application (platform=`"manual"`, data_type=`"application_selection"`) to seed inventory.

4) Make `collection_flow_applications` write explicit and observable
- In the application selection loop, explicitly call `create_collection_flow_link` for each selected application name (or asset) and log the created link ID; ensure a final `await db.commit()` after link creation (already present, verify success paths).
- Add tenant‑scoped query or test endpoint to list `collection_flow_applications` for the flow to validate writes in E2E.

5) Add diagnostics and guards
- After MFO phase execution returns, check result status; if failed or phase not found, return a 500 with clear detail to surface issues in the UI.
- In `GapAnalysisHandler`, log when `collection_flow_id` is missing and include the `master_flow_id` to ease tracing; attempt fallback resolution.

## Verification Checklist

- Application selection:
  - `migration.collection_flow_applications` includes one row per app with correct tenant fields.
- Phase execution:
  - `execute_phase('gap_analysis')` returns `status=completed`.
  - `migration.collection_gap_analysis` has a row for the collection flow with completeness and gap counts.
- Inventory seeding (if Option B chosen):
  - `migration.collected_data_inventory` has at least one record per selected application, with `collection_method='manual'` and `data_type='application_selection'`.

## SQL Snippets (tenant‑scoped)

- Check links:
```sql
SELECT id, application_name, canonical_application_id
FROM migration.collection_flow_applications
WHERE collection_flow_id = :flow_id
  AND client_account_id = :client
  AND engagement_id = :engagement;
```
- Check gap summary:
```sql
SELECT completeness_percentage, jsonb_array_length(critical_gaps) AS critical
FROM migration.collection_gap_analysis
WHERE collection_flow_id = :flow_id
  AND client_account_id = :client
  AND engagement_id = :engagement;
```
- Check inventory:
```sql
SELECT platform, data_type, resource_count
FROM collected_data_inventory
WHERE collection_flow_id = :flow_id;
```

## Risk & Rollout

- Low risk; changes are additive and targeted.
- Roll out phase name fix and context propagation first; validate DB writes via the above queries.
- Then evaluate Option A vs B for inventory population based on UX decisions.


