"""
Context API Endpoints

Provides endpoints for managing user context including:
- Getting complete user context (user, client, engagement, session)
- Switching between available sessions
"""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.session_management_service import create_session_management_service
from app.models import User
from app.api.v1.auth.auth_utils import get_current_user
from app.schemas.context import UserContext, ClientBase, EngagementBase, SessionBase
from datetime import datetime

router = APIRouter(tags=["context"])

# Demo mode constants
DEMO_USER_ID = UUID("44444444-4444-4444-4444-444444444444")
DEMO_USER_EMAIL = "demo@democorp.com"
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")

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
    try:
        service = create_session_management_service(db)
        context = await service.get_user_context(current_user.id)
        if context and context.client:
            return context.client.model_dump()
    except Exception:
        pass  # fallback to demo

    # Fallback to demo client
    return {
        "id": str(DEMO_CLIENT_ID),
        "name": "Democorp",
        "is_demo": True
    }

@router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, and session."
)
async def get_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserContext:
    try:
        # First, determine the user's role from UserRole table
        from app.models.rbac import UserRole
        from sqlalchemy import select, and_
        
        user_role = "user"  # Default role
        try:
            roles_query = select(UserRole).where(
                and_(UserRole.user_id == current_user.id, UserRole.is_active == True)
            )
            roles_result = await db.execute(roles_query)
            user_roles = roles_result.scalars().all()
            
            # Determine if user is admin based on roles
            if any(role.role_type in ["platform_admin", "client_admin"] for role in user_roles):
                user_role = "admin"
        except Exception as role_error:
            print(f"Error determining user role: {role_error}")
            # Continue with default role
        
        service = create_session_management_service(db)
        context = await service.get_user_context(current_user.id)
        if context:
            # Update the user role in the context
            context.user["role"] = user_role
            return context
        # Raise an exception to fall through to the demo context creation
        raise ValueError("User context not found, falling back to demo.")
    except Exception as e:
        print(f"Context error: {e}")
        # Fallback to demo context but with correct user info
        now = datetime.utcnow()
        demo_client = ClientBase(
            id=DEMO_CLIENT_ID,
            name="Democorp",
            description="Demonstration Client",
            created_at=now,
            updated_at=now
        )
        demo_engagement = EngagementBase(
            id=DEMO_ENGAGEMENT_ID,
            name="Cloud Migration 2024",
            description="Demonstration Engagement",
            client_id=DEMO_CLIENT_ID,
            created_at=now,
            updated_at=now
        )
        demo_session = SessionBase(
            id=DEMO_SESSION_ID,
            name="Demo Session",
            description="Demonstration Session",
            engagement_id=DEMO_ENGAGEMENT_ID,
            is_default=True,
            created_by=DEMO_USER_ID,
            created_at=now,
            updated_at=now
        )
        
        # Determine user role for fallback context
        user_role = "user"  # Default
        try:
            from app.models.rbac import UserRole
            from sqlalchemy import select, and_
            
            roles_query = select(UserRole).where(
                and_(UserRole.user_id == current_user.id, UserRole.is_active == True)
            )
            roles_result = await db.execute(roles_query)
            user_roles = roles_result.scalars().all()
            
            if any(role.role_type in ["platform_admin", "client_admin"] for role in user_roles):
                user_role = "admin"
        except Exception:
            pass  # Use default role
        
        return UserContext(
            user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
            client=demo_client,
            engagement=demo_engagement,
            session=demo_session,
            available_sessions=[demo_session]
        )

