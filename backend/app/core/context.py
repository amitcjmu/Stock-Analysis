"""
Context management for multi-tenant request handling.
Provides utilities for extracting and injecting client/engagement/session context.
"""

from typing import Optional, Dict, Any
from contextvars import ContextVar
from fastapi import Request, HTTPException
import uuid
import logging

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
_client_account_id: ContextVar[Optional[str]] = ContextVar('client_account_id', default=None)
_engagement_id: ContextVar[Optional[str]] = ContextVar('engagement_id', default=None) 
_session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

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
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.session_id = session_id
        self.user_id = user_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "session_id": self.session_id,
            "user_id": self.user_id
        }
    
    def __repr__(self):
        return f"RequestContext(client={self.client_account_id}, engagement={self.engagement_id}, session={self.session_id}, user={self.user_id})"


def extract_context_from_request(request: Request) -> RequestContext:
    """
    Extract context from request headers with demo client fallback.
    
    Header precedence:
    1. X-Client-Account-Id, X-Engagement-Id, X-Session-Id (explicit)
    2. X-Context-* headers (alternative naming)
    3. Demo client defaults (Pujyam Corp)
    
    Args:
        request: FastAPI request object
        
    Returns:
        RequestContext with extracted or default values
    """
    headers = request.headers
    
    # Extract context from headers (primary format)
    client_account_id = (
        headers.get("x-client-account-id") or 
        headers.get("x-context-client-id") or
        headers.get("client-account-id")
    )
    
    engagement_id = (
        headers.get("x-engagement-id") or
        headers.get("x-context-engagement-id") or  
        headers.get("engagement-id")
    )
    
    session_id = (
        headers.get("x-session-id") or
        headers.get("x-context-session-id") or
        headers.get("session-id")
    )
    
    user_id = (
        headers.get("x-user-id") or
        headers.get("x-context-user-id") or
        headers.get("user-id")
    )
    
    # Apply demo client defaults if no context provided
    if not client_account_id:
        client_account_id = DEMO_CLIENT_CONFIG["client_account_id"]
        logger.debug("No client context provided, using demo client: Pujyam Corp")
    
    if not engagement_id and (client_account_id == DEMO_CLIENT_CONFIG["client_account_id"] or client_account_id == "pujyam-corp"):
        engagement_id = DEMO_CLIENT_CONFIG["engagement_id"] 
        logger.debug("No engagement context provided, using demo engagement: Digital Transformation 2025")
    
    context = RequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        session_id=session_id,
        user_id=user_id
    )
    
    logger.debug(f"Extracted context from request: {context}")
    return context


def set_context(context: RequestContext) -> None:
    """
    Set context variables for the current request.
    
    Args:
        context: RequestContext to set
    """
    _client_account_id.set(context.client_account_id)
    _engagement_id.set(context.engagement_id)
    _session_id.set(context.session_id)
    _user_id.set(context.user_id)


def get_current_context() -> RequestContext:
    """
    Get current request context from context variables.
    
    Returns:
        Current RequestContext
    """
    return RequestContext(
        client_account_id=_client_account_id.get(),
        engagement_id=_engagement_id.get(),
        session_id=_session_id.get(),
        user_id=_user_id.get()
    )


def get_client_account_id() -> Optional[str]:
    """Get current client account ID."""
    return _client_account_id.get()


def get_engagement_id() -> Optional[str]:
    """Get current engagement ID.""" 
    return _engagement_id.get()


def get_session_id() -> Optional[str]:
    """Get current session ID."""
    return _session_id.get()


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return _user_id.get()


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
    Check if the current or provided client is the demo client.
    
    Args:
        client_account_id: Optional client ID to check (defaults to current context)
        
    Returns:
        True if this is the demo client
    """
    if client_account_id is None:
        client_account_id = get_client_account_id()
    
    return client_account_id == DEMO_CLIENT_CONFIG["client_account_id"] or client_account_id == "pujyam-corp"


def create_context_headers(context: RequestContext) -> Dict[str, str]:
    """
    Create HTTP headers from context for downstream requests.
    
    Args:
        context: RequestContext to convert
        
    Returns:
        Dictionary of HTTP headers
    """
    headers = {}
    
    if context.client_account_id:
        headers["X-Client-Account-Id"] = context.client_account_id
    
    if context.engagement_id:
        headers["X-Engagement-Id"] = context.engagement_id
        
    if context.session_id:
        headers["X-Session-Id"] = context.session_id
        
    if context.user_id:
        headers["X-User-Id"] = context.user_id
    
    return headers


async def resolve_demo_client_ids(db_session) -> None:
    """
    Resolve demo client slug to actual UUID after database initialization.
    This should be called during application startup.
    
    Args:
        db_session: Database session for lookup
    """
    try:
        from app.models.client_account import ClientAccount, Engagement
        from sqlalchemy import select
        
        # Find Pujyam Corp client by slug
        client_result = await db_session.execute(
            select(ClientAccount).where(ClientAccount.slug == "pujyam-corp")
        )
        demo_client = client_result.scalar_one_or_none()
        
        if demo_client:
            DEMO_CLIENT_CONFIG["client_account_id"] = str(demo_client.id)
            logger.info(f"✅ Resolved demo client ID: {demo_client.id}")
            
            # Find demo engagement
            engagement_result = await db_session.execute(
                select(Engagement).where(
                    Engagement.client_account_id == demo_client.id,
                    Engagement.slug == "digital-transformation-2025"
                )
            )
            demo_engagement = engagement_result.scalar_one_or_none()
            
            if demo_engagement:
                DEMO_CLIENT_CONFIG["engagement_id"] = str(demo_engagement.id)
                logger.info(f"✅ Resolved demo engagement ID: {demo_engagement.id}")
        else:
            logger.warning("⚠️  Demo client 'Pujyam Corp' not found in database")
            
    except Exception as e:
        logger.error(f"❌ Failed to resolve demo client IDs: {e}") 