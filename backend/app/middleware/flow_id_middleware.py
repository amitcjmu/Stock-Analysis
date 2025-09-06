"""
Middleware to enforce Flow ID requirement for discovery endpoints.
Ensures all discovery operations have proper flow context to prevent data mismatches.
"""

import logging
from typing import List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class FlowIDRequirementMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces Flow ID requirement for discovery endpoints.

    This middleware ensures that all discovery-related API calls include
    a valid Flow ID in the headers to maintain proper data context and
    prevent cross-flow data pollution.
    """

    def __init__(self, app, exempt_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or []

        # Default exempt paths that don't require Flow ID
        self.default_exempt_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth",
            "/api/v1/context",
            "/api/v1/admin",
            "/api/v1/unified-discovery/flow/health",
            "/api/v1/unified-discovery/flow/status",
            "/api/v1/unified-discovery/flows",  # Flow listing
            "/api/v1/unified-discovery/overview",  # Unified discovery overview
            "/api/v1/unified-discovery/assets",  # Assets endpoint uses flow_id as query param
        ]

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and enforce Flow ID requirement for discovery endpoints.
        """
        path = request.url.path

        # Skip validation for non-discovery endpoints
        if not self._is_discovery_endpoint(path):
            return await call_next(request)

        # Check if path is exempt
        if self._is_exempt_path(path):
            return await call_next(request)

        # Check for Flow ID in headers
        flow_id = request.headers.get("X-Flow-ID") or request.headers.get("x-flow-id")

        if not flow_id:
            logger.warning(
                f"Discovery endpoint accessed without Flow ID: {path}",
                extra={
                    "path": path,
                    "method": request.method,
                    "client": request.client.host if request.client else None,
                },
            )

            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Flow ID required for discovery operations",
                    "code": "FLOW_ID_REQUIRED",
                    "message": (
                        "Discovery operations require an active discovery flow context. "
                        "Please ensure X-Flow-ID header is set."
                    ),
                    "endpoint": path,
                },
            )

        # Log successful validation (debug level to avoid log spam)
        logger.debug(
            "Discovery request validated with Flow ID",
            extra={
                "path": path,
                "flow_id": (
                    flow_id[:8] + "..." if len(flow_id) > 8 else flow_id
                ),  # Truncate for security
            },
        )

        # Continue with the request
        return await call_next(request)

    def _is_discovery_endpoint(self, path: str) -> bool:
        """
        Check if the path is a discovery-related endpoint.
        """
        discovery_prefixes = [
            "/api/v1/unified-discovery/",
            # Legacy discovery endpoints removed - use MFO or unified-discovery
        ]

        return any(path.startswith(prefix) for prefix in discovery_prefixes)

    def _is_exempt_path(self, path: str) -> bool:
        """
        Check if the path is exempt from Flow ID requirement.
        """
        # Check default exempt paths
        for exempt in self.default_exempt_paths:
            if path.startswith(exempt):
                return True

        # Check custom exempt paths
        for exempt in self.exempt_paths:
            if path.startswith(exempt):
                return True

        # Special cases - endpoints that create or manage flows
        if path in [
            "/api/v1/unified-discovery/flow",
        ] or path.endswith("/create"):
            return True

        return False