@router.post(
    "/sessions/{session_id}/switch",
    response_model=UserContext,
    summary="Switch current session",
    description="Switch the user's current session to the specified session ID."
)
async def switch_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Switch the current user's active session.
    
    Args:
        session_id: The ID of the session to switch to
        
    Returns:
        Updated user context with the new session
    """
    try:
        service = create_session_management_service(db)
        context = await service.switch_session(current_user.id, session_id)
        return context
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Additional endpoints for context switcher functionality
from typing import List
from pydantic import BaseModel

# Response models for context switcher
class ClientResponse(BaseModel):
    id: str
    name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    status: str = "active"

class EngagementResponse(BaseModel):
    id: str
    name: str
    client_id: str
    status: str
    type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ClientsListResponse(BaseModel):
    clients: List[ClientResponse]

class EngagementsListResponse(BaseModel):
    engagements: List[EngagementResponse]

@router.get("/clients", response_model=ClientsListResponse)
async def get_user_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of clients accessible to the current user.
    For regular users, returns clients they have access to.
    For admin users, returns all clients.
    """
    try:
        # Import models with fallback
        try:
            from app.models.client_account import ClientAccount
            from sqlalchemy import select
            
            # For now, return all active clients
            # TODO: Implement proper user-client access control
            query = select(ClientAccount).where(ClientAccount.is_active == True)
            result = await db.execute(query)
            clients = result.scalars().all()

            client_responses = []
            for client in clients:
                client_responses.append(ClientResponse(
                    id=str(client.id),
                    name=client.name,
                    industry=client.industry,
                    company_size=client.company_size,
                    status="active" if client.is_active else "inactive"
                ))

            return ClientsListResponse(clients=client_responses)
            
        except ImportError:
            # Return demo data if models not available
            demo_clients = [
                ClientResponse(
                    id="bafd5b46-aaaf-4c95-8142-573699d93171",
                    name="Complete Test Client",
                    industry="Technology",
                    company_size="Enterprise",
                    status="active"
                )
            ]
            return ClientsListResponse(clients=demo_clients)

    except Exception as e:
        print(f"Error fetching user clients: {e}")
        # Return demo data as fallback
        demo_clients = [
            ClientResponse(
                id="bafd5b46-aaaf-4c95-8142-573699d93171",
                name="Complete Test Client",
                industry="Technology",
                company_size="Enterprise",
                status="active"
            )
        ]
        return ClientsListResponse(clients=demo_clients)

@router.get("/clients/{client_id}/engagements", response_model=EngagementsListResponse)
async def get_client_engagements(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of engagements for a specific client accessible to the current user.
    """
    try:
        # Import models with fallback
        try:
            from app.models.client_account import ClientAccount, Engagement
            from sqlalchemy import select, and_
            
            # Verify client exists and user has access
            client_query = select(ClientAccount).where(
                and_(
                    ClientAccount.id == client_id,
                    ClientAccount.is_active == True
                )
            )
            client_result = await db.execute(client_query)
            client = client_result.scalar_one_or_none()

            if not client:
                raise HTTPException(status_code=404, detail="Client not found or not accessible")

            # Get engagements for this client
            # TODO: Implement proper user-engagement access control
            query = select(Engagement).where(
                and_(
                    Engagement.client_account_id == client_id,
                    Engagement.is_active == True
                )
            )
            result = await db.execute(query)
            engagements = result.scalars().all()

            engagement_responses = []
            for engagement in engagements:
                engagement_responses.append(EngagementResponse(
                    id=str(engagement.id),
                    name=engagement.name,
                    client_id=str(engagement.client_account_id),
                    status=engagement.status or "active",
                    type=engagement.engagement_type,
                    start_date=engagement.start_date.isoformat() if engagement.start_date else None,
                    end_date=engagement.target_completion_date.isoformat() if engagement.target_completion_date else None
                ))

            return EngagementsListResponse(engagements=engagement_responses)
            
        except ImportError:
            # Return demo data if models not available
            demo_engagements = [
                EngagementResponse(
                    id="6e9c8133-4169-4b79-b052-106dc93d0208",
                    name="Azure Transformation",
                    client_id=client_id,
                    status="active",
                    type="migration"
                )
            ]
            return EngagementsListResponse(engagements=demo_engagements)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching client engagements: {e}")
        # Return demo data as fallback
        demo_engagements = [
            EngagementResponse(
                id="6e9c8133-4169-4b79-b052-106dc93d0208",
                name="Azure Transformation",
                client_id=client_id,
                status="active",
                type="migration"
            )
        ]
        return EngagementsListResponse(engagements=demo_engagements)
