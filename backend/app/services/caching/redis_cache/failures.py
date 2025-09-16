"""
Failure handling and dead letter queue operations for Redis.

Provides failure journaling, retry scheduling, and acknowledgment capabilities.
"""

import uuid
from typing import Any, Dict, List

from app.core.logging import get_logger

from .utils import redis_fallback

logger = get_logger(__name__)


class RedisFailureMixin:
    """Mixin for Redis failure handling operations"""

    @redis_fallback
    async def enqueue_failure(
        self, payload: Dict[str, Any], *, ttl: int = 7 * 24 * 3600
    ) -> bool:
        """Enqueue a failure payload to Redis for retry processing.
        Stores payload under fj:payload:{id} and pushes id to fj:queue:{client}:{engagement}.
        """

        # Sanitize and persist payload (best-effort redaction, recursive)
        def _sanitize(obj):
            redacted_keys = {
                "password",
                "token",
                "api_key",
                "authorization",
                "secret",
                "bearer",
            }
            if isinstance(obj, dict):
                out = {}
                for k, v in obj.items():
                    lk = str(k).lower()
                    if any(x in lk for x in redacted_keys):
                        out[k] = "***REDACTED***"
                    else:
                        out[k] = _sanitize(v)
                return out
            elif isinstance(obj, list):
                return [_sanitize(i) for i in obj]
            else:
                return obj

        try:
            failure_id = payload.get("id") or str(uuid.uuid4())
            payload["id"] = failure_id
            client = payload.get("client_account_id") or "-"
            engagement = payload.get("engagement_id") or "-"
            queue_key = f"fj:queue:{client}:{engagement}"
            payload_key = f"fj:payload:{failure_id}"
            payload = _sanitize(payload or {})
        except Exception:
            pass
        # Ensure JSON-serializable when storing and then push to queue
        try:
            await self.set(payload_key, payload, ttl)
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
