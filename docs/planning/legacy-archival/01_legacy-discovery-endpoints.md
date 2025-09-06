# Legacy Discovery Endpoints

## Current State
- Guard middleware: `backend/app/middleware/legacy_endpoint_guard.py` blocks all `/api/v1/discovery/*` with HTTP 410 and lists migration paths.
- Deprecated package: `backend/app/api/v1/endpoints/discovery_DEPRECATED/` raises `ImportError` if imported; retained for historical reference only.
- Redirect router: `backend/app/api/v1/endpoints/discovery.py` redirects to `/api/v1/unified-discovery`.

## Remaining References (Examples)
- Tests: `tests/backend/integration/test_end_to_end_workflow.py`, `tests/backend/test_multitenant_workflow.py`, `tests/docker/test_docker_containers.py`.
- Docs: search for `/api/v1/discovery/` in `docs/**`.

## Migration Paths
- Flows: use `/api/v1/flows/*` (Master Flow Orchestrator).
- Discovery specifics: use `/api/v1/unified-discovery/*`.

## Action Plan
- Remove deprecated router package after tests/docs are migrated.
- Update test suites to new endpoints or remove obsolete tests.
- Add CI check to fail on new `/api/v1/discovery/*` introductions (if not already covered).


