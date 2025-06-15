# Test Coverage Report & Remediation Tracker

_Last updated: 2025-06-14_

---

## 1. Executive Summary

Test coverage for the migration platform is currently **insufficient for production-readiness** due to broken imports, missing/renamed modules, and outdated test targets. This report summarizes the current state, root causes, and provides a file-by-file remediation checklist to systematically reach high coverage (≥90% backend, critical path frontend/e2e).

---

## 2. Test Suite Inventory

### Backend (Python, pytest)
- 31+ backend test files in `/tests/backend/` (unit, integration, agentic, RBAC, memory, multi-tenant, asset classification, 6R, etc.)
- Many tests reference `app.models.*`, `app.services.*`, but some modules (e.g., `asset_minimal.py`, `user.py`) do not exist or are misplaced/renamed.
- Several tests rely on agentic/crewAI workflows and asset learning.

### E2E (Playwright, TypeScript)
- 6+ E2E test specs in `/tests/e2e/` (admin, login, data import, 6R workflow, etc.)
- One Python E2E: `test_agent_user_interaction.py` (agentic user flows).

### Frontend
- At least one Playwright spec in `/tests/frontend/demoMode.spec.ts`.

---

## 3. Coverage Execution Status

- **Backend coverage run fails** due to import errors:
  - `ModuleNotFoundError` for `app.models.asset_minimal`, `app.models.user`, `app.services.asset_classification_learner`, and `backend.main`.
  - These missing modules prevent the majority of backend tests from running, so coverage is artificially low and not meaningful until resolved.

---

## 4. Root Causes & Remediation Steps

### A. Broken/Missing Imports
- Many test files reference modules that do not exist in the current codebase structure (likely due to recent refactors).
- `asset_minimal.py`, `user.py`, and `asset_classification_learner.py` are either archived, renamed, or removed.
- Some tests reference `backend.main` (should be `app.main` or similar).

### B. Test Discovery/Path Issues
- Some test files may not be discoverable due to path or naming issues.
- `sys.path.append` hacks present in tests (fragile, should use proper PYTHONPATH).

### C. Agentic/AI Integration
- Several tests rely on agentic CrewAI workflows and dynamic learning.
- Mocking and patching of agentic services is present, but coverage of fallback paths and error handling is unclear.

---

## 5. Remediation Plan

### Backend:
1. **Fix Import Paths**
   - Refactor all tests to match the current backend structure.
   - Remove or rewrite tests referencing non-existent modules.
   - Ensure all service/model imports reflect actual files (e.g., use `app.services.archived.asset_classification_learner` if that’s the real location).

2. **Restore/Replace Critical Test Targets**
   - If files like `asset_minimal.py` and `user.py` are essential, restore or rewrite them.
   - If they are deprecated, update test logic to use new model/service locations.

3. **Agentic Path Coverage**
   - Ensure all CrewAI/agentic workflow paths (including fallback and error cases) are covered by unit and integration tests.
   - Add tests for multi-tenancy, RBAC, and session management (especially after recent refactors).

4. **Test Discovery/Runner Config**
   - Use a `pytest.ini` or `conftest.py` to set up PYTHONPATH and fixtures.
   - Remove all `sys.path.append` hacks from test files.

5. **Coverage Metrics**
   - Once tests run, generate a coverage report (`pytest --cov=app --cov-report=html`).
   - Identify modules with <80% coverage and add/expand tests as needed.

### Frontend/E2E:
1. **Instrument Playwright for Coverage**
   - Use Playwright’s built-in coverage or instrument with `babel-plugin-istanbul` for React/TS code.
   - Ensure all critical user flows (login, session switching, discovery, admin, 6R) are covered.

2. **Expand E2E Coverage**
   - Add tests for error/edge cases, agentic UI fallback, and multi-tenant scenarios.

### CI/CD & Quality Gates
- Add a CI step to fail builds if backend coverage <90% or if critical frontend flows are not covered.
- Require all new features to include corresponding tests.

---

## 6. Remediation Tracker (File-by-File)

