"""
Cached context service implementation.
Provides caching capabilities for context-related operations.
"""

import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.context.services.client_service import ClientService
from app.api.v1.endpoints.context.services.engagement_service import EngagementService
from app.api.v1.endpoints.context.services.user_service import UserService
from app.constants.cache_keys import CacheKeys
from app.core.logging import get_logger
from app.models import User
from app.services.cache_invalidation import CacheInvalidationService
from app.services.caching.redis_cache import RedisCache

logger = get_logger(__name__)


class CachedContextService:
    """
    Service that wraps existing context services with caching capabilities.

    This service demonstrates how to integrate Redis caching with existing
    business logic while maintaining proper cache invalidation.
    """

    def __init__(
        self,
        db: AsyncSession,
        redis_cache: RedisCache,
        invalidation_service: CacheInvalidationService,
    ):
        self.db = db
        self.redis = redis_cache
        self.invalidation = invalidation_service

        # Wrap existing services
        self.user_service = UserService(db)
        self.client_service = ClientService(db)
        self.engagement_service = EngagementService(db)

    async def get_user_context_cached(
        self,
        user: User,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get user context with Redis caching.

        Args:
            user: Current user
            client_account_id: Client account for tenant isolation
            engagement_id: Optional engagement context

        Returns:
            User context dictionary with cache metadata
        """
        try:
            # Generate cache key with tenant isolation
            cache_key = CacheKeys.user_context(str(user.id))

            # Add tenant context to cache key for security
            if client_account_id:
                cache_key = f"{cache_key}:client:{client_account_id}"
            if engagement_id:
                cache_key = f"{cache_key}:engagement:{engagement_id}"

            logger.debug(f"Getting user context with cache key: {cache_key}")

            # Try to get from cache first
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.debug(f"Cache HIT for user context: {user.id}")

                # Add cache metadata
                return {
                    "data": cached_data,
                    "cache_metadata": {
                        "cached": True,
                        "cache_key": cache_key,
                        "retrieved_at": datetime.utcnow().isoformat(),
                    },
                }

            # Cache miss - get fresh data
            logger.debug(f"Cache MISS for user context: {user.id}")
            start_time = time.time()

            # Get fresh user context from existing service
            user_context = await self.user_service.get_user_context_with_flows(user)

            # Convert to dictionary for caching
            context_dict = _serialize_user_context(user_context)

            # Cache the data with appropriate TTL (1 hour for user context)
            ttl = 3600
            await self.redis.set(cache_key, context_dict, ttl)

            fetch_time_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Cached user context for {user.id} (fetch: {fetch_time_ms:.2f}ms)"
            )

            return {
                "data": context_dict,
                "cache_metadata": {
                    "cached": False,
                    "cache_key": cache_key,
                    "fetch_time_ms": fetch_time_ms,
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl_seconds": ttl,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get cached user context: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user context: {str(e)}",
            )

    async def get_clients_cached(
        self, user: User, client_account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user's accessible clients with caching."""
        try:
            cache_key = CacheKeys.user_clients(str(user.id))

            # Try cache first
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return {
                    "data": cached_data,
                    "cache_metadata": {"cached": True, "cache_key": cache_key},
                }

            # Cache miss - get fresh data
            start_time = time.time()
            clients = await self.client_service.get_user_clients(user)

            # Serialize clients data
            clients_data = [
                {
                    "id": str(client.id),
                    "name": client.name,
                    "created_at": (
                        client.created_at.isoformat() if client.created_at else None
                    ),
                }
                for client in clients
            ]

            # Cache for 30 minutes
            ttl = 1800
            await self.redis.set(cache_key, clients_data, ttl)

            fetch_time_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Cached clients for user {user.id} (fetch: {fetch_time_ms:.2f}ms)"
            )

            return {
                "data": clients_data,
                "cache_metadata": {
                    "cached": False,
                    "cache_key": cache_key,
                    "fetch_time_ms": fetch_time_ms,
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl_seconds": ttl,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get cached clients: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching clients: {str(e)}",
            )

    async def get_engagements_cached(
        self, user: User, client_account_id: str
    ) -> Dict[str, Any]:
        """Get client engagements with caching."""
        try:
            cache_key = CacheKeys.client_engagements(client_account_id)

            # Try cache first
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return {
                    "data": cached_data,
                    "cache_metadata": {"cached": True, "cache_key": cache_key},
                }

            # Cache miss - get fresh data
            start_time = time.time()
            engagements = await self.engagement_service.get_client_engagements(
                client_account_id
            )

            # Serialize engagements data
            engagements_data = [
                {
                    "id": str(engagement.id),
                    "name": engagement.name,
                    "client_id": str(engagement.client_id),
                    "created_at": (
                        engagement.created_at.isoformat()
                        if engagement.created_at
                        else None
                    ),
                }
                for engagement in engagements
            ]

            # Cache for 15 minutes
            ttl = 900
            await self.redis.set(cache_key, engagements_data, ttl)

            fetch_time_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Cached engagements for client {client_account_id} (fetch: {fetch_time_ms:.2f}ms)"
            )

            return {
                "data": engagements_data,
                "cache_metadata": {
                    "cached": False,
                    "cache_key": cache_key,
                    "fetch_time_ms": fetch_time_ms,
                    "cached_at": datetime.utcnow().isoformat(),
                    "ttl_seconds": ttl,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get cached engagements: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching engagements: {str(e)}",
            )

    async def invalidate_user_cache(self, user_id: str) -> Dict[str, Any]:
        """Invalidate all cache entries for a user."""
        try:
            patterns = [
                CacheKeys.user_context(user_id),
                CacheKeys.user_clients(user_id),
            ]

            invalidated_keys = []
            for pattern in patterns:
                keys = await self.redis.get_keys_pattern(f"{pattern}*")
                for key in keys:
                    await self.redis.delete(key)
                    invalidated_keys.append(key)

            return {
                "invalidated_keys": invalidated_keys,
                "invalidated_count": len(invalidated_keys),
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error invalidating cache: {str(e)}",
            )


def _serialize_user_context(user_context) -> Dict[str, Any]:
    """Convert user context object to dictionary for caching."""
    return {
        "user": {
            "id": str(user_context.user.id),
            "email": user_context.user.email,
            "username": user_context.user.username,
            "role": user_context.user.role,
            "is_active": user_context.user.is_active,
            "created_at": (
                user_context.user.created_at.isoformat()
                if user_context.user.created_at
                else None
            ),
        },
        "client": (
            {
                "id": str(user_context.client.id),
                "name": user_context.client.name,
                "created_at": (
                    user_context.client.created_at.isoformat()
                    if user_context.client.created_at
                    else None
                ),
            }
            if user_context.client
            else None
        ),
        "engagement": (
            {
                "id": str(user_context.engagement.id),
                "name": user_context.engagement.name,
                "client_id": str(user_context.engagement.client_id),
                "created_at": (
                    user_context.engagement.created_at.isoformat()
                    if user_context.engagement.created_at
                    else None
                ),
            }
            if user_context.engagement
            else None
        ),
        "session": (
            {
                "id": str(user_context.session.id),
                "engagement_id": (
                    str(user_context.session.engagement_id)
                    if user_context.session.engagement_id
                    else None
                ),
                "created_at": (
                    user_context.session.created_at.isoformat()
                    if user_context.session.created_at
                    else None
                ),
            }
            if user_context.session
            else None
        ),
        "active_flows": [
            {
                "id": str(flow.id),
                "name": flow.name,
                "flow_type": flow.flow_type,
                "status": flow.status,
                "engagement_id": (
                    str(flow.engagement_id) if flow.engagement_id else None
                ),
                "created_by": flow.created_by,
                "metadata": flow.metadata or {},
            }
            for flow in (user_context.active_flows or [])
        ],
        "primary_flow_id": (
            str(user_context.primary_flow_id) if user_context.primary_flow_id else None
        ),
    }
