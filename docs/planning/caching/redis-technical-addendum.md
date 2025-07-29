# Redis Technical Addendum - CrewAI Integration Specifications

## Executive Summary

This document provides detailed technical specifications for integrating Redis with the AI Modernize Migration Platform's CrewAI-based architecture. It focuses on specific integration points with the Master Flow Orchestrator, UnifiedDiscoveryFlow state management, and the complex ADR-012 child flow orchestration logic.

---

## 1. CrewAI Flow Integration Specifics

### 1.1 Master Flow Orchestrator Integration

The Master Flow Orchestrator manages multiple concurrent CrewAI flows. Redis integration must support:

```python
# backend/app/services/orchestrator/redis_flow_orchestrator.py
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from app.core.redis_config import redis_manager
from app.services.cache.flow_state_cache import flow_state_cache
from app.services.flows.events import flow_event_bus
from app.schemas.flow_events import FlowEvent

class RedisFlowOrchestrator:
    """Redis-enhanced Master Flow Orchestrator"""
    
    def __init__(self):
        self.orchestrator_prefix = "orchestrator:"
        self.flow_registry_key = f"{self.orchestrator_prefix}flows"
        self.flow_hierarchy_prefix = f"{self.orchestrator_prefix}hierarchy:"
        self.flow_locks_prefix = f"{self.orchestrator_prefix}locks:"
        self.ttl_active_flow = 3600  # 1 hour for active flows
        
    async def register_flow(
        self, 
        flow_id: str, 
        flow_type: str,
        parent_flow_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register a new CrewAI flow in the orchestrator"""
        if not redis_manager.is_available():
            return False
            
        try:
            flow_data = {
                "flow_id": flow_id,
                "flow_type": flow_type,
                "parent_flow_id": parent_flow_id,
                "status": "initializing",
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store flow data
            flow_key = f"{self.orchestrator_prefix}flow:{flow_id}"
            await redis_manager.redis.hset(
                flow_key,
                mapping={
                    "data": json.dumps(flow_data),
                    "status": "initializing",
                    "last_updated": datetime.utcnow().isoformat()
                }
            )
            await redis_manager.redis.expire(flow_key, self.ttl_active_flow)
            
            # Add to flow registry
            await redis_manager.redis.sadd(self.flow_registry_key, flow_id)
            
            # Establish parent-child relationship
            if parent_flow_id:
                hierarchy_key = f"{self.flow_hierarchy_prefix}{parent_flow_id}"
                await redis_manager.redis.sadd(hierarchy_key, flow_id)
                await redis_manager.redis.expire(hierarchy_key, self.ttl_active_flow)
            
            # Publish registration event
            await flow_event_bus.publish(
                FlowEvent(
                    flow_id=flow_id,
                    event_type="FLOW_REGISTERED",
                    payload={
                        "flow_type": flow_type,
                        "parent_flow_id": parent_flow_id,
                        "orchestrator_id": self.get_orchestrator_id()
                    },
                    timestamp=datetime.utcnow()
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register flow {flow_id}: {e}")
            return False
    
    async def acquire_flow_lock(
        self, 
        flow_id: str, 
        ttl: int = 30
    ) -> Optional[str]:
        """Acquire distributed lock for flow operations"""
        if not redis_manager.is_available():
            return None
            
        try:
            lock_key = f"{self.flow_locks_prefix}{flow_id}"
            lock_value = f"{self.get_orchestrator_id()}:{datetime.utcnow().isoformat()}"
            
            # Set lock with NX (only if not exists) and EX (expiry)
            acquired = await redis_manager.redis.set(
                lock_key,
                lock_value,
                nx=True,
                ex=ttl
            )
            
            return lock_value if acquired else None
            
        except Exception as e:
            logger.error(f"Failed to acquire lock for flow {flow_id}: {e}")
            return None
    
    async def get_child_flows(self, parent_flow_id: str) -> List[str]:
        """Get all child flows for a parent flow"""
        if not redis_manager.is_available():
            return []
            
        try:
            hierarchy_key = f"{self.flow_hierarchy_prefix}{parent_flow_id}"
            child_flows = await redis_manager.redis.smembers(hierarchy_key)
            return list(child_flows)
            
        except Exception as e:
            logger.error(f"Failed to get child flows for {parent_flow_id}: {e}")
            return []
```

### 1.2 UnifiedDiscoveryFlow State Management

The UnifiedDiscoveryFlow requires sophisticated state caching due to its complex multi-phase execution:

