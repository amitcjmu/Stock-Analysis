"""
Legacy Endpoint Guard Middleware

Blocks or warns on usage of legacy discovery endpoints to enforce MFO-first routing.

Behavior:
- Production (ENVIRONMENT=production) → return 410 Gone for /api/v1/discovery/* unless explicitly allowed.
- Non-production → allow by default but add X-Legacy-Endpoint-Used header and log a warning.
- Feature flag override: LEGACY_ENDPOINTS_ALLOW=1 allows passthrough in all environments (use sparingly).

This middleware is intentionally lightweight and early in the stack to prevent handler execution.
"""

import os
from app.core.env_flags import is_truthy_env

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class LegacyEndpointGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.allow_flag = is_truthy_env("LEGACY_ENDPOINTS_ALLOW", default=False)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path or ""

        # Only guard HTTP requests; skip websockets and other ASGI types
        if request.scope.get("type") != "http" or not path.startswith(
            "/api/v1/discovery"
        ):
            return await call_next(request)

        # Always annotate so downstream proxies/clients can detect legacy use
        def annotate(resp: Response) -> Response:
            resp.headers["X-Legacy-Endpoint-Used"] = "true"
            return resp

        # Allow override via feature flag
        if self.allow_flag:
            response = await call_next(request)
            return annotate(response)

        # Production: block with 410 Gone
        if self.environment == "production":
            return annotate(
                JSONResponse(
                    status_code=410,
                    content={
                        "detail": "Legacy discovery endpoints are deprecated. Use /api/v1/flows instead.",
                        "replacement": "/api/v1/flows",
                    },
                )
            )

        # Non-production: warn but allow
        response = await call_next(request)
        return annotate(response)
