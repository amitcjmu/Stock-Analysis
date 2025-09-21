## Migration & Rollout Plan

Phasing
- Phase A: Schema migrations (idempotent), repositories, read-only endpoints.
- Phase B: Agent tools updated; questionnaire generation for new categories.
- Phase C: Frontend fields & widgets; responses write to new tables.
- Phase D: Lifecycle adapter pilot; governance workflows.

Backfills
- Map existing `assets.technology_stack`, `os_version`, and imports to seed `vendor_products/product_versions` when unambiguous.
- Create placeholder resilience/compliance rows for in-scope assets.

Feature Flags
- Feature flags (service-layer): `collection.gaps.v1` to gate API writes; UI reads flag from capabilities.

Rollback Handlers
```python
class CollectionGapsFeatureFlag:
    @staticmethod
    async def rollback_phase_1():
        # 1. Disable feature flag in config/DB
        # 2. Hide UI (capabilities off)
        # 3. Preserve data (non-destructive)
        # 4. Log rollback metrics/events for audit
        return {"status": "rolled_back"}
```

Risk Controls
- Strict tenant scoping; structured errors; retries with idempotency keys.
- Circuit breakers for long-running queries; request timeouts; staged rollouts (shadow mode).

Rollback
- Disable flag; data remains; no destructive migrations.

Integration Testing Plan
- Catalog lookups: 1K vendors, verify overrides precedence.
- Questionnaire generation: 100+ applications; ensure MFO state sync.
- Bulk responses: 500+ responses; idempotent writes; latency < P95 1s per batch.
- Flow continuation: ensure continue-button loads questionnaires; resolve 422 blockers; incomplete flows handling.


