"""
RequestContext Header Enforcement Middleware

Per ADR-024 and Collection Flow design requirements, this middleware enforces
strict header-based authentication for collection endpoints.

IMPORTANT: This middleware ONLY applies to /api/v1/collection/* endpoints.
It requires X-Client-Account-ID, X-Engagement-ID, and X-User-ID headers.
Request body and query parameters are explicitly rejected.
"""

import logging
from typing import Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


class RequestContextEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce RequestContext headers for collection endpoints.

    Requirements (Per Design Doc Section 4 - API Contracts):
    - ✅ Require: X-Client-Account-ID, X-Engagement-ID, X-User-ID
    - ✅ Reject 400 Bad Request if headers missing
    - ✅ No body/query param fallback
    - ✅ Apply to all /api/v1/collection/* endpoints only
    """

    # Endpoints that require strict header enforcement
    ENFORCED_PREFIXES: Set[str] = {
        "/api/v1/collection/",
    }

    # Required headers (case-insensitive matching)
    REQUIRED_HEADERS = {
        "x-client-account-id": "Client Account ID",
        "x-engagement-id": "Engagement ID",
        "x-user-id": "User ID",
    }

    def __init__(self, app):
        super().__init__(app)
        logger.info(
            f"RequestContext enforcement enabled for: {', '.join(self.ENFORCED_PREFIXES)}"
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Check if request path requires header enforcement and validate headers.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from endpoint or 400 error if headers missing
        """
        # CORS preflight requests should always be exempt
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if this endpoint requires enforcement
        if not self._requires_enforcement(request.url.path):
            # Not a collection endpoint - skip enforcement
            return await call_next(request)

        # Validate required headers are present
        missing_headers = self._check_required_headers(request)

        if missing_headers:
            # Reject request with 400 Bad Request
            error_detail = (
                f"Missing required headers: {', '.join(missing_headers)}. "
                f"Collection endpoints require RequestContext headers ONLY. "
                f"Do NOT use request body or query parameters for tenant context."
            )

            logger.warning(
                safe_log_format(
                    "❌ Rejected collection request - Missing headers: {missing}",
                    missing=missing_headers,
                )
            )

            return JSONResponse(
                status_code=400,
                content={
                    "error": "Missing Required Headers",
                    "detail": error_detail,
                    "missing_headers": missing_headers,
                    "required_headers": list(self.REQUIRED_HEADERS.keys()),
                },
            )

        # Headers present - log and continue
        logger.debug(
            safe_log_format(
                "✅ Collection request validated - All required headers present"
            )
        )

        return await call_next(request)

    def _requires_enforcement(self, path: str) -> bool:
        """
        Check if the request path requires strict header enforcement.

        Args:
            path: Request URL path

        Returns:
            True if path matches enforced prefixes
        """
        return any(path.startswith(prefix) for prefix in self.ENFORCED_PREFIXES)

    def _check_required_headers(self, request: Request) -> list[str]:
        """
        Check which required headers are missing from the request.

        Uses case-insensitive header matching as per HTTP spec.

        Args:
            request: FastAPI request object

        Returns:
            List of missing header names (empty if all present)
        """
        missing = []

        # Convert headers to lowercase dict for case-insensitive lookup
        headers_lower = {k.lower(): v for k, v in request.headers.items()}

        for header_name, header_display_name in self.REQUIRED_HEADERS.items():
            if header_name not in headers_lower:
                missing.append(header_display_name)
            elif not headers_lower[header_name].strip():
                # Header present but empty
                missing.append(f"{header_display_name} (empty)")

        return missing


# Alias for backward compatibility
CollectionHeaderEnforcementMiddleware = RequestContextEnforcementMiddleware
