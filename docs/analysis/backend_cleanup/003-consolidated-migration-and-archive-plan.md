## Consolidated Migration and Archive Plan (003)

Generated: 2025-10-10

This consolidates 002-move-plan-and-migration-checklist and 002-actionable-migration-plan, updated with dependency-graph findings. It defines clear next steps with one source of truth.

---

### Executive Summary

- No truly orphaned files; archive only what’s confirmed unmounted or example-only.
- Two workstreams in parallel:
  - Migrate: decouple old crews and crew_class, standardize on child_flow_service + TenantScopedAgentPool.
  - Archive: unmounted endpoints, backups, and example agents (moved to examples).

---

### Final Classification

#### ✅ KEEP (actively used)
- backend/app/services/crewai_flows/crews/persistent_field_mapping.py
- backend/app/services/crewai_flows/crews/field_mapping_crew.py
- backend/app/services/crewai_flows/crews/dependency_analysis_crew/
- backend/app/services/crewai_flows/crews/technical_debt_crew.py
- backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/
- backend/app/services/crewai_flows/crews/component_analysis_crew/
- backend/app/services/crewai_flows/crews/architecture_standards_crew/
- backend/app/services/crewai_flows/crews/sixr_strategy_crew/
- backend/app/services/crewai_flows/crews/app_server_dependency_crew/
- backend/app/services/crewai_flows/crews/app_app_dependency_crew.py
- backend/app/services/crewai_flows/crews/asset_intelligence_crew.py
- backend/app/services/crewai_flows/config/crew_factory/factory.py
- backend/app/services/crews/base_crew.py
- Core platform folders: services/child_flow_services, services/persistent_agents, services/workflow_orchestration, repositories, models/schemas, core, middleware, caching, observability.

#### 🔄 MIGRATE (decouple before archive)
- backend/app/services/crewai_flows/crews/inventory_building_crew_original/ (mixed old/new)
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/ (heavily referenced)
- backend/app/services/crewai_flows/crews/agentic_asset_enrichment_crew.py (widely referenced)
- crew_class usage in configs/creation paths:
  - backend/app/services/flow_configs/discovery_flow_config.py
  - backend/app/services/sixr_engine_modular.py
  - backend/app/services/master_flow_orchestrator/operations/flow_creation_operations.py (constructor path)
  - backend/app/services/master_flow_orchestrator/operations/flow_lifecycle/state_operations.py
  - backend/app/services/flow_type_registry.py

#### 🗑️ ARCHIVE (safe now)
- Unmounted/legacy endpoints and backups:
  - backend/app/api/v1/endpoints/demo.py
  - backend/app/api/v1/endpoints/data_cleansing.py.bak
  - backend/app/api/v1/endpoints/flow_processing.py.backup
  - backend/app/api/v1/discovery/dependency_endpoints.py
  - backend/app/api/v1/discovery/chat_interface.py
  - backend/app/api/v1/discovery/app_server_mappings.py
- Legacy/superseded crews:
  - backend/app/services/crewai_flows/crews/inventory_building_crew_legacy.py
  - backend/app/services/crewai_flows/crews/collection/manual_collection_crew.py
  - backend/app/services/crewai_flows/crews/collection/data_synthesis_crew.py
