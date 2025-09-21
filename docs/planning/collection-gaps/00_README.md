## Collection Gaps: 7-Layer Design and Implementation Plan (Phase 1)

Purpose
- Provide a concrete, agentic-first design to evolve the Collection Flow beyond application-only initiation, enabling capture of broader data gaps (lifecycle/EoL, resilience RTO/RPO, compliance/residency, operational windows, licensing, dependency metadata, approvals/exceptions) across tenants, engagements, assets, and applications.
- Define changes across all 7 layers of the platform: API, Service, Repository, Model, Cache/Queue, Integration (agents/tools), and Frontend.

Key Outcomes
- Collection Flow can start with a configurable subject: tenant/engagement-wide, application, asset, or platform domain (ops/compliance/licensing).
- Adaptive questionnaires target all identified gaps; responses persist into normalized, tenant-scoped tables.
- Vendor lifecycle (EoL/EoS/EOSL) enrichment with provenance; manual fallback via questionnaires.
- Dependency capture UI and persistence (directionality, dataflow type, criticality).
- RTO/RPO, compliance scope, maintenance/blackout windows, licensing, approvals/exceptions captured and available for planning and wave scheduling.

Documents in this folder
- 01_requirements.md  — Minimal dataset vs current, and explicit gap list
- 02_architecture_7_layers.md — Layer-by-layer design (what changes and why)
- 03_schema_changes.sql.md — DB tables/columns, constraints, migration guidance
- 04_api_design.md — Endpoints, payloads, error contracts, polling
- 05_agent_integration.md — CrewAI tools, memory, gap detection, questionnaire generation
- 06_frontend_collection_flow.md — UX flow changes, components, field types
- 07_persistence_mapping.md — Questionnaire → DB mapping, idempotency
- 08_migration_plan.md — Rollout, backfills, feature flags, risk controls
- 09_telemetry_and_success_metrics.md — Metrics, dashboards, acceptance criteria

Reading Order
1) 01_requirements.md
2) 02_architecture_7_layers.md
3) 03_schema_changes.sql.md + 04_api_design.md
4) 05_agent_integration.md
5) 06_frontend_collection_flow.md
6) 07_persistence_mapping.md
7) 08_migration_plan.md + 09_telemetry_and_success_metrics.md


