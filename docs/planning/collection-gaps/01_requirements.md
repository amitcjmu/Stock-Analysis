## Phase 1 Requirements: Minimal Dataset vs Current and Gap List

Context
- Current collection flow starts with application selection, constraining gap capture to app-scoped data.
- Phase 1 expands collection to tenant- and asset-level attributes: lifecycle/EoL, resilience (RTO/RPO), compliance/residency, operational windows, licensing, dependency metadata, approvals/exceptions.

Minimal Viable Dataset (expanded)
- Identification: asset/app IDs; vendor, product, version (normalized); environment; owners.
- Lifecycle: end_of_life_date, end_of_support_date, extended_support_end, provenance, last_checked_at.
- Resilience: rto_minutes, rpo_minutes, sla_targets (uptime, response/resolution), dr_ha_posture.
- Compliance & data: compliance_scopes [SOX/HIPAA/PCI/GDPR/...], data_classification, residency, evidence_refs.
- Dependencies: upstream/downstream assets/services, relationship_nature, direction, criticality, dataflow_type.
- Operations: maintenance_windows, blackout_periods (tenant/app/asset scope), change windows.
- Licensing: license_type, renewal_date, contract_reference, support_tier.
- Governance: approvers, approval_requests (strategy/schedule/exception), migration_exceptions.

Current Coverage (high-level)
- Backend: `assets` rich core; `asset_dependencies`; `migration_waves`; `collection_flows`, `collection_gap_analysis`, `adaptive_questionnaires`, `collection_questionnaire_responses`. No normalized vendor lifecycle tables. No RTO/RPO fields. No ops windows/licensing/compliance normalization. Exceptions/approvals only in niche areas.
- Frontend: Adaptive forms pipeline; app selection; tech/business basics. Missing explicit inputs for lifecycle dates, resilience, ops windows, licensing, dependency mapping UX, generalized approvals.

Gaps to Close in Phase 1
- Normalized vendor lifecycle model and asset linkage.
- Resilience (RTO/RPO/SLA) capture and persistence.
- Compliance flags and data classification; optional CVE overlay stub.
- Maintenance/blackout windows at client/app/asset scope.
- Licensing/contracts linkage to assets/apps.
- General approvals and exception register.
- Dependency mapping enhancements (directionality, criticality, dataflow type) with UI capture.
- Adaptive questionnaires that target all above gaps and persist responses into normalized tables.

Non-Goals (Phase 1)
- Full automation for external lifecycle catalog sync; provide adapter interfaces + manual fallback.
- Deep CVE ingestion pipeline; add schema + UI capture hooks only.
- Execution-phase runbooks; this phase focuses on assessment & planning data readiness.

Success Criteria
- ≥95% of in-scope assets/apps have lifecycle + resilience + compliance + operations + licensing + dependency metadata.
- All captured with provenance, tenant isolation, and structured errors instead of mock data.
- Agent 6R recommendations median confidence ≥0.75; wave planning respects blackout/maintenance windows 100%.


