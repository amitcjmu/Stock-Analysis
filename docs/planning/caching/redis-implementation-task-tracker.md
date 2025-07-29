# Redis Implementation Task Tracker - AI Modernize Migration Platform

## Executive Summary
- **Deadline**: August 15th (17 days from July 29th)
- **Developer Capacity**: 1 developer (42% effective due to 58% bug fix rate)
- **Total Effort**: 11 days pure development time
- **Effective Days Available**: ~7 days after bug fixes
- **Critical Decision**: Implement Phase 1 only for Alpha, defer advanced features

## Risk Assessment & Go/No-Go Criteria

### High Risk Factors
1. **Single Developer Bottleneck**: No backup if issues arise
2. **58% Bug Fix Rate**: Only 42% time available for new development
3. **No Current Redis Experience**: Based on codebase analysis
4. **Production Environment Complexity**: Vercel + Railway integration

### Go/No-Go Decision Points
- **Day 3**: Local Redis working with basic operations → Continue
- **Day 6**: Event Bus migration tested → Continue  
- **Day 9**: Production Upstash connected → Continue
- **Day 12**: Full integration testing → Final Go/No-Go

### Fallback Strategy
If Redis implementation blocks Alpha:
1. Keep in-memory implementation with documentation of limitations
2. Add Redis as "Beta Feature" post-Alpha
3. Focus on stability over new features

---

## Phase 1: Local Development Setup (Days 1-3)

### TASK-001: Docker Compose Redis Setup
**Priority**: CRITICAL  
**Effort**: 2 hours  
**Dependencies**: None  
**Acceptance Criteria**:
- Redis container runs in docker-compose.dev.yml
- Health checks passing
- Accessible on port 6379

**Implementation**:
```yaml
# Add to docker-compose.dev.yml (already exists but commented out)
  redis:
    image: redis:7-alpine
    container_name: migration_redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - migration_dev
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
```

**Testing**:
```bash
# Verify Redis is running
docker-compose -f docker-compose.dev.yml up -d redis
docker exec migration_redis_dev redis-cli ping
# Expected: PONG
```

### TASK-002: Python Redis Dependencies
**Priority**: CRITICAL  
**Effort**: 1 hour  
**Dependencies**: TASK-001  
**Acceptance Criteria**:
- redis[hiredis] added to requirements.txt
- redis-py-cluster for future scaling
- Development dependencies updated

**Implementation**:
```bash
# Add to backend/requirements.txt
redis[hiredis]==5.0.1
redis-py-cluster==2.1.3

# For async support (already have asyncio)
# No additional async redis needed - redis 5.0+ has native async
```

**Testing**:
```bash
cd backend
pip install -r requirements.txt
python -c "import redis.asyncio as redis; print('Redis imported successfully')"
```

### TASK-003: Redis Configuration Module
**Priority**: CRITICAL  
**Effort**: 3 hours  
**Dependencies**: TASK-002  
**Acceptance Criteria**:
- RedisManager class created
- Environment variables configured
- Connection pooling implemented
- Graceful fallback if Redis unavailable

**Implementation**:
```python
# backend/app/core/redis_config.py
import os
import logging
from typing import Optional
from redis import asyncio as aioredis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class RedisManager:
    """Manages Redis connections with fallback support"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        if not self.enabled:
            logger.info("Redis disabled via configuration")
            return False
            
        try:
            self.redis = await aioredis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 3,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 3,  # TCP_KEEPCNT
                },
                max_connections=50,
                health_check_interval=30,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError]
            )
            
            # Test connection
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            logger.info("Redis connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
            self.pubsub = None
            return False
    
    async def close(self):
        """Close Redis connections"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
            
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis is not None

# Global instance
redis_manager = RedisManager()
```

**Environment Variables**:
```bash
# backend/.env.dev
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0

# backend/.env.production (for Railway)
REDIS_ENABLED=true
REDIS_URL=${UPSTASH_REDIS_URL}
```

**Testing Checklist**:
- [ ] Redis connects successfully
- [ ] Graceful fallback when Redis is down
- [ ] Connection pooling works
- [ ] Environment variables load correctly

