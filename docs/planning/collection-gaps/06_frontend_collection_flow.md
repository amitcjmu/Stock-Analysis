## Frontend: Collection Flow Modifications (Next.js)

Goals
- Allow starting collection by subject scope: tenant, engagement, application(s), asset(s), or domain (operations/compliance/licensing/lifecycle).
- Capture all gap categories with appropriate field widgets and persist via unified responses API.

Key Changes
- Start Wizard (new): choose scope + targets; pre-seed `collection_config.subject`.
- Adaptive Forms: extend field types and sections
  - Field types: `date_input` (EoL/EoS), `numeric_input` (rto_minutes, rpo_minutes), `multi_select` (compliance_scopes), `dependency_mapping` (interactive graph), `technology_selection` (vendor/product/version picker), `file_upload` (evidence/contract docs).
  - Sections: basic, technical, infrastructure, lifecycle, resilience, compliance, operations, licensing, dependencies, governance.
- Vendor/Product Picker: suggests normalized entries; fallback free-entry with agent normalization.
- Dependency Mapping: UI to add edges with `relationship_nature`, `direction`, `criticality`, `dataflow_type`.
- Completeness Dashboard: category badges; blockers; last-checked/provenance tooltips.
- Polling: standard 5s/15s; error banners use structured error codes.

Conventions & Existing Patterns
- snake_case only in new interfaces and API types (see CLAUDE.md).
- Reuse `ThreeColumnFieldMapper` where appropriate for complex attribute groups.
- Respect existing `AdaptiveForms.tsx` guard patterns (initialization refs; continue-flow fixes).

Phased UI Scope (Phase 1)
- Include: lifecycle dates (EoL/EoS), rto/rpo, maintenance windows.
- Defer: compliance matrices, licensing documents, visual dependency graphs (start with table-based editor).

API Usage
- Use `/collection/flows` to initialize with subject; `/questionnaires/generate` to load forms; `/responses` to save.
- Always include tenant headers; preserve snake_case.

UX Safeguards
- Save draft frequently; idempotent bulk saves.
- Guard against re-initialization loops (existing ref guards in `AdaptiveForms.tsx`).