```python
# backend/app/services/crewai_flows/unified_discovery_flow_redis.py
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
from app.services.cache.flow_state_cache import flow_state_cache
from typing import Dict, Any, Optional
import json

class RedisUnifiedDiscoveryFlow(UnifiedDiscoveryFlow):
    """Enhanced UnifiedDiscoveryFlow with Redis state management"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_cache_prefix = "discovery:state:"
        self.phase_cache_prefix = "discovery:phase:"
        self.agent_results_prefix = "discovery:agents:"
        
    async def save_phase_state(
        self, 
        phase: str, 
        state: Dict[str, Any]
    ) -> bool:
        """Save phase-specific state to Redis"""
        if not redis_manager.is_available():
            return await super().save_phase_state(phase, state)
            
        try:
            # Save to Redis with phase-specific TTL
            phase_key = f"{self.phase_cache_prefix}{self.flow_id}:{phase}"
            ttl = self._get_phase_ttl(phase)
            
            phase_data = {
                "phase": phase,
                "state": state,
                "saved_at": datetime.utcnow().isoformat(),
                "flow_id": self.flow_id
            }
            
            await redis_manager.redis.setex(
                phase_key,
                ttl,
                json.dumps(phase_data)
            )
            
            # Update phase tracking
            phases_key = f"{self.state_cache_prefix}{self.flow_id}:phases"
            await redis_manager.redis.sadd(phases_key, phase)
            await redis_manager.redis.expire(phases_key, 86400)  # 24 hours
            
            # Invalidate main cache to force refresh
            await flow_state_cache.invalidate(self.flow_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save phase state: {e}")
            return await super().save_phase_state(phase, state)
    
    async def get_phase_state(self, phase: str) -> Optional[Dict[str, Any]]:
        """Retrieve phase-specific state from Redis"""
        if not redis_manager.is_available():
            return await super().get_phase_state(phase)
            
        try:
            phase_key = f"{self.phase_cache_prefix}{self.flow_id}:{phase}"
            data = await redis_manager.redis.get(phase_key)
            
            if data:
                phase_data = json.loads(data)
                return phase_data.get("state")
            
            return await super().get_phase_state(phase)
            
        except Exception as e:
            logger.error(f"Failed to get phase state: {e}")
            return await super().get_phase_state(phase)
    
    def _get_phase_ttl(self, phase: str) -> int:
        """Get phase-specific TTL based on criticality"""
        phase_ttls = {
            "technology_analysis": 7200,      # 2 hours - heavyweight
            "data_discovery": 7200,           # 2 hours - heavyweight
            "middleware_discovery": 3600,     # 1 hour - medium
            "infrastructure_analysis": 3600,  # 1 hour - medium
            "synthesis": 1800,                # 30 minutes - lightweight
            "completed": 86400                # 24 hours - archival
        }
        return phase_ttls.get(phase, 3600)  # Default 1 hour
    
    async def cache_agent_results(
        self, 
        agent_name: str, 
        results: Dict[str, Any]
    ) -> bool:
        """Cache individual agent results for reuse"""
        if not redis_manager.is_available():
            return False
            
        try:
            agent_key = f"{self.agent_results_prefix}{self.flow_id}:{agent_name}"
            
            agent_data = {
                "agent": agent_name,
                "results": results,
                "cached_at": datetime.utcnow().isoformat(),
                "flow_id": self.flow_id
            }
            
            # Cache with agent-specific TTL
            ttl = 3600 if "analyzer" in agent_name else 1800
            await redis_manager.redis.setex(
                agent_key,
                ttl,
                json.dumps(agent_data)
            )
            
            # Track cached agents
            agents_key = f"{self.state_cache_prefix}{self.flow_id}:cached_agents"
            await redis_manager.redis.sadd(agents_key, agent_name)
            await redis_manager.redis.expire(agents_key, 86400)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache agent results: {e}")
            return False
```

### 1.3 FlowStateManager Integration

Integration with the existing FlowStateManager to support ADR-012 child flow logic:

```python
# backend/app/services/flows/redis_flow_state_manager.py
from app.services.flows.flow_state_manager import FlowStateManager
from app.core.redis_config import redis_manager
import json

class RedisFlowStateManager(FlowStateManager):
    """Enhanced FlowStateManager with Redis caching"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_transitions_key = "flow:transitions:"
        self.state_snapshots_key = "flow:snapshots:"
        
    async def transition_state(
        self, 
        flow_id: str,
        from_state: str,
        to_state: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record state transition in Redis for real-time tracking"""
        # Perform original transition
        result = await super().transition_state(
            flow_id, from_state, to_state, metadata
        )
        
        if result and redis_manager.is_available():
            try:
                # Record transition in Redis Stream
                transition_key = f"{self.state_transitions_key}{flow_id}"
                transition_data = {
                    "from_state": from_state,
                    "to_state": to_state,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": json.dumps(metadata or {})
                }
                
                await redis_manager.redis.xadd(
                    transition_key,
                    transition_data,
                    maxlen=1000,  # Keep last 1000 transitions
                    approximate=True
                )
                
                # Set expiry
                await redis_manager.redis.expire(transition_key, 86400)
                
                # Publish transition event
                await flow_event_bus.publish(
                    FlowEvent(
                        flow_id=flow_id,
                        event_type="STATE_TRANSITION",
                        payload={
                            "from": from_state,
                            "to": to_state,
                            "metadata": metadata
                        },
                        timestamp=datetime.utcnow()
                    )
                )
                
            except Exception as e:
                logger.error(f"Failed to record transition in Redis: {e}")
        
        return result
    
    async def save_state_snapshot(
        self, 
        flow_id: str,
        snapshot_id: str,
        state: Dict[str, Any]
    ) -> bool:
        """Save state snapshot for recovery and debugging"""
        if not redis_manager.is_available():
            return False
            
        try:
            snapshot_key = f"{self.state_snapshots_key}{flow_id}:{snapshot_id}"
            
            snapshot_data = {
                "flow_id": flow_id,
                "snapshot_id": snapshot_id,
                "state": state,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save snapshot with 7-day TTL
            await redis_manager.redis.setex(
                snapshot_key,
                604800,  # 7 days
                json.dumps(snapshot_data)
            )
            
            # Track snapshots
            snapshots_list_key = f"{self.state_snapshots_key}{flow_id}:list"
            await redis_manager.redis.lpush(snapshots_list_key, snapshot_id)
            await redis_manager.redis.ltrim(snapshots_list_key, 0, 9)  # Keep last 10
            await redis_manager.redis.expire(snapshots_list_key, 604800)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save state snapshot: {e}")
            return False
```

### 1.4 Agent Result Caching Patterns

Specific caching patterns for different agent types:

```python
# backend/app/services/cache/agent_result_cache.py
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json

class AgentResultCache:
    """Intelligent caching for CrewAI agent results"""
    
    def __init__(self):
        self.cache_prefix = "agent:results:"
        self.metadata_prefix = "agent:meta:"
        
        # Agent-specific TTL configurations
        self.agent_ttls = {
            # Technology analysis agents - longer cache
            "technology_analyzer": 7200,      # 2 hours
            "codebase_analyzer": 7200,        # 2 hours
            "database_analyzer": 3600,        # 1 hour
            
            # Discovery agents - medium cache
            "data_flow_analyzer": 3600,       # 1 hour
            "middleware_analyzer": 3600,      # 1 hour
            "infrastructure_analyzer": 1800,  # 30 minutes
            
            # Synthesis agents - short cache
            "migration_synthesizer": 900,     # 15 minutes
            "recommendation_agent": 900,      # 15 minutes
            
            # Default
            "default": 1800                   # 30 minutes
        }
    
    def _generate_cache_key(
        self, 
        agent_name: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate deterministic cache key based on inputs"""
        # Create stable hash of inputs
        cache_data = {
            "agent": agent_name,
            "input": input_data,
            "context": context or {}
        }
        
        # Sort keys for consistency
        stable_string = json.dumps(cache_data, sort_keys=True)
        hash_digest = hashlib.sha256(stable_string.encode()).hexdigest()[:16]
        
        return f"{self.cache_prefix}{agent_name}:{hash_digest}"
    
    async def get_cached_result(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached agent result if available"""
        if not redis_manager.is_available():
            return None
            
        try:
            cache_key = self._generate_cache_key(agent_name, input_data, context)
            
            # Check if cached result exists
            cached_data = await redis_manager.redis.get(cache_key)
            if not cached_data:
                return None
            
            result = json.loads(cached_data)
            
            # Update access metrics
            await self._update_cache_metrics(agent_name, "hit")
            
            # Extend TTL on access (cache warming)
            ttl = self.agent_ttls.get(agent_name, self.agent_ttls["default"])
            await redis_manager.redis.expire(cache_key, ttl)
            
            return result.get("output")
            
        except Exception as e:
            logger.error(f"Failed to get cached result for {agent_name}: {e}")
            await self._update_cache_metrics(agent_name, "error")
            return None
    
    async def cache_agent_result(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ) -> bool:
        """Cache agent execution result"""
        if not redis_manager.is_available():
            return False
            
        try:
            cache_key = self._generate_cache_key(agent_name, input_data, context)
            
            # Prepare cache data
            cache_data = {
                "agent": agent_name,
                "input": input_data,
                "output": output_data,
                "context": context or {},
                "cached_at": datetime.utcnow().isoformat(),
                "execution_time": execution_time
            }
            
            # Get agent-specific TTL
            ttl = self.agent_ttls.get(agent_name, self.agent_ttls["default"])
            
            # Cache the result
            await redis_manager.redis.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )
            
            # Store metadata for monitoring
            meta_key = f"{self.metadata_prefix}{agent_name}"
            await redis_manager.redis.hincrby(meta_key, "total_cached", 1)
            await redis_manager.redis.hset(
                meta_key, 
                "last_cached", 
                datetime.utcnow().isoformat()
            )
            
            # Update metrics
            await self._update_cache_metrics(agent_name, "set")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache result for {agent_name}: {e}")
            return False
    
    async def invalidate_agent_cache(
        self, 
        agent_name: str,
        pattern: Optional[str] = None
    ) -> int:
        """Invalidate cached results for an agent"""
        if not redis_manager.is_available():
            return 0
            
        try:
            if pattern:
                # Invalidate specific pattern
                search_pattern = f"{self.cache_prefix}{agent_name}:*{pattern}*"
            else:
                # Invalidate all for agent
                search_pattern = f"{self.cache_prefix}{agent_name}:*"
            
            # Find and delete matching keys
            deleted = 0
            cursor = 0
            while True:
                cursor, keys = await redis_manager.redis.scan(
                    cursor,
                    match=search_pattern,
                    count=100
                )
                
                if keys:
                    deleted += await redis_manager.redis.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Invalidated {deleted} cache entries for {agent_name}")
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for {agent_name}: {e}")
            return 0
    
    async def _update_cache_metrics(self, agent_name: str, metric_type: str):
        """Update cache performance metrics"""
        try:
            metrics_key = f"metrics:agent_cache:{agent_name}"
            await redis_manager.redis.hincrby(metrics_key, metric_type, 1)
            await redis_manager.redis.expire(metrics_key, 86400)  # 24 hour TTL
        except Exception:
            pass  # Don't fail on metrics

# Global agent cache instance
agent_result_cache = AgentResultCache()
```

---

## 2. Performance Optimization Details

### 2.1 Caching Keys and TTL Strategies

```python
# backend/app/services/cache/cache_config.py

CACHE_KEY_PATTERNS = {
    # Flow-level caching
    "flow_state": "cache:flow:state:{flow_id}",
    "flow_metadata": "cache:flow:meta:{flow_id}",
    "flow_events": "flow:events:{flow_id}",
    "flow_transitions": "flow:transitions:{flow_id}",
    
    # Agent-level caching
    "agent_results": "agent:results:{agent_name}:{hash}",
    "agent_metadata": "agent:meta:{agent_name}",
    
    # Discovery-specific caching
    "discovery_phase": "discovery:phase:{flow_id}:{phase}",
    "discovery_agents": "discovery:agents:{flow_id}:{agent}",
    
    # SSE connection tracking
    "sse_connections": "sse:connections:{connection_id}",
    "sse_flow_connections": "sse:connections:flow:{flow_id}",
    
    # Orchestrator caching
    "orchestrator_flows": "orchestrator:flows",
    "orchestrator_hierarchy": "orchestrator:hierarchy:{parent_id}",
    "orchestrator_locks": "orchestrator:locks:{flow_id}",
    
    # Metrics and monitoring
    "metrics_cache": "metrics:cache:{metric_type}",
    "metrics_agent": "metrics:agent_cache:{agent_name}"
}

TTL_STRATEGIES = {
    # Active flow states - short TTL for freshness
    "active_flow": 300,           # 5 minutes
    
    # Completed states - longer retention
    "completed_flow": 3600,       # 1 hour
    "failed_flow": 1800,          # 30 minutes
    
    # Agent results - varies by type
    "heavy_analysis": 7200,       # 2 hours (technology, codebase analysis)
    "medium_analysis": 3600,      # 1 hour (data flow, middleware)
    "light_analysis": 1800,       # 30 minutes (infrastructure)
    "synthesis": 900,             # 15 minutes (recommendations)
    
    # Event streams
    "event_stream": 86400,        # 24 hours
    "event_channel": 300,         # 5 minutes (pub/sub)
    
    # SSE connections
    "sse_connection": 300,        # 5 minutes (with heartbeat refresh)
    
    # Metrics
    "metrics_daily": 86400,       # 24 hours
    "metrics_hourly": 3600,       # 1 hour
    
    # Snapshots and archives
    "state_snapshot": 604800,     # 7 days
    "audit_trail": 2592000        # 30 days
}
```

### 2.2 Memory Usage Estimates