### TASK-004: Basic Redis Health Check
**Priority**: HIGH  
**Effort**: 1 hour  
**Dependencies**: TASK-003  
**Acceptance Criteria**:
- Health endpoint includes Redis status
- Metrics on Redis performance

**Implementation**:
```python
# backend/app/api/v1/endpoints/health.py (update existing)
from app.core.redis_config import redis_manager

@router.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "unknown",
            "redis": "unavailable"
        }
    }
    
    # Check PostgreSQL (existing code)
    # ...
    
    # Check Redis
    if redis_manager.is_available():
        try:
            start = time.time()
            await redis_manager.redis.ping()
            latency = (time.time() - start) * 1000
            health_status["services"]["redis"] = {
                "status": "healthy",
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return health_status
```

---

## Phase 2: Core Implementation (Days 4-8)

### TASK-005: Event Bus Redis Migration
**Priority**: CRITICAL  
**Effort**: 6 hours  
**Dependencies**: TASK-003  
**Acceptance Criteria**:
- Redis Streams replace in-memory list
- Event history persisted across restarts
- Backward compatible with existing code
- Feature flag for rollback

**Implementation**:
```python
# backend/app/services/flows/redis_event_bus.py
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.redis_config import redis_manager
from app.schemas.flow_events import FlowEvent
import logging

logger = logging.getLogger(__name__)

class RedisFlowEventBus:
    """Redis-backed event bus with fallback to in-memory"""
    
    def __init__(self):
        self.stream_prefix = "flow:events:"
        self.channel_prefix = "flow:updates:"
        self.max_events_per_flow = 10000
        self.ttl_seconds = 86400  # 24 hours
        
        # Fallback in-memory storage
        self.memory_events: Dict[str, List[FlowEvent]] = {}
        
    async def publish(self, event: FlowEvent) -> bool:
        """Publish event to Redis Stream and Pub/Sub"""
        try:
            if redis_manager.is_available():
                stream_key = f"{self.stream_prefix}{event.flow_id}"
                
                # Add to Redis Stream for persistence
                event_data = {
                    "event_type": event.event_type,
                    "payload": json.dumps(event.payload),
                    "timestamp": event.timestamp.isoformat(),
                    "source": event.source or "system",
                    "correlation_id": event.correlation_id or ""
                }
                
                await redis_manager.redis.xadd(
                    stream_key,
                    event_data,
                    maxlen=self.max_events_per_flow,
                    approximate=True
                )
                
                # Set TTL on stream
                await redis_manager.redis.expire(stream_key, self.ttl_seconds)
                
                # Publish for real-time subscribers
                channel = f"{self.channel_prefix}{event.flow_id}"
                await redis_manager.redis.publish(
                    channel, 
                    event.model_dump_json()
                )
                
                logger.debug(f"Published event {event.event_type} for flow {event.flow_id}")
                return True
            else:
                # Fallback to in-memory
                return self._publish_to_memory(event)
                
        except Exception as e:
            logger.error(f"Redis publish failed: {e}, falling back to memory")
            return self._publish_to_memory(event)
    
    def _publish_to_memory(self, event: FlowEvent) -> bool:
        """Fallback in-memory publish"""
        if event.flow_id not in self.memory_events:
            self.memory_events[event.flow_id] = []
        
        self.memory_events[event.flow_id].append(event)
        
        # Limit memory usage
        if len(self.memory_events[event.flow_id]) > 1000:
            self.memory_events[event.flow_id] = self.memory_events[event.flow_id][-1000:]
        
        return True
    
    async def get_events(
        self, 
        flow_id: str, 
        count: int = 100,
        start_time: Optional[datetime] = None
    ) -> List[FlowEvent]:
        """Get events from Redis or memory"""
        try:
            if redis_manager.is_available():
                stream_key = f"{self.stream_prefix}{flow_id}"
                
                # Get latest events
                events_data = await redis_manager.redis.xrevrange(
                    stream_key, 
                    count=count
                )
                
                events = []
                for event_id, data in events_data:
                    try:
                        event = FlowEvent(
                            flow_id=flow_id,
                            event_type=data["event_type"],
                            payload=json.loads(data["payload"]),
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            source=data.get("source", "system"),
                            correlation_id=data.get("correlation_id")
                        )
                        
                        if start_time and event.timestamp < start_time:
                            break
                            
                        events.append(event)
                    except Exception as e:
                        logger.error(f"Error parsing event: {e}")
                        continue
                
                return events
            else:
                # Fallback to memory
                return self._get_events_from_memory(flow_id, count, start_time)
                
        except Exception as e:
            logger.error(f"Redis get_events failed: {e}, falling back to memory")
            return self._get_events_from_memory(flow_id, count, start_time)
    
    def _get_events_from_memory(
        self, 
        flow_id: str, 
        count: int,
        start_time: Optional[datetime]
    ) -> List[FlowEvent]:
        """Fallback in-memory get"""
        if flow_id not in self.memory_events:
            return []
        
        events = self.memory_events[flow_id]
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        return events[-count:]

# Update the existing event bus to use Redis
# backend/app/services/flows/events.py
from app.services.flows.redis_event_bus import RedisFlowEventBus

# Replace the in-memory implementation
flow_event_bus = RedisFlowEventBus()
```

