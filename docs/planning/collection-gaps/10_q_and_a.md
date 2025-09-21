## Q&A: Critical Questions

1) Vendor Catalog Scoping
- Use global `vendor_products_catalog` and `product_versions_catalog` for shared data.
- Tenants can add overrides/additions via `tenant_vendor_products` and `tenant_product_versions`.
- Asset links can reference either catalog or tenant versions; isolation preserved.

2) Performance at Scale (10K+ assets/tenant)
- Composite indexes on foreign keys; batched upserts; pagination on queries.
- Precompute completeness snapshots in Redis; avoid heavy joins in UI paths.
- Async adapter refresh jobs throttled per tenant.

3) Backward Compatibility
- Feature flags around writes; new fields optional initially.
- Existing flows continue app-scoped; start-wizard adds broader scopes without breaking existing routes.

4) Agent Tool Conflicts
- Register new tools in ServiceRegistry; avoid per-call crew instantiation.
- Tools publish structured outputs; mapping registry coordinates writes.

5) Data Migration / Backfill
- Lightweight backfills for resilience/compliance rows.
- Heuristic prefill for vendor/product from OS/stack where unambiguous; mark provenance as heuristic.

6) Validation Rules Location
- Basic shape/range constraints in DB (CHECKs) for safety.
- Business rules in service layer; dynamic thresholds and recommendations in agents.

