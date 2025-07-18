"""
Context management for multi-tenant request handling.
Provides utilities for extracting and injecting client/engagement/flow context.
"""

from typing import Optional, Dict, Any, TypeVar, Callable
from contextvars import ContextVar
from fastapi import Request, HTTPException, Depends
from functools import wraps
from dataclasses import dataclass, asdict
import uuid
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Context variable for request context
_request_context: ContextVar[Optional['RequestContext']] = ContextVar(
    'request_context',
    default=None
)

# Legacy context variables for backward compatibility
_client_account_id: ContextVar[Optional[str]] = ContextVar('client_account_id', default=None)
_engagement_id: ContextVar[Optional[str]] = ContextVar('engagement_id', default=None) 
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_flow_id: ContextVar[Optional[str]] = ContextVar('flow_id', default=None)

# Demo client configuration with fixed UUIDs for frontend fallback
DEMO_CLIENT_CONFIG = {
    "client_account_id": "11111111-1111-1111-1111-111111111111",  # Fixed demo client UUID
    "client_name": "Demo Corporation",
    "engagement_id": "22222222-2222-2222-2222-222222222222",  # Fixed demo engagement UUID
    "engagement_name": "Demo Cloud Migration Project"
}

try:
    from app.models.client_account import ClientAccount, Engagement, User
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Client account models not available: {e}")
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None
    User = None


@dataclass
class RequestContext:
    """Enhanced request context with audit fields"""
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    user_id: Optional[str] = None
    flow_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Audit fields
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_version: Optional[str] = None
    
    # Feature flags
    feature_flags: Optional[Dict[str, bool]] = None
    
    def __post_init__(self):
        if self.feature_flags is None:
            self.feature_flags = {}
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if context has permission for resource/action"""
        # TODO: Implement permission checking
        return True
    
    def __repr__(self):
        return f"RequestContext(client={self.client_account_id}, engagement={self.engagement_id}, user={self.user_id}, flow={self.flow_id})"


def extract_context_from_request(request: Request) -> RequestContext:
    """
    Extract context from request headers with demo client fallback.
    
    Header precedence:
    1. X-Client-Account-Id, X-Engagement-Id (explicit)
    2. X-Context-* headers (alternative naming)
    3. Demo client defaults (Pujyam Corp)
    
    Args:
        request: FastAPI request object
        
    Returns:
        RequestContext with extracted or default values
    """
    headers = request.headers
    
    # Debug logging to see what headers we're receiving
    logger.info(f"🔍 Headers received: {dict(headers)}")
    
    # Extract context from headers (primary format)
    # Handle both uppercase and lowercase variations
    # Clean up comma-separated values that might come from multiple headers
    def clean_header_value(value: str) -> str:
        """Clean header value by taking first non-empty value if comma-separated"""
        if not value:
            return value
        # Split by comma and take the first non-empty value
        parts = [part.strip() for part in value.split(',') if part.strip()]
        return parts[0] if parts else value
    
    client_account_id = (
        headers.get("X-Client-Account-ID") or       # Frontend sends this format
        headers.get("x-client-account-id") or 
        headers.get("X-Client-Account-Id") or
        headers.get("x-context-client-id") or
        headers.get("client-account-id") or
        headers.get("X-Client-ID") or              # Frontend uses X-Client-ID
        headers.get("x-client-id")                 # Frontend uses x-client-id
    )
    if client_account_id:
        client_account_id = clean_header_value(client_account_id)
    
    engagement_id = (
        headers.get("X-Engagement-ID") or          # Frontend sends this format
        headers.get("x-engagement-id") or
        headers.get("X-Engagement-Id") or
        headers.get("x-context-engagement-id") or  
        headers.get("engagement-id")
    )
    if engagement_id:
        engagement_id = clean_header_value(engagement_id)
    
    user_id = (
        headers.get("X-User-ID") or                # Frontend sends this format
        headers.get("x-user-id") or
        headers.get("X-User-Id") or
        headers.get("x-context-user-id") or
        headers.get("user-id")
    )
    if user_id:
        user_id = clean_header_value(user_id)

    flow_id = (
        headers.get("X-Flow-ID") or
        headers.get("x-flow-id") or
        headers.get("X-Flow-Id")
    )
    if flow_id:
        flow_id = clean_header_value(flow_id)
    
    # Debug logging to see what we extracted
    logger.info(f"🔍 Extracted values - Client: {client_account_id}, Engagement: {engagement_id}, User: {user_id}, Flow: {flow_id}")
    
    # Flow ID is optional - no auto-generation needed
    
    # NO DEMO CLIENT FALLBACKS IN BACKEND - Security requirement for multi-tenancy
    # All context must be explicitly provided via headers
    
    context = RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        flow_id=flow_id
    )
    
    logger.info(f"🔍 Final context: {context}")
    return context


def get_request_context(request: Request) -> RequestContext:
    """
    Extract and return request context from a FastAPI request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        RequestContext extracted from request headers
    """
    context = extract_context_from_request(request)
    set_request_context(context)
    return context


def get_request_context_dependency(request: Request) -> RequestContext:
    """
    FastAPI dependency to extract and return request context.
    
    Args:
        request: FastAPI request object
        
    Returns:
        RequestContext extracted from request headers
    """
    context = extract_context_from_request(request)
    set_request_context(context)
    return context


def set_request_context(context: RequestContext) -> None:
    """Set the current request context"""
    _request_context.set(context)
    # Also set legacy context variables for backward compatibility
    _client_account_id.set(context.client_account_id)
    _engagement_id.set(context.engagement_id)
    _user_id.set(context.user_id)
    _flow_id.set(context.flow_id)
    logger.debug(f"Set context for client {context.client_account_id}")

def set_context(context: RequestContext) -> None:
    """Legacy function for backward compatibility"""
    set_request_context(context)


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context"""
    context = _request_context.get()
    if context:
        return context
    
    # Fallback to legacy context variables for backward compatibility
    client_id = _client_account_id.get()
    engagement_id = _engagement_id.get()
    user_id = _user_id.get()
    flow_id = _flow_id.get()
    
    if any([client_id, engagement_id, user_id, flow_id]):
        return RequestContext(
            client_account_id=client_id,
            engagement_id=engagement_id,
            user_id=user_id,
            flow_id=flow_id
        )
    
    return None