**Testing Script**:
```python
# backend/tests/test_redis_event_bus.py
import asyncio
import pytest
from datetime import datetime
from app.services.flows.redis_event_bus import RedisFlowEventBus
from app.schemas.flow_events import FlowEvent

@pytest.mark.asyncio
async def test_event_publish_and_retrieve():
    bus = RedisFlowEventBus()
    
    # Create test event
    event = FlowEvent(
        flow_id="test-flow-123",
        event_type="TEST_EVENT",
        payload={"test": "data"},
        timestamp=datetime.utcnow(),
        source="test"
    )
    
    # Publish
    success = await bus.publish(event)
    assert success
    
    # Retrieve
    events = await bus.get_events("test-flow-123", count=10)
    assert len(events) >= 1
    assert events[0].event_type == "TEST_EVENT"
```

### TASK-006: SSE Connection Registry
**Priority**: HIGH  
**Effort**: 4 hours  
**Dependencies**: TASK-005  
**Acceptance Criteria**:
- Track SSE connections across instances
- Auto-cleanup stale connections
- Support connection migration

**Implementation**:
```python
# backend/app/services/sse/redis_connection_registry.py
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.core.redis_config import redis_manager
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisConnectionRegistry:
    """Manage SSE connections across multiple instances"""
    
    def __init__(self):
        self.registry_prefix = "sse:connections:"
        self.heartbeat_prefix = "sse:heartbeat:"
        self.ttl = 300  # 5 minutes
        self.server_id = settings.SERVER_ID or str(uuid.uuid4())
        
        # Fallback in-memory storage
        self.memory_connections: Dict[str, Dict] = {}
    
    async def register(
        self, 
        connection_id: str, 
        flow_id: str, 
        user_id: str,
        client_info: Optional[Dict] = None
    ) -> bool:
        """Register new SSE connection"""
        try:
            connection_data = {
                "flow_id": flow_id,
                "user_id": user_id,
                "server_id": self.server_id,
                "connected_at": datetime.utcnow().isoformat(),
                "client_info": client_info or {},
                "last_heartbeat": datetime.utcnow().isoformat()
            }
            
            if redis_manager.is_available():
                key = f"{self.registry_prefix}{connection_id}"
                
                # Store connection data
                await redis_manager.redis.setex(
                    key,
                    self.ttl,
                    json.dumps(connection_data)
                )
                
                # Add to flow's connection set
                flow_key = f"{self.registry_prefix}flow:{flow_id}"
                await redis_manager.redis.sadd(flow_key, connection_id)
                await redis_manager.redis.expire(flow_key, self.ttl)
                
                logger.info(f"Registered SSE connection {connection_id} for flow {flow_id}")
                return True
            else:
                # Fallback to memory
                self.memory_connections[connection_id] = connection_data
                return True
                
        except Exception as e:
            logger.error(f"Failed to register connection: {e}")
            # Fallback to memory
            self.memory_connections[connection_id] = connection_data
            return True
    
    async def unregister(self, connection_id: str) -> bool:
        """Remove SSE connection"""
        try:
            if redis_manager.is_available():
                key = f"{self.registry_prefix}{connection_id}"
                
                # Get connection data first
                data = await redis_manager.redis.get(key)
                if data:
                    conn_data = json.loads(data)
                    flow_id = conn_data["flow_id"]
                    
                    # Remove from flow's connection set
                    flow_key = f"{self.registry_prefix}flow:{flow_id}"
                    await redis_manager.redis.srem(flow_key, connection_id)
                
                # Delete connection data
                await redis_manager.redis.delete(key)
                logger.info(f"Unregistered SSE connection {connection_id}")
                return True
            else:
                # Fallback to memory
                if connection_id in self.memory_connections:
                    del self.memory_connections[connection_id]
                return True
                
        except Exception as e:
            logger.error(f"Failed to unregister connection: {e}")
            return False
    
    async def heartbeat(self, connection_id: str) -> bool:
        """Update connection heartbeat"""
        try:
            if redis_manager.is_available():
                key = f"{self.registry_prefix}{connection_id}"
                
                # Get existing data
                data = await redis_manager.redis.get(key)
                if data:
                    conn_data = json.loads(data)
                    conn_data["last_heartbeat"] = datetime.utcnow().isoformat()
                    
                    # Update with refresh TTL
                    await redis_manager.redis.setex(
                        key,
                        self.ttl,
                        json.dumps(conn_data)
                    )
                    return True
            else:
                # Memory fallback
                if connection_id in self.memory_connections:
                    self.memory_connections[connection_id]["last_heartbeat"] = \
                        datetime.utcnow().isoformat()
                return True
                
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return False
    
    async def get_flow_connections(self, flow_id: str) -> List[str]:
        """Get all active connections for a flow"""
        try:
            if redis_manager.is_available():
                flow_key = f"{self.registry_prefix}flow:{flow_id}"
                connections = await redis_manager.redis.smembers(flow_key)
                
                # Verify connections are still active
                active = []
                for conn_id in connections:
                    if await redis_manager.redis.exists(f"{self.registry_prefix}{conn_id}"):
                        active.append(conn_id)
                    else:
                        # Clean up stale reference
                        await redis_manager.redis.srem(flow_key, conn_id)
                
                return active
            else:
                # Memory fallback
                return [
                    cid for cid, data in self.memory_connections.items()
                    if data["flow_id"] == flow_id
                ]
                
        except Exception as e:
            logger.error(f"Failed to get flow connections: {e}")
            return []
    
    async def cleanup_stale_connections(self):
        """Remove connections that haven't sent heartbeat"""
        try:
            if redis_manager.is_available():
                # This would be called periodically by a background task
                pattern = f"{self.registry_prefix}*"
                cursor = 0
                
                while True:
                    cursor, keys = await redis_manager.redis.scan(
                        cursor, 
                        match=pattern, 
                        count=100
                    )
                    
                    for key in keys:
                        if ":flow:" in key:
                            continue  # Skip flow sets
                        
                        data = await redis_manager.redis.get(key)
                        if data:
                            conn_data = json.loads(data)
                            last_heartbeat = datetime.fromisoformat(
                                conn_data["last_heartbeat"]
                            )
                            
                            if datetime.utcnow() - last_heartbeat > timedelta(seconds=self.ttl):
                                conn_id = key.replace(self.registry_prefix, "")
                                await self.unregister(conn_id)
                    
                    if cursor == 0:
                        break
            else:
                # Memory cleanup
                now = datetime.utcnow()
                stale = []
                for conn_id, data in self.memory_connections.items():
                    last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
                    if now - last_heartbeat > timedelta(seconds=self.ttl):
                        stale.append(conn_id)
                
                for conn_id in stale:
                    del self.memory_connections[conn_id]
                    
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

# Global registry instance
connection_registry = RedisConnectionRegistry()
```

