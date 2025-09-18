## Revised Implementation Plan — DiscoveryFlow Consolidation, Master FK Correction, Assessment Progress

Owner: Coding Assistant
Date: 2025-09-18

This is the authoritative revised plan. It supersedes any prior versions and is intentionally placed in a new file to avoid accidental overlap.

### Canonical DiscoveryFlow columns (data-driven)
- field_mapping_completed
- asset_inventory_completed
- dependency_analysis_completed
- tech_debt_assessment_completed

Legacy to remove: attribute_mapping_completed, inventory_completed, dependencies_completed, tech_debt_completed.

---

## 0) Outcomes (single PR)
- Canonical flags in model and DB; legacy dropped.
- Code (backend/frontend/tests) updated to canonical names with exact references below.
- FK fixed: discovery_flows.master_flow_id → crewai_flow_state_extensions.flow_id via single-transaction add/backfill/swap (small data volume).
- AssessmentFlow.progress = Integer across model and API.
- Boolean comparisons fixed where touched (== True instead of is True).

---

## 1) Model edits
- Note: DiscoveryFlow model already uses canonical column names; confirm and keep.
- backend/app/models/discovery_flow.py
  - Keep only canonical Boolean columns (not-null, default False): field_mapping_completed, asset_inventory_completed, dependency_analysis_completed, tech_debt_assessment_completed.
  - Update: calculate_progress, update_progress, get_current_phase, get_next_phase, is_complete, to_dict to use canonical names.

- backend/app/models/crewai_flow_state_extensions.py
  - Add: collection_flow_id (UUID, FK("collection_flows.id"), nullable=True), automation_tier (String(20)), collection_quality_score (Float), data_collection_metadata (JSONB, server_default '{}').

- backend/app/models/assessment_flow/core_models.py
  - Change: progress = Column(Integer, default=0, nullable=False).

---

## 2) Exact code refactors (legacy → canonical)

attribute_mapping_completed → field_mapping_completed
- backend/app/api/v1/endpoints/unified_discovery/field_mapping_handlers.py:130, 399
- backend/app/services/flow_orchestration/field_mapping_logic.py:372, 387
- backend/app/services/crewai_flows/flow_state_utils.py:70
- backend/app/api/v1/endpoints/unified_discovery/health_handlers.py:97
- backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:101, 105
- backend/app/services/discovery/phase_transition_service.py:106
- backend/app/services/discovery/field_mapping_helpers.py:36
- backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py:338
- backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:57, 218, 231, 257
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:89
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:45, 155
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:47, 63
- backend/app/services/discovery/flow_status/data_helpers.py:137
- backend/app/services/crewai_flows/flow_state_bridge.py:203
- backend/app/models/discovery_flow.py:59, 150, 171, 192, 209, 265
- backend/app/core/auto_seed_demo_data.py:98, 111
- Frontend: src/hooks/discovery/useDiscoveryFlowAutoDetection.ts; src/hooks/useUnifiedDiscoveryFlow.ts; src/types/discovery.ts

inventory_completed → asset_inventory_completed
- backend/app/api/v1/endpoints/flow_processing.py:338, 341, 451
- backend/app/services/crewai_flows/flow_state_utils.py:72
- backend/app/api/v1/endpoints/unified_discovery/health_handlers.py:99
- backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:111, 114
- backend/app/api/v1/endpoints/unified_discovery/asset_handlers.py:178, 185, 237
- backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:59, 222, 233, 259
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:92
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:47, 157
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:49
- backend/app/services/flow_orchestration/smart_discovery_service.py:292, 293
- backend/app/services/mfo_sync_agent.py:222
- backend/app/services/crewai_flows/flow_state_bridge.py:207
- backend/app/models/discovery_flow.py:63, 152, 173, 194, 211, 267
- backend/app/core/auto_seed_demo_data.py:100, 113
- Frontend: src/services/api/discoveryFlowService.ts; src/hooks/useUnifiedDiscoveryFlow.ts

dependencies_completed → dependency_analysis_completed
- backend/app/services/flow_orchestration/execution_engine_crew_discovery/phase_executors.py:386, 390, 394
- backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py:116, 118
- backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py:60, 224, 234, 260
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:93
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:48, 158
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:50
- backend/app/services/crewai_flows/flow_state_bridge.py:209
- backend/app/models/discovery_flow.py:66, 153, 174, 195, 212, 268
- backend/app/core/auto_seed_demo_data.py:101, 114
- Frontend: src/services/api/discoveryFlowService.ts; src/hooks/useUnifiedDiscoveryFlow.ts

tech_debt_completed → tech_debt_assessment_completed
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py:94
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py:49, 159
- backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py:51
- backend/app/services/crewai_flows/flow_state_bridge.py:211
- backend/app/models/discovery_flow.py:69, 154, 175, 196, 213, 269
- backend/app/core/auto_seed_demo_data.py:102, 115
- Frontend: src/services/api/discoveryFlowService.ts; src/hooks/useUnifiedDiscoveryFlow.ts

Boolean comparisons (fix where touched):
- backend/app/repositories/discovery_flow_repository/queries/flow_queries.py:143–148
- backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py:47–53, 58, 99
- backend/app/repositories/discovery_flow_repository/queries/analytics_queries.py:84

---

## 3) Migrations

068_discovery_columns_rename_and_cleanup.py (DB → canonical)
- Rename legacy columns → canonical (if legacy exists):
  - attribute_mapping_completed → field_mapping_completed
  - inventory_completed → asset_inventory_completed
  - dependencies_completed → dependency_analysis_completed
  - tech_debt_completed → tech_debt_assessment_completed
