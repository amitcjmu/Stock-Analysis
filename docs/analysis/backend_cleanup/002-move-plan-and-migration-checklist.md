## Backend Cleanup: Move Plan and Migration Checklist

Generated: 2025-10-10

This document consolidates next steps into two actionable sections: (1) Move Plan (archive moves), and (2) Migration Checklist (ADR-025 updates). It supersedes mixed discussions in prior reports.

---

### 1) Move Plan (Archive Moves)

Archive root: `backend/archive/`
- Policy: No runtime imports from `backend.archive`. Add pre-commit/CI guard after move.
- Examples go to `backend/archive/examples/`. Legacy crews/endpoints to `backend/archive/crews_legacy/` or `backend/archive/endpoints_legacy/`.

Moves (safe to archive)

1. Legacy crews
- from: `backend/app/services/crewai_flows/crews/inventory_building_crew_original/`
  to:   `backend/archive/crews_legacy/inventory_building_crew_original/`
- from: `backend/app/services/crewai_flows/crews/inventory_building_crew_legacy.py`
  to:   `backend/archive/crews_legacy/inventory_building_crew_legacy.py`
- from: `backend/app/services/crewai_flows/crews/collection/manual_collection_crew.py`
  to:   `backend/archive/crews_legacy/manual_collection_crew.py`
- from: `backend/app/services/crewai_flows/crews/collection/data_synthesis_crew.py`
  to:   `backend/archive/crews_legacy/data_synthesis_crew.py`
- from: `backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/`
  to:   `backend/archive/crews_legacy/optimized_field_mapping_crew/`
- from: `backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py`
  to:   `backend/archive/crews_legacy/agentic_asset_enrichment_crew.py`

2. Legacy single-file agents (keep as ADR-024 examples)
- from: `backend/app/services/agents/validation_workflow_agent_crewai.py`
  to:   `backend/archive/examples/validation_workflow_agent_crewai_example.py`
- from: `backend/app/services/agents/tier_recommendation_agent_crewai.py`
  to:   `backend/archive/examples/tier_recommendation_agent_crewai_example.py`
- from: `backend/app/services/agents/progress_tracking_agent_crewai.py`
  to:   `backend/archive/examples/progress_tracking_agent_crewai_example.py`
- from: `backend/app/services/agents/data_validation_agent_crewai.py`
  to:   `backend/archive/examples/data_validation_agent_crewai_example.py`
- from: `backend/app/services/agents/data_cleansing_agent_crewai.py`
  to:   `backend/archive/examples/data_cleansing_agent_crewai_example.py`
- from: `backend/app/services/agents/critical_attribute_assessor_crewai.py`
  to:   `backend/archive/examples/critical_attribute_assessor_crewai_example.py`
- from: `backend/app/services/agents/credential_validation_agent_crewai.py`
  to:   `backend/archive/examples/credential_validation_agent_crewai_example.py`
- from: `backend/app/services/agents/collection_orchestrator_agent_crewai.py`
  to:   `backend/archive/examples/collection_orchestrator_agent_crewai_example.py`
- from: `backend/app/services/agents/asset_inventory_agent_crewai.py`
  to:   `backend/archive/examples/asset_inventory_agent_crewai_example.py`

3. Unmounted routers and backups
- from: `backend/app/api/v1/endpoints/demo.py`
  to:   `backend/archive/endpoints_legacy/demo.py`
- from: `backend/app/api/v1/endpoints/data_cleansing.py.bak`
  to:   `backend/archive/endpoints_legacy/data_cleansing.py.bak`
- from: `backend/app/api/v1/endpoints/flow_processing.py.backup`
  to:   `backend/archive/endpoints_legacy/flow_processing.py.backup`
- from: `backend/app/api/v1/discovery/dependency_endpoints.py`
  to:   `backend/archive/endpoints_legacy/discovery_dependency_endpoints.py`
- from: `backend/app/api/v1/discovery/chat_interface.py`
  to:   `backend/archive/endpoints_legacy/discovery_chat_interface.py`
- from: `backend/app/api/v1/discovery/app_server_mappings.py`
  to:   `backend/archive/endpoints_legacy/discovery_app_server_mappings.py`

Post-move guardrails
- Update agents registry discovery to skip `archive` and `_example.py` suffix.
- Add pre-commit/CI check to fail on `from backend.archive` or `import backend.archive`.
- Remove explicit `ProgressTrackingAgent` import from `backend/app/services/agents/__init__.py`.

---

### 2) Migration Checklist (ADR-025)

Goal: Reduce reliance on `crew_class` for initialization; standardize on `child_flow_service` end-to-end.

Targets
- `backend/app/services/sixr_engine_modular.py`
- `backend/app/services/master_flow_orchestrator/operations/flow_lifecycle/state_operations.py`
- `backend/tests/unit/test_crew_factory.py`
- `backend/scripts/deployment/flow_type_configurations.py`

Steps
1. Discovery flow config audit
   - Confirm `backend/app/services/flow_configs/discovery_flow_config.py` keeps `child_flow_service=DiscoveryChildFlowService` as source of truth.
   - Add comment clarifying transitional use of `crew_class` if still required by creator paths.

2. Replace `crew_class` construction paths
   - In `flow_creation_operations.py`, prefer constructing via `child_flow_service(...)` for initialization logic, removing reliance on `flow_config.crew_class()`.
   - In `state_operations.py`, route resume/advance strictly through `child_flow_service.execute_phase(...)`.

3. Update orchestration utilities
   - Ensure `status_manager.py` and `flow_type_registry.py` treat `child_flow_service` as mandatory and `crew_class` as optional/deprecated.
   - Add runtime assertion if both are missing.

4. Tests
   - Refactor `tests/unit/test_crew_factory.py` to new initialization model using `child_flow_service`.
   - Add end-to-end tests covering creation, execute_phase, resume, and completion using `MasterFlowOrchestrator` + child services.

5. Deployment/config scripts
   - Update `scripts/deployment/flow_type_configurations.py` to remove `crew_class` fields and specify `child_flow_service` explicitly.

6. Observability
   - Add logs confirming `child_flow_service` path used for each phase.
   - Add health checks to verify no `Crew()` instantiation in production paths.

7. Safety net
   - Feature flag to fallback to existing `crew_class` only if `child_flow_service` import fails (temporary; remove after validation).

Success criteria
- No direct `Crew()` usage in hot paths.
- Master Flow Orchestrator uses child services exclusively for phase execution and (post-migration) also for initialization.
- All flow types registered without `crew_class` dependency.
- Tests green; router registry unaffected.