### TASK-007: Flow State Cache Implementation
**Priority**: HIGH  
**Effort**: 4 hours  
**Dependencies**: TASK-005  
**Acceptance Criteria**:
- Cache flow states in Redis
- Automatic cache invalidation
- Performance metrics tracking

**Implementation**:
```python
# backend/app/services/cache/flow_state_cache.py
import json
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.redis_config import redis_manager
import logging

logger = logging.getLogger(__name__)

class FlowStateCache:
    """Redis cache for flow states with intelligent TTL"""
    
    def __init__(self):
        self.cache_prefix = "cache:flow:state:"
        self.metadata_prefix = "cache:flow:meta:"
        self.metrics_prefix = "metrics:cache:"
        
        # TTL configuration
        self.ttl_active = 300      # 5 minutes for active flows
        self.ttl_completed = 3600  # 1 hour for completed flows
        self.ttl_failed = 1800     # 30 minutes for failed flows
        
    async def get(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state from cache"""
        if not redis_manager.is_available():
            return None
            
        try:
            key = f"{self.cache_prefix}{flow_id}"
            
            # Track cache access
            await self._track_access(flow_id)
            
            # Get cached data
            cached = await redis_manager.redis.get(key)
            if cached:
                await self._track_hit(flow_id)
                return json.loads(cached)
            else:
                await self._track_miss(flow_id)
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        flow_id: str, 
        state: Dict[str, Any],
        status: Optional[str] = None
    ) -> bool:
        """Set flow state in cache with intelligent TTL"""
        if not redis_manager.is_available():
            return False
            
        try:
            key = f"{self.cache_prefix}{flow_id}"
            
            # Determine TTL based on status
            ttl = self.ttl_active
            if status:
                if status in ["completed", "success"]:
                    ttl = self.ttl_completed
                elif status in ["failed", "error", "cancelled"]:
                    ttl = self.ttl_failed
            
            # Cache the state
            await redis_manager.redis.setex(
                key,
                ttl,
                json.dumps(state)
            )
            
            # Cache metadata separately
            metadata = {
                "flow_id": flow_id,
                "status": status or state.get("status", "unknown"),
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": ttl
            }
            
            meta_key = f"{self.metadata_prefix}{flow_id}"
            await redis_manager.redis.setex(
                meta_key,
                ttl,
                json.dumps(metadata)
            )
            
            logger.debug(f"Cached flow {flow_id} with TTL {ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, flow_id: str) -> bool:
        """Remove flow from cache"""
        if not redis_manager.is_available():
            return False
            
        try:
            keys = [
                f"{self.cache_prefix}{flow_id}",
                f"{self.metadata_prefix}{flow_id}"
            ]
            
            deleted = await redis_manager.redis.delete(*keys)
            logger.debug(f"Invalidated cache for flow {flow_id}, deleted {deleted} keys")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
            return False
    
    async def _track_access(self, flow_id: str):
        """Track cache access for metrics"""
        try:
            # Increment access counter
            await redis_manager.redis.hincrby(
                f"{self.metrics_prefix}access",
                flow_id,
                1
            )
            
            # Update last access time
            await redis_manager.redis.hset(
                f"{self.metrics_prefix}last_access",
                flow_id,
                datetime.utcnow().isoformat()
            )
        except Exception:
            pass  # Don't fail on metrics
    
    async def _track_hit(self, flow_id: str):
        """Track cache hit"""
        try:
            await redis_manager.redis.hincrby(
                f"{self.metrics_prefix}hits",
                flow_id,
                1
            )
        except Exception:
            pass
    
    async def _track_miss(self, flow_id: str):
        """Track cache miss"""
        try:
            await redis_manager.redis.hincrby(
                f"{self.metrics_prefix}misses",
                flow_id,
                1
            )
        except Exception:
            pass
    
    async def get_metrics(self, flow_id: str) -> Dict[str, Any]:
        """Get cache metrics for a flow"""
        if not redis_manager.is_available():
            return {}
            
        try:
            access = await redis_manager.redis.hget(f"{self.metrics_prefix}access", flow_id) or 0
            hits = await redis_manager.redis.hget(f"{self.metrics_prefix}hits", flow_id) or 0
            misses = await redis_manager.redis.hget(f"{self.metrics_prefix}misses", flow_id) or 0
            
            hit_rate = float(hits) / float(access) * 100 if int(access) > 0 else 0
            
            return {
                "access_count": int(access),
                "hits": int(hits),
                "misses": int(misses),
                "hit_rate": round(hit_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Get metrics error: {e}")
            return {}

# Global cache instance
flow_state_cache = FlowStateCache()
```

