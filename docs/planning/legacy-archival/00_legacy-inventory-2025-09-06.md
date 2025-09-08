# Legacy Inventory — 2025-09-06

This snapshot lists legacy or deprecated code to remove or migrate. Validate each item before deletion to avoid breaking dynamic agent flows.

## Summary
- Legacy discovery endpoints guarded and deprecated; references persist in tests/docs.
- `asyncio.run()` appears inside some application services/tools (not only scripts/tests).
- WebSocket usage exists in frontend hooks/components and backend endpoints; platform standard is HTTP polling for Vercel.
- Frontend retains deprecated hooks/services and backup components referenced in prior cleanup docs.

## Items

### Backend — Legacy Discovery
- `backend/app/middleware/legacy_endpoint_guard.py`: hard-blocks `/api/v1/discovery/*` (410 Gone) with migration hints.
- `backend/app/api/v1/endpoints/discovery_DEPRECATED/`: module raises on import; kept for historical reference.
- `backend/app/api/v1/endpoints/discovery.py`: legacy router that redirects to unified discovery.
- Tests referencing legacy endpoints (examples):
  - `tests/backend/integration/test_end_to_end_workflow.py`
  - `tests/backend/test_multitenant_workflow.py`
  - `tests/docker/test_docker_containers.py`

### Backend — `asyncio.run()` in app code
- `backend/app/services/tools/base_tool.py` (`AsyncBaseDiscoveryTool.run`)
- `backend/app/services/agents/intelligent_flow_agent/tools/status_tool.py` (thread + `asyncio.run` patterns)
- `backend/app/services/crewai_flows/tools/asset_creation_tool_legacy.py`
- Note: `scripts/`, `tests/`, and `seeding/` usage is acceptable; focus is app code.

### WebSockets — Backend/Frontend
- Backend endpoints/handlers:
  - `backend/app/api/v1/endpoints/websocket_cache.py`
  - `backend/app/services/websocket_cache_events.py`
- Frontend usage:
  - `src/lib/api/sixr.ts` (WebSocketManager)
  - `src/hooks/useWebSocket.ts`, `src/hooks/useSixRWebSocket.ts`
  - `src/contexts/GlobalContext/index.tsx` (ws connection)
  - Tests: `tests/frontend/integration/test_discovery_flow_ui.test.tsx`, e2e utilities

### Frontend — Legacy Components/Services (to confirm/remove)
- From prior cleanup docs:
  - `src/services/FlowService.ts` (Legacy services with console warnings)
  - `src/hooks/useFlow.ts` (deprecated hook)
  - `src/utils/api/apiTypes.ts` (legacy types)
  - Backup/example components under `src/components/**.backup` or examples

## Next Steps
- See topic docs for migration paths and concrete action lists.

## Verified & Safe-To-Remove Candidates (post-test-migration)
- Deprecated legacy discovery router/package after tests are migrated:
  - `backend/app/api/v1/endpoints/discovery_DEPRECATED/`
  - `backend/app/api/v1/endpoints/discovery.py`
- Legacy tool (no active usage observed):
  - `backend/app/services/crewai_flows/tools/asset_creation_tool_legacy.py`

## Critical Observations
- Legacy endpoint guard actively blocks `/api/v1/discovery/*`.
- `AsyncBaseDiscoveryTool` and `asset_creation_tool_legacy` appear unused; validate import graph prior to removal.
- The largest blocker is test suites still calling legacy endpoints; migrate them first.

## Recommended Action Plan (Phased)
1) Immediate
   - Remove `asset_creation_tool_legacy.py` if import graph confirms unused.
   - Mark `AsyncBaseDiscoveryTool` deprecated or remove if unused.
2) Medium Priority
   - Refactor `asyncio.run()` usage in app code to safe async patterns.
   - Migrate all tests to `/api/v1/flows/*` or `/api/v1/unified-discovery/*`.
3) Long-Term (Feature-Flagged)
   - Introduce `NEXT_PUBLIC_ENABLE_WEBSOCKETS` (default false) and backend flag.
   - Provide HTTP polling alternatives; gradually migrate consumers.
4) Final Cleanup
   - Remove legacy discovery packages and frontend legacy services after verification.
   - Archive this inventory as completed.

## Quick Wins (Can Be Done Immediately with Zero Risk)
- Remove `backend/app/services/crewai_flows/tools/asset_creation_tool_legacy.py` (confirmed no imports)
- Add deprecation warnings to `AsyncBaseDiscoveryTool` class in `base_tool.py`
- Create GitHub issues for each test file migration (11 files total)