| File/Area                                             | Type         | Status      | Notes/Next Steps                                             |
|------------------------------------------------------|--------------|-------------|-------------------------------------------------------------|
| backend/test_agent_monitor.py                        | Backend      | ⬜ Todo      | Fix imports, validate agent monitoring logic                 |
| backend/test_agentic_system.py                       | Backend      | ⬜ Todo      | Update for current agentic workflow structure                |
| backend/test_ai_learning.py                          | Backend      | ⬜ Todo      | Ensure learning system is referenced properly                |
| backend/test_api_integration.py                      | Backend      | ⬜ Todo      | Fix API imports, update endpoints if changed                 |
| backend/test_asset_classification.py                 | Backend      | ⬜ Todo      | Fix asset/model imports, update for agentic logic            |
| backend/test_cmdb_analysis.py                        | Backend      | ⬜ Todo      | Validate CMDB analysis logic, fix imports                    |
| backend/test_cmdb_endpoint.py                        | Backend      | ⬜ Todo      | API endpoint structure, fix imports                          |
| backend/test_crewai.py                               | Backend      | ⬜ Todo      | Validate CrewAI integration, patch as needed                 |
| backend/test_crewai_no_thinking.py                   | Backend      | ⬜ Todo      | Ensure fallback logic is covered                             |
| backend/test_crewai_service_updated.py               | Backend      | ⬜ Todo      | Validate new CrewAI service structure                        |
| backend/test_crewai_system.py                        | Backend      | ⬜ Todo      | System-level agentic workflow coverage                       |
| backend/test_crewai_with_litellm.py                  | Backend      | ⬜ Todo      | Validate LLM integration points                              |
| backend/test_deepinfra.py                            | Backend      | ⬜ Todo      | Fix imports, validate deepinfra integration                  |
| backend/test_deepinfra_llm.py                        | Backend      | ⬜ Todo      | LLM integration, fix imports                                 |
| backend/test_direct_api.py                           | Backend      | ⬜ Todo      | Direct API calls, update endpoints                           |
| backend/test_enhanced_field_mapping.py               | Backend      | ⬜ Todo      | Fix field mapping logic, ensure agentic learning             |
| backend/test_hanging_debug.py                        | Backend      | ⬜ Todo      | Debug hanging test logic, update as needed                   |
| backend/test_initialization_debug.py                 | Backend      | ⬜ Todo      | Initialization sequence, fix imports                         |
| backend/test_learning_system.py                      | Backend      | ⬜ Todo      | Learning system, agentic memory                              |
| backend/test_memory_system.py                        | Backend      | ⬜ Todo      | Memory system, multi-tenant coverage                         |
| backend/test_modular_rbac.py                         | Backend      | ⬜ Todo      | RBAC logic, fix imports                                      |
| backend/test_modular_rbac_api.py                     | Backend      | ⬜ Todo      | RBAC API, endpoints, fix imports                             |
| backend/test_monitored_execution.py                  | Backend      | ⬜ Todo      | Execution monitoring, agentic fallback                       |
| backend/test_multitenant_workflow.py                 | Backend      | ⬜ Todo      | Multi-tenant logic, context-aware repo                       |
| backend/test_no_thinking_mode.py                     | Backend      | ⬜ Todo      | No-thinking agentic fallback                                 |
| backend/test_production_ready.py                     | Backend      | ⬜ Todo      | Production-readiness, error/fallback coverage                |
| backend/test_rbac_only.py                            | Backend      | ⬜ Todo      | RBAC logic, fix imports                                      |
| backend/test_simple_analysis.py                      | Backend      | ⬜ Todo      | Simple analysis, fix imports                                 |
| backend/test_sixr_analysis.py                        | Backend      | ⬜ Todo      | 6R logic, agentic workflow                                   |
| backend/test_task_execution_debug.py                 | Backend      | ⬜ Todo      | Task execution, debug logic                                  |
| backend/test_smoke.py                               | Backend      | 🟡 In Progress | Backend service/endpoint/agentic smoke test. Ensures all core services, endpoints, and CrewAI initialization succeed after restart. Run after every deploy/restart. |
| frontend/demoMode.spec.ts                            | Frontend     | ⬜ Todo      | Expand for all demo flows, agentic UI fallback               |
| e2e/admin-interface.spec.ts                          | E2E          | ⬜ Todo      | Admin flows, multi-tenant checks                             |
| e2e/data-import-flow.spec.ts                         | E2E          | ⬜ Todo      | Data import, error handling                                  |
| e2e/debug-admin.spec.ts                              | E2E          | ⬜ Todo      | Admin debug, agentic fallback                                |
| e2e/debug-login.spec.ts                              | E2E          | ⬜ Todo      | Login, session switching                                     |
| e2e/simple-login.spec.ts                             | E2E          | ⬜ Todo      | Minimal login, fallback                                      |
| e2e/sixr_workflow.spec.ts                            | E2E          | ⬜ Todo      | 6R workflow, agentic path                                    |
| e2e/test_agent_user_interaction.py                   | E2E Python   | ⬜ Todo      | Agentic user flow, multi-tenant scenarios                    |

---

**Legend:**
- ⬜ Todo: Needs remediation
- 🟡 In Progress: Being remediated
- ✅ Complete: Fully passing and covered

---

## 7. Backend Smoke Test (Baseline Health Check)

A new file, `backend/test_smoke.py`, has been added. This test suite ensures:
- All critical backend modules and agentic services can be imported and initialized.
- CrewAI service and AgentManager initialize successfully.
- The `/health` endpoint is live and returns `200 OK`.
- The `/api/v1/discovery/analyze` endpoint is available and returns a valid response (200 or 422).

**Purpose:**
- Run this test after every backend restart or deploy to catch initialization errors before debugging application logic.
- If this test fails, troubleshoot initialization or import errors before deeper debugging.

Update the remediation tracker as this smoke test is stabilized and fully passing.

---

## 8. Next Steps
- Remediate each file/area above, updating the tracker as progress is made.
- Rerun coverage after each round of fixes.
- Expand tests for newly added/changed features.
- Enforce coverage thresholds in CI/CD.

---

_This file should be updated after each remediation step. For questions or to update the tracker, edit this markdown directly or via PR._