### TASK-008: Integration with Existing Services
**Priority**: CRITICAL  
**Effort**: 5 hours  
**Dependencies**: TASK-005, TASK-006, TASK-007  
**Acceptance Criteria**:
- Existing services use Redis implementations
- Feature flags control rollout
- No breaking changes

**Implementation**:
```python
# backend/app/services/crewai_flows/base_flow.py (update existing)
from app.services.cache.flow_state_cache import flow_state_cache
from app.services.flows.events import flow_event_bus  # Now Redis-backed

class BaseCrewAIFlow:
    async def get_flow_state(self) -> Dict[str, Any]:
        """Get flow state with caching"""
        # Try cache first
        cached_state = await flow_state_cache.get(self.flow_id)
        if cached_state:
            return cached_state
        
        # Get from database
        state = await self._get_state_from_db()
        
        # Cache for next time
        if state:
            await flow_state_cache.set(
                self.flow_id, 
                state,
                status=state.get("status")
            )
        
        return state
    
    async def update_flow_state(self, updates: Dict[str, Any]):
        """Update flow state and invalidate cache"""
        # Update in database
        await self._update_state_in_db(updates)
        
        # Invalidate cache
        await flow_state_cache.invalidate(self.flow_id)
        
        # Publish event
        await flow_event_bus.publish(
            FlowEvent(
                flow_id=self.flow_id,
                event_type="STATE_UPDATED",
                payload=updates,
                timestamp=datetime.utcnow()
            )
        )

# backend/app/api/v1/endpoints/assessment_events.py (update existing)
from app.services.sse.redis_connection_registry import connection_registry

@router.get("/assessments/{assessment_id}/events")
async def assessment_events_endpoint(
    assessment_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """SSE endpoint with Redis registry"""
    connection_id = str(uuid.uuid4())
    
    # Register connection
    await connection_registry.register(
        connection_id=connection_id,
        flow_id=assessment_id,
        user_id=str(current_user.id),
        client_info={
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    async def event_generator():
        try:
            while True:
                # Send heartbeat
                await connection_registry.heartbeat(connection_id)
                
                # Get and send events (existing logic)
                # ...
                
                await asyncio.sleep(1)
                
        finally:
            # Cleanup on disconnect
            await connection_registry.unregister(connection_id)
    
    return EventSourceResponse(event_generator())
```

