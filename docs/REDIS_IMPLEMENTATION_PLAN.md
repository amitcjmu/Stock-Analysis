# Redis Implementation Plan for AI Modernize Migration Platform

## Executive Summary

This plan outlines the phased integration of Redis into the AI Modernize Migration Platform to address current scalability limitations, enable horizontal scaling, and improve real-time capabilities. The implementation is designed to be non-disruptive, with each phase delivering immediate value while maintaining system stability.

## Current Architecture Limitations

1. **Single Instance Lock-in**: In-memory event bus prevents horizontal scaling
2. **Performance Bottlenecks**: Direct PostgreSQL queries for all state operations
3. **Lost Events**: Server restarts lose all in-memory event history
4. **No Task Queue**: Long-running operations block API responses
5. **Limited Real-time**: SSE connections not shared across instances

## Proposed Redis Architecture

```
┌─────────────┐     ┌─────────────────────────────────────┐
│   Vercel    │────▶│         Railway Platform             │
│  Frontend   │     │  ┌─────────────┐  ┌─────────────┐  │
└─────────────┘     │  │   Backend   │  │    Redis    │  │
                    │  │  Instance 1  │◀─┼─────────────┤  │
                    │  ├─────────────┤  │  Pub/Sub    │  │
                    │  │   Backend   │◀─┼─────────────┤  │
                    │  │  Instance 2  │  │  Cache      │  │
                    │  ├─────────────┤  ├─────────────┤  │
                    │  │   Workers   │◀─│  Task Queue │  │
                    │  └──────┬──────┘  └─────────────┘  │
                    │         │                           │
                    │  ┌──────▼──────┐                   │
                    │  │ PostgreSQL  │                   │
                    │  └─────────────┘                   │
                    └─────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Foundation & Quick Wins (Week 1-2)
**Goal**: Establish Redis infrastructure and implement high-impact, low-risk features

#### 1.1 Redis Infrastructure Setup
```python
# backend/app/core/redis_config.py
from redis import asyncio as aioredis
from app.core.config import settings

class RedisManager:
    def __init__(self):
        self.redis = None
        self.pubsub = None
        
    async def initialize(self):
        self.redis = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            socket_keepalive_options={
                1: 3,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 3,  # TCP_KEEPCNT
            }
        )
        self.pubsub = self.redis.pubsub()
        
    async def close(self):
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

redis_manager = RedisManager()
```

#### 1.2 Event Bus Migration
**Current**: `app/services/flows/events.py` - In-memory list
**New**: Redis Streams for persistent event history

```python
# backend/app/services/flows/redis_event_bus.py
class RedisFlowEventBus:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        self.stream_prefix = "flow:events:"
        self.max_events = 10000  # Per flow
        
    async def publish(self, event: FlowEvent):
        stream_key = f"{self.stream_prefix}{event.flow_id}"
        
        # Add to Redis Stream
        await self.redis.xadd(
            stream_key,
            {
                "event_type": event.event_type,
                "payload": json.dumps(event.payload),
                "timestamp": event.timestamp.isoformat(),
                "source": event.source
            },
            maxlen=self.max_events
        )
        
        # Publish to channel for real-time subscribers
        channel = f"flow:updates:{event.flow_id}"
        await self.redis.publish(channel, event.json())
        
    async def get_events(self, flow_id: str, count: int = 100):
        stream_key = f"{self.stream_prefix}{flow_id}"
        events = await self.redis.xrevrange(stream_key, count=count)
        return [self._parse_event(e) for e in events]
```

#### 1.3 SSE Connection Registry
**Current**: `app/api/v1/endpoints/assessment_events.py` - In-memory dict
**New**: Redis-backed connection tracking

```python
# backend/app/services/sse/redis_connection_registry.py
class RedisConnectionRegistry:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        self.registry_key = "sse:connections"
        self.ttl = 300  # 5 minutes
        
    async def register(self, connection_id: str, flow_id: str, user_id: str):
        connection_data = {
            "flow_id": flow_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "server_id": settings.SERVER_ID  # For multi-instance tracking
        }
        
        await self.redis.hset(
            self.registry_key,
            connection_id,
            json.dumps(connection_data)
        )
        
        # Auto-expire inactive connections
        await self.redis.expire(f"{self.registry_key}:{connection_id}", self.ttl)
        
    async def get_flow_connections(self, flow_id: str):
        all_connections = await self.redis.hgetall(self.registry_key)
        flow_connections = []
        
        for conn_id, data in all_connections.items():
            conn_data = json.loads(data)
            if conn_data["flow_id"] == flow_id:
                flow_connections.append(conn_id)
                
        return flow_connections
