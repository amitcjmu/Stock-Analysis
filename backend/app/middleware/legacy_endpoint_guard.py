"""
Legacy Endpoint Guard Middleware

BLOCKS all usage of legacy discovery endpoints to enforce MFO-first routing.

Behavior:
- ALL environments → return 410 Gone for /api/v1/discovery/*
- NO overrides allowed - legacy discovery endpoints are completely removed from codebase
- Use /api/v1/flows/* (MFO) or /api/v1/unified-discovery/* instead

This middleware is intentionally lightweight and early in the stack to prevent handler execution.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class LegacyEndpointGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # No environment or flag checks - always block legacy endpoints

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path or ""

        # Only guard HTTP requests; skip websockets and other ASGI types
        if request.scope.get("type") != "http" or not path.startswith(
            "/api/v1/discovery"
        ):
            return await call_next(request)

        # ALWAYS block legacy discovery endpoints - they are removed from codebase
        return JSONResponse(
            status_code=410,
            content={
                "error": "LEGACY_ENDPOINT_REMOVED",
                "detail": "All /api/v1/discovery/* endpoints have been permanently removed. "
                "Use /api/v1/flows/* (MFO) or /api/v1/unified-discovery/* instead.",
                "migration_paths": {
                    "/api/v1/discovery/flows/active": "/api/v1/flows/active",
                    "/api/v1/discovery/flows/{flow_id}/status": "/api/v1/flows/{flow_id}/status",
                    "/api/v1/discovery/flow/create": "/api/v1/flows/create",
                    "other": "Use /api/v1/unified-discovery/* for discovery-specific operations",
                },
            },
            headers={"X-Legacy-Endpoint-Blocked": "true"},
        )