- ADR-024 example agents (move to examples):
  - backend/app/services/agents/*_crewai.py → backend/archive/examples/*_crewai_example.py

---

### Move Plan (Archive Destinations)

Archive root: `backend/archive/`

1) Endpoints (legacy/unmounted)
- to: backend/archive/endpoints_legacy/{same_filename}

2) Legacy crews
- to: backend/archive/crews_legacy/{same_name_or_dir}

3) Example agents
- to: backend/archive/examples/{original_basename}_example.py

Guardrails after move
- Agent/registry discovery must skip `archive` and `_example.py`.
- Pre-commit/CI: forbid imports from `backend.archive`.
- Remove explicit `ProgressTrackingAgent` import from `services/agents/__init__.py`.

---

### Migration Workstream A: Remove Crew() in hot paths

Target pattern
```python
# OLD
from crewai import Crew
crew = Crew(agents=[...], tasks=[...], memory=False)

# NEW
from app.services.persistent_agents import TenantScopedAgentPool
agent = await TenantScopedAgentPool.get_agent(context, agent_type, service_registry)
result = await agent.process(input_data)
```

Files to implement wrappers and replace imports
- backend/app/services/field_mapping_executor/agent_executor.py
- backend/app/services/collection_readiness_service.py
- backend/app/services/flow_type_registry.py
- backend/app/services/persistent_agents/tenant_scoped_agent_pool.py (remove references pulling in crews)
- backend/app/services/child_flow_services/__init__.py (ensure no re-exports of crews)

Steps
1) Create per-domain persistent wrappers (if missing) that call TenantScopedAgentPool (e.g., field_mapping_persistent.py, dependency_analysis_persistent.py, etc.).
2) Replace imports from crews with persistent wrappers or phase executors (child_flow_services/handlers/phase_executors/**).
3) Run tests; ensure no direct Crew() instantiation remains in hot paths.

---

### Migration Workstream B: crew_class → child_flow_service

Goal: child_flow_service handles init and execution; remove crew_class.

Steps
1) discovery_flow_config.py: retain `child_flow_service=DiscoveryChildFlowService` as the primary field; annotate transitional use of crew_class.
2) flow_creation_operations.py: replace construction via `flow_config.crew_class()` with `await flow_config.child_flow_service.initialize_flow(...)` (add initializer if missing).
3) state_operations.py: ensure resume/advance paths call only `child_flow_service.execute_phase(...)`.
4) flow_type_registry.py: treat `child_flow_service` as required; mark crew_class optional/deprecated; add assertion if neither provided.
5) sixr_engine_modular.py: migrate to use child services.
6) tests/unit/test_crew_factory.py: refactor to test child service init/exec.

Success criteria
- 0 usages of Crew() in production paths.
- MFO uses child services exclusively (init + exec).
- All flow types registered without crew_class dependency.

---

### Dependency-driven Adjustments (from graphs)

- agentic_asset_enrichment_crew.py and optimized_field_mapping_crew/ are widely referenced; re-route importers first (Workstream A) before archiving.
- asset_intelligence_crew.py remains KEEP; multiple services depend on it.

---

### Pre-commit/CI Guards (copy-paste)

scripts/check_legacy_imports.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
FAILED=0

if git diff --cached -U0 -- '*.py' | grep -E "^\+.*(from|import)\s+backend\.archive\b"; then
  echo "❌ Import from backend.archive detected"; FAILED=1; fi

if git diff --cached -U0 -- '*.py' | grep -E "^\+.*\bCrew\("; then
  echo "❌ Direct Crew() usage detected. Use TenantScopedAgentPool."; FAILED=1; fi

if git diff --cached -U0 -- '*.py' | grep -E "^\+.*crew_class\s*="; then
  echo "❌ crew_class wiring detected. Use child_flow_service."; FAILED=1; fi

exit $FAILED
```

---

### Observability and Safety Nets

- Add logs confirming child_flow_service path per phase.
- Health checks to assert no Crew() in hot paths.
- Feature flag to temporarily fall back to crew_class init if child service init fails (remove after migration validated).

---

### Timeline & Milestones (suggested)

| Milestone | Outcome |
|-----------|---------|
| Archive Phase 1 | Endpoints/backups + example agents moved; guards enabled |
| Decouple Week 1 | Wrappers created; first batch of import replacements |
| Decouple Week 2 | All Crew() in hot paths removed; tests green |
| Config Week 3 | crew_class replaced by child services in creation paths |
| Cleanup Week 4 | Move migrated crews to archive; CI enforces new pattern |

---

### Acceptance Criteria

- [ ] No imports from backend.archive in src
- [ ] 0 direct Crew() calls in services
- [ ] All flow phases run via child_flow_service
- [ ] crew_class removed from configs (post-migration)
- [ ] All tests green; no router regressions