def get_required_context() -> RequestContext:
    """Get context or raise if not available"""
    context = get_current_context()
    if not context:
        raise RuntimeError("No request context available")
    return context


async def get_current_context_dependency() -> RequestContext:
    """
    FastAPI dependency function for getting current request context.
    This function can be used with Depends() to inject context into endpoints.
    
    Returns:
        Current RequestContext that was set by the middleware
        
    Usage:
        @app.get("/api/data")
        async def get_data(context: RequestContext = Depends(get_current_context_dependency)):
            # Use context.client_account_id, etc.
    """
    context = get_current_context()
    if not context:
        raise HTTPException(
            status_code=500,
            detail="No request context available. This usually means the context middleware is not properly configured."
        )
    return context

def clear_request_context() -> None:
    """Clear the current request context"""
    _request_context.set(None)
    # Also clear legacy variables
    _client_account_id.set(None)
    _engagement_id.set(None)
    _user_id.set(None)
    _flow_id.set(None)


def get_client_account_id() -> Optional[str]:
    """Get current client account ID."""
    return _client_account_id.get()


def get_engagement_id() -> Optional[str]:
    """Get current engagement ID.""" 
    return _engagement_id.get()


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return _user_id.get()


def get_flow_id() -> Optional[str]:
    """Get current flow ID."""
    return _flow_id.get()


