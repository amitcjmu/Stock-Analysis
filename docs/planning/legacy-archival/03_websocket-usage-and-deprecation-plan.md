# WebSocket Usage and Deprecation Plan

## Context
Production standard is HTTP polling (Vercel). WebSockets exist for cache events and analysis streaming.

## Findings
### Backend
- `backend/app/api/v1/endpoints/websocket_cache.py` (ws-cache events)
- `backend/app/services/websocket_cache_events.py` (manager and lifecycle)
### Frontend
- `src/lib/api/sixr.ts` (WebSocketManager)
- `src/hooks/useWebSocket.ts`, `src/hooks/useSixRWebSocket.ts`
- `src/contexts/GlobalContext/index.tsx` (connection management)

## Risks
- Vercel edge/serverless incompatibilities; CI banned patterns list flags WebSocket usage.

## Deprecation Strategy
- Short term: Feature-flag WS usage (`NEXT_PUBLIC_ENABLE_WEBSOCKETS=false` by default) on frontend; mirror with backend env flag.
- Mid term: Replace cache invalidation WS with polling endpoints; provide sixr progress polling; keep parity tests.
- Long term: Remove WS code paths and tests; consolidate on polling utilities.

## Action Items
- Add env flag `NEXT_PUBLIC_ENABLE_WEBSOCKETS=false` default; ensure all WS hooks respect it.
- Create polling equivalents for WS endpoints (cache events, sixr progress) and migrate consumers.
- Remove WS code after parity verified in staging.

## Feature Flag Implementation
1. Backend (settings):
```python
import os

ENABLE_WEBSOCKETS = os.getenv("ENABLE_WEBSOCKETS", "false").lower() == "true"
```

2. Frontend (hooks):
```typescript
if (!process.env.NEXT_PUBLIC_ENABLE_WEBSOCKETS) {
  return usePollingFallback();
}
```


