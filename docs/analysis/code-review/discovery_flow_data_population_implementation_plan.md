## Implementation Plan — Discovery Flow Data Population (Close the Gaps)

Date: 2025-09-18
Related analysis: `discovery_flow_data_population_audit.md`

This document enumerates concrete edits to enforce atomic phase updates, write-through persistence of derived flags, resilient error persistence, and comprehensive population of all `migration.discovery_flows` fields. The goal is to eliminate parallel/legacy paths and short-circuits, and to converge on one authoritative write-path per phase.

---

## 1) Create transactional phase-advance helper (authoritative path)

File (new): `backend/app/services/discovery/phase_persistence_helpers.py`
- Add function:
  - `async def advance_phase(db: AsyncSession, flow: DiscoveryFlow, target_phase: str, *, set_status: Optional[str] = None, extra_updates: Optional[dict] = None) -> PhaseTransitionResult`
    - Determine prior_phase from `flow.current_phase` and validate using a state machine (see §0.5)
    - Start transaction and lock row with `SELECT ... FOR UPDATE` (tenant scoped)
    - Set completion flag for prior_phase via `PHASE_FLAG_MAP`
    - Set `flow.current_phase = target_phase`
    - If `set_status`: set child `flow.status = set_status`
    - Call `flow.update_progress()` once
    - Apply `extra_updates` if provided
    - Persist and commit; return `PhaseTransitionResult(success, was_idempotent, prior_phase, warnings)`
- Dataclass:
  - `PhaseTransitionResult(success: bool, was_idempotent: bool, prior_phase: str, warnings: list[str])`
- Add a `PHASE_FLAG_MAP` dict with canonical names: data_import, field_mapping, data_cleansing, asset_inventory, dependency_analysis, tech_debt_assessment

Edits (call this helper instead of in-line updates):
- `backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py`
  - All places that directly set `discovery_flow.current_phase` (e.g., to `asset_inventory`) should call `advance_phase_with_persistence` with `prior_phase` derived from request/flow state
- `backend/app/services/discovery/phase_transition_service.py`
  - Replace `.values(current_phase=...)` bulk updates with fetching flows and invoking the helper to atomically mark completion and phase advance
- `backend/app/services/crewai_flows/unified_discovery_flow/handlers/*`
  - Any handler that ends by advancing phase or claiming completion must use the helper
- `backend/app/services/flow_orchestration/transition_utils.py`
  - Wrap programmatic transitions to call the helper

---

## 2) Write-through persistence for derived flags

File: `backend/app/services/discovery/flow_status/data_helpers.py`
- After deriving booleans (e.g., `data_import_completed = bool(discovery_flow.data_import_id and raw_data)`), compare with stored value and persist changes:
  - If value changed: set on model, call `flow.update_progress()`, persist and commit
- Add small utility function `persist_if_changed(db, flow, **flag_updates)` to coalesce updates and perform one commit
- Use the same locked instance (no re-fetch); refresh if needed

---

## 3) Explicit completion points per phase

3.1 Data import completion
- Files:
  - `backend/app/api/v1/endpoints/data_import/handlers/field_handler.py` (and any consolidated import-complete endpoint)
  - `backend/app/services/data_import/import_validator.py`
- Changes:
  - On successful import+validation: set `flow.data_import_completed = True`, `flow.update_progress()`, commit
  - If this immediately advances to next phase, use `advance_phase_with_persistence(..., prior_phase='data_import', next_phase='field_mapping')`

3.2 Field mapping completion
- Files:
  - `backend/app/services/flow_orchestration/field_mapping_logic.py`
  - `backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py`
- Changes:
  - Ensure we set `flow.field_mapping_completed = True` when mappings meet success criteria
  - When transitioning, call phase-advance helper with `prior_phase='field_mapping'`

3.3 Data cleansing completion
- Files:
  - `backend/app/services/crewai_flows/unified_discovery_flow/handlers/data_validation_handler.py`
  - (any bespoke cleansing handlers)
- Changes:
  - Set `flow.data_cleansing_completed = True` on success and use helper to move to next phase

3.4 Asset inventory completion
- Files:
  - `backend/app/api/v1/endpoints/unified_discovery/asset_handlers.py`
  - `backend/app/services/asset_creation_bridge_service.py`
- Changes:
  - After successful asset write-back(s), set `flow.asset_inventory_completed = True`
  - On transition, use helper (`prior_phase='asset_inventory'`)

3.5 Dependency analysis and tech debt assessment completion
- Files:
  - `backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_executors.py`
  - `backend/app/services/crewai_flows/flow_state_bridge.py`
- Changes:
  - On success: set `dependency_analysis_completed` / `tech_debt_assessment_completed` and transition via helper

---

## 4) Resilient error persistence

Files:
- `backend/app/services/crewai_flows/*` (phase handlers, executors)
- `backend/app/api/v1/endpoints/unified_discovery/*` (where phase work is orchestrated)

Changes:
- Wrap phase execution in try/except blocks that persist:
  - `flow.error_message`, `flow.error_phase`, `flow.error_details` (structured error)
