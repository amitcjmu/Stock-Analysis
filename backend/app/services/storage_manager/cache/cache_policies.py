"""
Cache eviction policies and strategies.
"""

from datetime import timedelta
from typing import Dict, List

from .cache_entry import CacheEntry
from .cache_types import CacheStrategy


class CacheEvictionPolicy:
    """Cache eviction policy manager with multiple strategies"""

    def __init__(self, strategy: CacheStrategy = CacheStrategy.LRU):
        self.strategy = strategy

    def should_evict(self, entries: Dict[str, CacheEntry], max_size: int) -> List[str]:
        """Determine which keys should be evicted"""
        if len(entries) <= max_size:
            return []

        num_to_evict = len(entries) - max_size

        if self.strategy == CacheStrategy.LRU:
            return self._evict_lru(entries, num_to_evict)
        elif self.strategy == CacheStrategy.LFU:
            return self._evict_lfu(entries, num_to_evict)
        elif self.strategy == CacheStrategy.FIFO:
            return self._evict_fifo(entries, num_to_evict)
        elif self.strategy == CacheStrategy.TTL:
            return self._evict_ttl(entries, num_to_evict)
        elif self.strategy == CacheStrategy.ADAPTIVE:
            return self._evict_adaptive(entries, num_to_evict)
        else:
            return self._evict_lru(entries, num_to_evict)  # Default to LRU

    def _evict_lru(
        self, entries: Dict[str, CacheEntry], num_to_evict: int
    ) -> List[str]:
        """Evict least recently used entries"""
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].last_accessed)
        return [key for key, _ in sorted_entries[:num_to_evict]]

    def _evict_lfu(
        self, entries: Dict[str, CacheEntry], num_to_evict: int
    ) -> List[str]:
        """Evict least frequently used entries"""
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].access_count)
        return [key for key, _ in sorted_entries[:num_to_evict]]

    def _evict_fifo(
        self, entries: Dict[str, CacheEntry], num_to_evict: int
    ) -> List[str]:
        """Evict first in, first out entries"""
        sorted_entries = sorted(entries.items(), key=lambda x: x[1].created_at)
        return [key for key, _ in sorted_entries[:num_to_evict]]

    def _evict_ttl(
        self, entries: Dict[str, CacheEntry], num_to_evict: int
    ) -> List[str]:
        """Evict entries based on TTL (expired first, then closest to expiry)"""
        expired = [key for key, entry in entries.items() if entry.is_expired]

        if len(expired) >= num_to_evict:
            return expired[:num_to_evict]

        # If not enough expired entries, evict those closest to expiry
        non_expired = [
            (key, entry) for key, entry in entries.items() if not entry.is_expired
        ]
        sorted_by_expiry = sorted(
            non_expired,
            key=lambda x: x[1].created_at + timedelta(seconds=x[1].ttl_seconds),
        )

        remaining_to_evict = num_to_evict - len(expired)
        additional_evictions = [key for key, _ in sorted_by_expiry[:remaining_to_evict]]

        return expired + additional_evictions

    def _evict_adaptive(
        self, entries: Dict[str, CacheEntry], num_to_evict: int
    ) -> List[str]:
        """Adaptive eviction based on access patterns and age"""
        # First evict expired entries
        expired = [key for key, entry in entries.items() if entry.is_expired]

        if len(expired) >= num_to_evict:
            return expired[:num_to_evict]

        # Calculate eviction scores based on multiple factors
        scores = {}
        for key, entry in entries.items():
            if entry.is_expired:
                continue

            # Score based on: age, access frequency, and last access time
            age_score = entry.age_seconds / 3600  # Normalize to hours
            frequency_score = 1.0 / max(entry.access_count, 1)  # Lower is worse
            recency_score = entry.idle_seconds / 3600

            # Combined score (higher means more likely to evict)
            combined_score = age_score + frequency_score + recency_score
            scores[key] = combined_score

        # Sort by score and evict highest scoring entries
        sorted_by_score = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        remaining_to_evict = num_to_evict - len(expired)
        additional_evictions = [key for key, _ in sorted_by_score[:remaining_to_evict]]

        return expired + additional_evictions