```python
# backend/docs/redis_memory_estimates.py

"""
Memory Usage Estimates for Typical Discovery Flows

Assumptions:
- Average flow runs for 30 minutes
- 10 concurrent flows during peak
- JSON serialization overhead ~20%
"""

MEMORY_ESTIMATES = {
    "per_flow_state": {
        "basic_metadata": 1,          # 1 KB - flow ID, status, timestamps
        "phase_states": 5,            # 5 KB - 5 phases × 1 KB each
        "agent_results": 20,          # 20 KB - 10 agents × 2 KB average
        "event_stream": 10,           # 10 KB - ~100 events × 100 bytes
        "total_per_flow": 36          # 36 KB per flow
    },
    
    "concurrent_flows": {
        "10_flows": 360,              # 360 KB
        "50_flows": 1800,             # 1.8 MB
        "100_flows": 3600             # 3.6 MB
    },
    
    "with_caching": {
        "agent_cache_hit_rate": 0.7,  # 70% cache hit rate
        "memory_saved": 0.5,          # 50% memory saved with dedup
        "effective_10_flows": 180,    # 180 KB
        "effective_50_flows": 900,    # 900 KB
        "effective_100_flows": 1800   # 1.8 MB
    },
    
    "upstash_free_tier": {
        "total_memory": 256,          # 256 MB free tier
        "reserved_overhead": 50,      # 50 MB Redis overhead
        "available": 206,             # 206 MB available
        "max_concurrent_flows": 5000  # Theoretical max with caching
    }
}

# Monitoring script
async def estimate_memory_usage(flow_id: str) -> Dict[str, int]:
    """Estimate memory usage for a specific flow"""
    if not redis_manager.is_available():
        return {}
        
    memory_info = {}
    
    # Check each component
    patterns = [
        f"cache:flow:state:{flow_id}",
        f"discovery:phase:{flow_id}:*",
        f"discovery:agents:{flow_id}:*",
        f"flow:events:{flow_id}"
    ]
    
    total_memory = 0
    for pattern in patterns:
        cursor = 0
        pattern_memory = 0
        
        while True:
            cursor, keys = await redis_manager.redis.scan(
                cursor, match=pattern, count=100
            )
            
            for key in keys:
                memory = await redis_manager.redis.memory_usage(key) or 0
                pattern_memory += memory
            
            if cursor == 0:
                break
        
        memory_info[pattern] = pattern_memory
        total_memory += pattern_memory
    
    memory_info["total"] = total_memory
    memory_info["total_kb"] = round(total_memory / 1024, 2)
    
    return memory_info
```

### 2.3 Connection Pooling Configuration

```python
# backend/app/core/redis_pool_config.py
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
import ssl

class OptimizedRedisPool:
    """Optimized Redis connection pool for Railway deployment"""
    
    @staticmethod
    def create_pool(redis_url: str, is_production: bool = False) -> ConnectionPool:
        """Create optimized connection pool"""
        
        # Production (Upstash) configuration
        if is_production:
            # Parse Upstash URL to extract components
            # Upstash requires specific SSL configuration
            
            pool = ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                
                # Connection pool settings
                max_connections=50,           # Upstash connection limit
                min_idle_time=300,           # 5 minutes idle before close
                connection_class=None,       # Use default
                
                # Health checking
                health_check_interval=30,    # Check every 30 seconds
                
                # Retry configuration
                retry_on_timeout=True,
                retry_on_error=[
                    ConnectionError,
                    TimeoutError,
                    ssl.SSLError
                ],
                retry=Retry(
                    ExponentialBackoff(base=1, cap=30),
                    retries=3
                ),
                
                # Socket configuration
                socket_connect_timeout=5,
                socket_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={
                    # TCP keepalive settings
                    1: 3,   # TCP_KEEPIDLE - start keepalive after 3s
                    2: 3,   # TCP_KEEPINTVL - interval between keepalives
                    3: 3,   # TCP_KEEPCNT - failed keepalives before declaring dead
                },
                
                # SSL/TLS for Upstash
                ssl_cert_reqs="required",
                ssl_check_hostname=True,
                ssl_ca_certs=None  # Use system CA bundle
            )
            
        else:
            # Development configuration
            pool = ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                max_connections=20,
                health_check_interval=60,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        
        return pool
    
    @staticmethod
    async def create_redis_client(
        pool: ConnectionPool,
        command_timeout: Optional[float] = None
    ) -> Redis:
        """Create Redis client with monitoring"""
        
        client = Redis(
            connection_pool=pool,
            single_connection_client=False,
            response_callbacks={}  # Use default callbacks
        )
        
        # Wrap client with monitoring
        return MonitoredRedisClient(client, command_timeout)

class MonitoredRedisClient:
    """Redis client wrapper with performance monitoring"""
    
    def __init__(self, client: Redis, command_timeout: Optional[float] = None):
        self.client = client
        self.command_timeout = command_timeout or 5.0
        
    async def execute_command(self, *args, **kwargs):
        """Execute Redis command with monitoring"""
        start_time = time.time()
        command = args[0] if args else "unknown"
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.client.execute_command(*args, **kwargs),
                timeout=self.command_timeout
            )
            
            # Record success metrics
            latency = (time.time() - start_time) * 1000
            await self._record_metric(command, "success", latency)
            
            return result
            
        except asyncio.TimeoutError:
            await self._record_metric(command, "timeout", self.command_timeout * 1000)
            raise
            
        except Exception as e:
            await self._record_metric(command, "error", 0)
            raise
    
    async def _record_metric(self, command: str, status: str, latency: float):
        """Record command metrics"""
        try:
            # Use a separate connection for metrics to avoid recursion
            metrics_key = f"metrics:redis:commands:{command.lower()}"
            
            # This would be sent to a metrics service
            logger.debug(
                f"Redis command: {command}, status: {status}, latency: {latency:.2f}ms"
            )
            
        except Exception:
            pass  # Don't fail on metrics
    
    def __getattr__(self, name):
        """Proxy all other methods to underlying client"""
        attr = getattr(self.client, name)
        
        if callable(attr):
            async def monitored_method(*args, **kwargs):
                return await self.execute_command(name.upper(), *args, **kwargs)
            return monitored_method
        
        return attr
```

---

## 3. Technical Implementation Notes

