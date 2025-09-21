## Questionnaire → Database Persistence Mapping

Mapping Rules
- Prefer `question_id == field_name` for simple fields to minimize ambiguity.
- For complex or multi-target fields, use a server-side mapping registry with handlers.
- Use idempotent upserts per response batch.
- Capture provenance in lifecycle and normalization tables where applicable.

Mapping Registry (service-layer)
```python
QUESTION_TO_TABLE_MAPPING = {
  "vendor_product": {"tables": ["tenant_vendor_products", "asset_product_links"], "handler": "map_vendor_product"},
  "product_version": {"tables": ["tenant_product_versions", "asset_product_links"], "handler": "map_product_version"},
  "lifecycle_dates": {"tables": ["lifecycle_milestones"], "handler": "map_lifecycle_dates"},
  "rto_rpo": {"tables": ["asset_resilience"], "handler": "map_resilience_metrics"},
  "maintenance_window": {"tables": ["maintenance_windows"], "handler": "map_maintenance_window"},
  "dependency_mapping": {"tables": ["asset_dependencies"], "handler": "map_dependencies"},
}

# Batch configuration
BATCH_CONFIG = {
  "default_size": 500,
  "max_size": 1000,
  "timeout_ms": 5000
}
```

Examples
- Lifecycle
  - question_id: `vendor_product` → link/create in `vendor_products`
  - question_id: `product_version` → `product_versions`
  - question_id: `end_of_life_date` → `lifecycle_milestones (end_of_life)` for linked product_version

- Resilience
  - `rto_minutes` → `asset_resilience.rto_minutes`
  - `rpo_minutes` → `asset_resilience.rpo_minutes`
  - `sla_targets` → `asset_resilience.sla_json`

- Compliance
  - `compliance_scopes` → `asset_compliance_flags.compliance_scopes`
  - `data_classification` → `asset_compliance_flags.data_classification`
  - `residency` → `asset_compliance_flags.residency`
  - `evidence_upload` → `asset_compliance_flags.evidence_refs`

- Operations
  - `maintenance_window` → `maintenance_windows`
  - `blackout_period` → `blackout_periods`

- Licensing
  - `license_type` → `asset_licenses.license_type`
  - `license_renewal_date` → `asset_licenses.renewal_date`
  - `contract_reference` → `asset_licenses.contract_reference`

- Dependencies
  - `dependency_mapping` → bulk rows in `asset_dependencies` with `relationship_nature`, `direction`, `criticality`, `dataflow_type`

- Governance
  - `exception_request` → `migration_exceptions` (+ optional `approval_requests`)

Idempotency
- Compute a deterministic key per response: `{asset_id}:{question_id}` or `{flow_id}:{question_id}:{scope}`.
- Use atomic transactions; update existing records matching key.

Validation & Errors
- Validate dates and numeric ranges; return structured errors for invalid input.


