"""
RBAC Access Validation Middleware
Middleware for validating user access to API endpoints based on RBAC system.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.context import get_current_context
from app.core.database import AsyncSessionLocal

# Import RBAC service with fallback
try:
    from app.services.rbac_service import (RBAC_MODELS_AVAILABLE,
                                           create_rbac_service)

    RBAC_SERVICE_AVAILABLE = True
except ImportError:
    RBAC_SERVICE_AVAILABLE = False
    create_rbac_service = None

logger = logging.getLogger(__name__)


class RBACMiddleware:
    """Middleware for RBAC access validation."""

    def __init__(self):
        self.rbac_enabled = RBAC_SERVICE_AVAILABLE

        # Define public endpoints that don't require authentication
        self.public_endpoints = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/register",
            "/api/v1/auth/registration-status",
            "/api/v1/auth/health",
            "/api/v1/auth/demo/create-admin-user",
            "/api/v1/demo",  # Demo endpoints for development
        }

        # Define admin-only endpoints
        self.admin_endpoints = {
            "/api/v1/auth/pending-approvals",
            "/api/v1/auth/approve-user",
            "/api/v1/auth/reject-user",
            "/api/v1/auth/grant-client-access",
            "/api/v1/auth/admin/dashboard-stats",
            "/api/v1/auth/admin/access-logs",
        }

        # Define read-only endpoints (require basic access)
        self.read_only_endpoints = {
            "/api/v1/discovery",
            "/api/v1/assets",
            "/api/v1/demo/assets",
            "/api/v1/auth/user-profile",
        }

        # Define write endpoints (require write access)
        self.write_endpoints = {
            "/api/v1/data-import",
            "/api/v1/discovery/data-import",
        }

        if not self.rbac_enabled:
            logger.warning(
                "RBAC Middleware initialized but RBAC service is not available"
            )

    async def __call__(self, request: Request, call_next):
        """Process request through RBAC validation."""

        # Skip RBAC validation if service is not available
        if not self.rbac_enabled:
            logger.debug("RBAC validation skipped - service not available")
            return await call_next(request)

        # Get request path and method
        path = request.url.path
        method = request.method

        # Check if endpoint is public
        if self._is_public_endpoint(path):
            logger.debug(f"Public endpoint accessed: {path}")
            return await call_next(request)

        # Extract user information from request
        user_id = self._extract_user_id(request)

        # If no user ID, check if anonymous access is allowed
        if not user_id:
            if self._allow_anonymous_access(path, method):
                logger.debug(f"Anonymous access allowed: {path}")
                return await call_next(request)
            else:
                return self._unauthorized_response("Authentication required")

        # Validate user access
        access_result = await self._validate_access(user_id, path, method, request)

        if not access_result["has_access"]:
            logger.warning(
                f"Access denied for user {user_id} to {path}: {access_result['reason']}"
            )
            return self._forbidden_response(access_result["reason"])

        # Access granted, proceed with request
        logger.debug(f"Access granted for user {user_id} to {path}")
        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (no authentication required)."""
        for public_path in self.public_endpoints:
            if path.startswith(public_path):
                return True
        return False

    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request headers or context."""
        # Check various common authentication header patterns
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Extract from Bearer token
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

                # Try JWT token first
                try:
                    from app.services.auth_services.jwt_service import \
                        JWTService

                    jwt_service = JWTService()
                    payload = jwt_service.verify_token(token)
                    if payload:
                        return payload.get("sub")
                except Exception as jwt_error:
                    logger.debug(f"JWT token verification failed: {jwt_error}")

                # Fallback to db-token format for backward compatibility
                if token.startswith("db-token-"):
                    try:
                        # Remove the "db-token-" prefix
                        token_content = token[9:]
                        # Find the last dash to separate user_id from hash
                        last_dash_index = token_content.rfind("-")
                        if last_dash_index > 0:
                            user_id_str = token_content[:last_dash_index]
                            return user_id_str
                    except Exception:
                        pass

        # Check custom headers
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        # Get from current context (if available from middleware)
        try:
            context = get_current_context()
            return context.user_id
        except Exception:
            pass

        # For development, allow demo user
        if request.headers.get("X-Demo-Mode") == "true":
            from app.core.demo_constants import DEMO_USER_ID

            return DEMO_USER_ID

        return None

    def _allow_anonymous_access(self, path: str, method: str) -> bool:
        """Check if anonymous access is allowed for this path/method."""
        # Allow OPTIONS requests for CORS preflight (no authentication needed)
        if method == "OPTIONS":
            return True

        # Allow GET requests to certain read-only endpoints in demo mode
        if method == "GET":
            demo_paths = ["/api/v1/demo", "/api/v1/health"]
            for demo_path in demo_paths:
                if path.startswith(demo_path):
                    return True

        return False

    async def _validate_access(
        self, user_id: str, path: str, method: str, request: Request
    ) -> Dict[str, Any]:
        """Validate user access to the requested resource."""
        try:
            # Create database session for RBAC validation
            async with AsyncSessionLocal() as db:
                rbac_service = create_rbac_service(db)

                # Determine resource type and action based on path and method
                resource_type, action = self._determine_resource_and_action(
                    path, method
                )

                # Validate access using RBAC service
                result = await rbac_service.validate_user_access(
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=self._extract_resource_id(path),
                    action=action,
                )

                return result

        except Exception as e:
            logger.error(f"Error validating access for user {user_id}: {e}")
            # In case of error, deny access for security
            return {"has_access": False, "reason": f"Access validation error: {str(e)}"}

    def _determine_resource_and_action(self, path: str, method: str) -> tuple[str, str]:
        """Determine resource type and action from path and HTTP method."""

        # Admin endpoints
        if any(path.startswith(admin_path) for admin_path in self.admin_endpoints):
            return "admin_console", "manage"

        # Client/engagement data endpoints
        if path.startswith("/api/v1/discovery") or path.startswith("/api/v1/assets"):
            if method in ["POST", "PUT", "PATCH", "DELETE"]:
                return "data", "write"
            else:
                return "data", "read"

        # Data import endpoints
        if path.startswith("/api/v1/data-import"):
            return "data", "write"

        # User profile endpoints
        if path.startswith("/api/v1/auth/user-profile"):
            if method in ["PUT", "PATCH"]:
                return "profile", "write"
            else:
                return "profile", "read"

        # Default to read access for GET, write for others
        if method == "GET":
            return "data", "read"
        else:
            return "data", "write"

    def _extract_resource_id(self, path: str) -> Optional[str]:
        """Extract resource ID from path if present."""
        # Simple extraction from common patterns like /api/v1/resource/{id}
        path_parts = path.split("/")

        # Look for UUID-like patterns in path
        for part in path_parts:
            if len(part) == 36 and part.count("-") == 4:  # UUID pattern
                return part

        return None

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return 401 Unauthorized response."""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "error",
                "message": message,
                "error_code": "AUTHENTICATION_REQUIRED",
                "details": {
                    "required_headers": ["Authorization", "X-User-ID"],
                    "auth_endpoint": "/api/v1/auth/register",
                },
            },
        )

    def _forbidden_response(self, reason: str) -> JSONResponse:
        """Return 403 Forbidden response."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": "error",
                "message": f"Access denied: {reason}",
                "error_code": "ACCESS_DENIED",
                "details": {
                    "contact": "admin@aiforce.com",
                    "request_access": "/api/v1/auth/register",
                },
            },
        )


# Factory function for adding middleware to FastAPI app
def add_rbac_middleware(app):
    """Add RBAC middleware to FastAPI application."""
    if RBAC_SERVICE_AVAILABLE:
        rbac_middleware = RBACMiddleware()
        app.middleware("http")(rbac_middleware)
        logger.info("RBAC middleware added to application")
    else:
        logger.warning("RBAC middleware not added - service not available")


# Decorator for protecting individual endpoints
def require_access(resource_type: str, action: str = "read"):
    """Decorator to require specific access for an endpoint."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented as a dependency in FastAPI
            # For now, just pass through
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Dependency for FastAPI endpoints
async def require_authentication(request: Request) -> str:
    """FastAPI dependency to require authentication."""
    if not RBAC_SERVICE_AVAILABLE:
        from app.core.demo_constants import DEMO_USER_ID

        return DEMO_USER_ID  # Fallback for development

    # Extract user ID
    middleware = RBACMiddleware()
    user_id = middleware._extract_user_id(request)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    return user_id


async def require_admin_access(request: Request) -> str:
    """FastAPI dependency to require admin access."""
    user_id = await require_authentication(request)

    if not RBAC_SERVICE_AVAILABLE:
        return user_id  # Fallback for development

    # 🚨 SECURITY FIX: Remove demo user bypass - all users must go through RBAC validation
    # No more blanket admin access for demo users

    try:
        # Validate admin access for ALL users (including demo users)
        async with AsyncSessionLocal() as db:
            rbac_service = create_rbac_service(db)
            access_result = await rbac_service.validate_user_access(
                user_id=user_id, resource_type="admin_console", action="read"
            )

            if not access_result["has_access"]:
                logger.warning(
                    f"Admin access denied for user {user_id}: {access_result.get('reason', 'Unknown reason')}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Admin access required: {access_result.get('reason', 'Insufficient privileges')}",
                )

        logger.info(f"Admin access granted for user {user_id}")
        return user_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating admin access for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin access validation failed",
        )
