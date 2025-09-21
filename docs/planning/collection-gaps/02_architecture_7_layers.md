## 7-Layer Architecture Changes for Collection Gaps (Phase 1)

Guiding Principles
- Agentic-first: all gap detection, question generation, and decisioning via CrewAI; no hard-coded thresholds.
- Multi-tenant: `client_account_id`, `engagement_id` on all reads/writes; ContextAwareRepository pattern.
- Orchestrated: Master Flow Orchestrator (MFO) remains source of truth; Collection Flow operates as child flow.
- Resilient: gracefull fallbacks; structured pending/not_ready errors; no mock data.

1) API Layer (FastAPI Routes)
- New/updated endpoints (under `/api/v1/collection` and unified flow orchestration):
  - POST `/collection/flows` — create collection flow with subject: {scope: tenant|engagement|application|asset|domain, ids: []}
  - GET `/collection/flows/{flow_id}` — includes `collection_config` subject and completeness by category
  - POST `/collection/flows/{flow_id}/questionnaires/generate` — agent-driven generation for all gap categories
  - POST `/collection/flows/{flow_id}/responses` — bulk upsert questionnaire responses (idempotent)
  - GET `/collection/flows/{flow_id}/gaps` — computed gaps with priorities
  - Catalog ops: GET/POST `vendor-products`, `product-versions`, `lifecycle-milestones`
  - Ops windows: CRUD `maintenance-windows`, `blackout-periods`
  - Licensing: CRUD `asset-licenses`
  - Governance: CRUD `approval-requests`, `migration-exceptions`

2) Service Layer (Business Logic)
- CollectionFlowService: add multi-subject kickoff; compute category completeness; delegate to Agent tools for gap analysis and questionnaire generation.
- ResponseMappingService: resolve `question_id` → target model(s), write idempotently; accumulate provenance.
- LifecycleEnrichmentService: plug-in adapters (vendor catalogs), cache results, update milestones and last_checked.
- DependencyService: validates mapping (directionality, criticality, dataflow_type).
- GovernanceService: approvals/exceptions workflows (status transitions).

3) Repository Layer (Data Access)
- Context-aware repos for each new entity: lifecycle, resilience, compliance, ops windows, licenses, governance.
- Bulk upserts with atomic transactions; explicit `migration` schema; idempotency keys per bulk write.

4) Model Layer (SQLAlchemy/Pydantic)
- New tables (see 03_schema_changes.sql.md):
  - `vendor_products`, `product_versions`, `lifecycle_milestones`, `asset_product_links`
  - `asset_resilience`, `asset_compliance_flags`, `asset_vulnerabilities`
  - `maintenance_windows`, `blackout_periods`, `asset_licenses`
  - `approval_requests`, `migration_exceptions`
- Extensions:
  - `asset_dependencies`: add `relationship_nature`, `direction`, `criticality`, `dataflow_type`.
  - `assets`: optional foreign keys to the above or JSON refs where appropriate.

5) Cache/Queue Layer
- Redis keys tenant-scoped for questionnaire generation results and completeness snapshots.
- Optional background jobs queue to sync lifecycle adapters; publish structured events for UI polling.

6) Integration Layer (Agents/Tools)
- GapAnalysisTool: compute missing fields across all categories given subject scope.
- QuestionnaireGenerationTool: enforce `question_id == field_name` for deterministic mapping.
- VendorLifecycleTool: search/normalize vendor→product→version; record provenance and confidence.
- DependencyGraphTool: assist with suggested dependencies from telemetry; confirm via UI.

7) Frontend Layer (Next.js)
- Collection Flow start wizard: choose subject scope (tenant/app/asset/domain) and targets.
- Adaptive Forms: new field types (date_input, numeric_input, multi_select, dependency_mapping, technology_selection); sectioned by category (basic, technical, compliance, operations, licensing, lifecycle, dependencies, governance).
- Completeness and blockers dashboard per category; provenance hover states; last-checked badges.

Error Contracts
- Never return mock data. Use: `{status: 'pending'|'not_ready', error_code, details}`.

Security
- Tenant isolation everywhere; PII minimization; safe serialization and parameterized SQL.


