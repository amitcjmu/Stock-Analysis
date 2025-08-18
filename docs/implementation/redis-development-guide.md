# Redis Development Guide

## Overview

This guide provides comprehensive instructions for working with Redis in the AI Modernize Migration Platform, including key patterns, local development setup, and debugging techniques.

## Redis Architecture in the Platform

### Current Implementation Status

The platform uses Redis for:
- **Event Bus**: Persistent event history using Redis Streams
- **Session Management**: SSE connection tracking
- **Caching**: Flow state and metadata caching
- **Task Queue**: Background job processing with Celery
- **Rate Limiting**: Distributed rate limiting across instances

### Key Design Principles

1. **Fallback Strategy**: All Redis operations have PostgreSQL fallbacks
2. **Multi-Tenant Isolation**: All keys include tenant context
3. **TTL Management**: Automatic expiration for cache efficiency
4. **Error Handling**: Graceful degradation when Redis is unavailable

## Local Development Setup

### 1. Docker Configuration

Redis runs as a Docker service alongside PostgreSQL and the application:

```yaml
# docker-compose.yml (excerpt)
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD:-}
```

### 2. Accessing Redis Container

```bash
# Connect to Redis CLI
docker exec -it migration_redis redis-cli

# Or with authentication (if password is set)
docker exec -it migration_redis redis-cli -a ${REDIS_PASSWORD}

# Using docker-compose
docker-compose exec redis redis-cli
```

### 3. Environment Configuration

```bash
# .env file
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional

# For Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

## Key Naming Conventions

### Namespace Structure

The platform uses hierarchical key naming for organization and multi-tenancy:

```
{service}:{feature}:{tenant_id}:{entity_id}:{specific_data}
```

### Common Key Patterns

#### 1. Flow-Related Keys

```bash
# Flow event streams
flow:events:{flow_id}                    # Redis Stream for flow events
flow:updates:{flow_id}                   # Pub/Sub channel for real-time updates
flow:state:{flow_id}                     # Cached flow state (5 min TTL)
flow:meta:{flow_id}                      # Flow metadata (1 hour TTL)

# Examples:
flow:events:abc123-def456-789xyz
flow:state:abc123-def456-789xyz
```

#### 2. User Session Keys

```bash
# SSE connections
sse:connections                          # Hash of all SSE connections
sse:connection:{connection_id}           # Individual connection data
sse:flow:{flow_id}:connections          # Connections for specific flow

# User sessions
session:{user_id}                        # User session data
session:active:{client_id}               # Active sessions for client
```

#### 3. Caching Keys

```bash
# Data caching
cache:assets:{engagement_id}             # Cached assets for engagement
cache:field_mappings:{flow_id}           # Field mapping cache
cache:analysis:{asset_id}                # Analysis results cache

# API response caching
api:discovery:{client_id}:{params_hash}  # API response cache
api:assets:{engagement_id}:{filters}     # Asset listing cache
```

#### 4. Task Queue Keys

```bash
# Celery task queues
celery:task:{task_id}                    # Task result storage
celery:queue:default                     # Default task queue
celery:queue:priority                    # High-priority tasks
celery:retry:{task_id}                   # Retry tracking
```

#### 5. Rate Limiting Keys

```bash
# Rate limiting
rate_limit:{user_id}:{minute}            # Per-minute rate limits
rate_limit:global:{endpoint}:{minute}    # Global endpoint limits
rate_limit:tenant:{client_id}:{hour}     # Tenant-level hourly limits
```

#### 6. Locking Keys

```bash
# Distributed locks
lock:flow:{flow_id}                      # Flow processing lock
lock:import:{import_id}                  # Data import lock
lock:analysis:{asset_id}                 # Asset analysis lock
```

## Redis Data Structures Used

### 1. Redis Streams (Event Bus)

```python
# Adding events to stream
XADD flow:events:{flow_id} * event_type "phase_completed" payload "{\"phase\":\"data_import\"}" timestamp "2025-01-18T12:00:00Z"

