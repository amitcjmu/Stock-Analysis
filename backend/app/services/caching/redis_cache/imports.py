"""
Import sample caching operations for Redis.

Handles caching of import data samples with encryption for sensitive data.
"""

from typing import Any, Dict, List, Optional

from .utils import redis_fallback


class RedisImportMixin:
    """Mixin for Redis import-related operations"""

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
