## Tactical Execution Plan (4 Weeks)

Week 1: Foundation
- Fix collection continuation bugs (per transition plan v4): continue-button questionnaires, 422s, incomplete flow blocking.
- Implement feature flags (service-layer) and UI gating.
- Implement AgentToolRegistry.

Week 2: Schema & Backend
- Deploy global+tenant catalog tables and indexes.
- Implement mapping registry service and idempotent bulk responses.
- Add resilience (`asset_resilience`) and operations (`maintenance_windows`, `blackout_periods`).

Week 3: Agent Integration
- Update GapAnalysisTool to flag lifecycle (vendor/product/EoL), RTO/RPO, maintenance windows.
- Implement simplified QuestionnaireGenerationTool for the above categories.
- Validate with TenantScopedAgentPool.

Week 4: Frontend MVP
- Add `date_input` and `numeric_input` field types; maintenance window simple form.
- End-to-end tests with 3 pilot tenants; shadow mode for 1 week.

Risk Mitigation
- Read-only catalog start; circuit breakers and timeouts; rollback handlers; staging automated rollback tests.


