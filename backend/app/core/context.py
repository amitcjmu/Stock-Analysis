"""
Context management for multi-tenant request handling.
Provides utilities for extracting and injecting client/engagement/session context.
"""

from typing import Optional, Dict, Any
from contextvars import ContextVar
from fastapi import Request, HTTPException, Depends
import uuid
import logging
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
_client_account_id: ContextVar[Optional[str]] = ContextVar('client_account_id', default=None)
_engagement_id: ContextVar[Optional[str]] = ContextVar('engagement_id', default=None) 
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

# Demo client configuration with proper UUIDs (using existing client from database)
DEMO_CLIENT_CONFIG = {
    "client_account_id": "bafd5b46-aaaf-4c95-8142-573699d93171",  # Complete Test Client UUID
    "client_name": "Complete Test Client",
    "engagement_id": "6e9c8133-4169-4b79-b052-106dc93d0208",  # Azure Transformation UUID
    "engagement_name": "Azure Transformation"
}


class RequestContext:
    """Container for request context information."""
    
    def __init__(
        self,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.session_id = session_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "user_id": self.user_id,
            "session_id": self.session_id
        }
    
    def __repr__(self):
        return f"RequestContext(client={self.client_account_id}, engagement={self.engagement_id}, user={self.user_id}, session={self.session_id})"


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

    session_id = (
        headers.get("X-Session-ID") or             # Frontend sends this format
        headers.get("x-session-id") or
        headers.get("X-Session-Id") or
        headers.get("x-context-session-id") or
        headers.get("session-id")
    )
    if session_id:
        session_id = clean_header_value(session_id)
    
    # Debug logging to see what we extracted
    logger.info(f"🔍 Extracted values - Client: {client_account_id}, Engagement: {engagement_id}, User: {user_id}, Session: {session_id}")
    
    # Generate a session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.debug(f"No session ID in headers, generated new one: {session_id}")
    
    # NO DEMO CLIENT FALLBACKS IN BACKEND - Security requirement for multi-tenancy
    # All context must be explicitly provided via headers
    
    context = RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        session_id=session_id
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
    set_context(context)
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
    set_context(context)
    return context


def set_context(context: RequestContext) -> None:
    """
    Set context variables for the current request.
    
    Args:
        context: RequestContext to set
    """
    _client_account_id.set(context.client_account_id)
    _engagement_id.set(context.engagement_id)
    _user_id.set(context.user_id)
    _session_id.set(context.session_id)


def get_current_context() -> RequestContext:
    """
    Get current request context from context variables.
    
    Returns:
        Current RequestContext
    """
    return RequestContext(
        client_account_id=_client_account_id.get(),
        engagement_id=_engagement_id.get(),
        user_id=_user_id.get(),
        session_id=_session_id.get()
    )


def get_client_account_id() -> Optional[str]:
    """Get current client account ID."""
    return _client_account_id.get()


def get_engagement_id() -> Optional[str]:
    """Get current engagement ID.""" 
    return _engagement_id.get()


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return _user_id.get()


def get_session_id() -> Optional[str]:
    """Get current session ID."""
    return _session_id.get()


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
            status_code=400,
            detail="Client account context is required. Please provide X-Client-Account-Id header."
        )
    
    if require_engagement and not context.engagement_id:
        raise HTTPException(
            status_code=400,
            detail="Engagement context is required. Please provide X-Engagement-Id header."
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
        
    if context.session_id:
        headers["X-Session-Id"] = context.session_id
    
    return headers


async def resolve_demo_client_ids(db_session) -> None:
    """
    Resolve and update demo client configuration from database.
    This ensures we're using actual UUIDs from the database.
    """
    try:
        from app.models.client_account import ClientAccount
        from app.models.engagement import Engagement
        
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