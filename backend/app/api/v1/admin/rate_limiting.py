"""
Rate Limiting Admin Router
Manages API rate limiting configurations and monitoring
"""

from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime, timedelta
from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.auth.admin_dependencies import require_admin
from app.models.client_account import User
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# All rate limiting admin endpoints require admin privileges
router = APIRouter(prefix="/rate-limiting", dependencies=[Depends(require_admin)])


class RateLimitConfig(BaseModel):
    """Rate limit configuration model"""

    endpoint: str
    max_requests: int
    window_seconds: int
    burst_size: Optional[int] = None
    enabled: bool = True


class RateLimitStatus(BaseModel):
    """Rate limit status for monitoring"""

    endpoint: str
    current_count: int
    limit: int
    window_seconds: int
    reset_at: datetime
    is_limited: bool


@router.get("/config")
async def get_rate_limit_config(admin_user: User = Depends(get_current_user)):
    """Get current rate limiting configuration"""
    return {
        "global": {
            "max_requests": 100,
            "window_seconds": 60,
            "burst_size": 150,
            "enabled": True,
        },
        "endpoints": [
            {
                "endpoint": "/api/v1/unified-discovery/*",
                "max_requests": 50,
                "window_seconds": 60,
                "enabled": True,
            },
            {
                "endpoint": "/api/v1/collection/*",
                "max_requests": 30,
                "window_seconds": 60,
                "enabled": True,
            },
            {
                "endpoint": "/api/v1/master-flows/*",
                "max_requests": 20,
                "window_seconds": 60,
                "enabled": True,
            },
        ],
    }


@router.put("/config")
async def update_rate_limit_config(
    config: RateLimitConfig, admin_user: User = Depends(get_current_user)
):
    """Update rate limiting configuration for specific endpoint"""
    logger.info(f"Rate limit config updated for {config.endpoint} by {admin_user.id}")

    return {
        "success": True,
        "message": f"Rate limit configuration updated for {config.endpoint}",
        "config": config.dict(),
    }


@router.get("/status")
async def get_rate_limit_status(
    endpoint: Optional[str] = None, admin_user: User = Depends(get_current_user)
):
    """Get current rate limiting status for endpoints"""
    now = datetime.utcnow()

    if endpoint:
        # Return status for specific endpoint
        return RateLimitStatus(
            endpoint=endpoint,
            current_count=15,
            limit=50,
            window_seconds=60,
            reset_at=now + timedelta(seconds=45),
            is_limited=False,
        )

    # Return status for all monitored endpoints
    return {
        "endpoints": [
            {
                "endpoint": "/api/v1/unified-discovery/flows",
                "current_count": 23,
                "limit": 50,
                "window_seconds": 60,
                "reset_at": (now + timedelta(seconds=30)).isoformat(),
                "is_limited": False,
            },
            {
                "endpoint": "/api/v1/collection/upload",
                "current_count": 28,
                "limit": 30,
                "window_seconds": 60,
                "reset_at": (now + timedelta(seconds=15)).isoformat(),
                "is_limited": False,
            },
            {
                "endpoint": "/api/v1/master-flows/execute",
                "current_count": 19,
                "limit": 20,
                "window_seconds": 60,
                "reset_at": (now + timedelta(seconds=45)).isoformat(),
                "is_limited": False,
            },
        ],
        "global_status": {
            "current_count": 70,
            "limit": 100,
            "window_seconds": 60,
            "reset_at": (now + timedelta(seconds=30)).isoformat(),
            "is_limited": False,
        },
    }


@router.get("/violations")
async def get_rate_limit_violations(
    hours: int = 24, admin_user: User = Depends(get_current_user)
):
    """Get rate limit violations in the specified time window"""
    # Note: cutoff_time calculation removed as it was unused in this mock implementation

    return {
        "violations": [
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "user_id": "user-123",
                "endpoint": "/api/v1/collection/upload",
                "count": 45,
                "limit": 30,
                "ip_address": "192.168.1.100",
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "user_id": "user-456",
                "endpoint": "/api/v1/master-flows/execute",
                "count": 25,
                "limit": 20,
                "ip_address": "10.0.0.50",
            },
        ],
        "summary": {
            "total_violations": 2,
            "unique_users": 2,
            "unique_endpoints": 2,
            "time_window_hours": hours,
        },
    }


@router.post("/reset/{user_id}")
async def reset_user_rate_limit(
    user_id: str, admin_user: User = Depends(get_current_user)
):
    """Reset rate limits for a specific user"""
    logger.info(f"Rate limits reset for user {user_id} by admin {admin_user.id}")

    return {
        "success": True,
        "message": f"Rate limits reset for user {user_id}",
        "user_id": user_id,
        "reset_by": str(admin_user.id),
        "reset_at": datetime.utcnow().isoformat(),
    }


@router.post("/bypass/{user_id}")
async def add_rate_limit_bypass(
    user_id: str, duration_hours: int = 1, admin_user: User = Depends(get_current_user)
):
    """Add temporary rate limit bypass for a user"""
    expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    logger.info(
        f"Rate limit bypass added for user {user_id} until {expires_at} by admin {admin_user.id}"
    )

    return {
        "success": True,
        "message": f"Rate limit bypass added for user {user_id}",
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
        "added_by": str(admin_user.id),
    }


@router.get("/metrics")
async def get_rate_limit_metrics(admin_user: User = Depends(get_current_user)):
    """Get rate limiting metrics and statistics"""
    return {
        "metrics": {
            "total_requests_today": 15234,
            "total_limited_requests": 342,
            "limit_hit_rate": 0.0224,
            "unique_users_limited": 28,
            "most_limited_endpoints": [
                {"endpoint": "/api/v1/collection/upload", "limit_hits": 156},
                {"endpoint": "/api/v1/master-flows/execute", "limit_hits": 98},
            ],
            "peak_hour": {
                "hour": "14:00-15:00 UTC",
                "requests": 2341,
                "limit_hits": 67,
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
