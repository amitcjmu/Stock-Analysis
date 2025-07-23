"""
Admin endpoints for rate limit management and monitoring.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.auth.auth_utils import get_current_user
from app.middleware.adaptive_rate_limiter import get_adaptive_rate_limiter
from app.models.client_account import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require user to be a platform admin."""
    if current_user.role != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@router.get("/rate-limit/stats")
async def get_rate_limit_stats(
    client_key: Optional[str] = Query(None, description="Specific client key to query"),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Get rate limit statistics.

    If client_key is provided, returns stats for that specific client.
    Otherwise returns overall system stats.
    """
    rate_limiter = get_adaptive_rate_limiter()

    if client_key:
        # Get stats for specific client
        stats = rate_limiter.get_client_stats(client_key)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No stats found for client: {client_key}",
            )
        return {"client_key": client_key, "stats": stats}
    else:
        # Get overall system stats
        total_clients = len(rate_limiter.user_contexts)
        total_buckets = len(rate_limiter.buckets)

        # Sample some active clients
        sample_size = min(10, total_clients)
        sample_clients = list(rate_limiter.user_contexts.keys())[:sample_size]

        return {
            "total_clients": total_clients,
            "total_buckets": total_buckets,
            "configurations": rate_limiter.base_configs,
            "endpoint_costs": rate_limiter.endpoint_costs,
            "sample_clients": [
                {
                    "client_key": client_key,
                    "stats": rate_limiter.get_client_stats(client_key),
                }
                for client_key in sample_clients
            ],
        }


@router.post("/rate-limit/reset/{client_key}")
async def reset_client_rate_limit(
    client_key: str, current_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Reset rate limits for a specific client.
    Useful for testing or resolving issues.
    """
    rate_limiter = get_adaptive_rate_limiter()
    rate_limiter.reset_client(client_key)

    logger.info(
        f"Rate limits reset for client {client_key} by admin {current_user.email}"
    )

    return {
        "status": "success",
        "message": f"Rate limits reset for client: {client_key}",
    }


@router.post("/rate-limit/cleanup")
async def cleanup_inactive_clients(
    inactive_hours: int = Query(
        24, ge=1, le=168, description="Hours of inactivity before cleanup"
    ),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Clean up rate limit data for inactive clients.
    """
    rate_limiter = get_adaptive_rate_limiter()

    # Get count before cleanup
    before_count = len(rate_limiter.user_contexts)

    # Perform cleanup
    rate_limiter.cleanup_inactive(inactive_hours)

    # Get count after cleanup
    after_count = len(rate_limiter.user_contexts)
    cleaned_count = before_count - after_count

    logger.info(
        f"Cleaned up {cleaned_count} inactive clients by admin {current_user.email}"
    )

    return {
        "status": "success",
        "clients_before": before_count,
        "clients_after": after_count,
        "clients_cleaned": cleaned_count,
        "inactive_hours": inactive_hours,
    }


@router.put("/rate-limit/config")
async def update_rate_limit_config(
    user_type: str = Query(
        ..., description="User type: anonymous, authenticated, testing, development"
    ),
    capacity: Optional[int] = Query(None, ge=1, description="Token bucket capacity"),
    refill_rate: Optional[float] = Query(None, ge=0.1, description="Tokens per second"),
    burst_capacity: Optional[int] = Query(
        None, ge=0, description="Additional burst capacity"
    ),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Update rate limit configuration for a user type.
    Changes apply to new buckets only.
    """
    rate_limiter = get_adaptive_rate_limiter()

    if user_type not in rate_limiter.base_configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user type. Must be one of: {list(rate_limiter.base_configs.keys())}",
        )

    # Update configuration
    config = rate_limiter.base_configs[user_type]
    if capacity is not None:
        config["capacity"] = capacity
    if refill_rate is not None:
        config["refill_rate"] = refill_rate
    if burst_capacity is not None:
        config["burst_capacity"] = burst_capacity

    logger.info(
        f"Rate limit config updated for {user_type} by admin {current_user.email}",
        extra={"new_config": config},
    )

    return {
        "status": "success",
        "user_type": user_type,
        "config": config,
        "note": "Changes apply to new rate limit buckets only",
    }


@router.put("/rate-limit/endpoint-cost")
async def update_endpoint_cost(
    endpoint: str = Query(..., description="Endpoint path pattern"),
    cost: int = Query(..., ge=1, le=100, description="Token cost for the endpoint"),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Update the token cost for a specific endpoint.
    """
    rate_limiter = get_adaptive_rate_limiter()

    # Update endpoint cost
    rate_limiter.endpoint_costs[endpoint] = cost

    logger.info(
        f"Endpoint cost updated for {endpoint} to {cost} by admin {current_user.email}"
    )

    return {
        "status": "success",
        "endpoint": endpoint,
        "cost": cost,
        "all_costs": rate_limiter.endpoint_costs,
    }


@router.get("/rate-limit/test-detection")
async def test_detection_patterns(
    user_agent: Optional[str] = Query(None, description="User agent to test"),
    host: Optional[str] = Query(None, description="Host to test"),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Test if given headers would be detected as testing/development.
    """
    rate_limiter = get_adaptive_rate_limiter()

    request_meta = {
        "user_agent": user_agent or "",
        "host": host or "",
        "origin": host or "",
        "referer": "",
    }

    # Test against patterns
    is_testing = rate_limiter._is_testing_request(request_meta)
    is_development = rate_limiter._is_development_request(request_meta)

    return {
        "request_meta": request_meta,
        "detected_as_testing": is_testing,
        "detected_as_development": is_development,
        "testing_patterns": rate_limiter.testing_patterns,
        "dev_indicators": rate_limiter.dev_indicators,
    }
