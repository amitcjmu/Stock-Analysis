# Task Brief: python-crewai-fastapi-expert

## Mission
Implement the FastAPI backend components for the Redis caching solution, including middleware, cache invalidation services, WebSocket events, and security measures to achieve 70-80% reduction in API calls.

## Context
The platform experiences excessive API calls due to lack of proper caching. Your task is to implement server-side caching with proper invalidation, ETag support, and real-time cache synchronization via WebSockets.

## Primary Objectives

### 1. Cache Middleware Implementation (Week 1)
- Create FastAPI middleware for cache operations
- Implement ETag generation and validation
- Add cache headers to responses
- Integrate OpenTelemetry for distributed tracing

### 2. Cache Invalidation Service (Week 2)
- Build centralized CacheInvalidationService
- Implement WebSocket cache invalidation events
- Create invalidation triggers for all entity types
- Design cascade invalidation patterns

### 3. API Endpoint Enhancement (Week 2-3)
- Modify endpoints to use Redis caching
- Add conditional request support (If-None-Match)
- Implement request coalescing
- Add cache-aware error handling

### 4. Security Implementation (Week 3)
- Implement field-level encryption for sensitive data
- Add cache access auditing
- Ensure multi-tenant isolation
- Create cache security middleware

## Specific Deliverables

### Week 1 Deliverables

```python
# 1. Cache Middleware
# File: backend/app/middleware/cache_middleware.py
from fastapi import Request, Response
from app.services.caching import RedisCache
import hashlib
import json

class CacheMiddleware:
    def __init__(self, redis: RedisCache):
        self.redis = redis
    
    async def __call__(self, request: Request, call_next):
        # Check if request is cacheable
        if request.method == "GET" and self.is_cacheable(request.url.path):
            # Generate cache key
            cache_key = self.generate_cache_key(request)
            
            # Check ETag
            if if_none_match := request.headers.get("If-None-Match"):
                cached_etag = await self.redis.get(f"{cache_key}:etag")
                if cached_etag == if_none_match:
                    return Response(status_code=304)
            
            # Check cache
            cached_response = await self.redis.get(cache_key)
            if cached_response:
                return JSONResponse(
                    content=cached_response["data"],
                    headers={
                        "ETag": cached_response["etag"],
                        "X-Cache": "HIT",
                        "Cache-Control": cached_response["cache_control"]
                    }
                )
        
        # Process request
        response = await call_next(request)
        
        # Cache response if appropriate
        # Implementation continues...
```

```python
# 2. Cache Invalidation Service
# File: backend/app/services/cache_invalidation.py
from app.services.caching import RedisCache
from app.services.websocket import broadcast_event

class CacheInvalidationService:
    def __init__(self, redis: RedisCache):
        self.redis = redis
    
    async def on_field_mapping_bulk_operation(self, import_id: str):
        """Invalidate field mappings after bulk approval/rejection"""
        # Delete cache entries
        await self.redis.delete(f"v1:field_mappings:{import_id}")
        await self.redis.delete(f"v1:import:{import_id}:mappings")
        
        # Broadcast WebSocket event
        await broadcast_event({
            "type": "cache_invalidation",
            "entity": "field_mappings",
            "import_id": import_id,
            "action": "bulk_operation"
        })
    
    async def on_user_context_changed(self, user_id: str):
        """Invalidate user context and related caches"""
        await self.redis.delete(f"v1:user:context:{user_id}")
        await self._invalidate_pattern(f"v1:user:{user_id}:*")
        
        await broadcast_event({
            "type": "cache_invalidation",
            "entity": "user_context",
            "user_id": user_id
        })
```

### Week 2-3 Deliverables

```python
# 3. Enhanced API Endpoints
# File: backend/app/api/v1/endpoints/context.py
@router.get("/context/me", response_model=UserContextResponse)
async def get_user_context(
    request: Request,
    user: User = Depends(get_current_user),
    redis: RedisCache = Depends(get_redis_cache)
):
    cache_key = CacheKeys.user_context(user.id)
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        etag = generate_etag(cached)
        if request.headers.get("If-None-Match") == etag:
            return Response(status_code=304)
        
        return JSONResponse(
            content=cached,
            headers={
                "ETag": etag,
                "Cache-Control": "private, max-age=3600",
                "X-Cache": "HIT"
            }
        )
    
    # Fetch fresh data
    context = await build_user_context(user)
    
    # Cache with encryption for sensitive fields
    await redis.set_secure(cache_key, context, ttl=3600)
    
    etag = generate_etag(context)
    return JSONResponse(
        content=context,
        headers={
            "ETag": etag,
            "Cache-Control": "private, max-age=3600",
            "X-Cache": "MISS"
        }
    )
```

```python
# 4. WebSocket Cache Events
# File: backend/app/services/websocket/cache_events.py
from fastapi import WebSocket
from typing import Dict, Set

class CacheEventManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = set()
        self.connections[user_id].add(websocket)
    
    async def broadcast_cache_invalidation(self, event: dict):
        """Broadcast cache invalidation to relevant clients"""
        # Determine affected users based on event type
        affected_users = await self.get_affected_users(event)
        
        for user_id in affected_users:
            if user_id in self.connections:
                for websocket in self.connections[user_id]:
                    try:
                        await websocket.send_json({
                            "type": "cache_invalidation",
                            "data": event
                        })
                    except:
                        # Remove dead connections
                        self.connections[user_id].remove(websocket)
```

## Technical Requirements

### Performance Requirements
- Cache operations must add < 10ms latency
- Support 10,000+ concurrent requests
- Implement circuit breaker for cache failures
- Graceful degradation when Redis is unavailable

### Security Requirements
- Implement field-level encryption for PII
- Audit all cache operations
- Ensure tenant isolation in all cache keys
- Validate cache integrity with checksums

### Integration Requirements
- Work with pgvector-data-architect on cache schema
- Coordinate with nextjs-ui-architect on WebSocket events
- Align with qa-playwright-tester on test scenarios
- Collaborate with devsecops-linting-engineer on security

## Success Criteria
- 70-80% reduction in database queries
- All endpoints support conditional requests
- WebSocket events deliver within 100ms
- Zero security vulnerabilities in cache layer

## Resources
- FastAPI documentation on middleware
- Redis Python client documentation
- WebSocket implementation examples
- Current API structure in `backend/app/api/`

## Communication
- Daily updates to progress dashboard
- Coordinate with pgvector-data-architect on schema
- Weekly sync with orchestrator
- Immediate escalation for blockers

## Timeline
- Week 1: Middleware and basic caching
- Week 2: Invalidation service and WebSockets
- Week 3: Security and optimization
- Ongoing: Support integration with other teams

---
**Assigned by**: Claude Code (Orchestrator)
**Start Date**: Immediate
**Priority**: Critical Path