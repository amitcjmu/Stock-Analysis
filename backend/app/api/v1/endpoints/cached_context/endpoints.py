"""
Cached context API endpoints.
Handles cached context operations with Redis caching and ETag support.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.core.logging import get_logger
from app.models import User
from app.services.cache_invalidation import (
    CacheInvalidationService,
    get_cache_invalidation_service,
)
from app.services.caching.redis_cache import RedisCache, get_redis_cache
from app.utils.cache_utils import handle_conditional_request

from .service import CachedContextService

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/me",
    summary="Get cached user context",
    description="Get complete user context with Redis caching and ETag support",
    response_description="User context with cache metadata",
)
async def get_cached_user_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_cache: RedisCache = Depends(get_redis_cache),
    invalidation_service: CacheInvalidationService = Depends(
        get_cache_invalidation_service
    ),
) -> JSONResponse:
    """
    Get complete user context with Redis caching.

    This endpoint demonstrates:
    - Redis caching with proper tenant isolation
    - ETag generation for conditional requests
    - Cache metadata in response
    - Performance monitoring
    """
    try:
        # Extract tenant context from headers for security
        client_account_id = request.headers.get("X-Client-Account-ID")
        engagement_id = request.headers.get("X-Engagement-ID")

        # Create cached service
        service = CachedContextService(db, redis_cache, invalidation_service)

        # Get cached user context
        result = await service.get_user_context_cached(
            current_user, client_account_id, engagement_id
        )

        # Prepare response data
        response_data = {
            "user_context": result["data"],
            "cache_metadata": result["cache_metadata"],
        }

        # Determine cache control based on whether data was cached
        if result["cache_metadata"]["cached"]:
            cache_control = "private, max-age=300"  # 5 minutes for cached data
            cache_status = "HIT"
        else:
            cache_control = "private, max-age=3600"  # 1 hour for fresh data
            cache_status = "MISS"

        # Use cache utility for conditional request handling
        response, was_not_modified = handle_conditional_request(
            request=request,
            data=response_data,
            cache_control=cache_control,
            extra_headers={
                "X-Cache": cache_status,
                "Vary": "X-Client-Account-ID, X-Engagement-ID",
            },
        )

        # Add fetch time header if data wasn't cached
        if not result["cache_metadata"]["cached"] and not was_not_modified:
            response.headers["X-Fetch-Time"] = (
                f"{result['cache_metadata'].get('fetch_time_ms', 0):.2f}ms"
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cached user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user context: {str(e)}",
        )


@router.get(
    "/clients",
    summary="Get cached user clients",
    description="Get user's accessible clients with Redis caching",
)
async def get_cached_clients(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_cache: RedisCache = Depends(get_redis_cache),
    invalidation_service: CacheInvalidationService = Depends(
        get_cache_invalidation_service
    ),
) -> JSONResponse:
    """Get user's accessible clients with caching."""
    try:
        client_account_id = request.headers.get("X-Client-Account-ID")

        service = CachedContextService(db, redis_cache, invalidation_service)
        result = await service.get_clients_cached(current_user, client_account_id)

        response_data = {
            "clients": result["data"],
            "cache_metadata": result["cache_metadata"],
        }

        # Determine cache control
        cache_status = "HIT" if result["cache_metadata"]["cached"] else "MISS"
        cache_control = "private, max-age=1800"  # 30 minutes

        response, _ = handle_conditional_request(
            request=request,
            data=response_data,
            cache_control=cache_control,
            extra_headers={"X-Cache": cache_status},
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cached clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clients: {str(e)}",
        )


@router.get(
    "/engagements",
    summary="Get cached client engagements",
    description="Get client engagements with Redis caching",
)
async def get_cached_engagements(
    request: Request,
    client_account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_cache: RedisCache = Depends(get_redis_cache),
    invalidation_service: CacheInvalidationService = Depends(
        get_cache_invalidation_service
    ),
) -> JSONResponse:
    """Get client engagements with caching."""
    try:
        service = CachedContextService(db, redis_cache, invalidation_service)
        result = await service.get_engagements_cached(current_user, client_account_id)

        response_data = {
            "engagements": result["data"],
            "cache_metadata": result["cache_metadata"],
        }

        # Determine cache control
        cache_status = "HIT" if result["cache_metadata"]["cached"] else "MISS"
        cache_control = "private, max-age=900"  # 15 minutes

        response, _ = handle_conditional_request(
            request=request,
            data=response_data,
            cache_control=cache_control,
            extra_headers={"X-Cache": cache_status},
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cached engagements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching engagements: {str(e)}",
        )


@router.post(
    "/invalidate/{user_id}",
    summary="Invalidate user context cache",
    description="Clear all cached data for a specific user",
)
async def invalidate_user_context(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis_cache: RedisCache = Depends(get_redis_cache),
    invalidation_service: CacheInvalidationService = Depends(
        get_cache_invalidation_service
    ),
) -> Dict[str, Any]:
    """
    Invalidate all cached data for a specific user.

    This endpoint demonstrates cache invalidation patterns.
    """
    try:
        # Validate UUID format
        UUID(user_id)

        service = CachedContextService(db, redis_cache, invalidation_service)
        result = await service.invalidate_user_cache(user_id)

        return {
            **result,
            "invalidated_at": datetime.utcnow().isoformat(),
            "invalidated_by": current_user.email,
        }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error invalidating cache: {str(e)}",
        )


@router.get(
    "/stats",
    summary="Get cache statistics",
    description="Get Redis cache performance statistics",
)
async def get_cache_stats(
    redis_cache: RedisCache = Depends(get_redis_cache),
) -> Dict[str, Any]:
    """
    Get cache performance statistics.

    This endpoint demonstrates cache monitoring capabilities.
    """
    try:
        # Get Redis info
        redis_info = await redis_cache.get_info()

        # Calculate cache statistics
        stats = {
            "redis_info": {
                "used_memory_human": redis_info.get("used_memory_human", "unknown"),
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_commands_processed": redis_info.get(
                    "total_commands_processed", 0
                ),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0),
            },
            "cache_keys": {
                "user_contexts": await redis_cache.count_keys_pattern("user_context:*"),
                "user_clients": await redis_cache.count_keys_pattern("user_clients:*"),
                "client_engagements": await redis_cache.count_keys_pattern(
                    "client_engagements:*"
                ),
            },
            "performance": {
                "hit_rate": _calculate_hit_rate(
                    redis_info.get("keyspace_hits", 0),
                    redis_info.get("keyspace_misses", 0),
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        return stats

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching cache statistics: {str(e)}",
        )


def _calculate_hit_rate(hits: int, misses: int) -> float:
    """Calculate cache hit rate percentage."""
    total = hits + misses
    return (hits / total * 100) if total > 0 else 0.0