- Drop unused fields if present: import_session_id, flow_description
- Ensure canonical booleans are NOT NULL DEFAULT false
- Emit audit (NOTICE or temp table) if legacy and canonical differ before rename

069_fix_discovery_master_fk_swap.py (simple swap, small volume)
- BEGIN;
- ALTER TABLE add master_flow_id_new UUID;
- UPDATE ... SET master_flow_id_new = cfse.flow_id FROM migration.crewai_flow_state_extensions cfse WHERE discovery_flows.master_flow_id = cfse.id;
- (Optional fallback) UPDATE by df.flow_id = cfse.flow_id AND tenants match for NULLs;
- ALTER TABLE ADD CONSTRAINT fk_discovery_master_new FOREIGN KEY (master_flow_id_new) REFERENCES migration.crewai_flow_state_extensions(flow_id);
- ALTER TABLE DROP COLUMN master_flow_id;
- ALTER TABLE RENAME COLUMN master_flow_id_new TO master_flow_id;
- COMMIT;

070_add_missing_cfse_fields_if_needed.py (idempotent)
- ALTER TABLE crewai_flow_state_extensions ADD COLUMN IF NOT EXISTS:
  - collection_flow_id UUID,
  - automation_tier VARCHAR(50),
  - collection_quality_score FLOAT,
  - data_collection_metadata JSONB DEFAULT '{}'

---

## 4) Tests & verification
- Update tests; add migration checks; run full suite.
- Post-migration SQL: no NULL `master_flow_id` except true orphans; random sample equality with CFSE.flow_id; canonical present, legacy absent.

Pre-/Post-migration verification snippets (include in PR):
- Orphans: master_flow_id NOT IN (SELECT flow_id FROM CFSE)
- Column presence/absence checks in information_schema
- Count sanity: total discovery_flows ~< 200; assets ~< 100

---

## 5) PR contents
- Model edits, refactors (backend/frontend), migrations 068/069, tests.
- PR body: reference counts, FK strategy, audit/rollback.

### Exhaustive file inventory to update (legacy → canonical)
- Backend runtime
  - backend/app/services/discovery_flow_completion_service.py
  - backend/app/services/assessment_flow_service/assessors/readiness_assessor.py
  - backend/app/services/agents/agent_service_layer/handlers/data_handler.py
  - backend/app/services/agents/agent_service_layer/handlers/asset_handler.py
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_status.py
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_validation.py
  - backend/app/services/agents/agent_service_layer/handlers/flow_handler_navigation.py
  - backend/app/services/discovery/flow_status/data_helpers.py
  - backend/app/services/discovery/field_mapping_helpers.py
  - backend/app/services/discovery/phase_transition_service.py
  - backend/app/services/flow_orchestration/field_mapping_logic.py
  - backend/app/services/flow_orchestration/smart_discovery_service.py
  - backend/app/services/mfo_sync_agent.py
  - backend/app/services/crewai_flows/flow_state_utils.py
  - backend/app/services/crewai_flows/flow_state_bridge.py
  - backend/app/services/crewai_flows/unified_discovery_flow/handlers/field_mapping_persistence.py
  - backend/app/services/crewai_flows/unified_discovery_flow/phase_controller.py
  - backend/app/api/v1/endpoints/unified_discovery/field_mapping_handlers.py
  - backend/app/api/v1/endpoints/unified_discovery/flow_execution_handlers.py
  - backend/app/api/v1/endpoints/unified_discovery/asset_handlers.py
  - backend/app/api/v1/endpoints/unified_discovery/health_handlers.py
  - backend/app/api/v1/endpoints/flow_processing.py
  - backend/app/services/discovery_flow_service/integrations/crewai_integration.py
  - backend/app/services/discovery_flow_service/managers/summary_manager.py
  - backend/app/repositories/discovery_flow_repository/queries/flow_queries.py
  - backend/app/repositories/discovery_flow_repository/queries/analytics_queries.py
  - backend/app/repositories/discovery_flow_repository/commands/flow_phase_management.py
  - backend/app/repositories/discovery_flow_repository/specifications/flow_specs.py
  - backend/app/models/discovery_flow.py
  - backend/app/core/auto_seed_demo_data.py

- Frontend runtime
  - src/hooks/discovery/useDiscoveryFlowAutoDetection.ts
  - src/hooks/useUnifiedDiscoveryFlow.ts
  - src/hooks/discovery/attribute-mapping/useFlowDetection.ts
  - src/hooks/discovery/useInventoryLogic.ts
  - src/hooks/discovery/useTechDebtLogic.ts
  - src/hooks/discovery/useDiscoveryFlowList.ts
  - src/services/api/discoveryFlowService.ts
  - src/types/discovery.ts
  - src/pages/discovery/DependencyAnalysis.tsx
  - src/pages/discovery/TechDebtAnalysis.tsx

- Tests
  - tests/backend/services/test_import_validator_flow_handling.py
  - tests/backend/test_agent_service_layer.py

- Seed/scripts
  - backend/scripts/seed_discovery_flow_tables.py
  - backend/scripts/seed_test_data.py
  - backend/scripts/seed_minimal_demo.py
  - backend/scripts/properly_reset_flow_to_field_mapping.py
  - backend/scripts/investigate_discovery_flow.py
  - backend/scripts/check_flow_status.py
  - backend/scripts/approve_field_mappings.py


