## Feature: Master Flow State Enrichment and Writer Fixes

### Summary
Enrich the master flow table `crewai_flow_state_extensions` with reliable, lightweight orchestration data while keeping heavy, phase-specific data in child flows (e.g., `discovery_flows.crewai_state_data`). Fix broken writers and add targeted repository APIs so key JSONB fields in the master table are consistently populated: `flow_persistence_data`, `flow_metadata`, `phase_transitions`, `phase_execution_times`, `agent_collaboration_log`, `agent_performance_metrics`, `memory_usage_metrics`, `error_history`, `retry_count`.

This plan preserves the two-table design (master + child) and leverages the secure Redis cache already in use. It focuses on correctness, observability, and minimal risk changes.

### Background (Current State)
- Master writes are limited to status and occasional persistence/metadata merges.
- Most detailed state persists to `discovery_flows.crewai_state_data` and secure Redis.
- Several master JSONB fields remain empty because:
  - Progress tracker persists to a non-existent repository and calls a method with mismatched signature, so metadata updates never land.
  - There are no repository methods that write to analytics fields (phase transitions, timings, collaboration, performance, memory, errors, retries).
- Two-table design is intentional (see `docs/analysis/Notes/000-lessons.md`). We keep it.

### Goals
- Populate master-level orchestration fields reliably without duplicating heavy payloads.
- Fix broken writers and standardize update pathways.
- Expose clear repository APIs for master JSONB updates.
- Keep child flows as the source for phase-heavy data; store summaries/indices in master.

### Non-goals
- No schema changes; use existing JSONB fields.
- No change to multi-tenant scoping or two-table pattern.

### High-level Architecture
- Master (`crewai_flow_state_extensions`): orchestration status, summaries, analytics, recent transitions, last progress snapshot, small metadata.
- Child (`discovery_flows.crewai_state_data`): detailed phase results and large agent outputs.
- Cache: encrypted snapshots and checkpoints via `PostgresFlowStateStore` + `SecureCache`.

### Feature Flag
- `MASTER_STATE_ENRICHMENT_ENABLED` (default: true). When false, enrichment calls no-op while fixes to broken writers (correctness) still apply.

---

## Implementation Plan

### 1) Fix Progress Writer
- File: `backend/app/services/crewai_flows/flow_progress_tracker.py`
- Problems:
  - Imports `MasterFlowRepository` (does not exist).
  - Calls `PostgresFlowStateStore.update_flow_status` with unsupported args (`current_phase`, `metadata`).

- Edits:
  - Replace nonexistent repo with `CrewAIFlowStateExtensionsRepository`.
  - Either:
    - A) Extend `PostgresFlowStateStore.update_flow_status` to accept optional `current_phase` and `metadata`, or
    - B) Call `master_repo.update_flow_status(...)` for metadata and keep `store.update_flow_status(flow_id, status)` for status only.

- Recommended approach (B - minimal surface change):
  - In `_persist_progress_to_database`:
    - Instantiate `CrewAIFlowStateExtensionsRepository` with context.
    - Call `await repo.update_flow_status(flow_id=self.flow_id, status=progress_data.get("workflow_status", "processing"), metadata={"progress_data": progress_data, "is_processing": progress_data.get("is_processing"), "awaiting_user_approval": progress_data.get("awaiting_user_input")})`.
    - Remove the invalid `current_phase` arg or push it via `metadata` or add `phase_transitions` (see Section 2) when phase changes.

