"""
Security Headers Middleware
Adds security headers to all HTTP responses.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response, request)

        return response

    def _add_security_headers(self, response: Response, request: Request):
        """Add comprehensive security headers."""

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent page from being embedded in frames (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy header, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HTTP Strict Transport Security (HSTS)
        # Only add if using HTTPS
        if request.url.scheme == "https" or settings.ENVIRONMENT == "production":
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (CSP)
        csp_policy = self._build_csp_policy(request)
        response.headers["Content-Security-Policy"] = csp_policy

        # Permissions Policy (Feature Policy)
        response.headers[
            "Permissions-Policy"
        ] = "geolocation=(), microphone=(), camera=()"

        # Server identification
        response.headers["Server"] = "AI-Force-Migration-Platform"

        # Remove potentially sensitive headers (using del instead of pop for MutableHeaders)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        logger.debug(f"Added security headers to response for {request.url.path}")

    def _build_csp_policy(self, request: Request) -> str:
        """Build Content Security Policy based on environment."""

        # Base CSP policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles for UI components
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests",
        ]

        # Development environment adjustments
        env = getattr(settings, "ENVIRONMENT", "development").lower()
        is_dev = env in ["development", "dev", "local", "localhost"] or env not in [
            "production",
            "prod",
        ]

        if is_dev:
            # Allow localhost connections for development
            csp_directives = [
                (
                    directive.replace(
                        "'self'",
                        "'self' localhost:* 127.0.0.1:* http://localhost:* http://127.0.0.1:*",
                    )
                    if "connect-src" in directive or "default-src" in directive
                    else directive
                )
                for directive in csp_directives
            ]

            # Allow unsafe-eval for development tools
            csp_directives = [
                (
                    directive.replace(
                        "script-src 'self'",
                        "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
                    )
                    if "script-src" in directive
                    else directive
                )
                for directive in csp_directives
            ]

        # API endpoints don't need strict CSP
        if request.url.path.startswith("/api/"):
            # Very permissive CSP for API endpoints
            if is_dev:
                csp_directives = [
                    "default-src *",
                    "script-src *",
                    "style-src *",
                    "img-src *",
                    "font-src *",
                    "connect-src *",
                    "frame-ancestors *",
                ]
            else:
                csp_directives = [
                    "default-src 'self'",
                    "connect-src 'self'",
                    "frame-ancestors 'none'",
                ]

        return "; ".join(csp_directives)


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log security-related events."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Log security events and suspicious activity."""

        # Check for suspicious patterns
        self._check_suspicious_patterns(request)

        # Process request
        response = await call_next(request)

        # Log security events
        self._log_security_events(request, response)

        return response

    def _check_suspicious_patterns(self, request: Request):
        """Check for suspicious request patterns."""

        suspicious_patterns = [
            # SQL injection patterns
            "union select",
            "drop table",
            "insert into",
            "delete from",
            # XSS patterns
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            # Path traversal
            "../",
            "..\\",
            "%2e%2e",
            # Command injection
            "|",
            "&",
            ";",
            "`",
            "$(",
        ]

        # Check URL path
        path_lower = request.url.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                logger.warning(
                    f"Suspicious pattern detected in URL: {pattern}",
                    extra={
                        "client_ip": (
                            request.client.host if request.client else "unknown"
                        ),
                        "path": request.url.path,
                        "pattern": pattern,
                        "user_agent": request.headers.get("user-agent", ""),
                    },
                )

        # Check query parameters
        if request.url.query:
            query_lower = request.url.query.lower()
            for pattern in suspicious_patterns:
                if pattern in query_lower:
                    logger.warning(
                        f"Suspicious pattern detected in query: {pattern}",
                        extra={
                            "client_ip": (
                                request.client.host if request.client else "unknown"
                            ),
                            "query": request.url.query,
                            "pattern": pattern,
                            "user_agent": request.headers.get("user-agent", ""),
                        },
                    )

    def _log_security_events(self, request: Request, response: Response):
        """Log security-related events."""

        # Log authentication failures
        if response.status_code == 401:
            logger.info(
                "Authentication failure",
                extra={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", ""),
                },
            )

        # Log authorization failures
        elif response.status_code == 403:
            logger.info(
                "Authorization failure",
                extra={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", ""),
                },
            )

        # Log rate limiting
        elif response.status_code == 429:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", ""),
                },
            )