- Classify and set:
  - retryable (e.g., transient I/O), non_retryable (validation/data), partial (subset processed)
  - Persist `error_details` with `error_code`, `recovery_hint`
- Ensure `agent_state` and `phase_state` record partial progress even on errors

---

## 5) Populate audit / summary fields consistently

Files:
- `backend/app/services/discovery/phase_persistence_helpers.py` (the new helper)

Changes:
- When `prior_phase` set to completed, append it to `flow.phases_completed` (list semantics)
- If all completion flags are true:
  - set `flow.status = 'completed'`
  - set `flow.completed_at = now()`
  - commit

---

## 6) Update progress everywhere flags are changed

Files:
- All files listed in section 3 that set phase flags

Changes:
- Call `flow.update_progress()` before commit whenever any completion flag toggles

---

## 7) Eliminate parallel/legacy short-circuits and direct writes

Files (replace direct writes with helper usage):
- `backend/app/services/discovery/phase_transition_service.py` (replace `.values(current_phase=...)`)
- `backend/app/services/discovery_flow_service/managers/summary_manager.py` (avoid mutating flow without helper)
- `backend/app/services/discovery_flow_service/integrations/crewai_integration.py` (transition paths)
- `backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py` (all phase advances)

---

## 8) Tests to add/update

Files:
- `tests/backend/services/test_import_validator_flow_handling.py`
- `tests/backend/test_agent_service_layer.py`
- New tests for transactional helper:
  - `tests/backend/services/test_phase_persistence_helpers.py`

Scenarios:
- Advancing from import→field_mapping marks `data_import_completed = True`, updates progress, sets `current_phase='field_mapping'`
- Asset write-back sets `asset_inventory_completed = True` and transitions
- Error in phase execution persists error_message/error_phase/details and status
- All flags complete → status='completed', completed_at set

---

## 9) One-off reconciliation script (post-merge repair)

File (new): `backend/scripts/reconcile_discovery_flows.py`
- Iterate flows; infer flags from existing artifacts (imports, assets, analysis JSON)
- Only fix when: data present AND no phase errors logged AND transition valid per state machine
- Set missing flags; recompute progress; fix `current_phase`; mark completed flows where appropriate
- Default to `--dry-run`; `--apply` to persist; tenant-scoped; CSV report preview

---

## 10) PR checklist (must-haves)

- [ ] New helper added; all transition call sites use helper (no direct current_phase writes)
- [ ] Data import completion sets `data_import_completed`
- [ ] Write-through in `flow_status/data_helpers.py` for derived flags
- [ ] Error persistence standardized across handlers
- [ ] `phases_completed` appended on completion; `completed_at`/`status` set on full completion
- [ ] All changed files call `flow.update_progress()` when flags change
- [ ] Tests updated/added and passing
- [ ] Reconciliation script included with README usage notes

---

## 11) File inventory (to edit in this PR)

- New:
  - `backend/app/services/discovery/phase_persistence_helpers.py`
  - `backend/scripts/reconcile_discovery_flows.py`

- Modified (transition + persistence wiring):
  - `backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py`
  - `backend/app/api/v1/endpoints/unified_discovery/asset_handlers.py`
  - `backend/app/services/discovery/phase_transition_service.py`
  - `backend/app/services/flow_orchestration/field_mapping_logic.py`
  - `backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py`
  - `backend/app/services/crewai_flows/unified_discovery_flow/handlers/data_validation_handler.py`
  - `backend/app/services/asset_creation_bridge_service.py`
  - `backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_executors.py`
  - `backend/app/services/crewai_flows/flow_state_bridge.py`
  - `backend/app/services/discovery/flow_status/data_helpers.py`
  - `backend/app/services/discovery_flow_service/integrations/crewai_integration.py`
  - `backend/app/services/discovery_flow_service/managers/summary_manager.py`

- Tests:
  - `tests/backend/services/test_import_validator_flow_handling.py`
  - `tests/backend/test_agent_service_layer.py`
  - `tests/backend/services/test_phase_persistence_helpers.py` (new)

---

## 12) Rollout

Order:
1) Merge PR with code changes + tests
2) Run one-off reconciliation script in staging; verify
3) Run script in production (backup first)
4) Monitor flow consistency dashboards
5) Add Prometheus metrics:
   - `discovery_flow_phase_transitions_total{phase, outcome}`
   - `discovery_flow_phase_transition_duration_seconds{phase}` (histogram)
   - `discovery_flow_flag_updates_total{flag, result}`
   - `discovery_flow_consistency_violations_total{type}`
   - Alerts: invalid transitions, failure rates by phase, violations > threshold

---

## 13) Rollback strategy

- In dev: restore from last DB backup/snapshot or run reconciliation script in reverse (setting flags back to pre-change state) using CSV report
- Add a temporary feature flag to bypass helper (route through a no-op wrapper) if emergency unblock is needed
- Keep commits granular: revert helper wiring commit to restore old behavior quickly if required