### 2) Add Master Repository APIs for Analytics Fields
- File: `backend/app/repositories/crewai_flow_state_extensions_repository.py`
- Add methods (merge into JSONB and cap list sizes):
  - `async def add_phase_transition(self, flow_id: str, phase: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> None`
  - `async def record_phase_execution_time(self, flow_id: str, phase: str, execution_time_ms: float) -> None`
  - `async def append_agent_collaboration(self, flow_id: str, entry: Dict[str, Any]) -> None` (keep last 100)
  - `async def update_memory_usage_metrics(self, flow_id: str, metrics: Dict[str, Any]) -> None`
  - `async def update_agent_performance_metrics(self, flow_id: str, metrics: Dict[str, Any]) -> None`
  - `async def add_error_entry(self, flow_id: str, phase: str, error: str, details: Optional[Dict[str, Any]] = None) -> None` (keep last 100)
  - `async def increment_retry_count(self, flow_id: str) -> None`
  - `async def update_flow_metadata(self, flow_id: str, metadata_updates: Dict[str, Any]) -> None` (merge into `flow_metadata`)

- Implementation notes:
  - Reuse `_ensure_json_serializable` utility to sanitize payloads.
  - Select flow by `flow_id`, `client_account_id`, `engagement_id`, then JSON-merge and `update(...)`.
  - Guard with feature flag: skip enrich writes when `MASTER_STATE_ENRICHMENT_ENABLED=false`.

### 3) Wire Enrichment Calls from Orchestration and Phase Execution
- Files:
  - `backend/app/services/flow_orchestration/execution_engine_initialization.py`
  - `backend/app/services/crewai_flows/unified_discovery_flow/*` (phase handlers/flow_finalization)
  - `backend/app/repositories/discovery_flow_repository/commands/flow_commands.py`

- Where to call:
  - On phase start: `add_phase_transition(phase, status="processing")`.
  - On phase end: `add_phase_transition(phase, status="completed")` and `record_phase_execution_time(phase, ms)`.
  - When agents log notable actions: `append_agent_collaboration(entry)`.
  - On errors: `add_error_entry(phase, error, details)` and optional `increment_retry_count()` when retried.
  - When progress tracker changes phase name, call `add_phase_transition` and push `progress_data` via `update_flow_metadata`.

### 4) Lightweight Performance Instrumentation
- Files:
  - `backend/app/services/crewai_flows/unified_discovery_flow/phase_handlers.py`
  - `backend/app/services/crewai_flows/unified_discovery_flow/flow_finalization.py`

- Add timing around each phase execution and persist via `record_phase_execution_time(...)`.
  - Keep only totals per phase in master; detailed metrics remain in logs or child state.

### 5) Backfill Script (Optional but Recommended)
- File (NEW): `backend/scripts/maintenance/backfill_master_state_from_child.py`
- Functionality:
  - For recent flows, read `discovery_flows.crewai_state_data` and synthesize:
    - Last known `current_phase`, completion flags, and rough timings if present.
    - A compact `progress_snapshot` → write to `flow_metadata`.
    - A set of `phase_transitions` based on observed phase order.
  - Cap sizes and avoid heavy payloads.

### 6) Tests
- Add or extend tests:
  - `tests/backend/flows/test_master_flow_enrichment.py` (NEW)
    - Creates a flow → simulates phase start/end → asserts master `phase_transitions`, `phase_execution_times` populated.
    - Appends collaboration entries and errors → asserts caps and merges.
    - Validates progress tracker writes master metadata (fix regression from broken writer).
  - Update existing E2E where appropriate to assert presence of master summaries alongside child state.

### 7) API/Status Consumers
- Ensure status endpoints prefer master summaries for top-level views and optionally include a small `child_flow_status` projection (already supported in `FlowStatusManager`).

---

## File-by-File Edit Checklist

1) `backend/app/services/crewai_flows/flow_progress_tracker.py`
- Replace nonexistent `MasterFlowRepository` import with `CrewAIFlowStateExtensionsRepository`.
- In `_persist_progress_to_database`:
  - Instantiate `CrewAIFlowStateExtensionsRepository(db, context.client_account_id, context.engagement_id, context.user_id)`.
  - Call `update_flow_status(flow_id, status, metadata=...)` (no `current_phase` arg).
  - Optionally detect phase change to call `add_phase_transition`.

2) `backend/app/repositories/crewai_flow_state_extensions_repository.py`
- Add enrichment methods listed in Section 2.
- Reuse `_ensure_json_serializable` and enforce caps (e.g., keep last 100 transitions/errors/collaboration entries).

