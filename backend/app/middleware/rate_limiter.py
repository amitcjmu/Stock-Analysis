"""
Rate Limiting Middleware
Implements rate limiting for API endpoints to prevent abuse.
"""

import logging
import time
from collections import defaultdict, deque
from typing import Dict, Optional

from fastapi import Request, status
# Secure logging functions not used in this file
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self):
        # Store request timestamps for each client
        self.requests: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        window_start = now - window_seconds

        # Get request queue for this client
        client_requests = self.requests[client_key]

        # Remove old requests outside the window
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) >= limit:
            return False

        # Add current request
        client_requests.append(now)
        return True

    def get_reset_time(self, client_key: str, window_seconds: int) -> int:
        """Get when the rate limit resets for a client."""
        client_requests = self.requests[client_key]
        if not client_requests:
            return 0

        # Reset time is when the oldest request expires
        return int(client_requests[0] + window_seconds)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to specific endpoints."""

    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

        # Define rate limits for different endpoint patterns
        self.rate_limits = {
            "/api/v1/auth/login": {"limit": 5, "window": 60},  # 5 requests per minute
            "/api/v1/auth/register": {
                "limit": 3,
                "window": 60,
            },  # 3 requests per minute
            "/api/v1/auth/password/change": {
                "limit": 3,
                "window": 300,
            },  # 3 requests per 5 minutes
            # Stricter limit for the write-intensive file upload endpoint
            "/api/v1/data-import/store-import": {
                "limit": 15,
                "window": 60,
            },  # 15 uploads per minute
            # More lenient general limit for other data import (mostly read) operations
            "/api/v1/data-import": {
                "limit": 60,
                "window": 60,
            },  # 60 requests per minute
            "default": {"limit": 100, "window": 60},  # Default: 100 requests per minute
        }

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to the request."""

        # Skip rate limiting for health checks and static files
        if self._should_skip_rate_limiting(request.url.path):
            return await call_next(request)

        # Get client identifier (IP address + user agent hash)
        client_key = self._get_client_key(request)

        # Get rate limit for this endpoint
        rate_limit = self._get_rate_limit(request.url.path)

        # Check if request is allowed
        if not self.rate_limiter.is_allowed(
            client_key, rate_limit["limit"], rate_limit["window"]
        ):
            # Rate limit exceeded
            reset_time = self.rate_limiter.get_reset_time(
                client_key, rate_limit["window"]
            )

            logger.warning(
                f"Rate limit exceeded for {client_key} on {request.url.path}",
                extra={
                    "client_key": client_key,
                    "path": request.url.path,
                    "method": request.method,
                    "limit": rate_limit["limit"],
                    "window": rate_limit["window"],
                },
            )

            return Response(
                content='{"error": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(rate_limit["limit"]),
                    "X-RateLimit-Window": str(rate_limit["window"]),
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limit["limit"])
        response.headers["X-RateLimit-Window"] = str(rate_limit["window"])

        return response

    def _should_skip_rate_limiting(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path."""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static/",
            "/debug/",
        ]

        return any(path.startswith(skip_path) for skip_path in skip_paths)

    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier."""
        # Use IP address as primary identifier
        client_ip = request.client.host if request.client else "unknown"

        # Add user agent hash for additional uniqueness
        user_agent = request.headers.get("user-agent", "")
        user_agent_hash = str(hash(user_agent))[:8]

        return f"{client_ip}:{user_agent_hash}"

    def _get_rate_limit(self, path: str) -> Dict[str, int]:
        """Get the most specific rate limit configuration for a path."""
        # Check for exact match first, as it's the most specific
        if path in self.rate_limits:
            return self.rate_limits[path]

        # Find all patterns that the path starts with
        matching_patterns = [
            pattern
            for pattern in self.rate_limits
            if pattern != "default" and path.startswith(pattern)
        ]

        # If there are matching patterns, find the most specific (longest) one
        if matching_patterns:
            most_specific_pattern = max(matching_patterns, key=len)
            return self.rate_limits[most_specific_pattern]

        # Return default limit if no other pattern matches
        return self.rate_limits["default"]


# Global rate limiter instance
global_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return global_rate_limiter
