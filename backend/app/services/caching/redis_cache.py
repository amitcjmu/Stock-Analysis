"""
Redis Cache Service with Upstash and Local Redis Support

This service provides a unified interface for Redis caching with support for:
- Upstash Redis (for production)
- redis.asyncio (for local async Redis)
- Synchronous Redis fallback (wrapped in async)
- In-memory fallback when Redis is unavailable
"""

import asyncio
import json
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security.cache_encryption import SecureCache

logger = get_logger(__name__)


def redis_fallback(func):
    """Decorator to handle Redis failures gracefully"""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.enabled or self.client is None:
            logger.debug(f"Redis disabled or unavailable, skipping {func.__name__}")
            return _get_fallback_result(func.__name__)

        try:
            return await func(self, *args, **kwargs)
        except (ConnectionError, TimeoutError) as e:
            # Network-related errors - likely Redis is down
            logger.warning(f"Redis connection error in {func.__name__}: {str(e)}")
            return _get_fallback_result(func.__name__)
        except (json.JSONDecodeError, ValueError) as e:
            # Data format errors - log but don't fail
            logger.error(f"Redis data error in {func.__name__}: {str(e)}")
            return _get_fallback_result(func.__name__)
        except Exception as e:
            # Unexpected errors - log with full details
            logger.error(
                f"Unexpected Redis error in {func.__name__}: {type(e).__name__}: {str(e)}"
            )
            return _get_fallback_result(func.__name__)

    return wrapper


def _get_fallback_result(operation_name: str):
    """Get appropriate fallback value for a given operation"""
    # Read operations return None
    if operation_name in [
        "get",
        "get_flow_state",
        "get_import_sample",
        "get_mapping_pattern",
        "acquire_lock",
    ]:
        return None
    # Existence checks return False
    elif operation_name in ["exists"]:
        return False
    # IMPORTANT: When Redis is unavailable, allow flow registration to succeed
    # This prevents "flow already exists" errors when Redis is not configured
    elif operation_name in ["register_flow_atomic"]:
        logger.warning(
            "Redis unavailable - allowing flow registration without deduplication check"
        )
        return True
    # Write operations that should "succeed" silently
    elif operation_name in ["set", "delete", "release_lock", "unregister_flow_atomic"]:
        return True
    # List operations return empty list
    elif operation_name in ["get_active_flows", "get_sse_clients"]:
        return []
    # Default to False for unknown operations
    else:
        logger.warning(f"No fallback defined for operation: {operation_name}")
        return False