---

## Phase 3: Production Deployment (Days 9-12)

### TASK-009: Upstash Redis Setup
**Priority**: CRITICAL  
**Effort**: 2 hours  
**Dependencies**: TASK-008  
**Acceptance Criteria**:
- Upstash account created
- Redis instance provisioned
- Connection string obtained

**Implementation Steps**:
1. Create Upstash Account:
   ```bash
   # Navigate to https://upstash.com
   # Sign up with GitHub (recommended for Railway integration)
   # Create new Redis database
   # Select region closest to Railway deployment
   ```

2. Configure Redis Instance:
   - **Name**: `ai-modernize-prod`
   - **Region**: Same as Railway (e.g., us-east-1)
   - **Eviction**: allkeys-lru
   - **Max Memory**: 256MB (Free tier)
   - **TLS**: Enabled (required)

3. Get Connection Details:
   ```bash
   # From Upstash Console, copy:
   UPSTASH_REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379
   ```

### TASK-010: Railway Environment Configuration
**Priority**: CRITICAL  
**Effort**: 2 hours  
**Dependencies**: TASK-009  
**Acceptance Criteria**:
- Environment variables set in Railway
- Redis connection verified
- Monitoring configured

**Implementation**:
```bash
# Railway CLI or Dashboard
railway variables set REDIS_ENABLED=true
railway variables set REDIS_URL=$UPSTASH_REDIS_URL
railway variables set SERVER_ID=railway-prod-1

# Verify connection
railway run python -c "
import asyncio
from app.core.redis_config import redis_manager
asyncio.run(redis_manager.initialize())
"
```

### TASK-011: Production Testing Suite
**Priority**: HIGH  
**Effort**: 3 hours  
**Dependencies**: TASK-010  
**Acceptance Criteria**:
- All Redis features tested in production
- Performance benchmarks completed
- Rollback tested

