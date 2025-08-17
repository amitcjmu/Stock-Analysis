"""
Cache Management Module for Storage Manager

This module provides caching functionality through modular components:
- cache_types: Enums and data classes for cache configuration
- cache_entry: Cache entry management and metadata
- cache_metrics: Performance monitoring and metrics collection
- cache_policies: Eviction policies and cache strategies
- multi_level_cache: Main multi-level cache implementation
"""

# Import main classes for backward compatibility
from .cache_types import CacheStrategy, CacheLevel
from .cache_entry import CacheEntry
from .cache_metrics import CachePerformanceMetrics
from .cache_policies import CacheEvictionPolicy
from .multi_level_cache import MultiLevelCache

__all__ = [
    "CacheStrategy",
    "CacheLevel",
    "CacheEntry",
    "CachePerformanceMetrics",
    "CacheEvictionPolicy",
    "MultiLevelCache",
]
