# Legacy Archival Documentation

This section inventories legacy and deprecated code paths to remove or migrate, aligned with the agentic-first, flow-based architecture. Use these docs to plan removals, prevent regressions, and track progress.

## Scope
- Legacy discovery endpoints and handlers
- Misuse of `asyncio.run()` in application code (not scripts/tests)
- WebSocket usage slated for deprecation in favor of HTTP polling
- Frontend legacy components, hooks, and services
- Tests and docs referencing legacy APIs

## How to Use
1. Review the latest inventory snapshot (00_legacy-inventory-YYYY-MM-DD.md).
2. For each topic-specific doc, follow the migration paths and action items.
3. Keep removals tenant-safe and agentic-first; avoid reintroducing hard-coded rules.

## Index
- 00_legacy-inventory-2025-09-06.md
- 01_legacy-discovery-endpoints.md
- 02_asyncio-run-misuse.md
- 03_websocket-usage-and-deprecation-plan.md
- 04_frontend-legacy-components-and-services.md
- 05_tests-and-docs-with-legacy-references.md


