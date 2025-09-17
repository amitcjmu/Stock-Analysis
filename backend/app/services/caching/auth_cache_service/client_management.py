"""
Client and engagement management for Authentication Cache Service

Handles caching of client lists, engagement data, and related organizational
structures for efficient access and reduced database load.
"""

from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.core.security.cache_encryption import sanitize_for_logging

from .base import CacheKeys, CacheTTL

logger = get_logger(__name__)


class ClientManagementMixin:
    """
    Mixin providing client and engagement caching functionality

    Handles:
    - User client list caching
    - Client engagement list caching
    - Data sanitization for security

    Requires:
    - self._get_from_cache()
    - self._set_to_cache()
    """

    # Client and Engagement Caching

    async def get_user_clients(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get user's client list from cache"""
        key = CacheKeys.USER_CLIENTS.format(user_id=user_id)
        return await self._get_from_cache(key, use_secure=False)

    async def set_user_clients(
        self, user_id: str, clients: List[Dict[str, Any]]
    ) -> bool:
        """Set user's client list in cache"""
        key = CacheKeys.USER_CLIENTS.format(user_id=user_id)

        # Sanitize sensitive data before caching
        sanitized_clients = []
        for client in clients:
            sanitized_client = sanitize_for_logging(client)
            sanitized_clients.append(sanitized_client)

        success = await self._set_to_cache(
            key, sanitized_clients, ttl=CacheTTL.CLIENT_LIST, use_secure=False
        )

        if success:
            logger.debug(f"Cached {len(clients)} clients for user {user_id}")

        return success

    async def get_client_engagements(
        self, client_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get client's engagement list from cache"""
        key = CacheKeys.CLIENT_ENGAGEMENTS.format(client_id=client_id)
        return await self._get_from_cache(key, use_secure=False)

    async def set_client_engagements(
        self, client_id: str, engagements: List[Dict[str, Any]]
    ) -> bool:
        """Set client's engagement list in cache"""
        key = CacheKeys.CLIENT_ENGAGEMENTS.format(client_id=client_id)

        success = await self._set_to_cache(
            key, engagements, ttl=CacheTTL.ENGAGEMENTS, use_secure=False
        )

        if success:
            logger.debug(
                f"Cached {len(engagements)} engagements for client {client_id}"
            )

        return success