### 3.1 Error Handling Patterns

```python
# backend/app/services/cache/redis_error_handler.py
from functools import wraps
import asyncio
from typing import TypeVar, Callable, Optional, Any
from app.core.redis_config import redis_manager

T = TypeVar('T')

def redis_fallback(
    fallback_value: Optional[T] = None,
    fallback_function: Optional[Callable] = None,
    log_errors: bool = True
):
    """Decorator for Redis operations with automatic fallback"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                # Check Redis availability first
                if not redis_manager.is_available():
                    logger.debug(f"{func.__name__}: Redis unavailable, using fallback")
                    
                    if fallback_function:
                        return await fallback_function(*args, **kwargs)
                    return fallback_value
                
                # Execute Redis operation with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=5.0  # 5 second timeout
                )
                return result
                
            except asyncio.TimeoutError:
                if log_errors:
                    logger.warning(f"{func.__name__}: Redis timeout, using fallback")
                    
            except Exception as e:
                if log_errors:
                    logger.error(f"{func.__name__}: Redis error: {e}, using fallback")
            
            # Use fallback
            if fallback_function:
                return await fallback_function(*args, **kwargs)
            return fallback_value
            
        return wrapper
    return decorator

# Usage example
class FlowService:
    
    @redis_fallback(fallback_value={}, log_errors=True)
    async def get_flow_state_with_fallback(self, flow_id: str) -> Dict[str, Any]:
        """Get flow state from Redis with automatic fallback"""
        return await flow_state_cache.get(flow_id)
    
    @redis_fallback(
        fallback_function=lambda self, flow_id: self._get_state_from_db(flow_id)
    )
    async def get_flow_state_smart(self, flow_id: str) -> Dict[str, Any]:
        """Get flow state from Redis, fallback to DB"""
        return await flow_state_cache.get(flow_id)
```

### 3.2 Monitoring and Alerting Setup

```python
# backend/app/monitoring/redis_health_monitor.py
from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta
from app.core.redis_config import redis_manager
from app.services.notifications import alert_service

class RedisHealthMonitor:
    """Comprehensive Redis health monitoring"""
    
    def __init__(self):
        self.check_interval = 60  # Check every minute
        self.alert_thresholds = {
            "memory_usage_percent": 80,
            "connection_count": 40,
            "slow_commands_ms": 100,
            "error_rate_percent": 5
        }
        self.monitoring_active = False
        
    async def start_monitoring(self):
        """Start background monitoring task"""
        self.monitoring_active = True
        asyncio.create_task(self._monitoring_loop())
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                health_status = await self.check_redis_health()
                
                # Check thresholds and alert
                await self._check_alerts(health_status)
                
                # Store metrics
                await self._store_metrics(health_status)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                
            await asyncio.sleep(self.check_interval)
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        if not redis_manager.is_available():
            return {"status": "unavailable", "timestamp": datetime.utcnow()}
            
        try:
            # Get Redis INFO
            info = await redis_manager.redis.info()
            
            # Calculate metrics
            memory_usage_percent = (
                float(info.get("used_memory", 0)) / 
                float(info.get("maxmemory", 1)) * 100
                if info.get("maxmemory", 0) > 0 else 0
            )
            
            # Get slow log
            slow_log = await redis_manager.redis.slowlog_get(10)
            slow_commands = [
                {
                    "command": " ".join(log["command"]),
                    "duration_ms": log["duration"] / 1000,
                    "timestamp": log["start_time"]
                }
                for log in slow_log
            ]
            
            # Calculate error rate
            total_commands = info.get("total_commands_processed", 1)
            failed_commands = info.get("rejected_connections", 0)
            error_rate = (failed_commands / total_commands * 100) if total_commands > 0 else 0
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow(),
                "metrics": {
                    "memory_usage_percent": round(memory_usage_percent, 2),
                    "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                    "connected_clients": info.get("connected_clients", 0),
                    "ops_per_second": info.get("instantaneous_ops_per_sec", 0),
                    "error_rate_percent": round(error_rate, 2),
                    "uptime_hours": round(info.get("uptime_in_seconds", 0) / 3600, 2),
                    "keyspace_info": info.get("db0", {}),
                    "slow_commands": slow_commands[:5]  # Top 5 slow commands
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
    
    async def _check_alerts(self, health_status: Dict[str, Any]):
        """Check thresholds and send alerts"""
        if health_status["status"] != "healthy":
            await alert_service.send_alert(
                level="critical",
                message=f"Redis health check failed: {health_status.get('error', 'Unknown error')}",
                context=health_status
            )
            return
            
        metrics = health_status.get("metrics", {})
        
        # Check each threshold
        alerts = []
        
        if metrics.get("memory_usage_percent", 0) > self.alert_thresholds["memory_usage_percent"]:
            alerts.append(
                f"High memory usage: {metrics['memory_usage_percent']}%"
            )
            
        if metrics.get("connected_clients", 0) > self.alert_thresholds["connection_count"]:
            alerts.append(
                f"High connection count: {metrics['connected_clients']}"
            )
            
        if metrics.get("error_rate_percent", 0) > self.alert_thresholds["error_rate_percent"]:
            alerts.append(
                f"High error rate: {metrics['error_rate_percent']}%"
            )
            
        # Check slow commands
        slow_commands = metrics.get("slow_commands", [])
        if slow_commands:
            max_duration = max(cmd["duration_ms"] for cmd in slow_commands)
            if max_duration > self.alert_thresholds["slow_commands_ms"]:
                alerts.append(
                    f"Slow commands detected: {max_duration:.2f}ms"
                )
        
        # Send consolidated alert
        if alerts:
            await alert_service.send_alert(
                level="warning",
                message="Redis performance issues detected",
                context={
                    "issues": alerts,
                    "metrics": metrics
                }
            )
    
    async def _store_metrics(self, health_status: Dict[str, Any]):
        """Store metrics for historical analysis"""
        if health_status["status"] != "healthy":
            return
            
        try:
            # Store in Redis time series (if available)
            metrics = health_status["metrics"]
            timestamp = int(datetime.utcnow().timestamp())
            
            # Store each metric
            metric_keys = [
                ("memory_usage_percent", metrics.get("memory_usage_percent", 0)),
                ("connected_clients", metrics.get("connected_clients", 0)),
                ("ops_per_second", metrics.get("ops_per_second", 0)),
                ("error_rate_percent", metrics.get("error_rate_percent", 0))
            ]
            
            for metric_name, value in metric_keys:
                key = f"metrics:redis:{metric_name}"
                
                # Store as sorted set with timestamp as score
                await redis_manager.redis.zadd(
                    key,
                    {f"{timestamp}:{value}": timestamp}
                )
                
                # Keep only last 24 hours
                cutoff = timestamp - 86400
                await redis_manager.redis.zremrangebyscore(key, 0, cutoff)
                
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

# Global monitor instance
redis_health_monitor = RedisHealthMonitor()
```

