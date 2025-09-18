## Discovery Flow Data Population Audit (Expanded)

Date: 2025-09-18
Target flow_id: ac206b08-a732-451f-a101-8d98821a0885

### Table columns and expected population paths

Legend: [W] expected writer(s), [R] readers/consumers, [G] identified gap risk

- id (UUID):
  - [W] DB default; set at creation via SQLAlchemy default
- flow_id (UUID):
  - [W] Generated; also used as CFSE.flow_id; set at flow initialization
- master_flow_id (UUID):
  - [W] FK to CFSE.flow_id; set during orchestration creation or migration swap
  - [G] Some records may still be null if CFSE record missing
- client_account_id, engagement_id, user_id:
  - [W] Provided from request context at flow creation; enforced on repos
- data_import_id (UUID):
  - [W] Set when import is created/attached to flow (import handlers)
  - [G] Flows created before import attachment may remain null
- flow_name (varchar):
  - [W] Provided at initialization; set by orchestrator/service
- status (varchar):
  - [W] Updated by completion service and flow controllers (e.g., 'active', 'completed')
  - [R] summary_manager aggregates by status
  - [G] Paths advance `current_phase` but never touch `status`
- progress_percentage (float8):
  - [W] DiscoveryFlow.update_progress(); must be called after flag updates
  - [G] Not recalculated in several handlers; remains default 0.0
- data_import_completed (bool):
  - [W] Should be set true on successful import/validation completion
  - [R] gate checks in flow_execution_handlers
  - [G] Derived in responses, not persisted; missing explicit write
- field_mapping_completed (bool):
  - [W] field_mapping_logic, field_mapping_persistence on success
  - [G] Early returns may skip the set
- data_cleansing_completed (bool):
  - [W] data cleansing handlers (not comprehensively wired)
  - [G] Phase exists but completion set is missing in several paths
- asset_inventory_completed (bool):
  - [W] asset_handlers after asset write-back succeeds
  - [G] If asset write-back fails/skipped, flag remains false despite phase advance
- dependency_analysis_completed (bool):
  - [W] dependency phase executors
  - [G] Fast-forwarding transitions do not set flag
- tech_debt_assessment_completed (bool):
  - [W] tech debt phase controller
  - [G] Same as above
- learning_scope (varchar), memory_isolation_level (varchar):
  - [W] Defaults at creation; updated by config endpoints if any
  - [G] Defaults remain; may be acceptable
- assessment_ready (bool):
  - [W] readiness_assessor toggles when thresholds met
  - [G] Depends on previous flags; if flags unset, readiness remains false
- phase_state (jsonb), agent_state (jsonb):
  - [W] flow_state_bridge, crew execution bridges update during phases
  - [G] Missing writes when agent execution bypassed or errors swallowed
- flow_type (varchar):
  - [W] Set to 'unified_discovery' or 'discovery' at init; some places default to 'discovery'
- current_phase (varchar):
  - [W] flow_execution_handlers, phase_transition_service, flow_execution_service
  - [G] Advanced independently from flags; needs atomic updates
- phases_completed (json):
  - [W] Not consistently maintained; intended for audit trail
  - [G] Remains '[]' unless explicitly updated
- flow_state, crew_outputs, field_mappings, discovered_assets, dependencies, tech_debt_analysis (json):
  - [W] Written by respective phase handlers on success
  - [G] Many remain null due to short-circuited agent paths or lack of persistence on error
- crewai_persistence_id (uuid), crewai_state_data (jsonb):
  - [W] CFSE integration sets/pulls; sometimes unused
- error_message (text), error_phase (varchar), error_details (json):
  - [W] Set on exceptions; observed in some handlers
  - [G] Errors not propagated; empty despite failures
- created_at, updated_at, completed_at:
  - [W] DB defaults; completed_at should be set on finish
  - [G] completed_at left null when status switches not executed

### Parallel/bypass paths to terminate
- Setting `current_phase` without phase completion flags (flow_execution_handlers, phase_transition_service) → must be wrapped in transactional helper updating both and progress.
- Deriving flags in response builders (flow_status/data_helpers) without persisting → convert to write-through.
- Skipping persistence when agent execution fails silently → ensure error paths still persist partial state and explicit failure flags.

### Concrete remediation plan (code hotspots)
1) Transactional phase-advance utility (single source of truth)
   - Inputs: flow, new_phase, prior_phase_name
   - Actions: set prior_phase_completed=True; set current_phase=new_phase; call update_progress(); set status if necessary; commit
   - Wire into: unified_discovery/flow_execution_handlers.py, discovery/phase_transition_service.py, transition_utils.py
2) Write-through derivations
   - In flow_status/data_helpers.py, after computing boolean flags from data sources, persist on the model if they differ; commit
3) Explicit completion points
   - Data import completion handler: when import+validation pass, set data_import_completed=True, recompute progress
   - Asset write-back: on success, set asset_inventory_completed=True
4) Resilient error persistence
   - Wrap phase handlers to always write error_message/error_phase/error_details on exceptions; keep agent_state/phase_state updates consistent
5) Populate audit fields
   - phases_completed: append phase on completion
   - completed_at: set when all flags complete; set status='completed'

### One-off reconciliation script (for existing flows)
- For each flow:
  - If data_import_id has raw records → set data_import_completed=True
  - If assets exist for flow → set asset_inventory_completed=True
  - If dependency graph exists → set dependency_analysis_completed=True
  - If tech_debt_analysis JSON exists → set tech_debt_assessment_completed=True
  - Recompute progress_percentage; set current_phase to first incomplete phase
  - If all flags True → set status='completed', completed_at=now()

### Verification for target flow (run in dev/staging)
- Check import presence and raw record counts
- Check assets linked to this flow
- Inspect CFSE.phase_transitions for phase evidence
- After applying fixes, ensure flags and JSON fields populated appropriately; `current_phase` and flags are consistent
