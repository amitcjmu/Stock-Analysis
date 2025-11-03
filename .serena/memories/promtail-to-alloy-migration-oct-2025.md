# Promtail to Alloy Migration - October 31, 2025

## Decision
Migrated from Promtail to Grafana Alloy for log collection.

## Reason
Promtail deprecated with EOL March 2, 2026. Grafana Alloy is the strategic replacement.

## Timeline
- **LTS Start**: February 13, 2025 (critical fixes only)
- **EOL Date**: March 2, 2026 (no further support)
- **Migration**: October 31, 2025 (proactive, before EOL)

## Changes Made
1. **docker-compose.observability.yml**: Replaced `promtail` service with `alloy` service
2. **Removed**: `observability/promtail-config.yaml`
3. **Using**: `observability/alloy-config.alloy` (unified config)
4. **Ports**: 12345 (Alloy UI/API), 4317 (OTLP gRPC), 4318 (OTLP HTTP)

## Verification
✅ All Grafana dashboard panels working
✅ Logs flowing to Loki correctly
✅ Error logs showing full details
✅ Phase transition logs visible

## Benefits
- **Unified collector**: Logs + Traces + Metrics in one agent
- **OTLP support**: Native OpenTelemetry compatibility
- **Future-proof**: Active development, long-term support
- **Performance**: More efficient than multiple agents

## Access
- Alloy UI: http://localhost:12345
- Alloy Ready: http://localhost:12345/-/ready

## Reference
Migration summary: `/tmp/promtail-to-alloy-migration-summary.md`
Dashboard screenshot: `.playwright-mcp/alloy-dashboard-verification.png`

## Note
Promtail was a fallback due to previous Alloy installation issues. This migration completes the proper Alloy setup without fallbacks.
