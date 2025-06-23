"""
FastAPI middleware for automatic context injection.
Extracts multi-tenant context from request headers and makes it available via context variables.
"""

from typing import Callable, Optional, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

from .context import (
    extract_context_from_request, 
    set_context, 
    validate_context,
    RequestContext,
    is_demo_client
)

# Import security audit service
try:
    from app.services.security_audit_service import SecurityAuditService
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False
    SecurityAuditService = None

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
        exempt_paths: Optional[list] = None
    ):
        """
        Initialize context middleware.
        
        Args:
            app: FastAPI application
            require_client: Whether to require client context (default: True)
            require_engagement: Whether to require engagement context (default: False)
            exempt_paths: List of paths to exempt from context requirements
        """
        super().__init__(app)
        self.require_client = require_client
        self.require_engagement = require_engagement
        self.exempt_paths = exempt_paths or [
            "/health",
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
            # /me endpoint for context initialization
            "/api/v1/me"
        ]
    
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
        
        # Check if path is exempt from context requirements
        path = request.url.path
        
        # CORS preflight requests (OPTIONS) should always be exempt
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Special handling for root path - only match exactly '/'
        is_exempt = False
        for exempt_path in self.exempt_paths:
            if exempt_path == '/' and path == '/':
                is_exempt = True
                break
            elif exempt_path != '/' and path.startswith(exempt_path):
                is_exempt = True
                break

        # Role-based exemption for admin endpoints
        is_admin_endpoint = self._is_admin_endpoint(path)
        user_id = self._extract_user_id(request)
        is_platform_admin = False
        
        if is_admin_endpoint:
            if not user_id:
                # Block unauthenticated access to admin endpoints
                logger.warning(f"Unauthenticated access blocked for admin endpoint: {path}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Authentication required",
                        "detail": "Admin endpoints require authentication",
                        "path": path
                    }
                )
            
            is_platform_admin = await self._check_platform_admin(user_id)
            if not is_platform_admin:
                # Block non-admin access to admin endpoints
                logger.warning(f"Non-admin access blocked for {path} by user {user_id}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Access denied",
                        "detail": "Platform administrator role required",
                        "path": path
                    }
                )
            
            # Grant exemption for platform admins
            is_exempt = True
            logger.info(f"Admin exemption granted for {path} to user {user_id}")
            
            # Security audit logging for admin access
            try:
                from app.services.security_audit_service import SecurityAuditService
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as audit_db:
                    audit_service = SecurityAuditService(audit_db)
                    await audit_service.log_admin_access(
                        user_id=user_id,
                        endpoint=path,
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent")
                    )
            except Exception as audit_error:
                logger.warning(f"Failed to log admin access audit: {audit_error}")
                # Don't fail the request if audit logging fails

        if is_exempt:
            return await call_next(request)
        
        # Initialize context variable
        context = RequestContext()
        
        # Extract context from request
        try:
            from app.core.context import extract_context_from_request, validate_context, set_context, is_demo_client
            
            context = extract_context_from_request(request)
            
            # Validate context for non-exempt paths
            validate_context(
                context, 
                require_client=self.require_client,
                require_engagement=self.require_engagement
            )
            
            # Set context for the request
            set_context(context)
            
            # Log context info
            log_level = logging.DEBUG if is_demo_client(context.client_account_id) else logging.INFO
            logger.log(log_level, f"Request context: {context} | Path: {path}")
            
        except Exception as e:
            logger.error(f"Context extraction failed for {path}: {e}")
            
            # Return error for non-exempt paths
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Context extraction failed",
                    "detail": str(e),
                    "path": path
                }
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add context info to response headers for debugging
            if hasattr(response, 'headers'):
                response.headers["X-Context-Client"] = context.client_account_id or "none"
                response.headers["X-Context-Engagement"] = context.engagement_id or "none"
                response.headers["X-Context-Demo"] = str(is_demo_client(context.client_account_id))
            
            # Log processing time
            process_time = time.time() - start_time
            logger.debug(f"Request processed in {process_time:.3f}s | Context: {context}")
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            raise
    
    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if endpoint is admin-only and should allow context exemption for platform admins."""
        admin_paths = [
            "/api/v1/admin/",                    # All admin CRUD operations
            "/api/v1/auth/admin/",               # Admin dashboard and management
            "/api/v1/auth/user-profile/",        # User profile management
            "/api/v1/auth/pending-approvals",    # User approval management
            "/api/v1/auth/approve-user",         # User approval actions
            "/api/v1/auth/reject-user",          # User rejection actions
            "/api/v1/auth/active-users",         # Active user management
            "/api/v1/auth/admin/create-user",    # Admin user creation
            "/api/v1/auth/admin/access-logs",    # Access log viewing
            "/api/v1/auth/admin/dashboard-stats" # Admin dashboard statistics
        ]
        return any(path.startswith(admin_path) for admin_path in admin_paths)
    
    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request headers."""
        return (
            request.headers.get("X-User-ID") or
            request.headers.get("x-user-id") or
            request.headers.get("X-User-Id")
        )
    
    async def _check_platform_admin(self, user_id: str) -> bool:
        """Check if user is a platform administrator."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.rbac import UserRole
            from sqlalchemy import select, and_
            
            async with AsyncSessionLocal() as db:
                query = select(UserRole).where(
                    and_(
                        UserRole.user_id == user_id,
                        UserRole.role_type == 'platform_admin',
                        UserRole.is_active == True
                    )
                )
                result = await db.execute(query)
                return result.scalar_one_or_none() is not None
                
        except Exception as e:
            logger.error(f"Error checking platform admin status for {user_id}: {e}")
            return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Additional middleware for detailed request logging with context.
    """
    
    def __init__(self, app: Callable, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request details with context information.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from downstream handler
        """
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        start_time = time.time()
        
        # Extract basic request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        
        # Log request start
        logger.info(f"🔄 {method} {url} | IP: {client_ip} | Agent: {user_agent[:50]}...")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            status_code = response.status_code
            
            # Use different log levels based on status
            if status_code >= 500:
                log_level = logging.ERROR
                emoji = "❌"
            elif status_code >= 400:
                log_level = logging.WARNING
                emoji = "⚠️"
            else:
                log_level = logging.INFO
                emoji = "✅"
            
            logger.log(
                log_level,
                f"{emoji} {method} {url} | Status: {status_code} | Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"❌ {method} {url} | Error: {e} | Time: {process_time:.3f}s")
            raise


async def get_current_context_dependency() -> RequestContext:
    """
    FastAPI dependency for getting current request context.
    
    Returns:
        Current RequestContext
        
    Usage:
        @app.get("/api/data")
        async def get_data(context: RequestContext = Depends(get_current_context_dependency)):
            # Use context.client_account_id, etc.
    """
    from .context import get_current_context
    return get_current_context()


def create_context_aware_dependency(require_client: bool = True, require_engagement: bool = False):
    """
    Create a context dependency with specific requirements.
    
    Args:
        require_client: Whether client context is required
        require_engagement: Whether engagement context is required
        
    Returns:
        FastAPI dependency function
        
    Usage:
        require_engagement = create_context_aware_dependency(require_engagement=True)
        
        @app.get("/api/engagement-data")
        async def get_engagement_data(context: RequestContext = Depends(require_engagement)):
            # Context is guaranteed to have engagement_id
    """
    async def context_dependency() -> RequestContext:
        from .context import get_current_context
        context = get_current_context()
        
        # Validate requirements
        validate_context(
            context,
            require_client=require_client,
            require_engagement=require_engagement
        )
        
        return context
    
    return context_dependency 