### Testing Strategy and QA Guide

This document defines how we organize and execute tests across the platform. It focuses on pytest-based tests. Playwright suites are documented separately and excluded from scope here per current priority.

#### Goals
- Consistent, Docker-first execution
- Clear suite definitions (smoke, sanity, regression, performance)
- Curated regression per phase/flow
- Legacy cleanup to reduce noise and flakiness

#### Environments
- Local development: Docker containers only
- Production: not used for test execution

Required services for backend and API integration tests:
- `migration_backend` (FastAPI)
- `migration_frontend` (UI when needed for connectivity checks)
- `migration_db` (PostgreSQL)

#### Execution (Step-by-step)
1) Start containers (auto-detected compose file)
```bash
python tests/run_tests_docker.py --suites backend --no-cleanup
```
If you prefer manual start:
```bash
docker compose -f config/docker/docker-compose.yml up -d
```

2) Discover where tests live INSIDE the backend container
```bash
docker exec -it migration_backend bash -lc 'ls -1d backend/tests tests/backend tests 2>/dev/null || true'
```
Note the first existing path. The runner scripts auto-detect this as well.

3) Run curated suites (markers)
```bash
# Discovery regression
docker exec -it migration_backend bash -lc "python -m pytest \"$( [ -d backend/tests ] && echo backend/tests || { [ -d tests/backend ] && echo tests/backend || echo tests; } )\" -m 'regression and discovery' -v --tb=short"

# Collection regression
docker exec -it migration_backend bash -lc "python -m pytest \"$( [ -d backend/tests ] && echo backend/tests || { [ -d tests/backend ] && echo tests/backend || echo tests; } )\" -m 'regression and collection' -v --tb=short"
```

4) Run everything (pytest backend + docker integration) via runner
```bash
python tests/run_tests_docker.py --suites backend docker
```

#### Markers and Taxonomy
Add these markers to tests as applicable:
- Phase markers: `discovery`, `collection`, `assessment`, `planning`, `execute`, `modernize`, `decommission`, `finops`
- Suite markers: `smoke`, `sanity`, `regression`, `e2e` (pytest-based), `performance`, `flaky`
- Existing markers retained: `unit`, `integration`, `docker`, `backend`, `multitenant`, `agentic`

Tips:
- List tests: `docker exec -it migration_backend python -m pytest <detected_path> --collect-only -q`
- Filter by name: `-k 'substring'`
- Stop on first failure: `-x`
- Longer tracebacks: `--tb=long`

#### Curated Regression Suites (pytest)
- Discovery: `tests/backend/flows/test_unified_discovery_flow.py`, `tests/backend/test_api_integration.py`, `tests/test_flow_creation.py`, `tests/test_e2e_validation.py`, `tests/backend/services/test_master_flow_orchestrator.py`
- Collection: `tests/backend/integration/test_collection_flow_mfo.py`
- Cross-flow: `tests/backend/test_sixr_analysis.py`, `tests/backend/test_agentic_system.py`, `tests/backend/test_crewai_system.py`, `tests/backend/test_smoke.py`
- Performance: `tests/backend/performance/*`

Annotate these with `regression` and corresponding phase markers.

#### Endpoint Alignment
- Unified Discovery actions (initialize/status): `/api/v1/unified-discovery/flow/initialize`, `/api/v1/unified-discovery/flow/{flow_id}/status`
- Active flows listing: use the currently supported endpoint. Backward compatibility exists; prefer unified listing if available: `/api/v1/unified-discovery/flows/active`. Some tests still rely on `/api/v1/discovery/flows/active` where required.
- Health: `/api/v1/unified-discovery/flow/health`

#### Flakiness and Reliability
- Retries in CI only: add `pytest-rerunfailures` with `--reruns 2 --reruns-delay 3`
- Timeouts: default 300s; consider lower for unit tests
- Isolation: avoid `xdist` for DB-heavy suites unless fixtures are isolation-safe
- Quarantine: mark known unstable tests `@pytest.mark.flaky` and exclude from required CI jobs

#### Reporting
- JUnit XML: `tests/results/junit.xml`
- Coverage: HTML `tests/coverage/html`, XML `tests/coverage/coverage.xml`

#### How to interpret failures (for new QA)
- Pytest prints the failing test nodeid: `path/to/file.py::TestClass::test_function`
- The traceback bottom frames show the exact application file and line that raised the error, e.g. `app/services/foo.py:123`
- Use `--tb=long -vv -s` to see full stack and prints. Start by opening the bottom-most app frame file/line in your editor.
- Common outcomes:
  - "deselected" = your marker didn’t match any tests in the detected path; re-run with the detected path or use `--collect-only` to confirm presence.
  - Deprecation warnings (Pydantic/SQLAlchemy) do not indicate failures; focus on FAIL blocks.

#### CI Recommended Matrix (GitHub Actions)
- PR: smoke + unit + lint + coverage upload
- Main: sanity + key integration
- Nightly: full regression + performance

#### Legacy Cleanup
Remove tests referencing legacy `/api/v1/discovery/flow/*` endpoints. Prefer unified endpoints as above. Keep discovery assets listing endpoints where currently supported.

#### Ownership and Maintenance
- QA owns curated suite definitions in `docs/testing/REGRESSION_CATALOG.md`
- Engineering maintains markers and keeps scripts aligned to supported endpoints


