"""
Client Routes

API endpoints for client-related operations.
"""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models import User

from ..models.context_schemas import ClientsListResponse
from ..services.client_service import ClientService

router = APIRouter()


@router.get(
    "/clients/default",
    response_model=dict,
    summary="Get default client",
    description="Get the default client for the current user or demo client if none is set."
)
async def get_default_client(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Get default client context for current user"""
    try:
        service = ClientService(db)
        
        # Get user role
        user_role, actual_role_type = await service.get_user_role(current_user.id)
        
        # Check if demo user
        if str(current_user.id) == "44444444-4444-4444-4444-444444444444":
            context = service.create_demo_context(
                str(current_user.id), 
                current_user.email, 
                user_role
            )
            # Return just the client part as dict
            if context.client:
                return {
                    "id": str(context.client.id),
                    "name": context.client.name,
                    "status": "active",
                    "type": "enterprise",
                    "created_at": context.client.created_at.isoformat() if context.client.created_at else None,
                    "updated_at": context.client.updated_at.isoformat() if context.client.updated_at else None,
                    "metadata": {
                        "industry": "Technology",
                        "size": "Enterprise",
                        "location": "Global"
                    }
                }
        
        # Try to get context from user's client access
        context = await service.get_user_context_from_access(current_user, user_role)
        if context and context.client:
            return {
                "id": str(context.client.id),
                "name": context.client.name,
                "status": "active",
                "type": "enterprise",
                "created_at": context.client.created_at.isoformat() if context.client.created_at else None,
                "updated_at": context.client.updated_at.isoformat() if context.client.updated_at else None,
                "metadata": {
                    "description": context.client.description or "",
                    "engagement_id": str(context.engagement.id) if context.engagement else None,
                    "engagement_name": context.engagement.name if context.engagement else None
                }
            }
        
        # Platform admin fallback
        if user_role == "platform_admin":
            context = await service.get_admin_context(current_user, user_role)
            if context and context.client:
                return {
                    "id": str(context.client.id),
                    "name": context.client.name,
                    "status": "active",
                    "type": "enterprise",
                    "created_at": context.client.created_at.isoformat() if context.client.created_at else None,
                    "updated_at": context.client.updated_at.isoformat() if context.client.updated_at else None,
                    "metadata": {
                        "description": context.client.description or "",
                        "engagement_id": str(context.engagement.id) if context.engagement else None,
                        "engagement_name": context.engagement.name if context.engagement else None,
                        "admin_context": True
                    }
                }
        
        # No accessible clients found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No accessible clients or engagements found for user. Please contact administrator."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/clients", response_model=ClientsListResponse)
async def get_user_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClientsListResponse:
    """
    Get list of clients accessible to the current user.
    
    Returns all clients the user has access to based on their role and permissions.
    """
    service = ClientService(db)
    
    # Check if user is platform admin
    user_role, _ = await service.get_user_role(current_user.id)
    is_platform_admin = user_role == "platform_admin"
    
    return await service.get_user_clients(current_user.id, is_platform_admin)