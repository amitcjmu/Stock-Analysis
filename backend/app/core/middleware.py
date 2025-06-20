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

logger = logging.getLogger(__name__)


class ContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for extracting and injecting multi-tenant context.
    
    This middleware:
    1. Extracts context from request headers
    2. Validates context if required
    3. Sets context variables for the request scope
    4. Provides fallback to demo client (Pujyam Corp)
    5. Logs context for debugging
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
            "/static"
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
        
        # Special handling for root path - only match exactly '/'
        is_exempt = False
        for exempt_path in self.exempt_paths:
            if exempt_path == '/' and path == '/':
                is_exempt = True
                break
            elif exempt_path != '/' and path.startswith(exempt_path):
                is_exempt = True
                break

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