# Reading events from stream
XREVRANGE flow:events:{flow_id} + - COUNT 10

# Creating consumer groups
XGROUP CREATE flow:events:{flow_id} processors $ MKSTREAM
```

### 2. Hashes (Structured Data)

```python
# SSE connection registry
HSET sse:connections connection_123 "{\"flow_id\":\"abc123\",\"user_id\":\"user456\"}"
HGETALL sse:connections

# Flow metadata
HSET flow:meta:{flow_id} status "running" phase "field_mapping" progress "45"
HGET flow:meta:{flow_id} status
```

### 3. Sets (Collection Management)

```python
# Active flows per engagement
SADD engagement:{engagement_id}:flows {flow_id1} {flow_id2}
SMEMBERS engagement:{engagement_id}:flows

# User's active connections
SADD user:{user_id}:connections connection_123 connection_456
SCARD user:{user_id}:connections
```

### 4. Sorted Sets (Time-based Data)

```python
# Recent flow activities (with timestamps)
ZADD recent:flows:{client_id} 1705579200 {flow_id1} 1705579260 {flow_id2}
ZREVRANGE recent:flows:{client_id} 0 10 WITHSCORES

# Rate limiting (sliding window)
ZADD rate_limit:sliding:{user_id} 1705579200 request_1 1705579201 request_2
ZREMRANGEBYSCORE rate_limit:sliding:{user_id} -inf (1705579140)  # Remove old entries
```

### 5. Strings (Simple Caching)

```python
# Cached JSON data with TTL
SET cache:flow:state:{flow_id} "{\"status\":\"running\",\"progress\":45}" EX 300
GET cache:flow:state:{flow_id}

# Distributed locks
SET lock:flow:{flow_id} {unique_identifier} NX EX 30
```

## Development Code Patterns

### 1. Redis Manager Service

```python
# backend/app/services/redis_manager.py
import asyncio
import json
from typing import Optional, Dict, List, Any
from redis import asyncio as aioredis
from ..core.config import settings

class RedisManager:
    """Centralized Redis management service"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.pubsub = self.redis.pubsub()
            # Test connection
            await self.redis.ping()
            print("Redis connection established")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.redis = None
            self.pubsub = None
    
    async def close(self):
        """Close Redis connections"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis is not None
    
    async def safe_execute(self, func, *args, fallback=None, **kwargs):
        """Execute Redis command with fallback"""
        if not self.is_available():
            return fallback
        
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"Redis operation failed: {e}")
            return fallback

# Global instance
redis_manager = RedisManager()
```

### 2. Flow Event Bus Implementation

```python
# backend/app/services/flow_event_bus.py
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

class FlowEventBus:
    """Redis-backed event bus for flow events"""
    
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.stream_prefix = "flow:events:"
        self.channel_prefix = "flow:updates:"
        self.max_events = 10000
    
    async def publish_event(
        self,
        flow_id: UUID,
        event_type: str,
        payload: Dict[str, Any],
        source: str = "system"
    ):
        """Publish event to stream and notify subscribers"""
        if not self.redis.is_available():
            # Fallback: store in PostgreSQL event log
            return await self._store_event_in_db(flow_id, event_type, payload, source)
        
        stream_key = f"{self.stream_prefix}{flow_id}"
        event_data = {
            "event_type": event_type,
            "payload": json.dumps(payload),
            "timestamp": datetime.utcnow().isoformat(),
            "source": source
        }
        
        # Add to Redis Stream
        await self.redis.safe_execute(
            self.redis.redis.xadd,
            stream_key,
            event_data,
            maxlen=self.max_events
        )
        
        # Publish to real-time channel
        channel = f"{self.channel_prefix}{flow_id}"
        await self.redis.safe_execute(
            self.redis.redis.publish,
            channel,
            json.dumps(event_data)
        )
    
    async def get_events(
        self,
        flow_id: UUID,
        count: int = 100,
        start: str = "+",
        end: str = "-"
    ) -> List[Dict[str, Any]]:
        """Get events from stream"""
        if not self.redis.is_available():
            # Fallback: get from PostgreSQL
            return await self._get_events_from_db(flow_id, count)
        
        stream_key = f"{self.stream_prefix}{flow_id}"
        events = await self.redis.safe_execute(
            self.redis.redis.xrevrange,
            stream_key,
            start,
            end,
            count=count,
            fallback=[]
        )
        
        return [self._parse_event(event) for event in events]
    
    def _parse_event(self, event_data) -> Dict[str, Any]:
        """Parse Redis stream event data"""
        event_id, fields = event_data
        return {
            "id": event_id,
            "event_type": fields.get("event_type"),
            "payload": json.loads(fields.get("payload", "{}")),
            "timestamp": fields.get("timestamp"),
            "source": fields.get("source")
        }
