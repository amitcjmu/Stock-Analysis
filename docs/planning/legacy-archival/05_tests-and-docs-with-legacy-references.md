# Tests and Docs with Legacy API References

## Findings
- Backend tests referencing `/api/v1/discovery/*` (non-exhaustive):
  - `tests/backend/integration/test_end_to_end_workflow.py`
  - `tests/backend/integration/test_error_handling.py`
  - `tests/backend/test_multitenant_workflow.py`
  - `tests/backend/test_crewai_flow_validation.py`
  - `tests/backend/test_cmdb_endpoint.py`
  - `tests/backend/debug_asset_inventory.py`
  - `tests/backend/test_dependency_api.py`
  - `tests/docker/test_docker_containers.py`
- Documentation files referencing old endpoints: search `docs/**` for `/api/v1/discovery/`.

## Migration Guidance
- Update test endpoints to `/api/v1/flows/*` or `/api/v1/unified-discovery/*`.
- Remove tests that validate legacy-only behavior.
- Refresh doc examples and curl commands to new endpoints.

## Action Items
- Create a checklist of files to update with owners and deadlines.
- Add CI to block new mentions of `/api/v1/discovery/` in code/docs (except in this archival folder).

## Migration Tracking Checklist
- [ ] test_end_to_end_workflow.py
- [ ] test_error_handling.py  
- [ ] test_multitenant_workflow.py
- [ ] test_crewai_flow_validation.py
- [ ] test_cmdb_endpoint.py
- [ ] debug_asset_inventory.py
- [ ] test_dependency_api.py
- [ ] test_docker_containers.py
- [ ] Update README.md examples
- [ ] Update API documentation
- [ ] Add CI check for legacy endpoint mentions
