## Backend Cleanup Inventory (Candidates)

Generated: 2025-10-10

Purpose: Comprehensive candidate list for archiving/move based on agreed criteria. Review and refine before actioning.

Scope criteria
- Crew-based implementations: Anything under `backend/app/services/crewai_flows/crews/**` or suffixed `_original`, or code that instantiates `Crew()` outside the persistent pool context.
- Legacy single-file agents not used by persistent paths: `backend/app/services/agents/*_crewai.py` that aren’t called by endpoints/phase executors and are not resolved via `TenantScopedAgentPool`.
- Old executors/validators superseded by service-layer equivalents: Files that duplicate logic now in `agent_service_layer/`, `manual_collection/validation_service.py`, or phase executors.
- Unmounted routers and demo endpoints: Endpoints not included in the router registry.
- Deprecated configuration paths: Any code using `crew_class` rather than child flow service (ADR-025).

Notes
- This is a candidates list; some items may still be needed for reference/tests. Mark “keep as example” vs “archive” during review.
- Excludes bytecode and `__pycache__` entries.

---

### 1) Crew-based implementations (directory and explicit Crew usage)

1.a Directory: backend/app/services/crewai_flows/crews/ (Python files)
- backend/app/services/crewai_flows/crews/__init__.py
- backend/app/services/crewai_flows/crews/data_import_validation_crew.py
- backend/app/services/crewai_flows/crews/collection/manual_collection_crew.py
- backend/app/services/crewai_flows/crews/optimized_crew_base.py
- backend/app/services/crewai_flows/crews/field_mapping_crew.py
- backend/app/services/crewai_flows/crews/asset_intelligence_crew.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/crew.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/tasks.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/tools.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/agents.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/__init__.py
- backend/app/services/crewai_flows/crews/app_app_dependency_crew.py
- backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/crew.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/tasks.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/execution.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/agents.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/memory_helpers.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/__init__.py
- backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py
- backend/app/services/crewai_flows/crews/technical_debt_crew.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/crew.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/tasks.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/tools.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/agents.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/__init__.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/crew.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/tasks.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/tools.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/fallback.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/agents.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/__init__.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/crew.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/tasks.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/tools.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/agents.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/utils.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/__init__.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/crew.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/tasks.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/tools.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/fallback.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/agents.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/__init__.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/crew.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/tasks.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/tools.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/fallback.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/agents.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/__init__.py
- backend/app/services/crewai_flows/crews/persistent_field_mapping.py
- backend/app/services/crewai_flows/crews/simple_field_mapper.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/crew.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/tasks.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/tools.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/agents.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/__init__.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_legacy.py
- backend/app/services/crewai_flows/crews/crew_config.py
- backend/app/services/crewai_flows/crews/collection/data_synthesis_crew.py
- backend/app/services/crewai_flows/crews/collection/__init__.py

1.b Explicit Crew usage (outside persistent pool context) – candidates
- backend/app/services/flow_orchestration/execution_engine_core.py
- backend/app/services/field_mapping_executor/agent_executor.py
- backend/app/services/crewai_flows/crews/field_mapping_crew.py
- backend/app/services/crewai_flows/crews/asset_intelligence_crew.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/tasks.py
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/crew.py
- backend/app/services/crewai_flows/crews/app_app_dependency_crew.py
- backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py
- backend/app/services/agentic_intelligence/risk_assessment_agent/crew_builder.py
- backend/app/services/agentic_intelligence/modernization_agent/crew_builder.py
- backend/app/services/agentic_intelligence/business_value_agent/crew_builder.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/crew.py
- backend/app/services/crewai_flows/crews/technical_debt_crew.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/crew.py
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/crew.py
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/crew.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/crew.py
- backend/app/services/crewai_flows/crews/component_analysis_crew/crew.py
- backend/app/services/crewai_flows/crews/architecture_standards_crew/crew.py
- backend/app/services/crewai_flows/config/crew_factory/factory.py
- backend/app/services/crewai_flows/crews/persistent_field_mapping.py
- backend/app/services/flow_orchestration/execution_engine_crew.py
- backend/app/services/crews/base_crew.py
- backend/app/services/crewai_flows/config/embedder_config.py
- backend/app/services/ai_analysis/ai_validation_service.py
- backend/app/services/agents/intelligent_flow_agent/agent.py
- backend/app/services/agents/flow_processing/crew.py
- backend/app/services/agents/flow_processing/agent.py
- backend/app/schemas/agent_schemas.py
- backend/app/api/v1/endpoints/data_import/agentic_critical_attributes/services/agent_coordinator.py

---

### 2) Legacy single-file agents not used by persistent paths (candidates)
- backend/app/services/agents/validation_workflow_agent_crewai.py
- backend/app/services/agents/tier_recommendation_agent_crewai.py
- backend/app/services/agents/progress_tracking_agent_crewai.py
- backend/app/services/agents/data_validation_agent_crewai.py
- backend/app/services/agents/data_cleansing_agent_crewai.py
- backend/app/services/agents/critical_attribute_assessor_crewai.py
- backend/app/services/agents/credential_validation_agent_crewai.py
- backend/app/services/agents/collection_orchestrator_agent_crewai.py
- backend/app/services/agents/asset_inventory_agent_crewai.py

Signals observed
- Not retrieved via `TenantScopedAgentPool.get_agent(...)`.
- Primarily example-style ADR-024 agents; not invoked by endpoints/phase executors.

---

### 3) Old executors/validators superseded by service-layer or phase executors (candidates)
- backend/app/services/crewai_flows/crews/data_import_validation_crew.py
- backend/app/services/crewai_flows/crews/field_mapping_crew.py
- backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py
- backend/app/services/crewai_flows/crews/persistent_field_mapping.py
- backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py
- backend/app/services/crewai_flows/crews/collection/manual_collection_crew.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/** (crew/tasks/tools/execution)

Current equivalents
- Service-layer handlers: `backend/app/services/agents/agent_service_layer/**`
- Manual collection validator: `backend/app/services/manual_collection/validation_service.py`
- Phase executors: `backend/app/services/crewai_flows/handlers/phase_executors/**`

---

### 4) Unmounted routers and demo endpoints (candidates)
- backend/app/api/v1/endpoints/demo.py
- backend/app/api/v1/endpoints/data_cleansing.py.bak
- backend/app/api/v1/endpoints/flow_processing.py.backup
- backend/app/api/v1/discovery/dependency_endpoints.py
- backend/app/api/v1/discovery/chat_interface.py
- backend/app/api/v1/discovery/app_server_mappings.py

Notes
- Router registry (`backend/app/api/v1/router_registry.py`) avoids registering legacy discovery endpoints; treat discovery/* as legacy.
- Validate each candidate against router_registry import lists before archiving.

---

### 5) Deprecated configuration paths (crew_class) – must migrate per ADR-025
- backend/app/services/master_flow_orchestrator/operations/flow_creation_operations.py
- backend/app/services/flow_configs/collection_flow_config.py
- backend/tests/unit/test_crew_factory.py
- backend/app/services/flow_type_registry.py
- backend/scripts/deployment/flow_type_configurations.py
- backend/app/services/sixr_engine_modular.py
- backend/app/services/master_flow_orchestrator/operations/flow_lifecycle/state_operations.py
- backend/app/services/flow_configs/discovery_flow_config.py

Recommended action
- Replace `crew_class` with child flow service reference and ensure Master Flow Orchestrator integration per ADR-025.

---

### Next steps
- Confirm each candidate’s status: archive, keep-as-example, or keep-active.
- After approval, move to `backend/archive/**` with READMEs and add registry/discovery skip rules and pre-commit checks.



