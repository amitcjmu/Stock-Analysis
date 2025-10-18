## Focused Map: Current Architecture vs Legacy (Browse-First Guide)

Updated: 2025-10-10

This guide helps you browse only the code aligned with current design decisions (MFO + child services, persistent agents, multi-tenant repos, LLM tracking) and avoid legacy paths.

### Follow (authoritative entry points)
- backend/app/api/v1/router_registry.py  ← mounted APIs (truth)
- backend/app/services/master_flow_orchestrator/
- backend/app/services/child_flow_services/
- backend/app/services/persistent_agents/tenant_scoped_agent_pool.py
- backend/app/services/crewai_flows/crews/persistent_field_mapping.py
- backend/app/services/crewai_flows/crews/field_mapping_crew.py  (fallback)
- backend/app/services/multi_model_service.py
- backend/app/repositories/  (ContextAwareRepository usage)

### Prefer (modern patterns to emulate)
- RequestContext propagation through services → repositories
- Async SQLAlchemy with atomic begin → flush → commit
- UUID PKs for relationships; `flow_id` only for MFO calls
- JSON NaN/Infinity sanitization before responses
- LLM calls via `multi_model_service.generate_response(...)`

### Deprioritize / Legacy (do not follow for architecture)
- backend/app/api/v1/discovery/* (legacy endpoints; blocked in prod)
- backend/app/api/v1/endpoints/*.{bak,backup}
- backend/app/api/v1/endpoints/demo.py
- backend/app/services/agents/*_crewai.py (single-file agents not in persistent pool)
- backend/app/services/crewai_flows/crews/field_mapping_crew_fast.py
- backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/ (investigate; likely unused)
- Any codepaths invoking `/api/v1/discovery/*` in app code
- Services using `asyncio.run(...)` in request paths

### Coexistence (do not delete; read with context)
- backend/app/services/flow_configs/*  (crew_class for initialization)
- backend/app/services/flow_type_registry.py  (crew_class optional)
- backend/app/services/master_flow_orchestrator/operations/
  - flow_creation_operations.py  (may instantiate crew_class)
  - flow_lifecycle/state_operations.py  (resumption path w/ crew_class)

### Quick commands (ripgrep)
```bash
# 1) What’s actually mounted (start here)
rg "router\.include_router" backend/app/api/v1/router_registry.py -n

# 2) Find legacy endpoint usage to avoid in app code
rg "/api/v1/discovery/" -n --glob '!docs/**' --glob '!tests/**' --glob '!scripts/**'

# 3) Distinguish init (crew_class) from execution (child services)
rg "crew_class" backend/app/services -n

# 4) Flag asyncio.run in services (modernize/avoid for architecture)
rg "asyncio\.run\(" backend/app -n
```

### Reading order (minimal set to grok the system)
1. master_flow_orchestrator/ (creation/resume, lifecycle)
2. child_flow_services/ (Discovery/Collection execution)
3. persistent_agents/tenant_scoped_agent_pool.py
4. crewai_flows/crews/persistent_field_mapping.py → field_mapping_crew.py (fallback)
5. multi_model_service.py (LLM usage + cost tracking)
6. repositories/ used by child services (confirm ContextAwareRepository and tenant scoping)
7. router_registry.py (final binding)

### Optional verification
- CHANGELOG.md entries from 2025-08 forward confirm: legacy discovery endpoints deprecated; ADR-025 child services in use; LLM tracking centralized.
- docs/analysis/backend_cleanup/001-comprehensive-review-report.md lists safe-to-archive items and confirms persistent vs crew fallback roles.

### Notes
- Treat any `/api/v1/discovery/*` references in docs/tests as historical context; do not follow them for implementation.
- Keep `crew_class` in flow configs for init until ADR-025 migration tickets are completed; execution should go through child services.