```

#### 1.4 Flow State Caching
**Current**: Direct PostgreSQL queries for every state check
**New**: Read-through cache with smart invalidation

```python
# backend/app/services/crewai_flows/redis_state_cache.py
class RedisFlowStateCache:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        self.cache_prefix = "flow:state:"
        self.metadata_prefix = "flow:meta:"
        self.ttl = 300  # 5 minutes for full state
        self.metadata_ttl = 3600  # 1 hour for metadata
        
    async def get_state(self, flow_id: str) -> Optional[dict]:
        # Try cache first
        cached = await self.redis.get(f"{self.cache_prefix}{flow_id}")
        if cached:
            return json.loads(cached)
        return None
        
    async def set_state(self, flow_id: str, state: dict):
        # Cache full state with TTL
        await self.redis.setex(
            f"{self.cache_prefix}{flow_id}",
            self.ttl,
            json.dumps(state)
        )
        
        # Cache metadata separately with longer TTL
        metadata = {
            "status": state.get("status"),
            "phase": state.get("current_phase"),
            "updated_at": datetime.utcnow().isoformat()
        }
        await self.redis.setex(
            f"{self.metadata_prefix}{flow_id}",
            self.metadata_ttl,
            json.dumps(metadata)
        )
        
    async def invalidate(self, flow_id: str):
        await self.redis.delete(
            f"{self.cache_prefix}{flow_id}",
            f"{self.metadata_prefix}{flow_id}"
        )
```

### Phase 2: Performance & Scalability (Week 3-4)
**Goal**: Implement task queue and advanced caching strategies

#### 2.1 Background Task Queue with Celery
```python
# backend/app/tasks/__init__.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "migration_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.flow_tasks", "app.tasks.agent_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes
    task_soft_time_limit=1500,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# backend/app/tasks/flow_tasks.py
from app.tasks import celery_app
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow

@celery_app.task(bind=True, max_retries=3)
def process_flow_phase(self, flow_id: str, phase: str, context: dict):
    try:
        flow = UnifiedDiscoveryFlow(flow_id=flow_id, context=context)
        result = flow.execute_phase(phase)
        return result
    except Exception as exc:
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def process_data_import_batch(flow_id: str, batch_data: list):
    """Process large data imports in background"""
    from app.services.data_import_service import DataImportService
    service = DataImportService()
    return service.process_batch(flow_id, batch_data)
