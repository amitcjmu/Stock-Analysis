"""
Security Dependencies for API Endpoints

Provides security-enforced dependencies that ensure proper multi-tenant isolation.
All API endpoints should use these dependencies instead of raw context extraction.
"""

import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, extract_context_from_request
from app.core.database import get_db

logger = logging.getLogger(__name__)


class SecurityError(HTTPException):
    """Security violation exception"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"SECURITY VIOLATION: {detail}"
        )


def get_verified_context(
    request: Request,
    require_client: bool = True,
    require_engagement: bool = True,
    require_user: bool = True
) -> RequestContext:
    """
    Extract and verify request context with strict security enforcement.
    
    Args:
        request: FastAPI request
        require_client: Whether client_account_id is required
        require_engagement: Whether engagement_id is required  
        require_user: Whether user_id is required
        
    Returns:
        Verified RequestContext
        
    Raises:
        SecurityError: If required context is missing
    """
    context = extract_context_from_request(request)
    
    # Log security audit
    logger.info(
        f"🔒 Security Context Check - Path: {request.url.path}, "
        f"Client: {context.client_account_id}, "
        f"Engagement: {context.engagement_id}, "
        f"User: {context.user_id}"
    )
    
    # Enforce required fields
    if require_client and not context.client_account_id:
        logger.error(f"🚨 SECURITY: Missing client_account_id for {request.url.path}")
        raise SecurityError("Client account context is required for multi-tenant security")
    
    if require_engagement and not context.engagement_id:
        logger.error(f"🚨 SECURITY: Missing engagement_id for {request.url.path}")
        raise SecurityError("Engagement context is required for project isolation")
        
    if require_user and not context.user_id:
        logger.error(f"🚨 SECURITY: Missing user_id for {request.url.path}")
        raise SecurityError("User context is required for audit trail")
    
    # Validate UUIDs
    import uuid
    try:
        if context.client_account_id:
            uuid.UUID(context.client_account_id)
        if context.engagement_id:
            uuid.UUID(context.engagement_id)
        if context.user_id:
            uuid.UUID(context.user_id)
    except ValueError as e:
        logger.error(f"🚨 SECURITY: Invalid UUID in context - {e}")
        raise SecurityError("Invalid context format - UUIDs required")
    
    logger.info(f"✅ Security context verified for {request.url.path}")
    return context


def get_client_context(request: Request) -> RequestContext:
    """Get context with client_account_id required"""
    return get_verified_context(request, require_client=True, require_engagement=False, require_user=False)


def get_project_context(request: Request) -> RequestContext:
    """Get context with client and engagement required"""
    return get_verified_context(request, require_client=True, require_engagement=True, require_user=False)


def get_full_context(request: Request) -> RequestContext:
    """Get context with all fields required"""
    return get_verified_context(request, require_client=True, require_engagement=True, require_user=True)


async def verify_tenant_access(
    db: AsyncSession,
    context: RequestContext,
    resource_type: str,
    resource_id: str
) -> bool:
    """
    Verify that the current context has access to a specific resource.
    
    Args:
        db: Database session
        context: Request context
        resource_type: Type of resource (e.g., 'flow', 'asset', 'assessment')
        resource_id: ID of the resource
        
    Returns:
        True if access is allowed
        
    Raises:
        SecurityError: If access is denied
    """
    # Map resource types to their models and tenant fields
    resource_map = {
        'flow': ('discovery_flow', 'client_account_id'),
        'master_flow': ('crewai_flow_state_extensions', 'client_account_id'),
        'asset': ('asset', 'client_account_id'),
        'assessment': ('assessment_flow', 'client_account_id')
    }
    
    if resource_type not in resource_map:
        raise SecurityError(f"Unknown resource type: {resource_type}")
    
    table_name, tenant_field = resource_map[resource_type]
    
    # Verify ownership through direct query
    from sqlalchemy import text
    query = text(f"""
        SELECT 1 FROM {table_name}
        WHERE id = :resource_id
        AND {tenant_field} = :client_id
    """)
    
    result = await db.execute(
        query,
        {"resource_id": resource_id, "client_id": context.client_account_id}
    )
    
    if not result.scalar():
        logger.error(
            f"🚨 SECURITY: Tenant access denied - "
            f"Client {context.client_account_id} attempted to access "
            f"{resource_type} {resource_id}"
        )
        raise SecurityError(f"Access denied to {resource_type}")
    
    return True


# Dependency injection functions for FastAPI

def SecureClient(
    request: Request = Depends()
) -> RequestContext:
    """FastAPI dependency for client-scoped endpoints"""
    return get_client_context(request)


def SecureProject(
    request: Request = Depends()
) -> RequestContext:
    """FastAPI dependency for project-scoped endpoints"""
    return get_project_context(request)


def SecureUser(
    request: Request = Depends()
) -> RequestContext:
    """FastAPI dependency for user-scoped endpoints"""
    return get_full_context(request)


async def SecureResource(
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(SecureUser)
):
    """
    FastAPI dependency to verify resource access.
    
    Usage:
        @router.get("/flows/{flow_id}")
        async def get_flow(
            flow_id: str,
            _: None = Depends(lambda: SecureResource("flow", flow_id))
        ):
    """
    await verify_tenant_access(db, context, resource_type, resource_id)
    return None