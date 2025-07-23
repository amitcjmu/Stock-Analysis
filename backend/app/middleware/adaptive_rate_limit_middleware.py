"""
Adaptive Rate Limiting Middleware
Implements intelligent rate limiting that adapts to user behavior.
"""

import logging
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.middleware.adaptive_rate_limiter import (
    AdaptiveRateLimiter,
    get_adaptive_rate_limiter,
)
from app.services.auth_services.jwt_service import JWTService

logger = logging.getLogger(__name__)


class AdaptiveRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply adaptive rate limiting to API endpoints.
    """

    def __init__(self, app, rate_limiter: Optional[AdaptiveRateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_adaptive_rate_limiter()

        # Paths to skip rate limiting
        self.skip_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static/",
            "/debug/",
            "/api/v1/admin/rate-limit",  # Admin endpoints for rate limit management
        }

        # Special handling for certain paths
        self.auth_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/password/change",
            "/api/v1/auth/refresh",
        }

    async def dispatch(self, request: Request, call_next):
        """Apply adaptive rate limiting to the request."""

        # Skip rate limiting for exempt paths
        if self._should_skip_rate_limiting(request.url.path):
            return await call_next(request)

        # Extract client information
        client_key = self._get_client_key(request)
        endpoint = self._normalize_endpoint(request.url.path)

        # Build request metadata for adaptive decisions
        request_meta = await self._build_request_metadata(request)

        # Check rate limit
        is_allowed, rate_limit_info = self.rate_limiter.is_allowed(
            client_key=client_key, endpoint=endpoint, request_meta=request_meta
        )

        if not is_allowed:
            # Rate limit exceeded
            return self._build_rate_limit_response(rate_limit_info)

        # Process request
        try:
            response = await call_next(request)

            # Add rate limit headers to successful responses
            self._add_rate_limit_headers(response, rate_limit_info)

            return response

        except Exception as e:
            # Log but don't modify the error response
            logger.error(f"Error processing request: {str(e)}")
            raise

    def _should_skip_rate_limiting(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path."""
        return any(path.startswith(skip_path) for skip_path in self.skip_paths)

    def _get_client_key(self, request: Request) -> str:
        """
        Get unique client identifier.
        Uses a combination of IP, user agent, and authenticated user ID.
        """
        # Primary identifier: IP address
        client_ip = request.client.host if request.client else "unknown"

        # Add user agent hash for additional uniqueness
        user_agent = request.headers.get("user-agent", "")
        user_agent_hash = str(hash(user_agent))[:8]

        # For authenticated requests, include user ID
        auth_header = request.headers.get("authorization", "")
        user_id = None

        if auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                jwt_service = JWTService()
                payload = jwt_service.verify_token(token)
                user_id = payload.get("sub") if payload else None
            except Exception:
                # Invalid token, treat as anonymous
                pass

        if user_id:
            return f"user:{user_id}:{client_ip}"
        else:
            return f"anon:{client_ip}:{user_agent_hash}"

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for rate limiting.
        Removes path parameters to group similar endpoints.
        """
        # Remove trailing slashes
        path = path.rstrip("/")

        # Replace UUIDs and common ID patterns with placeholders
        import re

        # UUID pattern
        path = re.sub(
            r"/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
            "/{id}",
            path,
            flags=re.IGNORECASE,
        )

        # Numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        # Common patterns like 'flow_abc123'
        path = re.sub(r"/flow_[a-zA-Z0-9]+", "/flow_{id}", path)
        path = re.sub(r"/session_[a-zA-Z0-9]+", "/session_{id}", path)

        return path

    async def _build_request_metadata(self, request: Request) -> dict:
        """Build metadata about the request for adaptive decisions."""
        headers = dict(request.headers)

        # Extract user information from auth token
        user_id = None
        auth_header = headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                jwt_service = JWTService()
                payload = jwt_service.verify_token(token)
                user_id = payload.get("sub") if payload else None
            except Exception:
                pass

        # Detect testing/development environment
        host = headers.get("host", "").lower()
        origin = headers.get("origin", "").lower()
        user_agent = headers.get("user-agent", "").lower()
        referer = headers.get("referer", "").lower()

        # Check for test environment headers
        is_test_env = (
            headers.get("x-test-environment") == "true"
            or headers.get("x-automated-test") == "true"
            or "test" in host
            or "localhost" in host
            or "127.0.0.1" in host
        )

        return {
            "user_id": user_id,
            "host": host,
            "origin": origin,
            "user_agent": user_agent,
            "referer": referer,
            "is_authenticated": bool(user_id),
            "is_testing": is_test_env,
            "is_development": "localhost" in host or "127.0.0.1" in host,
            "method": request.method,
            "path": request.url.path,
        }

    def _build_rate_limit_response(self, rate_limit_info: dict) -> JSONResponse:
        """Build a 429 response with rate limit information."""
        retry_after = rate_limit_info.get("retry_after", 60)

        # Build informative error message
        error_detail = {
            "error": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": f"Too many requests. Please retry after {retry_after} seconds.",
            "rate_limit_info": {
                "limit": rate_limit_info.get("limit"),
                "remaining": rate_limit_info.get("remaining", 0),
                "reset": rate_limit_info.get("reset"),
                "retry_after": retry_after,
                "user_type": rate_limit_info.get("user_type", "unknown"),
            },
        }

        # Log detailed info for debugging
        logger.warning(
            "Rate limit exceeded",
            extra={
                **rate_limit_info,
                "adaptive_multiplier": rate_limit_info.get("adaptive_multiplier", 1.0),
                "endpoint_cost": rate_limit_info.get("endpoint_cost", 1),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_detail,
            headers={
                "X-RateLimit-Limit": str(rate_limit_info.get("limit", 0)),
                "X-RateLimit-Remaining": str(rate_limit_info.get("remaining", 0)),
                "X-RateLimit-Reset": str(rate_limit_info.get("reset", 0)),
                "Retry-After": str(retry_after),
                "X-RateLimit-UserType": rate_limit_info.get("user_type", "unknown"),
            },
        )

    def _add_rate_limit_headers(self, response: Response, rate_limit_info: dict):
        """Add rate limit headers to the response."""
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(
            rate_limit_info.get("remaining", 0)
        )
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info.get("reset", 0))
        response.headers["X-RateLimit-UserType"] = rate_limit_info.get(
            "user_type", "unknown"
        )

        # Add adaptive info in development mode
        if rate_limit_info.get("user_type") == "development":
            response.headers["X-RateLimit-Adaptive-Multiplier"] = str(
                rate_limit_info.get("adaptive_multiplier", 1.0)
            )
            response.headers["X-RateLimit-Endpoint-Cost"] = str(
                rate_limit_info.get("endpoint_cost", 1)
            )