```

#### 2.2 Agent Progress Broadcasting
```python
# backend/app/services/agents/redis_progress_tracker.py
class RedisAgentProgressTracker:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        self.channel_prefix = "agent:progress:"
        
    async def update_progress(
        self, 
        flow_id: str, 
        agent_name: str, 
        progress: float,
        status: str,
        details: Optional[dict] = None
    ):
        progress_data = {
            "flow_id": flow_id,
            "agent": agent_name,
            "progress": progress,
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update in Redis Hash for current state
        await self.redis.hset(
            f"agent:state:{flow_id}",
            agent_name,
            json.dumps(progress_data)
        )
        
        # Publish to channel for real-time updates
        channel = f"{self.channel_prefix}{flow_id}"
        await self.redis.publish(channel, json.dumps(progress_data))
        
    async def get_flow_progress(self, flow_id: str) -> dict:
        """Get all agent progress for a flow"""
        agent_states = await self.redis.hgetall(f"agent:state:{flow_id}")
        return {
            agent: json.loads(state) 
            for agent, state in agent_states.items()
        }
```

#### 2.3 Distributed Rate Limiting
```python
# backend/app/middleware/redis_rate_limiter.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_manager: RedisManager):
        super().__init__(app)
        self.redis = redis_manager.redis
        
    async def dispatch(self, request: Request, call_next):
        # Get rate limit key (by user or IP)
        user_id = request.state.user_id if hasattr(request.state, "user_id") else None
        key = f"rate_limit:{user_id or request.client.host}"
        
        # Check rate limit (e.g., 100 requests per minute)
        current_minute = int(time.time() / 60)
        rate_key = f"{key}:{current_minute}"
        
        try:
            current_count = await self.redis.incr(rate_key)
            if current_count == 1:
                await self.redis.expire(rate_key, 60)
                
            if current_count > 100:
                raise HTTPException(429, "Rate limit exceeded")
                
        except Exception as e:
            # Don't block requests if Redis is down
            logger.error(f"Rate limit check failed: {e}")
            
        response = await call_next(request)
        return response
```

### Phase 3: Advanced Features (Week 5-6)
**Goal**: Implement distributed coordination and advanced caching

#### 3.1 Distributed Locks for Flow Operations
```python
# backend/app/services/locks/redis_lock_manager.py
import asyncio
from typing import Optional

class RedisLockManager:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        
    async def acquire_lock(
        self, 
        resource: str, 
        ttl: int = 30,
        retry_times: int = 10,
        retry_delay: float = 0.1
    ) -> Optional[str]:
        """Acquire a distributed lock using SET NX with TTL"""
        lock_key = f"lock:{resource}"
        identifier = str(uuid.uuid4())
        
        for _ in range(retry_times):
            acquired = await self.redis.set(
                lock_key, 
                identifier, 
                nx=True, 
                ex=ttl
            )
            if acquired:
                return identifier
                
            await asyncio.sleep(retry_delay)
            
        return None
        
    async def release_lock(self, resource: str, identifier: str):
        """Release lock only if we own it"""
        lock_key = f"lock:{resource}"
        
        # Lua script for atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        await self.redis.eval(lua_script, 1, lock_key, identifier)
        
    @asynccontextmanager
    async def lock(self, resource: str, ttl: int = 30):
        """Context manager for distributed locks"""
        identifier = await self.acquire_lock(resource, ttl)
        if not identifier:
            raise LockAcquisitionError(f"Could not acquire lock for {resource}")
            
        try:
            yield identifier
        finally:
            await self.release_lock(resource, identifier)
```

#### 3.2 Multi-Instance SSE Coordination
```python
# backend/app/services/sse/redis_sse_broker.py
class RedisSSEBroker:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        self.pubsub = redis_manager.pubsub
        self.subscriptions = {}
        
    async def subscribe_to_flow(self, flow_id: str, callback):
        """Subscribe to flow updates across all instances"""
        channel = f"flow:updates:{flow_id}"
        
        if channel not in self.subscriptions:
            await self.pubsub.subscribe(channel)
            self.subscriptions[channel] = []
            
        self.subscriptions[channel].append(callback)
        
        # Start listening in background
        asyncio.create_task(self._listen_for_messages(channel))
        
    async def _listen_for_messages(self, channel: str):
        """Listen for Redis pub/sub messages"""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                
                # Call all registered callbacks
                for callback in self.subscriptions.get(channel, []):
                    await callback(data)
                    
    async def broadcast_to_flow(self, flow_id: str, event_data: dict):
        """Broadcast event to all instances watching this flow"""
        channel = f"flow:updates:{flow_id}"
        await self.redis.publish(channel, json.dumps(event_data))
```

#### 3.3 Smart Caching Strategy
```python
# backend/app/services/cache/intelligent_cache.py
class IntelligentFlowCache:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        self.stats_prefix = "cache:stats:"
        
    async def get_with_tracking(self, key: str) -> Optional[dict]:
        """Get from cache and track access patterns"""
        # Track access for intelligent TTL adjustment
        await self.redis.zincrby(
            f"{self.stats_prefix}access_count",
            1,
            key
        )
        
        cached = await self.redis.get(key)
        if cached:
            # Track hit rate
            await self.redis.hincrby(f"{self.stats_prefix}hits", key, 1)
            return json.loads(cached)
        else:
            # Track miss rate
            await self.redis.hincrby(f"{self.stats_prefix}misses", key, 1)
            return None
            
    async def set_with_intelligent_ttl(self, key: str, value: dict):
        """Set cache with TTL based on access patterns"""
        # Get access frequency
        access_count = await self.redis.zscore(
            f"{self.stats_prefix}access_count",
            key
        ) or 0
        
        # Adjust TTL based on access frequency
        if access_count > 100:
            ttl = 3600  # 1 hour for hot data
        elif access_count > 10:
            ttl = 600   # 10 minutes for warm data
        else:
            ttl = 300   # 5 minutes for cold data
            
        await self.redis.setex(key, ttl, json.dumps(value))
```

## Implementation Timeline

### Week 1-2: Phase 1 Foundation
- [ ] Add Redis to Railway project
- [ ] Implement RedisManager and configuration
- [ ] Migrate Event Bus to Redis Streams
- [ ] Implement SSE Connection Registry
- [ ] Add basic flow state caching
- [ ] Deploy and monitor Phase 1

### Week 3-4: Phase 2 Performance
- [ ] Set up Celery workers on Railway
- [ ] Implement background task processing
- [ ] Add agent progress broadcasting
- [ ] Implement rate limiting
- [ ] Add performance monitoring
- [ ] Load test Phase 2 features

### Week 5-6: Phase 3 Advanced
- [ ] Implement distributed locks
- [ ] Add multi-instance SSE support
- [ ] Implement intelligent caching
- [ ] Add cache warming strategies
- [ ] Performance optimization
- [ ] Documentation and training

## Monitoring & Success Metrics

### Key Performance Indicators
1. **Response Time**: Target 50% reduction in API response times
2. **Throughput**: Support 10x more concurrent flows
3. **Reliability**: Zero event loss during deployments
4. **Scalability**: Linear scaling with additional instances

### Monitoring Setup
```python
# backend/app/monitoring/redis_metrics.py
class RedisMetricsCollector:
    def __init__(self, redis_manager: RedisManager):
        self.redis = redis_manager.redis
        
    async def record_metric(self, metric_name: str, value: float, tags: dict = None):
        timestamp = int(time.time())
        key = f"metrics:{metric_name}:{timestamp // 60}"  # Per minute
        
        await self.redis.hincrby(key, "count", 1)
        await self.redis.hincrbyfloat(key, "sum", value)
        await self.redis.expire(key, 86400)  # 24 hour retention
        
    async def get_metrics(self, metric_name: str, minutes: int = 60):
        current = int(time.time())
        metrics = []
        
        for i in range(minutes):
            timestamp = (current // 60 - i) * 60
            key = f"metrics:{metric_name}:{timestamp // 60}"
            
            data = await self.redis.hgetall(key)
            if data:
                count = int(data.get("count", 0))
                sum_val = float(data.get("sum", 0))
                metrics.append({
                    "timestamp": timestamp,
                    "count": count,
                    "average": sum_val / count if count > 0 else 0
                })
                
        return metrics
```

## Risk Mitigation

### Potential Risks & Mitigations
1. **Redis Downtime**
   - Mitigation: Graceful degradation to direct PostgreSQL
   - Circuit breaker pattern for Redis operations

2. **Data Consistency**
   - Mitigation: PostgreSQL remains source of truth
   - Cache invalidation on all write operations

3. **Increased Complexity**
   - Mitigation: Phased rollout with feature flags
   - Comprehensive logging and monitoring

### Rollback Strategy
Each phase can be rolled back independently using feature flags:
```python
# backend/app/core/feature_flags.py
REDIS_FEATURES = {
    "event_bus": os.getenv("ENABLE_REDIS_EVENT_BUS", "false") == "true",
    "state_cache": os.getenv("ENABLE_REDIS_STATE_CACHE", "false") == "true",
    "task_queue": os.getenv("ENABLE_REDIS_TASK_QUEUE", "false") == "true",
    "sse_broker": os.getenv("ENABLE_REDIS_SSE_BROKER", "false") == "true",
}
```

## Conclusion

This phased approach to Redis integration will transform the AI Modernize Migration Platform from a single-instance application to a horizontally scalable, enterprise-ready system. Each phase delivers immediate value while maintaining system stability and data integrity.

The implementation prioritizes:
1. **Non-disruptive deployment** - Existing functionality remains intact
2. **Incremental value** - Each phase provides immediate benefits
3. **Production readiness** - Monitoring, error handling, and rollback capabilities
4. **Future extensibility** - Foundation for additional Redis-powered features

With Redis, the platform will support 10x more concurrent flows, provide real-time updates across multiple instances, and maintain high availability during deployments.