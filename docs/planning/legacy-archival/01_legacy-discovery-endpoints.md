# Legacy Discovery Endpoints

## Current State
- Guard middleware: `backend/app/middleware/legacy_endpoint_guard.py` blocks all `/api/v1/discovery/*` with HTTP 410 and lists migration paths.
- Deprecated package: `backend/app/api/v1/endpoints/discovery_DEPRECATED/` raises `ImportError` if imported; retained for historical reference only.
- Redirect router: `backend/app/api/v1/endpoints/discovery.py` redirects to `/api/v1/unified-discovery`.

## Remaining References (Examples)
- Tests (non-exhaustive):
  - `tests/backend/integration/test_end_to_end_workflow.py`
  - `tests/backend/test_multitenant_workflow.py`
  - `tests/backend/integration/test_error_handling.py`
  - `tests/backend/test_crewai_flow_validation.py`
  - `tests/backend/test_cmdb_endpoint.py`
  - `tests/backend/debug_asset_inventory.py`
  - `tests/backend/test_dependency_api.py`
  - `tests/docker/test_docker_containers.py`
- Docs: search for `/api/v1/discovery/` in `docs/**`.

## Migration Paths
- Flows: use `/api/v1/flows/*` (Master Flow Orchestrator).
- Discovery specifics: use `/api/v1/unified-discovery/*`.

## Migration Examples
Replace in test files:
- OLD: `/api/v1/discovery/flows/active`
- NEW: `/api/v1/flows/active`

- OLD: `/api/v1/discovery/flow/create`
- NEW: `/api/v1/flows/create`

- OLD: `/api/v1/discovery/flow/{flow_id}/status`
- NEW: `/api/v1/flows/{flow_id}/status`

## Action Plan
- Phase 1 (Immediate): Ensure guard middleware stays enabled; block accidental regressions.
- Phase 2 (Tests): Update all tests to `/api/v1/flows/*` or `/api/v1/unified-discovery/*`.
- Phase 3 (Removal): Delete `discovery_DEPRECATED` package and redirect router after tests pass.
- Phase 4 (Docs): Refresh docs to remove legacy references.
- CI: Fail on new `/api/v1/discovery/*` mentions outside this archival folder.