class RedisCache:
    """Unified Redis cache service with multiple backend support"""

    def __init__(self):
        self.enabled = settings.REDIS_ENABLED
        self.client = None
        self.client_type = None
        self.default_ttl = settings.REDIS_DEFAULT_TTL

        if not self.enabled:
            logger.info("Redis cache is disabled")
            return

        # Try to initialize Redis client
        self._initialize_client()
        # Initialize secure cache wrapper for sensitive data
        self.secure_cache = SecureCache(self)

    def _initialize_client(self):
        """Initialize the appropriate Redis client based on configuration"""
        # Try Upstash Redis first (for production)
        if hasattr(settings, "UPSTASH_REDIS_URL") and settings.UPSTASH_REDIS_URL:
            try:
                from upstash_redis import Redis as UpstashRedis

                self.client = UpstashRedis(
                    url=settings.UPSTASH_REDIS_URL, token=settings.UPSTASH_REDIS_TOKEN
                )
                self.client_type = "upstash"
                logger.info("Connected to Upstash Redis")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to Upstash Redis: {e}")

        # Try async Redis (for local development)
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            try:
                import redis.asyncio as redis_async

                self.client = redis_async.from_url(
                    settings.REDIS_URL, decode_responses=True
                )
                self.client_type = "async"
                logger.info("Connected to async Redis")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to async Redis: {e}")

        # Fallback to sync Redis wrapped in async
        if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
            try:
                import redis

                sync_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self.client = AsyncRedisWrapper(sync_client)
                self.client_type = "sync_wrapped"
                logger.info("Connected to Redis (sync client wrapped)")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to sync Redis: {e}")

        # If all fail, disable Redis
        logger.warning("No Redis connection available, caching disabled")
        self.enabled = False

    @redis_fallback
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.client_type == "upstash":
                value = self.client.get(key)
            else:
                value = await self.client.get(key)

            if value:
                return json.loads(value) if isinstance(value, str) else value
            return None
        except json.JSONDecodeError:
            # Return raw value if not JSON
            return value
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {str(e)}")
            return None

    @redis_fallback
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized = (
                json.dumps(value, default=str) if not isinstance(value, str) else value
            )

            if self.client_type == "upstash":
                # Upstash uses setex with different parameter order
                self.client.setex(key, ttl, serialized)
            elif hasattr(self.client, "setex"):
                # Standard Redis clients
                await self.client.setex(key, ttl, serialized)
            else:
                # Use set with ex parameter
                await self.client.set(key, serialized, ex=ttl)

            return True
        except Exception as e:
            # Sanitize error logging to prevent sensitive data exposure
            logger.error(
                f"Redis set error for key {key}: {str(e)} (value type: {type(value).__name__})"
            )
            return False

    async def set_secure(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        force_encrypt: bool = False,
    ) -> bool:
        """Set value in cache with automatic encryption for sensitive data"""
        return await self.secure_cache.set(key, value, ttl, force_encrypt)

    async def get_secure(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic decryption"""
        return await self.secure_cache.get(key)

    @redis_fallback
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.client_type == "upstash":
                self.client.delete(key)
            else:
                await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {str(e)}")
            return False

    @redis_fallback
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if self.client_type == "upstash":
                return bool(self.client.exists(key))
            else:
                result = await self.client.exists(key)
                return bool(result)
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {str(e)}")
            return False

    @redis_fallback
    async def acquire_lock(self, resource: str, ttl: int = 30) -> Optional[str]:
        """Acquire distributed lock with atomic operation"""
        key = f"lock:{resource}"
        lock_id = str(uuid.uuid4())

        try:
            if self.client_type == "upstash":
                # Upstash doesn't support SET NX directly, use atomic get-set pattern
                # Use SETNX equivalent with Upstash
                result = self.client.set(key, lock_id, nx=True, ex=ttl)
                return lock_id if result else None
            else:
                # Standard Redis with SET NX
                result = await self.client.set(key, lock_id, nx=True, ex=ttl)
                return lock_id if result else None
        except AttributeError:
            # Fallback for clients without nx parameter
            # This is NOT atomic and has race condition, but better than nothing
            try:
                exists = await self.exists(key)
                if not exists:
                    success = await self.set(key, lock_id, ttl)
                    return lock_id if success else None
                return None
            except Exception as e:
                logger.error(f"Redis lock fallback error: {str(e)}")
                return None

    @redis_fallback
    async def release_lock(self, resource: str, lock_id: str) -> bool:
        """Release distributed lock if we own it"""
        key = f"lock:{resource}"

        try:
            # Check if we own the lock
            current_lock = await self.get(key)
            if current_lock == lock_id:
                return await self.delete(key)
            return False
        except Exception as e:
            logger.error(f"Redis release lock error: {str(e)}")
            return False

    # Flow State Caching
    @redis_fallback
    async def cache_flow_state(
        self, flow_id: str, state: Dict[str, Any], ttl: int = 3600
    ) -> bool:
        """Cache flow state with encryption for sensitive data"""
        key = f"flow:state:{flow_id}"
        # Flow state contains sensitive data like client_account_id, user_id, etc.
        return await self.set_secure(key, state, ttl, force_encrypt=True)

    @redis_fallback
    async def invalidate_flow_cache(self, flow_id: str) -> bool:
        """Invalidate all cached data related to a flow"""
        try:
            keys_to_delete = [
                f"flow:state:{flow_id}",
                f"flow:exists:{flow_id}",
                f"flow:metadata:{flow_id}",
                f"flow:phase:*:{flow_id}",  # Phase results
                f"flow:agent:*:{flow_id}",  # Agent results
                f"lock:flow:{flow_id}",  # Flow locks
                f"lock:flow:status:{flow_id}",  # Status locks
            ]

            if self.client_type == "upstash":
                # Upstash doesn't support pattern deletion, delete known keys
                for key in keys_to_delete:
                    if "*" not in key:
                        self.client.delete(key)
            else:
                # For Redis with SCAN support, find and delete pattern keys
                pipeline = self.client.pipeline()

                for key_pattern in keys_to_delete:
                    if "*" in key_pattern:
                        # Use SCAN to find matching keys
                        cursor = "0"
                        while True:
                            cursor, keys = await self.client.scan(
                                cursor=cursor, match=key_pattern, count=100
                            )
                            for key in keys:
                                pipeline.delete(key)
                            if cursor == "0":
                                break
                    else:
                        pipeline.delete(key_pattern)

                await pipeline.execute()

            logger.info(f"Invalidated all cache entries for flow {flow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate flow cache: {str(e)}")
            return False

    @redis_fallback
    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state from cache with decryption"""
        key = f"flow:state:{flow_id}"
        return await self.get_secure(key)

    # Import Sample Caching
    @redis_fallback
    async def cache_import_sample(
        self, import_id: str, sample_data: List[Dict[str, Any]], ttl: int = 3600
    ) -> bool:
        """Cache import sample with encryption for sensitive data"""
        key = f"import:sample:{import_id}"
        # Import samples may contain PII and sensitive business data
        return await self.set_secure(key, sample_data, ttl, force_encrypt=True)

    @redis_fallback
    async def get_import_sample(self, import_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get import sample from cache with decryption"""
        key = f"import:sample:{import_id}"
        return await self.get_secure(key)

    # Failure Journal / DLQ helpers
    @redis_fallback
    async def enqueue_failure(
        self, payload: Dict[str, Any], *, ttl: int = 7 * 24 * 3600
    ) -> bool:
        """Enqueue a failure payload to Redis for retry processing.
        Stores payload under fj:payload:{id} and pushes id to fj:queue:{client}:{engagement}.
        """
        try:
            failure_id = payload.get("id") or str(uuid.uuid4())
            payload["id"] = failure_id
            client = payload.get("client_account_id") or "-"
            engagement = payload.get("engagement_id") or "-"
            queue_key = f"fj:queue:{client}:{engagement}"
            payload_key = f"fj:payload:{failure_id}"

            # Sanitize and persist payload (best-effort redaction)
            try:
                redacted_keys = {
                    "password",
                    "token",
                    "api_key",
                    "authorization",
                    "secret",
                    "bearer",
                }
                sanitized = {}
                for k, v in (payload or {}).items():
                    lk = str(k).lower()
                    sanitized[k] = (
                        "***REDACTED***" if any(x in lk for x in redacted_keys) else v
                    )
                payload = sanitized
            except Exception:
                pass
            await self.set(payload_key, payload, ttl)

            # Push to queue (RPUSH to preserve FIFO)
            if self.client_type == "upstash":
                result = self.client.rpush(queue_key, failure_id)
                if hasattr(result, "__await__"):
                    await result
            else:
                await self.client.rpush(queue_key, failure_id)
            return True
        except Exception as e:
            logger.error(f"Redis enqueue_failure error: {e}")
            return False

    @redis_fallback
    async def schedule_retry(
        self,
        failure_id: str,
        when_epoch: int,
        *,
        client: str = "-",
        engagement: str = "-",
    ) -> bool:
        """Schedule a retry by adding the failure id to a sorted set with score=when."""
        try:
            zkey = f"fj:retry:{client}:{engagement}"
            if self.client_type == "upstash":
                result = self.client.zadd(zkey, {failure_id: when_epoch})
                if hasattr(result, "__await__"):
                    await result
            else:
                await self.client.zadd(zkey, {failure_id: when_epoch})
            return True
        except Exception as e:
            logger.error(f"Redis schedule_retry error: {e}")
            return False

    @redis_fallback
    async def claim_due(
        self, client: str, engagement: str, now_epoch: int, batch: int = 50
    ) -> List[str]:
        """Claim due retries (IDs) from sorted set fj:retry, removing them atomically."""
        try:
            zkey = f"fj:retry:{client}:{engagement}"
            ids: List[str] = []
            if self.client_type == "upstash":
                # Attempt to reduce race window using a pipeline (if supported)
                try:
                    pipe = getattr(self.client, "pipeline", None)
                    if callable(pipe):
                        p = pipe()
                        p.zrangebyscore(zkey, "-inf", now_epoch, count=batch)
                        res = p.execute() if hasattr(p, "execute") else (await p.exec())  # type: ignore
                        res = await res if hasattr(res, "__await__") else res
                        ids = (res or [])[0] if isinstance(res, list) else (res or [])
                        ids = ids or []
                        if ids:
                            rem = self.client.zrem(zkey, *ids)
                            if hasattr(rem, "__await__"):
                                await rem
                    else:
                        raw = self.client.zrangebyscore(
                            zkey, "-inf", now_epoch, count=batch
                        )
                        ids = await raw if hasattr(raw, "__await__") else raw
                        ids = ids or []
                        if ids:
                            rem = self.client.zrem(zkey, *ids)
                            if hasattr(rem, "__await__"):
                                await rem
                except Exception:
                    ids = []
            else:
                # Atomic fetch-and-remove via Lua script
                script = (
                    "local key = KEYS[1] "
                    "local max = ARGV[1] "
                    "local cnt = tonumber(ARGV[2]) "
                    "local ids = redis.call('ZRANGEBYSCORE', key, '-inf', max, 'LIMIT', 0, cnt) "
                    "if #ids > 0 then redis.call('ZREM', key, unpack(ids)) end "
                    "return ids"
                )
                try:
                    eval_res = await self.client.eval(script, 1, zkey, now_epoch, batch)
                    ids = list(eval_res or [])
                except Exception:
                    # Fallback to non-atomic sequence if eval unsupported
                    ids = await self.client.zrangebyscore(
                        zkey, "-inf", now_epoch, start=0, num=batch
                    )
                    ids = ids or []
                    if ids:
                        await self.client.zrem(zkey, *ids)
            return ids or []
        except Exception as e:
            logger.error(f"Redis claim_due error: {e}")
            return []

    @redis_fallback
    async def ack_failure(
        self, failure_id: str, *, client: str = "-", engagement: str = "-"
    ) -> bool:
        """Acknowledge a processed failure: remove payload and any queue occurrences."""
        try:
            payload_key = f"fj:payload:{failure_id}"
            await self.delete(payload_key)
            # Best-effort removal from queue if present
            qkey = f"fj:queue:{client}:{engagement}"
            if self.client_type == "upstash":
                # Best-effort LREM equivalent isn't available; tolerate no-op
                return True
            else:
                await self.client.lrem(qkey, 0, failure_id)
                return True
        except Exception as e:
            logger.error(f"Redis ack_failure error: {e}")
            return False

    # Pattern Learning Cache
    @redis_fallback
    async def cache_mapping_pattern(
        self, pattern_key: str, pattern: Dict[str, Any], ttl: int = 86400  # 24 hours
    ) -> bool:
        """Cache field mapping pattern with encryption"""
        key = f"pattern:mapping:{pattern_key}"
        # Mapping patterns contain client-specific field names and structure
        return await self.set_secure(key, pattern, ttl, force_encrypt=True)

    @redis_fallback
    async def get_mapping_pattern(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """Get field mapping pattern from cache with decryption"""
        key = f"pattern:mapping:{pattern_key}"
        return await self.get_secure(key)

    # Atomic Flow Registration Operations
    @redis_fallback
    async def register_flow_atomic(
        self,
        flow_id: str,
        flow_type: str,
        flow_data: Dict[str, Any],
        ttl: int = 86400,  # 24 hours
    ) -> bool:
        """
        Atomically register a new flow with all necessary keys.
        This prevents race conditions during flow creation.
        """
        try:
            # Use pipeline for atomic operations where supported
            if self.client_type == "upstash":
                # Upstash doesn't support pipelines, use individual operations
                # But still maintain order and check for conflicts

                # Check if flow already exists (prevent duplicate registration)
                exists_key = f"flow:exists:{flow_id}"
                if self.client.get(exists_key):
                    logger.warning(f"Flow {flow_id} already registered")
                    return False

                # Set all flow-related keys
                success = True

                # 1. Mark flow as existing
                self.client.setex(exists_key, ttl, "1")

                # 2. Store flow metadata
                metadata_key = f"flow:metadata:{flow_id}"
                self.client.setex(
                    metadata_key,
                    ttl,
                    json.dumps(
                        {
                            "flow_type": flow_type,
                            "created_at": datetime.utcnow().isoformat(),
                            "client_id": flow_data.get("client_id"),
                            "engagement_id": flow_data.get("engagement_id"),
                            "user_id": flow_data.get("user_id"),
                        }
                    ),
                )

                # 3. Initialize flow state
                state_key = f"flow:state:{flow_id}"
                self.client.setex(state_key, ttl, json.dumps(flow_data))

                # 4. Add to active flows set
                active_key = f"flows:active:{flow_type}"
                # Upstash doesn't have SADD with TTL, use regular key
                active_flows = self.client.get(active_key)
                if active_flows:
                    active_list = json.loads(active_flows)
                    if flow_id not in active_list:
                        active_list.append(flow_id)
                else:
                    active_list = [flow_id]
                self.client.setex(active_key, ttl, json.dumps(active_list))

                return success

            else:
                # Use pipeline for Redis implementations that support it
                pipeline = self.client.pipeline()

                # Check if flow already exists
                exists_key = f"flow:exists:{flow_id}"
                exists = await self.client.get(exists_key)
                if exists:
                    logger.warning(f"Flow {flow_id} already registered")
                    return False

                # Set all flow-related keys atomically
                pipeline.setex(exists_key, ttl, "1")

                metadata_key = f"flow:metadata:{flow_id}"
                pipeline.setex(
                    metadata_key,
                    ttl,
                    json.dumps(
                        {
                            "flow_type": flow_type,
                            "created_at": datetime.utcnow().isoformat(),
                            "client_id": flow_data.get("client_id"),
                            "engagement_id": flow_data.get("engagement_id"),
                            "user_id": flow_data.get("user_id"),
                        }
                    ),
                )

                state_key = f"flow:state:{flow_id}"
                pipeline.setex(state_key, ttl, json.dumps(flow_data))

                # Add to active flows set
                active_key = f"flows:active:{flow_type}"
                pipeline.sadd(active_key, flow_id)
                pipeline.expire(active_key, ttl)

                # Execute pipeline atomically
                results = await pipeline.execute()
                return all(results)

        except Exception as e:
            logger.error(f"Failed to register flow atomically: {str(e)}")
            return False

    @redis_fallback
    async def unregister_flow_atomic(self, flow_id: str, flow_type: str) -> bool:
        """
        Atomically unregister a flow and clean up all related keys.
        """
        try:
            if self.client_type == "upstash":
                # Manual cleanup for Upstash
                self.client.delete(f"flow:exists:{flow_id}")
                self.client.delete(f"flow:metadata:{flow_id}")
                self.client.delete(f"flow:state:{flow_id}")
                self.client.delete(f"lock:flow:{flow_id}")

                # Remove from active flows
                active_key = f"flows:active:{flow_type}"
                active_flows = self.client.get(active_key)
                if active_flows:
                    active_list = json.loads(active_flows)
                    if flow_id in active_list:
                        active_list.remove(flow_id)
                        self.client.set(active_key, json.dumps(active_list))

                return True

            else:
                # Use pipeline for atomic cleanup
                pipeline = self.client.pipeline()

                pipeline.delete(f"flow:exists:{flow_id}")
                pipeline.delete(f"flow:metadata:{flow_id}")
                pipeline.delete(f"flow:state:{flow_id}")
                pipeline.delete(f"lock:flow:{flow_id}")

                # Remove from active flows set
                active_key = f"flows:active:{flow_type}"
                pipeline.srem(active_key, flow_id)

                results = await pipeline.execute()
                return any(results)  # At least one key was deleted

        except Exception as e:
            logger.error(f"Failed to unregister flow atomically: {str(e)}")
            return False

    @redis_fallback
    async def get_active_flows(self, flow_type: str) -> List[str]:
        """Get list of active flows for a given type"""
        try:
            active_key = f"flows:active:{flow_type}"

            if self.client_type == "upstash":
                # Upstash uses JSON list
                active_flows = self.client.get(active_key)
                return json.loads(active_flows) if active_flows else []
            else:
                # Redis uses SET
                members = await self.client.smembers(active_key)
                return list(members) if members else []

        except Exception as e:
            logger.error(f"Failed to get active flows: {str(e)}")
            return []

    # SSE Registry (Note: Upstash doesn't support pub/sub)
    async def register_sse_client(self, client_id: str, flow_id: str) -> bool:
        """Register SSE client (uses regular key-value, not pub/sub)"""
        if self.client_type == "upstash":
            # Upstash doesn't support pub/sub, use key-value instead
            key = f"sse:client:{client_id}"
            return await self.set(
                key,
                {"flow_id": flow_id, "connected_at": datetime.utcnow().isoformat()},
                ttl=3600,
            )
        else:
            # For Redis with pub/sub support
            try:
                # Store client info
                key = f"sse:client:{client_id}"
                await self.set(
                    key,
                    {"flow_id": flow_id, "connected_at": datetime.utcnow().isoformat()},
                    ttl=3600,
                )

                # Publish connection event
                if hasattr(self.client, "publish"):
                    await self.client.publish(
                        f"sse:flow:{flow_id}",
                        json.dumps(
                            {"event": "client_connected", "client_id": client_id}
                        ),
                    )
                return True
            except Exception as e:
                logger.error(f"Failed to register SSE client: {e}")
                return False

    @redis_fallback
    async def unregister_sse_client(self, client_id: str) -> bool:
        """Unregister SSE client"""
        key = f"sse:client:{client_id}"
        return await self.delete(key)

    @redis_fallback
    async def get_sse_clients(self, flow_id: str) -> List[str]:
        """Get all SSE clients for a flow (scan-based for Upstash compatibility)"""
        clients = []
        pattern = "sse:client:*"

        try:
            if self.client_type == "upstash":
                # Upstash doesn't support SCAN, need to track clients differently
                # This is a limitation - would need to maintain a separate set of client IDs
                logger.warning("SSE client listing not fully supported with Upstash")
                return []
            else:
                # Use SCAN for other Redis implementations
                cursor = "0"
                while cursor != 0:
                    cursor, keys = await self.client.scan(
                        cursor=cursor, match=pattern, count=100
                    )
                    for key in keys:
                        client_data = await self.get(
                            key.decode() if isinstance(key, bytes) else key
                        )
                        if client_data and client_data.get("flow_id") == flow_id:
                            client_id = key.split(":")[-1]
                            clients.append(client_id)
                    if cursor == "0":
                        break
                return clients
        except Exception as e:
            logger.error(f"Failed to get SSE clients: {e}")
            return []


class AsyncRedisWrapper:
    """
    Wrapper to make synchronous Redis client async-compatible.

    Uses asyncio.to_thread to run blocking operations in a thread pool,
    preventing them from blocking the event loop.
    """

    def __init__(self, sync_client):
        self.sync_client = sync_client
        # Log warning about potential performance impact
        logger.warning(
            "Using synchronous Redis client in async mode. "
            "Consider installing redis[asyncio] for better performance."
        )

    async def get(self, key: str):
        """Async wrapper for sync get"""
        return await asyncio.to_thread(self.sync_client.get, key)

    async def set(
        self, key: str, value: str, ex: Optional[int] = None, nx: bool = False
    ):
        """Async wrapper for sync set"""
        return await asyncio.to_thread(self.sync_client.set, key, value, ex=ex, nx=nx)

    async def setex(self, key: str, ttl: int, value: str):
        """Async wrapper for sync setex"""
        return await asyncio.to_thread(self.sync_client.setex, key, ttl, value)

    async def delete(self, key: str):
        """Async wrapper for sync delete"""
        return await asyncio.to_thread(self.sync_client.delete, key)

    async def exists(self, key: str):
        """Async wrapper for sync exists"""
        return await asyncio.to_thread(self.sync_client.exists, key)

    async def scan(self, cursor=0, match=None, count=100):
        """Async wrapper for sync scan"""
        return await asyncio.to_thread(
            self.sync_client.scan, cursor, match=match, count=count
        )

    async def publish(self, channel: str, message: str):
        """Async wrapper for sync publish"""
        return await asyncio.to_thread(self.sync_client.publish, channel, message)

    def pipeline(self):
        """Create a pipeline for atomic operations"""
        return AsyncPipelineWrapper(self.sync_client.pipeline())

    async def smembers(self, key: str):
        """Async wrapper for sync smembers"""
        return await asyncio.to_thread(self.sync_client.smembers, key)

    async def sadd(self, key: str, *values):
        """Async wrapper for sync sadd"""
        return await asyncio.to_thread(self.sync_client.sadd, key, *values)

    async def srem(self, key: str, *values):
        """Async wrapper for sync srem"""
        return await asyncio.to_thread(self.sync_client.srem, key, *values)

    async def expire(self, key: str, ttl: int):
        """Async wrapper for sync expire"""
        return await asyncio.to_thread(self.sync_client.expire, key, ttl)


class AsyncPipelineWrapper:
    """Wrapper to make synchronous Redis pipeline async-compatible"""

    def __init__(self, sync_pipeline):
        self.sync_pipeline = sync_pipeline

    def setex(self, key: str, ttl: int, value: str):
        """Add setex command to pipeline"""
        self.sync_pipeline.setex(key, ttl, value)
        return self

    def delete(self, key: str):
        """Add delete command to pipeline"""
        self.sync_pipeline.delete(key)
        return self

    def sadd(self, key: str, *values):
        """Add sadd command to pipeline"""
        self.sync_pipeline.sadd(key, *values)
        return self

    def srem(self, key: str, *values):
        """Add srem command to pipeline"""
        self.sync_pipeline.srem(key, *values)
        return self

    def expire(self, key: str, ttl: int):
        """Add expire command to pipeline"""
        self.sync_pipeline.expire(key, ttl)
        return self

    async def execute(self):
        """Execute pipeline asynchronously"""
        return await asyncio.to_thread(self.sync_pipeline.execute)


# Singleton instance
_redis_cache_instance = None


def get_redis_cache() -> RedisCache:
    """Get singleton Redis cache instance"""
    global _redis_cache_instance
    if _redis_cache_instance is None:
        _redis_cache_instance = RedisCache()
    return _redis_cache_instance


# Global instance for easy importing
redis_cache = get_redis_cache()
