# Legacy Code Removal Patterns (Jan 2025)

## Completed Legacy Removals

### Backend Discovery Endpoints
**Removed Files:**
- `backend/app/api/v1/endpoints/discovery.py` (redirect router)
- `backend/app/api/v1/endpoints/discovery_DEPRECATED/` (entire package)
- `backend/app/services/crewai_flows/tools/asset_creation_tool_legacy.py`

**Migration Path:**
- `/api/v1/discovery/*` → `/api/v1/unified-discovery/*`
- All 8 test files updated to use new endpoints

### AsyncIO to AnyIO Migration
**Pattern:** Replace `asyncio.run()` with anyio blocking portal
```python
# Files updated:
# - backend/app/services/tools/base_tool.py
# - backend/app/services/agents/intelligent_flow_agent/tools/status_tool.py
# - backend/app/services/crewai_flows/tools/asset_creation_tool.py
```

### Deprecation Warnings
**Use FutureWarning, not DeprecationWarning:**
```python
warnings.warn(
    "AsyncBaseDiscoveryTool is deprecated and will be removed on 2025-02-01.",
    FutureWarning,  # Not DeprecationWarning
    stacklevel=2
)
```

## Frontend Migration Status

### Legacy Services Inventory (38 files)
**Still Using FlowService:** 24 files
**Still Using useFlow:** 22 files
**Migration Progress:** ~50% already using masterFlowService

### High-Priority Migrations
1. `src/components/flows/MasterFlowDashboard.tsx`
2. `src/pages/discovery/EnhancedDiscoveryDashboard/index.tsx`
3. `src/components/discovery/EnhancedFlowManagementDashboard.tsx`

### Migration Checklist Location
`docs/planning/legacy-archival/07_frontend-migration-checklist.md`

## Environment Variable Patterns

### Vite vs Next.js Naming
**Frontend (Vite):** `VITE_ENABLE_WEBSOCKETS`
**Frontend (Next.js):** `NEXT_PUBLIC_ENABLE_WEBSOCKETS`
**Backend:** `ENABLE_WEBSOCKETS`

**Key Learning:** Check build system before naming env vars

## CI/CD Guardrails

### GitHub Actions Legacy Detection
```yaml
# .github/workflows/enforce-policies.yml
# Excludes warning messages and comments about legacy code
grep -r "/api/v1/discovery" backend/app/ \
  --exclude-dir=__pycache__ \
  --exclude-dir="discovery" | \
  grep -v "router_registry.py" | \
  grep -v "LEGACY.*DEPRECATED" | \
  grep -v "deprecated.*removed" | \
  grep -v "# Legacy" | \
  grep -v "# DO NOT"
```

## Service Registry Pattern Enforcement

### Asset Creation Tools
**Legacy pattern removed:** Direct database access
**New pattern required:** ServiceRegistry instance
```python
# ServiceRegistry is now mandatory
if registry is None:
    raise ValueError(
        "ServiceRegistry instance is required. "
        "Legacy asset creation tools have been removed."
    )
```

## Test Migration Patterns

### Endpoint Updates
```python
# OLD
response = await client.post("/api/v1/discovery/flows")

# NEW
response = await client.post("/api/v1/unified-discovery/flows")
```

### Files Successfully Migrated
- test_end_to_end_workflow.py
- test_error_handling.py
- test_multitenant_workflow.py
- test_crewai_flow_validation.py
- test_cmdb_endpoint.py
- debug_asset_inventory.py
- test_dependency_api.py
- test_docker_containers.py

## Key Decisions

1. **Remove, don't deprecate:** Legacy code attracts usage
2. **Force new patterns:** No fallbacks to legacy
3. **Document migration paths:** Clear before/after examples
4. **Automate detection:** CI blocks legacy patterns
5. **Track progress:** Detailed checklists with file inventories