3) `backend/app/services/flow_orchestration/execution_engine_initialization.py`
- After initialization handler returns, call `add_phase_transition("initialization", "completed", metadata=init_result_summary)`.
- In `_start_*_flow_background` routines, before execution: add `processing` transition; on completion: add `completed` transition and record timing.

4) `backend/app/repositories/discovery_flow_repository/commands/flow_commands.py`
- In `update_phase_completion`:
  - After DB update, call master repo:
    - `add_phase_transition(phase, "completed")`
    - Optionally `record_phase_execution_time(...)` if duration available.

5) (Optional) `backend/app/services/crewai_flows/persistence/postgres_store.py`
- No signature changes required with approach (B). If preferred, add optional `current_phase`/`metadata` args and write to `flow_configuration`/`flow_metadata` safely.

---

## Acceptance Criteria
- When a discovery flow runs:
  - Master record has:
    - `flow_status` reflecting lifecycle transitions (initialized → processing → completed/failed/paused).
    - `flow_persistence_data.current_phase` updated by store saves.
    - `phase_transitions` includes at least one `processing` and one `completed` per executed phase.
    - `phase_execution_times[phase].execution_time_ms` recorded for executed phases.
    - `flow_metadata.last_progress_update` contains the latest snapshot written by the progress tracker.
    - `agent_collaboration_log` has capped recent entries when agents report activities.
    - `error_history` grows on failures; `retry_count` increments on retries.
- Listing/status endpoints return master summaries; child projections remain accessible for details.

### Example DB Checks (read-only)
```sql
-- Verify master orchestration data is populated
SELECT flow_status, flow_persistence_data->>'current_phase' AS current_phase,
       jsonb_array_length(flow_metadata->'phase_transitions') AS transitions_count,
       jsonb_object_keys(phase_execution_times) AS phases_timed
FROM migration.crewai_flow_state_extensions
WHERE flow_id = :flow_id::uuid AND client_account_id = :client::uuid;

-- Confirm child has detailed payloads
SELECT progress_percentage, current_phase,
       jsonb_typeof(crewai_state_data) AS state_type
FROM migration.discovery_flows
WHERE flow_id = :flow_id::uuid AND client_account_id = :client::uuid;
```

---

## Rollout & Risk Management
- Rollout behind `MASTER_STATE_ENRICHMENT_ENABLED`.
- Caps on arrays (transitions, errors, collaboration) to control JSON growth.
- Strict JSON serialization via shared utility.
- No schema migration; zero-downtime rollout.

## Dev/QA Notes
- Run tests in Docker containers per project rules:
```bash
docker-compose up -d --build
docker exec -it migration_backend python -m pytest tests/
```

---

## Task Breakdown (for coding agents)

1) Progress tracker fixes (1 dev hour)
- Edit `flow_progress_tracker.py`: replace import, fix `_persist_progress_to_database` to call master repo with `metadata` only.

2) Repository enrichment methods (3-4 dev hours)
- Add methods to `crewai_flow_state_extensions_repository.py` with serialization and caps.

3) Wire calls from flow orchestration (2-3 dev hours)
- Add transitions/timings/errors/collab writes in init/background execution and phase handlers.

4) Tests (2 dev hours)
- Add `test_master_flow_enrichment.py` with assertions for populated master fields.

5) Optional backfill (2 dev hours)
- Create `scripts/maintenance/backfill_master_state_from_child.py` and validate on a sample dataset.

---

## References
- `backend/app/models/crewai_flow_state_extensions.py`
- `backend/app/repositories/crewai_flow_state_extensions_repository.py`
- `backend/app/repositories/discovery_flow_repository/commands/flow_commands.py`
- `backend/app/services/crewai_flows/persistence/postgres_store.py`
- `backend/app/services/flow_orchestration/execution_engine_initialization.py`
- `docs/analysis/Notes/000-lessons.md` (two-table pattern)