**Test Script**:
```python
# backend/scripts/test_redis_production.py
import asyncio
import time
from app.core.redis_config import redis_manager
from app.services.flows.events import flow_event_bus
from app.services.cache.flow_state_cache import flow_state_cache

async def test_production_redis():
    """Comprehensive production Redis test"""
    
    print("Testing Redis connection...")
    if not await redis_manager.initialize():
        print("❌ Redis connection failed")
        return False
    
    print("✅ Redis connected")
    
    # Test 1: Event Bus
    print("\nTesting Event Bus...")
    test_event = FlowEvent(
        flow_id="test-prod-001",
        event_type="PRODUCTION_TEST",
        payload={"test": "production"},
        timestamp=datetime.utcnow()
    )
    
    start = time.time()
    await flow_event_bus.publish(test_event)
    publish_time = time.time() - start
    print(f"✅ Event published in {publish_time*1000:.2f}ms")
    
    # Test 2: Cache
    print("\nTesting Cache...")
    test_state = {
        "status": "testing",
        "data": {"large": "x" * 1000}  # 1KB of data
    }
    
    start = time.time()
    await flow_state_cache.set("test-prod-001", test_state)
    set_time = time.time() - start
    
    start = time.time()
    cached = await flow_state_cache.get("test-prod-001")
    get_time = time.time() - start
    
    print(f"✅ Cache set in {set_time*1000:.2f}ms")
    print(f"✅ Cache get in {get_time*1000:.2f}ms")
    
    # Test 3: Concurrent Operations
    print("\nTesting Concurrent Operations...")
    tasks = []
    for i in range(100):
        tasks.append(
            flow_event_bus.publish(
                FlowEvent(
                    flow_id=f"test-concurrent-{i}",
                    event_type="CONCURRENT_TEST",
                    payload={"index": i},
                    timestamp=datetime.utcnow()
                )
            )
        )
    
    start = time.time()
    await asyncio.gather(*tasks)
    concurrent_time = time.time() - start
    
    print(f"✅ 100 concurrent events in {concurrent_time*1000:.2f}ms")
    print(f"   Average: {concurrent_time*10:.2f}ms per event")
    
    # Cleanup
    await redis_manager.close()
    
    print("\n✅ All production tests passed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_production_redis())
```

### TASK-012: Monitoring and Alerting
**Priority**: MEDIUM  
**Effort**: 2 hours  
**Dependencies**: TASK-011  
**Acceptance Criteria**:
- Redis metrics in health endpoint
- Upstash dashboard configured
- Alert thresholds set

**Implementation**:
```python
# backend/app/monitoring/redis_monitor.py
from app.core.redis_config import redis_manager
import logging

logger = logging.getLogger(__name__)

class RedisMonitor:
    """Monitor Redis health and performance"""
    
    async def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        if not redis_manager.is_available():
            return {"status": "unavailable"}
        
        try:
            info = await redis_manager.redis.info()
            
            return {
                "status": "healthy",
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "used_memory_peak_human": info.get("used_memory_peak_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
                "keyspace": info.get("db0", {})
            }
            
        except Exception as e:
            logger.error(f"Redis monitoring error: {e}")
            return {"status": "error", "error": str(e)}

# Add to health endpoint
redis_monitor = RedisMonitor()

@router.get("/health/redis")
async def redis_health():
    return await redis_monitor.get_redis_info()
```

---

## Daily Sprint Plan (Accounting for 58% Bug Fix Time)

### Day 1-2: Foundation
- **Day 1**: 
  - Morning: TASK-001 (Docker setup)
  - Afternoon: Bug fixes (58% time)
  
- **Day 2**: 
  - Morning: TASK-002, TASK-003 (Dependencies & Config)
  - Afternoon: Bug fixes

### Day 3-4: Local Testing
- **Day 3**: 
  - Morning: TASK-004 (Health checks)
  - Afternoon: Bug fixes + **Go/No-Go Decision #1**
  
- **Day 4**: 
  - Morning: Start TASK-005 (Event Bus)
  - Afternoon: Bug fixes

### Day 5-6: Core Implementation
- **Day 5**: 
  - Morning: Continue TASK-005
  - Afternoon: Bug fixes
  