```

### 3. Caching Service

```python
# backend/app/services/cache_service.py
import json
from typing import Optional, Any, Dict
from uuid import UUID

class CacheService:
    """Redis-backed caching service"""
    
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.default_ttl = 300  # 5 minutes
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if not self.redis.is_available():
            return None
        
        cached = await self.redis.safe_execute(
            self.redis.redis.get,
            key,
            fallback=None
        )
        
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return cached
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set cached value with TTL"""
        if not self.redis.is_available():
            return False
        
        ttl = ttl or self.default_ttl
        serialized = json.dumps(value) if not isinstance(value, str) else value
        
        return await self.redis.safe_execute(
            self.redis.redis.setex,
            key,
            ttl,
            serialized,
            fallback=False
        )
    
    async def delete(self, key: str):
        """Delete cached value"""
        if not self.redis.is_available():
            return False
        
        return await self.redis.safe_execute(
            self.redis.redis.delete,
            key,
            fallback=False
        )
    
    async def get_flow_state(self, flow_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached flow state"""
        key = f"flow:state:{flow_id}"
        return await self.get(key)
    
    async def set_flow_state(
        self,
        flow_id: UUID,
        state: Dict[str, Any],
        ttl: int = 300
    ):
        """Cache flow state"""
        key = f"flow:state:{flow_id}"
        await self.set(key, state, ttl)
        
        # Also cache metadata separately with longer TTL
        metadata = {
            "status": state.get("status"),
            "phase": state.get("current_phase"),
            "progress": state.get("progress_percentage"),
            "updated_at": datetime.utcnow().isoformat()
        }
        meta_key = f"flow:meta:{flow_id}"
        await self.set(meta_key, metadata, ttl * 12)  # 1 hour
```

### 4. SSE Connection Registry

```python
# backend/app/services/sse_registry.py
import json
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

class SSEConnectionRegistry:
    """Redis-backed SSE connection tracking"""
    
    def __init__(self, redis_manager):
        self.redis = redis_manager
        self.registry_key = "sse:connections"
        self.connection_ttl = 300  # 5 minutes
    
    async def register_connection(
        self,
        connection_id: str,
        flow_id: UUID,
        user_id: UUID,
        client_id: UUID
    ):
        """Register new SSE connection"""
        if not self.redis.is_available():
            # Fallback: store in memory or skip
            return False
        
        connection_data = {
            "flow_id": str(flow_id),
            "user_id": str(user_id),
            "client_id": str(client_id),
            "connected_at": datetime.utcnow().isoformat(),
            "server_id": settings.SERVER_ID
        }
        
        # Store in hash
        await self.redis.safe_execute(
            self.redis.redis.hset,
            self.registry_key,
            connection_id,
            json.dumps(connection_data)
        )
        
        # Set expiration for cleanup
        expire_key = f"sse:expire:{connection_id}"
        await self.redis.safe_execute(
            self.redis.redis.setex,
            expire_key,
            self.connection_ttl,
            connection_id
        )
        
        return True
    
    async def unregister_connection(self, connection_id: str):
        """Remove SSE connection"""
        if not self.redis.is_available():
            return False
        
        await self.redis.safe_execute(
            self.redis.redis.hdel,
            self.registry_key,
            connection_id
        )
        
        expire_key = f"sse:expire:{connection_id}"
        await self.redis.safe_execute(
            self.redis.redis.delete,
            expire_key
        )
    
    async def get_flow_connections(self, flow_id: UUID) -> List[str]:
        """Get all connections for a flow"""
        if not self.redis.is_available():
            return []
        
        all_connections = await self.redis.safe_execute(
            self.redis.redis.hgetall,
            self.registry_key,
            fallback={}
        )
        
        flow_connections = []
        for conn_id, data in all_connections.items():
            try:
                conn_data = json.loads(data)
                if conn_data["flow_id"] == str(flow_id):
                    flow_connections.append(conn_id)
            except (json.JSONDecodeError, KeyError):
                # Clean up invalid entries
                await self.unregister_connection(conn_id)
        
        return flow_connections