### 3.3 Database Migration Considerations

```python
# backend/app/migrations/add_redis_tracking_tables.py
"""
Add tables for Redis fallback tracking and audit

These tables ensure we can track Redis usage and maintain
consistency when Redis is unavailable.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create redis_cache_audit table
    op.create_table(
        'redis_cache_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flow_id', sa.String(), nullable=False),
        sa.Column('cache_key', sa.String(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),  # GET, SET, INVALIDATE
        sa.Column('hit_miss', sa.String()),  # HIT, MISS, null for SET
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('latency_ms', sa.Float()),
        sa.Column('error', sa.Text()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(
        'idx_redis_cache_audit_flow_id',
        'redis_cache_audit',
        ['flow_id']
    )
    op.create_index(
        'idx_redis_cache_audit_timestamp',
        'redis_cache_audit',
        ['timestamp']
    )
    
    # Create redis_fallback_log table
    op.create_table(
        'redis_fallback_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service', sa.String(), nullable=False),  # Which service fell back
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),  # timeout, error, unavailable
        sa.Column('fallback_source', sa.String()),  # memory, database, etc
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('context', postgresql.JSONB()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for monitoring fallback frequency
    op.create_index(
        'idx_redis_fallback_timestamp',
        'redis_fallback_log',
        ['timestamp']
    )

def downgrade():
    op.drop_table('redis_fallback_log')
    op.drop_table('redis_cache_audit')
```

---

## 4. Code Architecture

### 4.1 Service Layer Organization

```
backend/app/services/
├── cache/
│   ├── __init__.py
│   ├── base_cache.py              # Abstract base for cache implementations
│   ├── flow_state_cache.py        # Flow state caching logic
│   ├── agent_result_cache.py      # Agent result caching
│   ├── cache_config.py            # Cache configuration and TTLs
│   └── redis_error_handler.py     # Error handling decorators
│
├── redis/
│   ├── __init__.py
│   ├── redis_event_bus.py         # Redis-backed event bus
│   ├── redis_connection_registry.py # SSE connection tracking
│   ├── redis_flow_orchestrator.py  # Flow orchestration with Redis
│   └── redis_flow_state_manager.py # State management with Redis
│
└── monitoring/
    ├── __init__.py
    ├── redis_monitor.py           # Basic Redis monitoring
    └── redis_health_monitor.py    # Comprehensive health checks
```

### 4.2 Modification Points for Existing Files

```python
# backend/app/core/config.py
# ADD: Redis configuration settings
REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")
REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
REDIS_SSL_REQUIRED: bool = Field(default=False, env="REDIS_SSL_REQUIRED")
REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")

# backend/app/main.py
# ADD: Redis initialization on startup
from app.core.redis_config import redis_manager
from app.monitoring.redis_health_monitor import redis_health_monitor

@app.on_event("startup")
async def startup_event():
    # Existing startup code...
    
    # Initialize Redis
    if settings.REDIS_ENABLED:
        redis_connected = await redis_manager.initialize()
        if redis_connected:
            logger.info("Redis initialized successfully")
            # Start monitoring
            await redis_health_monitor.start_monitoring()
        else:
            logger.warning("Redis initialization failed, using fallback mode")

@app.on_event("shutdown")
async def shutdown_event():
    # Existing shutdown code...
    
    # Close Redis connections
    await redis_manager.close()

# backend/app/services/crewai_flows/base_flow.py
# MODIFY: Add Redis caching to base flow
from app.services.cache.flow_state_cache import flow_state_cache
from app.services.cache.agent_result_cache import agent_result_cache

class BaseCrewAIFlow:
    # ADD: Cache integration methods
    async def _get_cached_state(self) -> Optional[Dict[str, Any]]:
        """Get flow state from cache"""
        return await flow_state_cache.get(self.flow_id)
    
    async def _cache_state(self, state: Dict[str, Any]):
        """Cache flow state"""
        await flow_state_cache.set(
            self.flow_id, 
            state, 
            status=state.get("status")
        )
    
    async def _execute_agent_with_cache(
        self, 
        agent_name: str,
        agent_callable: Callable,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent with result caching"""
        # Check cache first
        cached_result = await agent_result_cache.get_cached_result(
            agent_name, 
            inputs,
            context={"flow_id": self.flow_id}
        )
        
        if cached_result:
            logger.info(f"Using cached result for {agent_name}")
            return cached_result
        
        # Execute agent
        start_time = time.time()
        result = await agent_callable(inputs)
        execution_time = time.time() - start_time
        
        # Cache result
        await agent_result_cache.cache_agent_result(
            agent_name,
            inputs,
            result,
            context={"flow_id": self.flow_id},
            execution_time=execution_time
        )
        
        return result
```

### 4.3 Test File Organization

```
backend/tests/
├── unit/
│   ├── cache/
│   │   ├── test_flow_state_cache.py
│   │   ├── test_agent_result_cache.py
│   │   └── test_cache_fallback.py
│   │
│   └── redis/
│       ├── test_redis_event_bus.py
│       ├── test_redis_connection_registry.py
│       └── test_redis_orchestrator.py
│
├── integration/
│   ├── test_redis_integration.py
│   ├── test_flow_with_caching.py
│   └── test_sse_with_redis.py
│
└── performance/
    ├── test_cache_performance.py
    ├── test_concurrent_flows.py
    └── test_redis_load.py
```

---

## 5. Production Considerations

### 5.1 Upstash Redis Configuration