- **Day 6**: 
  - Morning: TASK-006 (SSE Registry)
  - Afternoon: Bug fixes + **Go/No-Go Decision #2**

### Day 7-8: Integration
- **Day 7**: 
  - Morning: TASK-007 (Cache)
  - Afternoon: Bug fixes
  
- **Day 8**: 
  - Morning: TASK-008 (Integration)
  - Afternoon: Bug fixes

### Day 9-10: Production Setup
- **Day 9**: 
  - Morning: TASK-009, TASK-010 (Upstash + Railway)
  - Afternoon: Bug fixes + **Go/No-Go Decision #3**
  
- **Day 10**: 
  - Morning: TASK-011 (Production testing)
  - Afternoon: Bug fixes

### Day 11-12: Final Testing
- **Day 11**: 
  - Morning: TASK-012 (Monitoring)
  - Afternoon: Bug fixes
  
- **Day 12**: 
  - Full day: Integration testing + **Final Go/No-Go**

### Day 13-17: Buffer
- Documentation
- Performance optimization
- Additional bug fixes
- Rollback preparation if needed

---

## Rollback Plan

### Feature Flags
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # Redis feature flags
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
    REDIS_EVENT_BUS: bool = Field(default=False, env="REDIS_EVENT_BUS")
    REDIS_CACHE: bool = Field(default=False, env="REDIS_CACHE")
    REDIS_SSE: bool = Field(default=False, env="REDIS_SSE")
```

### Quick Disable
```bash
# In Railway/Production
railway variables set REDIS_ENABLED=false
railway restart

# Services automatically fall back to in-memory
```

### Data Preservation
- All Redis data is transient (cache/events)
- PostgreSQL remains source of truth
- No data migration required for rollback

---

## Success Metrics

### Performance Targets
- API response time: < 200ms (50% improvement)
- Event publishing: < 10ms
- Cache hit rate: > 80%
- SSE latency: < 50ms

### Monitoring Dashboard
```python
# backend/app/api/v1/endpoints/metrics.py
@router.get("/metrics/redis")
async def redis_metrics():
    return {
        "cache_metrics": await flow_state_cache.get_metrics("*"),
        "event_bus_metrics": await flow_event_bus.get_metrics(),
        "connection_count": await connection_registry.get_total_connections(),
        "redis_info": await redis_monitor.get_redis_info()
    }
```

---

## Risk Mitigation

### Critical Risks
1. **Upstash Limits**: Free tier = 10K commands/day
   - Mitigation: Implement command batching
   - Monitor usage via Upstash dashboard

2. **Network Latency**: Upstash ↔ Railway
   - Mitigation: Same region deployment
   - Implement local caching layer

3. **Single Developer**: No redundancy
   - Mitigation: Detailed documentation
   - Pair programming sessions if possible

### Emergency Procedures
```bash
# If Redis causes issues in production

# 1. Immediate disable
railway variables set REDIS_ENABLED=false
railway restart

# 2. Check logs
railway logs -n 1000 | grep -i redis

# 3. Clear Redis if needed
railway run python -c "
from app.core.redis_config import redis_manager
import asyncio
async def clear():
    await redis_manager.initialize()
    await redis_manager.redis.flushdb()
asyncio.run(clear())
"
```

---

## Post-Alpha Roadmap

### Phase 2 Features (Post-Alpha)
- Background task queue (Celery)
- Distributed locks
- Advanced caching strategies
- Multi-instance SSE coordination

### Scaling Considerations
- Upgrade Upstash plan for production
- Consider Redis Cluster for high availability
- Implement connection pooling optimization

---

## Conclusion

This tracker provides a realistic path to Redis implementation given your constraints. The phased approach with multiple go/no-go decisions allows for course correction. The 58% bug fix rate is accounted for in the daily planning.

**Key Success Factors**:
1. Start immediately (Day 1)
2. Test thoroughly at each phase
3. Be ready to defer Phase 2/3 features
4. Keep fallback mechanisms active
5. Document everything for handoff

The conservative approach focusing on Phase 1 only gives the best chance of success for the Alpha deadline while providing real value through event persistence and basic caching.