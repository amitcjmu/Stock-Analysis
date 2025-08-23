### Suite Matrix

| Suite | Markers | Purpose | Typical Command |
|---|---|---|---|
| Smoke | `smoke and backend` | Fast PR gate | `docker exec -it migration_backend python -m pytest -m "smoke and backend" -q` |
| Sanity | `sanity and backend` | Broader PR/merge validation | `docker exec -it migration_backend python -m pytest -m "sanity and backend"` |
| Discovery Regression | `regression and discovery` | Full Discovery flow coverage | `docker exec -it migration_backend python -m pytest -m "regression and discovery"` |
| Collection Regression | `regression and collection` | Full Collection flow coverage | `docker exec -it migration_backend python -m pytest -m "regression and collection"` |
| Cross-flow Regression | `regression and (agentic or multitenant)` | Platform-wide behaviors | `docker exec -it migration_backend python -m pytest -m "regression and agentic"` |
| Performance | `performance` | Perf validation (opt-in) | `docker exec -it migration_backend python -m pytest -m performance` |
| Full Regression | `backend + docker` | All pytest backend + docker tests | `python tests/run_tests_docker.py --suites backend docker` |

Note: Playwright suites are managed under `tests/e2e/` and are out of scope for this pytest matrix.