```python
# backend/app/core/upstash_config.py
from typing import Dict, Any
import os

class UpstashConfig:
    """Production configuration for Upstash Redis"""
    
    @staticmethod
    def get_connection_params() -> Dict[str, Any]:
        """Get Upstash-specific connection parameters"""
        
        # Parse Upstash URL
        upstash_url = os.getenv("UPSTASH_REDIS_URL", "")
        
        return {
            # Connection settings
            "url": upstash_url,
            "decode_responses": True,
            
            # SSL/TLS (required for Upstash)
            "ssl": True,
            "ssl_cert_reqs": "required",
            "ssl_check_hostname": True,
            
            # Connection pool
            "max_connections": 50,  # Upstash limit
            "socket_connect_timeout": 10,  # Higher for cross-region
            "socket_timeout": 10,
            
            # Retry configuration
            "retry_on_timeout": True,
            "retry_on_error": [ConnectionError, TimeoutError],
            
            # Health checking
            "health_check_interval": 60,  # Less frequent for production
            
            # Command encoding
            "encoding": "utf-8",
            "encoding_errors": "strict"
        }
    
    @staticmethod
    def get_limits() -> Dict[str, int]:
        """Get Upstash service limits"""
        
        plan = os.getenv("UPSTASH_PLAN", "free")
        
        limits = {
            "free": {
                "max_memory_mb": 256,
                "max_connections": 100,
                "max_commands_per_day": 10000,
                "max_bandwidth_mb_per_day": 100
            },
            "pay_as_you_go": {
                "max_memory_mb": 1024,
                "max_connections": 1000,
                "max_commands_per_day": 1000000,
                "max_bandwidth_mb_per_day": 10000
            }
        }
        
        return limits.get(plan, limits["free"])
    
    @staticmethod
    def get_optimizations() -> Dict[str, Any]:
        """Get Upstash-specific optimizations"""
        
        return {
            # Batch operations to reduce command count
            "batch_size": 100,
            "pipeline_commands": True,
            
            # Compression for large values
            "compress_threshold_bytes": 1024,  # Compress > 1KB
            
            # TTL strategy to manage memory
            "aggressive_ttl": True,
            "default_ttl_multiplier": 0.8,  # 80% of normal TTL
            
            # Connection reuse
            "connection_pool_recycle": 3600,  # Recycle every hour
            
            # Regional optimization
            "prefer_regional_endpoint": True
        }
```

### 5.2 Security Considerations

```python
# backend/app/security/redis_security.py
from typing import Optional, Dict, Any
import hmac
import hashlib
import json
from datetime import datetime

class RedisSecurityManager:
    """Security manager for Redis operations"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        
    def sign_data(self, data: Dict[str, Any]) -> str:
        """Sign data before storing in Redis"""
        # Add timestamp
        data_with_timestamp = {
            **data,
            "_timestamp": datetime.utcnow().isoformat()
        }
        
        # Create signature
        data_string = json.dumps(data_with_timestamp, sort_keys=True)
        signature = hmac.new(
            self.secret_key,
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return signed data
        return json.dumps({
            "data": data_with_timestamp,
            "signature": signature
        })
    
    def verify_data(self, signed_data: str) -> Optional[Dict[str, Any]]:
        """Verify and extract signed data from Redis"""
        try:
            parsed = json.loads(signed_data)
            data = parsed.get("data", {})
            signature = parsed.get("signature", "")
            
            # Recreate signature
            data_string = json.dumps(data, sort_keys=True)
            expected_signature = hmac.new(
                self.secret_key,
                data_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Verify signature
            if hmac.compare_digest(signature, expected_signature):
                # Remove internal timestamp
                data.pop("_timestamp", None)
                return data
            else:
                logger.warning("Invalid signature detected in Redis data")
                return None
                
        except Exception as e:
            logger.error(f"Failed to verify Redis data: {e}")
            return None
    
    def sanitize_key(self, key: str) -> str:
        """Sanitize Redis key to prevent injection"""
        # Remove potentially dangerous characters
        sanitized = key.replace(" ", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in "_-:")
        
        # Limit length
        return sanitized[:200]
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storing"""
        # This would use proper encryption library
        # Placeholder for demonstration
        from cryptography.fernet import Fernet
        
        # Generate key from secret
        key = hashlib.sha256(self.secret_key).digest()
        key_b64 = base64.urlsafe_b64encode(key)
        f = Fernet(key_b64)
        
        return f.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted: str) -> str:
        """Decrypt sensitive data from Redis"""
        from cryptography.fernet import Fernet
        
        key = hashlib.sha256(self.secret_key).digest()
        key_b64 = base64.urlsafe_b64encode(key)
        f = Fernet(key_b64)
        
        return f.decrypt(encrypted.encode()).decode()

# Usage in Redis operations
security_manager = RedisSecurityManager(settings.SECRET_KEY)

# Before storing sensitive data
async def store_sensitive_flow_data(flow_id: str, sensitive_data: Dict[str, Any]):
    # Sign and potentially encrypt
    signed_data = security_manager.sign_data(sensitive_data)
    
    # Sanitize key
    safe_key = security_manager.sanitize_key(f"sensitive:{flow_id}")
    
    # Store in Redis
    await redis_manager.redis.setex(
        safe_key,
        3600,  # 1 hour TTL
        signed_data
    )

# When retrieving
async def get_sensitive_flow_data(flow_id: str) -> Optional[Dict[str, Any]]:
    safe_key = security_manager.sanitize_key(f"sensitive:{flow_id}")
    signed_data = await redis_manager.redis.get(safe_key)
    
    if signed_data:
        return security_manager.verify_data(signed_data)
    return None
```

### 5.3 Backup and Recovery Procedures