```

## Redis CLI Commands for Development

### Basic Inspection Commands

```bash
# Connect to Redis
docker exec -it migration_redis redis-cli

# Basic information
INFO                              # Redis server info
DBSIZE                           # Number of keys in current DB
MEMORY USAGE                     # Memory usage stats

# Key inspection
KEYS *                           # List all keys (avoid in production)
KEYS flow:*                      # List keys matching pattern
TYPE flow:events:abc123          # Get key data type
TTL flow:state:abc123            # Get key TTL
```

### Flow-related Inspection

```bash
# View flow events
XLEN flow:events:{flow_id}                    # Number of events in stream
XRANGE flow:events:{flow_id} - +              # All events
XREVRANGE flow:events:{flow_id} + - COUNT 10  # Latest 10 events

# Check flow state cache
GET flow:state:{flow_id}                      # Cached flow state
HGETALL flow:meta:{flow_id}                   # Flow metadata

# SSE connections
HGETALL sse:connections                       # All SSE connections
HGET sse:connections connection_123           # Specific connection
```

### Cache Management

```bash
# Check cached data
GET cache:assets:{engagement_id}              # Cached assets
GET api:discovery:{client_id}:{hash}          # API response cache

# Cache statistics
INFO memory                                   # Memory usage
INFO stats                                    # Operation stats

# Clear cache patterns
DEL cache:*                                   # Delete all cache keys
EVAL "return redis.call('del', unpack(redis.call('keys', ARGV[1])))" 0 "cache:*"
```

### Task Queue Inspection

```bash
# Celery queues
LLEN celery                                   # Default queue length
LLEN celery:priority                          # Priority queue length

# Task results
GET celery-task-meta-{task_id}                # Task result
KEYS celery-task-meta-*                       # All task results
```

### Performance Monitoring

```bash
# Monitor commands in real-time
MONITOR                                       # Watch all commands

# Slow log
SLOWLOG GET 10                                # Get 10 slowest commands
SLOWLOG LEN                                   # Number of slow commands
SLOWLOG RESET                                 # Clear slow log

# Connection info
CLIENT LIST                                   # Active connections
CLIENT INFO                                   # Current connection info
```

## Debugging and Troubleshooting

### Common Redis Issues

#### 1. Connection Problems

```bash
# Test Redis connectivity
docker exec migration_redis redis-cli ping
# Expected: PONG

# Check Redis container status
docker ps | grep redis
docker logs migration_redis

# Check network connectivity
docker exec migration_backend ping migration_redis
```

#### 2. Memory Issues

```bash
# Check memory usage
docker exec migration_redis redis-cli INFO memory

# Check memory policy
docker exec migration_redis redis-cli CONFIG GET maxmemory-policy

# Find large keys
docker exec migration_redis redis-cli --bigkeys
```

#### 3. Performance Issues

```bash
# Check for slow commands
docker exec migration_redis redis-cli SLOWLOG GET

# Monitor real-time operations
docker exec migration_redis redis-cli MONITOR

