"""
Async wrapper classes for synchronous Redis clients.

Provides async compatibility for sync Redis operations using asyncio.to_thread.
"""

import asyncio
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


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
