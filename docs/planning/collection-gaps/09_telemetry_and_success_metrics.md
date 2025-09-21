## Telemetry and Success Metrics

Metrics (tenant-scoped)
- Lifecycle coverage: % assets with vendor+product+version+EoL/EoS.
- Resilience capture: % assets with RTO & RPO.
- Compliance capture: % assets with scopes + classification.
- Ops constraints: # windows/blackouts per app/asset; scheduling conflicts avoided.
- Licensing capture: % assets with renewal date.
- Dependency quality: % assets with dependencies; edges with direction/criticality.
- Questionnaire efficiency: completion time, drop-off rate, validation error rate.
- Agent confidence: median confidence in 6R decisions pre/post data capture.

Dashboards
- Category completeness heatmap; blockers; last-checked lifespan for lifecycle.

Alerts
- Lifecycle data older than N days; licenses near renewal; blackout conflicts with planned waves.

Monitoring & Alerting
- Export metrics to Grafana (existing stack); define thresholds:
  - Lifecycle coverage < 50% (warn), < 30% (critical)
  - Response mapping failures > 1% (warn)
  - Batch latency P95 > 2s (warn), > 5s (critical)
- Dashboards: category completeness, queue/backlog, error rates, agent confidence trends.

Go / No-Go Criteria
- GO: collection bugs fixed, feature flags on, integration tests passing, pilot tenant ready, rollback tested.
- NO-GO: unresolved critical bugs, no monitoring, performance untested, no rollback validation.

Success Timeline (Phase 1)
- Week 1: 50% lifecycle (vendor/product only)
- Week 2: Add EoL/EoS for top 100 products
- Week 3: 60% assets with RTO/RPO
- Week 4: 70% coverage, 0.60 confidence; shadow mode wrap-up


