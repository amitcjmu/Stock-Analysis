"""
Multi-level cache implementation with hierarchical storage.
"""

import asyncio
import time
from collections import deque
from typing import Any, Dict, Optional

from app.core.logging import get_logger

from ..base import BaseStorageBackend
from .cache_entry import CacheEntry
from .cache_metrics import CachePerformanceMetrics
from .cache_policies import CacheEvictionPolicy
from .cache_types import CacheLevel, CacheStrategy

logger = get_logger(__name__)


class MultiLevelCache:
    """
    Multi-level cache manager with hierarchical storage.

    Implements a cache hierarchy with different levels (L1, L2, L3)
    each with different performance characteristics and capacity.
    """

    def __init__(
        self,
        l1_backend: Optional[BaseStorageBackend] = None,
        l2_backend: Optional[BaseStorageBackend] = None,
        l3_backend: Optional[BaseStorageBackend] = None,
        l1_max_size: int = 1000,
        l2_max_size: int = 10000,
        l3_max_size: int = 100000,
        eviction_strategy: CacheStrategy = CacheStrategy.LRU,
    ):
        self.backends = {
            CacheLevel.L1: l1_backend,
            CacheLevel.L2: l2_backend,
            CacheLevel.L3: l3_backend,
        }

        self.max_sizes = {
            CacheLevel.L1: l1_max_size,
            CacheLevel.L2: l2_max_size,
            CacheLevel.L3: l3_max_size,
        }

        self.eviction_policy = CacheEvictionPolicy(eviction_strategy)
        self.metrics = {level: CachePerformanceMetrics() for level in CacheLevel}

        # In-memory cache entries for tracking metadata
        self.cache_entries: Dict[CacheLevel, Dict[str, CacheEntry]] = {
            level: {} for level in CacheLevel
        }

        self._lock = asyncio.Lock()
        self._response_times = deque(maxlen=1000)  # Track recent response times

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache with basic implementation"""
        start_time = time.time()

        try:
            async with self._lock:
                # Try L1 cache first (in-memory)
                if key in self.cache_entries[CacheLevel.L1]:
                    entry = self.cache_entries[CacheLevel.L1][key]
                    if not entry.is_expired:
                        entry.touch()
                        self.metrics[CacheLevel.L1].hits += 1
                        return entry.value

                # Cache miss - simplified implementation
                self.metrics[CacheLevel.L1].misses += 1
                return None

        finally:
            response_time = (time.time() - start_time) * 1000
            self._response_times.append(response_time)

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in multi-level cache"""
        try:
            async with self._lock:
                entry = CacheEntry(key=key, value=value, ttl_seconds=ttl_seconds)

                # Store in L1 cache
                self.cache_entries[CacheLevel.L1][key] = entry

                # Check if eviction is needed
                if (
                    len(self.cache_entries[CacheLevel.L1])
                    > self.max_sizes[CacheLevel.L1]
                ):
                    keys_to_evict = self.eviction_policy.should_evict(
                        self.cache_entries[CacheLevel.L1], self.max_sizes[CacheLevel.L1]
                    )
                    for evict_key in keys_to_evict:
                        self.cache_entries[CacheLevel.L1].pop(evict_key, None)
                        self.metrics[CacheLevel.L1].evictions += 1

                return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from all cache levels"""
        try:
            async with self._lock:
                found = False
                for level in CacheLevel:
                    if key in self.cache_entries[level]:
                        del self.cache_entries[level][key]
                        found = True
                return found
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear(self, level: Optional[CacheLevel] = None):
        """Clear cache entries"""
        async with self._lock:
            if level:
                self.cache_entries[level].clear()
            else:
                for lvl in CacheLevel:
                    self.cache_entries[lvl].clear()

    def get_metrics(self, level: Optional[CacheLevel] = None) -> Dict:
        """Get cache performance metrics"""
        if level:
            return {
                "level": level.value,
                "metrics": self.metrics[level],
                "size": len(self.cache_entries[level]),
                "max_size": self.max_sizes[level],
            }
        else:
            return {
                lvl.value: {
                    "metrics": self.metrics[lvl],
                    "size": len(self.cache_entries[lvl]),
                    "max_size": self.max_sizes[lvl],
                }
                for lvl in CacheLevel
            }