```python
# backend/app/services/backup/redis_backup.py
from typing import Dict, List, Any
import asyncio
import json
from datetime import datetime
from app.core.redis_config import redis_manager
from app.db.session import AsyncSessionLocal

class RedisBackupService:
    """Backup and recovery for Redis data"""
    
    def __init__(self):
        self.backup_prefix = "backup:"
        self.critical_patterns = [
            "flow:events:*",
            "cache:flow:state:*",
            "orchestrator:*",
            "agent:results:*"
        ]
        
    async def backup_critical_data(self) -> Dict[str, Any]:
        """Backup critical Redis data to PostgreSQL"""
        backup_id = f"redis_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_data = {
            "backup_id": backup_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {}
        }
        
        if not redis_manager.is_available():
            return {"error": "Redis not available"}
        
        try:
            # Backup each critical pattern
            for pattern in self.critical_patterns:
                pattern_data = await self._backup_pattern(pattern)
                backup_data["data"][pattern] = pattern_data
            
            # Store in PostgreSQL
            async with AsyncSessionLocal() as db:
                backup_record = RedisBackup(
                    backup_id=backup_id,
                    backup_data=backup_data,
                    created_at=datetime.utcnow()
                )
                db.add(backup_record)
                await db.commit()
            
            logger.info(f"Redis backup completed: {backup_id}")
            return {
                "backup_id": backup_id,
                "patterns_backed_up": len(self.critical_patterns),
                "total_keys": sum(
                    len(data) for data in backup_data["data"].values()
                )
            }
            
        except Exception as e:
            logger.error(f"Redis backup failed: {e}")
            return {"error": str(e)}
    
    async def _backup_pattern(self, pattern: str) -> List[Dict[str, Any]]:
        """Backup all keys matching pattern"""
        backed_up_data = []
        cursor = 0
        
        while True:
            cursor, keys = await redis_manager.redis.scan(
                cursor,
                match=pattern,
                count=100
            )
            
            for key in keys:
                try:
                    # Get key type
                    key_type = await redis_manager.redis.type(key)
                    
                    # Get value based on type
                    if key_type == "string":
                        value = await redis_manager.redis.get(key)
                    elif key_type == "list":
                        value = await redis_manager.redis.lrange(key, 0, -1)
                    elif key_type == "set":
                        value = list(await redis_manager.redis.smembers(key))
                    elif key_type == "hash":
                        value = await redis_manager.redis.hgetall(key)
                    elif key_type == "stream":
                        # Get last 100 entries
                        value = await redis_manager.redis.xrevrange(key, count=100)
                    else:
                        value = None
                    
                    # Get TTL
                    ttl = await redis_manager.redis.ttl(key)
                    
                    backed_up_data.append({
                        "key": key,
                        "type": key_type,
                        "value": value,
                        "ttl": ttl if ttl > 0 else None
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to backup key {key}: {e}")
            
            if cursor == 0:
                break
        
        return backed_up_data
    
    async def restore_from_backup(
        self, 
        backup_id: str,
        patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Restore Redis data from backup"""
        try:
            # Get backup from PostgreSQL
            async with AsyncSessionLocal() as db:
                backup = await db.execute(
                    select(RedisBackup).where(
                        RedisBackup.backup_id == backup_id
                    )
                )
                backup_record = backup.scalar_one_or_none()
                
                if not backup_record:
                    return {"error": "Backup not found"}
            
            backup_data = backup_record.backup_data
            patterns_to_restore = patterns or list(backup_data["data"].keys())
            
            restored_count = 0
            
            for pattern in patterns_to_restore:
                if pattern in backup_data["data"]:
                    pattern_data = backup_data["data"][pattern]
                    
                    for item in pattern_data:
                        try:
                            await self._restore_key(item)
                            restored_count += 1
                        except Exception as e:
                            logger.error(
                                f"Failed to restore key {item['key']}: {e}"
                            )
            
            return {
                "backup_id": backup_id,
                "restored_patterns": len(patterns_to_restore),
                "restored_keys": restored_count
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"error": str(e)}
    
    async def _restore_key(self, key_data: Dict[str, Any]):
        """Restore individual key"""
        key = key_data["key"]
        key_type = key_data["type"]
        value = key_data["value"]
        ttl = key_data.get("ttl")
        
        # Restore based on type
        if key_type == "string":
            if ttl:
                await redis_manager.redis.setex(key, ttl, value)
            else:
                await redis_manager.redis.set(key, value)
                
        elif key_type == "list":
            await redis_manager.redis.delete(key)  # Clear existing
            if value:
                await redis_manager.redis.rpush(key, *value)
                
        elif key_type == "set":
            await redis_manager.redis.delete(key)
            if value:
                await redis_manager.redis.sadd(key, *value)
                
        elif key_type == "hash":
            await redis_manager.redis.delete(key)
            if value:
                await redis_manager.redis.hset(key, mapping=value)
                
        elif key_type == "stream":
            # Streams are append-only, just add entries
            for entry_id, fields in value:
                await redis_manager.redis.xadd(key, fields)
        
        # Set TTL if specified
        if ttl and ttl > 0 and key_type != "string":
            await redis_manager.redis.expire(key, ttl)

# Scheduled backup task
async def scheduled_redis_backup():
    """Run periodic Redis backups"""
    backup_service = RedisBackupService()
    
    while True:
        try:
            # Run backup
            result = await backup_service.backup_critical_data()
            
            if "error" not in result:
                logger.info(f"Scheduled backup completed: {result}")
            else:
                logger.error(f"Scheduled backup failed: {result}")
                
        except Exception as e:
            logger.error(f"Backup task error: {e}")
        
        # Wait for next backup interval (every 6 hours)
        await asyncio.sleep(21600)
```

---

## Summary

This technical addendum provides comprehensive implementation details for integrating Redis with the CrewAI-based AI Modernize Migration Platform. Key highlights include:

1. **CrewAI Integration**: Specific patterns for integrating Redis with the Master Flow Orchestrator, UnifiedDiscoveryFlow, and FlowStateManager

2. **Performance Optimization**: Detailed caching strategies, memory estimates, and connection pooling configurations optimized for Railway/Upstash deployment

3. **Technical Implementation**: Comprehensive error handling, monitoring, and database migration strategies

4. **Code Architecture**: Clear organization of new services and modification points for existing code

5. **Production Readiness**: Security considerations, backup procedures, and Upstash-specific optimizations

The implementation follows a phased approach with built-in fallback mechanisms, ensuring the system remains functional even if Redis is unavailable. All code examples are designed to integrate seamlessly with the existing CrewAI architecture while providing significant performance improvements for the Alpha release.