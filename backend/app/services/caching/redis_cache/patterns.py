"""
Pattern learning and mapping cache operations for Redis.

Handles caching of field mapping patterns with encryption.
"""

from typing import Any, Dict, Optional

from .utils import redis_fallback


class RedisPatternMixin:
    """Mixin for Redis pattern learning operations"""

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