# Check key expiration
docker exec migration_redis redis-cli TTL flow:state:{flow_id}
```

### Redis Health Check Script

```python
# scripts/check_redis_health.py
import asyncio
import sys
from app.services.redis_manager import redis_manager

async def check_redis_health():
    """Comprehensive Redis health check"""
    try:
        await redis_manager.initialize()
        
        if not redis_manager.is_available():
            print("❌ Redis not available")
            return False
        
        # Test basic operations
        test_key = "health:check:test"
        
        # Test SET/GET
        await redis_manager.redis.set(test_key, "test_value", ex=10)
        value = await redis_manager.redis.get(test_key)
        
        if value != "test_value":
            print("❌ Redis SET/GET test failed")
            return False
        
        # Test hash operations
        hash_key = "health:check:hash"
        await redis_manager.redis.hset(hash_key, "field1", "value1")
        hash_value = await redis_manager.redis.hget(hash_key, "field1")
        
        if hash_value != "value1":
            print("❌ Redis HASH test failed")
            return False
        
        # Test pub/sub
        channel = "health:check:channel"
        await redis_manager.redis.publish(channel, "test_message")
        
        # Clean up
        await redis_manager.redis.delete(test_key, hash_key)
        
        print("✅ Redis health check passed")
        return True
        
    except Exception as e:
        print(f"❌ Redis health check failed: {e}")
        return False
    finally:
        await redis_manager.close()

if __name__ == "__main__":
    result = asyncio.run(check_redis_health())
    sys.exit(0 if result else 1)
```

### Performance Monitoring

```python
# backend/app/monitoring/redis_monitor.py
import time
from typing import Dict, Any
from ..services.redis_manager import redis_manager

class RedisMonitor:
    """Redis performance monitoring"""
    
    @staticmethod
    async def get_redis_stats() -> Dict[str, Any]:
        """Get comprehensive Redis statistics"""
        if not redis_manager.is_available():
            return {"status": "unavailable"}
        
        info = await redis_manager.redis.info()
        
        return {
            "status": "available",
            "memory": {
                "used": info.get("used_memory_human"),
                "peak": info.get("used_memory_peak_human"),
                "total_system": info.get("total_system_memory_human")
            },
            "connections": {
                "connected_clients": info.get("connected_clients"),
                "max_clients": info.get("maxclients"),
                "total_connections": info.get("total_connections_received")
            },
            "operations": {
                "commands_processed": info.get("total_commands_processed"),
                "ops_per_sec": info.get("instantaneous_ops_per_sec"),
                "hits": info.get("keyspace_hits"),
                "misses": info.get("keyspace_misses")
            },
            "persistence": {
                "rdb_last_save": info.get("rdb_last_save_time"),
                "aof_enabled": info.get("aof_enabled")
            }
        }
    
    @staticmethod
    async def check_key_patterns() -> Dict[str, int]:
        """Analyze key patterns and counts"""
        patterns = [
            "flow:*",
            "cache:*", 
            "sse:*",
            "rate_limit:*",
            "lock:*",
            "celery*"
        ]
        
        results = {}
        for pattern in patterns:
            keys = await redis_manager.safe_execute(
                redis_manager.redis.keys,
                pattern,
                fallback=[]
            )
            results[pattern] = len(keys)
        
        return results
```

## Best Practices

### 1. Key Design
- Use consistent, hierarchical naming conventions
- Include tenant context in multi-tenant keys
- Implement appropriate TTLs for all cached data
- Avoid using KEYS command in production
- Use specific patterns for different data types

### 2. Error Handling
- Always implement fallback strategies
- Use try-catch blocks for Redis operations
- Monitor Redis availability and performance
- Implement circuit breaker patterns for resilience

### 3. Performance
- Use pipelining for bulk operations
- Implement connection pooling appropriately
- Monitor memory usage and set appropriate limits
- Use appropriate data structures for use cases

### 4. Security
- Implement proper authentication if needed
- Use network isolation in production
- Monitor for suspicious access patterns
- Implement rate limiting to prevent abuse

---

*Last Updated: 2025-01-18*