def validate_context(context: RequestContext, require_client: bool = True, require_engagement: bool = False) -> None:
    """
    Validate that required context is present.
    
    Args:
        context: RequestContext to validate
        require_client: Whether client account ID is required
        require_engagement: Whether engagement ID is required
        
    Raises:
        HTTPException: If required context is missing
    """
    if require_client and not context.client_account_id:
        raise HTTPException(
            status_code=403,  # Changed from 400 to 403 for security
            detail="Client account context is required for multi-tenant security. Please provide X-Client-Account-Id header."
        )
    
    if require_engagement and not context.engagement_id:
        raise HTTPException(
            status_code=403,  # Changed from 400 to 403 for security
            detail="Engagement context is required for multi-tenant security. Please provide X-Engagement-Id header."
        )


def is_demo_client(client_account_id: Optional[str] = None) -> bool:
    """
    Check if the given client account ID matches our demo client.
    
    Args:
        client_account_id: Client account ID to check, or None to use current context
        
    Returns:
        True if this is the demo client
    """
    if client_account_id is None:
        client_account_id = get_client_account_id()
    
    return client_account_id == DEMO_CLIENT_CONFIG["client_account_id"]


def create_context_headers(context: RequestContext) -> Dict[str, str]:
    """
    Create HTTP headers from request context.
    
    Args:
        context: RequestContext to convert to headers
        
    Returns:
        Dictionary of headers
    """
    headers = {}
    
    if context.client_account_id:
        headers["X-Client-Account-Id"] = context.client_account_id
    
    if context.engagement_id:
        headers["X-Engagement-Id"] = context.engagement_id
        
    if context.user_id:
        headers["X-User-Id"] = context.user_id
        
    if context.flow_id:
        headers["X-Flow-Id"] = context.flow_id
    
    return headers


async def resolve_demo_client_ids(db_session) -> None:
    """
    Resolve and update demo client configuration from database.
    This ensures we're using actual UUIDs from the database.
    """
    try:
        from app.models.client_account import ClientAccount, Engagement
        
        # Find the Complete Test Client
        client = await db_session.execute(
            select(ClientAccount).where(ClientAccount.name == "Complete Test Client")
        )
        client = client.scalar_one_or_none()
        
        if client:
            DEMO_CLIENT_CONFIG["client_account_id"] = str(client.id)
            
            # Find the Azure Transformation engagement
            engagement = await db_session.execute(
                select(Engagement).where(
                    Engagement.client_account_id == client.id,
                    Engagement.name == "Azure Transformation"
                )
            )
            engagement = engagement.scalar_one_or_none()
            
            if engagement:
                DEMO_CLIENT_CONFIG["engagement_id"] = str(engagement.id)
                
        logger.info(f"✅ Demo client configuration resolved: {DEMO_CLIENT_CONFIG}")
        
    except Exception as e:
        logger.warning(f"⚠️ Could not resolve demo client IDs from database: {e}")
        # Keep using the hardcoded UUIDs as fallback


# Decorators for context management
T = TypeVar('T')

def require_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that ensures context is available"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_current_context()
        if not context:
            raise RuntimeError(f"Context required for {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def inject_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that injects context as first argument"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_required_context()
        return func(context, *args, **kwargs)
    return wrapper

def with_context(
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    **extra_fields
):
    """Decorator to run function with specific context"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = RequestContext(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                request_id=f"test-{func.__name__}",
                **extra_fields
            )
            
            # Set context
            token = _request_context.set(context)
            try:
                return await func(*args, **kwargs)
            finally:
                _request_context.reset(token)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = RequestContext(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                request_id=f"test-{func.__name__}",
                **extra_fields
            )
            
            # Set context
            token = _request_context.set(context)
            try:
                return func(*args, **kwargs)
            finally:
                _request_context.reset(token)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Context propagation for async tasks
class ContextTask:
    """Wrapper for asyncio tasks that preserves context"""
    
    @staticmethod
    def create_task(coro, *, name=None):
        """Create task that preserves current context"""
        context = get_current_context()
        
        async def wrapped():
            if context:
                set_request_context(context)
            try:
                return await coro
            finally:
                if context:
                    clear_request_context()
        
        import asyncio
        return asyncio.create_task(wrapped(), name=name) 