"""
Cache type definitions and enums for the storage manager cache system.
"""

from enum import Enum


class CacheStrategy(str, Enum):
    """Cache strategy types"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live based
    ADAPTIVE = "adaptive"  # Adaptive strategy based on usage patterns


class CacheLevel(str, Enum):
    """Cache hierarchy levels"""

    L1 = "l1"  # Fast in-memory cache
    L2 = "l2"  # Redis cache
    L3 = "l3"  # Database cache
    PERSISTENT = "persistent"  # Long-term storage
