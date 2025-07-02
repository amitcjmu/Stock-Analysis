# Real-Time Updates Strategy (Without WebSockets)

## Why Not WebSockets?

Given the deployment architecture:
- **Frontend**: Vercel (serverless, no persistent connections)
- **Backend**: Railway (containerized)
- **Future**: AWS with multiple Docker instances

WebSockets would require:
- Sticky sessions
- Load balancer WebSocket support
- Complex state synchronization across instances
- Persistent connection management

## Recommended Approach: HTTP/2 with SSE and Smart Polling

### Option 1: Server-Sent Events (SSE) - Preferred
```python
# backend/app/api/v1/events.py
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter()

@router.get("/flows/{flow_id}/events")
async def flow_events(flow_id: str, request: Request):
    async def event_generator():
        last_state = None
        while True:
            if await request.is_disconnected():
                break
                
            # Get current flow state
            current_state = await get_flow_state(flow_id)
            
            # Only send if changed
            if current_state != last_state:
                yield {
                    "event": "flow_update",
                    "data": json.dumps(current_state),
                    "id": str(current_state.get("version", 0))
                }
                last_state = current_state
                
            await asyncio.sleep(1)  # Poll interval
            
    return EventSourceResponse(event_generator())
```

### Option 2: Smart HTTP Polling with ETags
```python
# backend/app/api/v1/discovery.py
from fastapi import Header, Response, status
import hashlib

@router.get("/flows/{flow_id}/status")
async def get_flow_status(
    flow_id: str,
    response: Response,
    if_none_match: Optional[str] = Header(None)
):
    flow_state = await get_flow_state(flow_id)
    
    # Generate ETag from state
    state_json = json.dumps(flow_state, sort_keys=True)
    etag = hashlib.md5(state_json.encode()).hexdigest()
    
    # Return 304 if not modified
    if if_none_match == etag:
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return None
        
    # Return data with ETag
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache"
    return flow_state
```

### Option 3: Push Notifications via Queue
```python
# backend/app/services/notification_service.py
from app.core.redis import redis_client
import json

class NotificationService:
    async def publish_flow_update(self, flow_id: str, update: dict):
        """Publish update to Redis for distribution"""
        channel = f"flow_updates:{flow_id}"
        await redis_client.publish(
            channel, 
            json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "flow_id": flow_id,
                "update": update
            })
        )
        
    async def get_pending_updates(self, flow_id: str, since: datetime):
        """Get updates since timestamp"""
        key = f"flow_updates_log:{flow_id}"
        updates = await redis_client.zrangebyscore(
            key,
            since.timestamp(),
            "+inf"
        )
        return [json.loads(u) for u in updates]
```

## Frontend Implementation

### React Hook for Real-Time Updates
```typescript
// src/hooks/useFlowUpdates.ts
import { useEffect, useState } from 'react';
import { EventSourcePolyfill } from 'event-source-polyfill';

export const useFlowUpdates = (flowId: string) => {
  const [flowState, setFlowState] = useState(null);
  const [error, setError] = useState(null);
  
  // Option 1: SSE
  useEffect(() => {
    const eventSource = new EventSourcePolyfill(
      `${API_URL}/flows/${flowId}/events`,
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      }
    );
    
    eventSource.addEventListener('flow_update', (e) => {
      const data = JSON.parse(e.data);
      setFlowState(data);
    });
    
    eventSource.onerror = (error) => {
      setError(error);
      // Fallback to polling
      startPolling();
    };
    
    return () => eventSource.close();
  }, [flowId]);
  
  // Option 2: Smart Polling Fallback
  const startPolling = () => {
    let etag = null;
    
    const poll = async () => {
      try {
        const headers = {
          'Authorization': `Bearer ${getAuthToken()}`,
          ...(etag && { 'If-None-Match': etag })
        };
        
        const response = await fetch(
          `${API_URL}/flows/${flowId}/status`,
          { headers }
        );
        
        if (response.status === 304) {
          // No changes
          return;
        }
        
        etag = response.headers.get('ETag');
        const data = await response.json();
        setFlowState(data);
      } catch (err) {
        setError(err);
      }
    };
    
    const interval = setInterval(poll, 2000); // 2s polling
    poll(); // Initial fetch
    
    return () => clearInterval(interval);
  };
  
  return { flowState, error };
};
```

## Architecture Benefits

### SSE Advantages
- Works with HTTP/2
- Auto-reconnect built-in
- Unidirectional (perfect for status updates)
- Works through proxies/load balancers
- Degrades gracefully to polling

### Smart Polling Advantages
- Simple and reliable
- Works everywhere
- ETags prevent unnecessary data transfer
- Easy to implement caching
- No special infrastructure needed

### Hybrid Approach
1. Try SSE first
2. Fall back to smart polling if SSE fails
3. Use Redis for cross-instance communication
4. Implement client-side state reconciliation

## Implementation Priority

1. **Phase 1**: Smart polling with ETags (quick win)
2. **Phase 2**: Add SSE support
3. **Phase 3**: Redis-based notification system
4. **Phase 4**: Add push notification support

## Infrastructure Requirements

### Current (Railway/Vercel)
- No special requirements
- Works with existing setup

### Future (AWS)
- Redis/ElastiCache for pub/sub
- CloudFront supports SSE
- ALB supports HTTP/2
- No sticky sessions needed

## Migration Path

1. Start with polling (already partially implemented via agent UI bridge)
2. Add ETag support for efficiency
3. Implement SSE endpoints
4. Add Redis for multi-instance coordination
5. Monitor and optimize based on usage patterns

This approach provides real-time updates without the complexity and limitations of WebSockets in a serverless/containerized environment.