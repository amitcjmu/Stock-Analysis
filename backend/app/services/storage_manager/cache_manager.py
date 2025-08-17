"""
Storage Manager Cache Manager Module

Provides caching strategies, performance monitoring, and intelligent
cache management for storage operations. This module has been modularized
into the cache/ directory for better maintainability.

Backward compatibility wrapper for the original cache_manager.py
"""

# Import all classes from the modularized cache module
from .cache import (
    CacheEntry,
    CacheLevel,
    CachePerformanceMetrics,
    CacheStrategy,
    CacheEvictionPolicy,
    MultiLevelCache,
    create_multi_level_cache,
)

# Re-export for backward compatibility
__all__ = [
    "CacheStrategy",
    "CacheLevel",
    "CacheEntry",
    "CachePerformanceMetrics",
    "CacheEvictionPolicy",
    "MultiLevelCache",
    "create_multi_level_cache",
]
