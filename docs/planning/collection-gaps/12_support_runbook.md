## Support Runbook (Collection Gaps Phase 1)

Common Issues
- Continue flow shows no questionnaires → Verify MFO linkage; check `/status`; ensure feature flag enabled.
- 422 on responses → Validate question_id vs mapping registry; inspect server logs for handler errors.
- Catalog mismatch → Use vendor/product picker; if missing, add tenant override; avoid free-text when possible.
- Slow bulk saves → Reduce batch size to 500; check DB pool size; verify indexes present.

Diagnostics
- API: `/health`, `/collection/flows/{id}`, `/collection/flows/{id}/gaps`.
- DB: count rows in new tables; verify tenant scoping in queries.
- Agents: verify TenantScopedAgentPool and memory patch loaded; check agent logs.

Data Validation Queries
```sql
-- Orphaned lifecycle milestones (no asset links)
SELECT COUNT(*) AS orphaned_milestones
FROM migration.lifecycle_milestones lm
WHERE NOT EXISTS (
  SELECT 1 FROM migration.asset_product_links apl
  WHERE apl.catalog_version_id = lm.catalog_version_id
     OR apl.tenant_version_id = lm.tenant_version_id
);
```

Rollback Steps
- Disable `collection.gaps.v1` flag; UI hides fields; data preserved.

Escalation
- If lifecycle adapter stalls: switch to manual capture; log provenance and retry schedule.

Performance Baselines
- Track collection flow completion time pre-change; target ≤20% increase.
- Alert if runtime >2x baseline; investigate batch sizes, DB pool, indexes.

