## API Design: Collection Gaps (Phase 1)

Conventions
- snake_case payloads; tenant headers `X-Client-Account-ID`, `X-Engagement-ID` mandatory.
- Structured errors only; never mock results.

Collection Flow
- POST `/api/v1/collection/flows`
  - Body: `{ flow_name, subject: { scope: 'tenant'|'engagement'|'application'|'asset'|'domain', ids?: string[], domain_type?: 'operations'|'compliance'|'licensing'|'lifecycle' }, automation_tier? }`
  - Returns: `{ id, flow_id, subject, collection_config, current_phase }`

- GET `/api/v1/collection/flows/{flow_id}`
  - Returns: flow details + `completeness_by_category`, `pending_gaps`

- POST `/api/v1/collection/flows/{flow_id}/questionnaires/generate`
  - Request body (Pydantic model): `{ categories: Optional[List[str]], priority: Optional[Literal['critical','high','all']] }`
  - Returns: `[ AdaptiveQuestionnaire ]`

- POST `/api/v1/collection/flows/{flow_id}/responses`
  - Body: `{ responses: [ {question_id, response_value, asset_id?, application_id?, metadata?} ] }`
  - Behavior: idempotent bulk write; maps to target tables (see 07_persistence_mapping.md)
  - Returns: `{ upserted: n, by_target: {table: n} }`

- GET `/api/v1/collection/flows/{flow_id}/gaps`
  - Returns: `{ critical: [...], high: [...], optional: [...] }`

Catalogs & Lifecycle
- GET `/api/v1/catalog/vendor-products?query=...`
- POST `/api/v1/catalog/vendor-products`
- GET `/api/v1/catalog/vendor-products/{id}/versions`
- POST `/api/v1/catalog/vendor-products/{id}/versions`
- POST `/api/v1/lifecycle/milestones:refresh` (async; adapter-based)

Operations
- CRUD `/api/v1/operations/maintenance-windows`
- CRUD `/api/v1/operations/blackout-periods`

Licensing
- CRUD `/api/v1/licenses/assets`

Governance
- CRUD `/api/v1/governance/approval-requests`
- CRUD `/api/v1/governance/migration-exceptions`

Dependency Management
- POST `/api/v1/assets/{asset_id}/dependencies` (bulk upsert with new fields)
- GET `/api/v1/assets/{asset_id}/dependencies`

Polling & Status
- GET `/api/v1/collection/flows/{flow_id}/status` → standard polling pattern (5s active/15s waiting)

Security & Validation
- All endpoints: tenant scoping in repositories.
- Request size limits and per-tenant rate limits (configurable).

MFO Integration
- All collection flows are created and tracked under `crewai_flow_state_extensions` via MasterFlowOrchestrator.
- `collection_flows.master_flow_id` must be set and used for lifecycle and status transitions per ADR-006.


