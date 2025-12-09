"""
Main context middleware for automatic multi-tenant context injection.
Extracts tenant context from request headers and makes it available via context variables.
"""

import logging
import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..security.secure_logging import safe_log_format
from .admin_access import handle_admin_access, is_admin_endpoint

logger = logging.getLogger(__name__)


class ContextMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware with comprehensive security audit logging.
    Tracks all admin access, security violations, and suspicious activity.
    """

    def __init__(
        self,
        app: Callable,
        require_client: bool = True,
        require_engagement: bool = False,
        exempt_paths: Optional[list] = None,
        additional_exempt_paths: Optional[list] = None,
    ):
        """
        Initialize context middleware.

        Args:
            app: FastAPI application
            require_client: Whether to require client context (default: True)
            require_engagement: Whether to require engagement context (default: False)
            exempt_paths: Complete list of exempt paths (overrides defaults)
            additional_exempt_paths: Additional paths to add to defaults (extends defaults)
        """
        super().__init__(app)
        self.require_client = require_client
        self.require_engagement = require_engagement

        # Define core exempt paths that should always be exempt
        default_exempt_paths = [
            "/health",
            "/api/v1/health",  # Health endpoint - no tenant context needed
            "/api/v1/health/database",  # Database health - no tenant context needed
            "/api/v1/unified-discovery/health",  # Unified discovery health - no tenant context needed
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/debug/routes",
            "/static",
            # Authentication endpoints - should not require context
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/registration-status",
            "/api/v1/auth/health",
            "/api/v1/auth/demo/create-admin-user",
            "/api/v1/auth/demo/status",
            "/api/v1/auth/demo/reset",
            "/api/v1/auth/demo/health",
            "/api/v1/auth/system/info",
            "/api/v1/auth/refresh",  # Token refresh - should not require context
            # Password reset endpoints - public, no tenant context needed
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/validate-reset-token",
            "/api/v1/auth/reset-password",
            # /me endpoint for context initialization
            "/api/v1/me",
            # Feedback view endpoint - admin feature, no tenant context needed
            "/api/v1/chat/feedback",
        ]

        if exempt_paths is not None:
            # Complete override of defaults (backward compatibility)
            self.exempt_paths = exempt_paths
        else:
            # Use defaults and extend with additional paths
            self.exempt_paths = default_exempt_paths.copy()
            if additional_exempt_paths:
                self.exempt_paths.extend(additional_exempt_paths)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with context extraction and injection.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from downstream handler
        """
        start_time = time.time()
        path = request.url.path

        # CORS preflight requests should always be exempt
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check exemptions and handle admin access
        is_exempt = await self._handle_exemptions_and_admin_access(request, path)

        if is_exempt:
            return await call_next(request)

        # Process request with context
        return await self._process_request_with_context(
            request, call_next, path, start_time
        )

    async def _handle_exemptions_and_admin_access(
        self, request: Request, path: str
    ) -> bool:
        """Handle exemptions and admin endpoint access control."""
        # Check standard path exemptions
        is_exempt = self._check_path_exemptions(path)

        # Handle admin endpoint access
        if is_admin_endpoint(path):
            admin_response = await handle_admin_access(request, path)
            if admin_response is not None:
                # Access denied - raise appropriate exception
                raise HTTPException(status_code=admin_response.status_code)
            is_exempt = True  # Admin access granted

        return is_exempt

    def _check_path_exemptions(self, path: str) -> bool:
        """Check if path matches exemption patterns."""
        for exempt_path in self.exempt_paths:
            if exempt_path == "/" and path == "/":
                return True
            elif exempt_path != "/" and path.startswith(exempt_path):
                return True
        return False

    async def _process_request_with_context(
        self, request: Request, call_next: Callable, path: str, start_time: float
    ) -> Response:
        """Process request that requires context extraction."""
        # Extract and validate context
        context = await self._extract_and_validate_context(request, path)
        if context is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Context extraction failed", "path": path},
            )

        # Process request
        try:
            response = await call_next(request)
            self._add_context_headers(response, context)

            # Log processing time
            process_time = time.time() - start_time
            logger.debug(
                f"Request processed in {process_time:.3f}s | Context: {context}"
            )

            return response
        except Exception as e:
            logger.error(safe_log_format("Request processing failed: {e}", e=e))
            raise

    async def _extract_and_validate_context(self, request: Request, path: str):
        """Extract and validate request context."""
        try:
            from app.core.context import (
                extract_context_from_request,
                set_request_context,
            )
            from app.core.context import is_demo_client
            from app.core.context_utils import validate_context

            context = extract_context_from_request(request)
            validate_context(
                context,
                require_client=self.require_client,
                require_engagement=self.require_engagement,
            )
            set_request_context(context)

            # Log context info
            log_level = (
                logging.DEBUG
                if is_demo_client(context.client_account_id)
                else logging.INFO
            )
            logger.log(log_level, f"Request context: {context} | Path: {path}")

            return context
        except Exception as e:
            logger.error(
                safe_log_format(
                    "Context extraction failed for {path}: {e}", path=path, e=e
                )
            )
            return None

    def _add_context_headers(self, response, context):
        """Add context information to response headers."""
        if hasattr(response, "headers"):
            from app.core.context import is_demo_client

            response.headers["X-Context-Client"] = context.client_account_id or "none"
            response.headers["X-Context-Engagement"] = context.engagement_id or "none"
            response.headers["X-Context-Demo"] = str(
                is_demo_client(context.client_account_id)
            )
