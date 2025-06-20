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
    🔑 PLATFORM ADMIN: Gets all clients. Regular users: Only clients with explicit access.
    """
    try:
        # Import models with fallback
        try:
            from app.models.client_account import ClientAccount
            from app.models.rbac import ClientAccess, UserProfile, UserRole
            from sqlalchemy import select, and_, or_
            
            # ✅ PLATFORM ADMIN FIX: Check if user is platform admin
            role_query = select(UserRole).where(
                and_(
                    UserRole.user_id == str(current_user.id),
                    UserRole.role_type == 'platform_admin',
                    UserRole.is_active == True
                )
            )
            role_result = await db.execute(role_query)
            is_platform_admin = role_result.scalar_one_or_none() is not None
            
            if is_platform_admin:
                # 🔑 Platform admins get ALL active clients
                all_clients_query = select(ClientAccount).where(
                    ClientAccount.is_active == True
                )
                result = await db.execute(all_clients_query)
                all_clients = result.scalars().all()
                
                client_responses = []
                for client in all_clients:
                    client_responses.append(ClientResponse(
                        id=str(client.id),
                        name=client.name,
                        industry=client.industry,
                        company_size=client.company_size,
                        status="active" if client.is_active else "inactive"
                    ))
                
                return ClientsListResponse(clients=client_responses)
            
            else:
                # Regular users: Get clients with explicit access via client_access table
                access_query = select(ClientAccess, ClientAccount).join(
                    ClientAccount, ClientAccess.client_account_id == ClientAccount.id
                ).where(
                    and_(
                        ClientAccess.user_profile_id == str(current_user.id),
                        ClientAccess.is_active == True,
                        ClientAccount.is_active == True
                    )
                )
                
                result = await db.execute(access_query)
                accessible_clients = result.all()

                client_responses = []
                for client_access, client in accessible_clients:
                    client_responses.append(ClientResponse(
                        id=str(client.id),
                        name=client.name,
                        industry=client.industry,
                        company_size=client.company_size,
                        status="active" if client.is_active else "inactive"
                    ))

                # If no clients found and user is demo user, return demo client
                if not client_responses and str(current_user.id) == "44444444-4444-4444-4444-444444444444":
                    demo_client_query = select(ClientAccount).where(
                        and_(
                            ClientAccount.id == "11111111-1111-1111-1111-111111111111",
                            ClientAccount.is_active == True
                        )
                    )
                    demo_result = await db.execute(demo_client_query)
                    demo_client = demo_result.scalar_one_or_none()
                    
                    if demo_client:
                        client_responses.append(ClientResponse(
                            id=str(demo_client.id),
                            name=demo_client.name,
                            industry=demo_client.industry,
                            company_size=demo_client.company_size,
                            status="active"
                        ))

                return ClientsListResponse(clients=client_responses)
            
        except ImportError:
            # Return demo data if models not available
            demo_clients = [
                ClientResponse(
                    id="11111111-1111-1111-1111-111111111111",
                    name="Democorp",
                    industry="Technology",
                    company_size="Enterprise",
                    status="active"
                )
            ]
            return ClientsListResponse(clients=demo_clients)

    except Exception as e:
        print(f"Error fetching user clients: {e}")
        # Return demo data as fallback for demo user only
        if str(current_user.id) == "44444444-4444-4444-4444-444444444444":
            demo_clients = [
                ClientResponse(
                    id="11111111-1111-1111-1111-111111111111",
                    name="Democorp",
                    industry="Technology",
                    company_size="Enterprise",
                    status="active"
                )
            ]
            return ClientsListResponse(clients=demo_clients)
        else:
            # Non-demo users get empty list if there's an error
            return ClientsListResponse(clients=[])

@router.get("/clients/{client_id}/engagements", response_model=EngagementsListResponse)
async def get_client_engagements(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of engagements for a specific client accessible to the current user.
    🔑 PLATFORM ADMIN: Gets all engagements. Regular users: Only for accessible clients.
    """
    try:
        # Import models with fallback
        try:
            from app.models.client_account import ClientAccount, Engagement
            from app.models.rbac import ClientAccess, UserRole
            from sqlalchemy import select, and_
            
            # ✅ PLATFORM ADMIN FIX: Check if user is platform admin
            role_query = select(UserRole).where(
                and_(
                    UserRole.user_id == str(current_user.id),
                    UserRole.role_type == 'platform_admin',
                    UserRole.is_active == True
                )
            )
            role_result = await db.execute(role_query)
            is_platform_admin = role_result.scalar_one_or_none() is not None
            
            # Verify client exists and is active
            client_query = select(ClientAccount).where(
                and_(
                    ClientAccount.id == client_id,
                    ClientAccount.is_active == True
                )
            )
            client_result = await db.execute(client_query)
            client = client_result.scalar_one_or_none()

            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            
            if not is_platform_admin:
                # Regular users: Verify they have access to this client
                access_check_query = select(ClientAccess).where(
                    and_(
                        ClientAccess.user_profile_id == str(current_user.id),
                        ClientAccess.client_account_id == client_id,
                        ClientAccess.is_active == True
                    )
                )
                access_result = await db.execute(access_check_query)
                client_access = access_result.scalar_one_or_none()
                
                # Special case for demo user accessing demo client
                is_demo_access = (
                    str(current_user.id) == "44444444-4444-4444-4444-444444444444" and
                    client_id == "11111111-1111-1111-1111-111111111111"
                )
                
                if not client_access and not is_demo_access:
                    raise HTTPException(status_code=403, detail="Access denied: No permission for this client")

            # Get engagements for this client (platform admins and authorized users)
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
            # Return demo data if models not available (only for demo client)
            if client_id == "11111111-1111-1111-1111-111111111111":
                demo_engagements = [
                    EngagementResponse(
                        id="22222222-2222-2222-2222-222222222222",
                        name="Cloud Migration 2024",
                        client_id=client_id,
                        status="active",
                        type="migration"
                    )
                ]
                return EngagementsListResponse(engagements=demo_engagements)
            else:
                return EngagementsListResponse(engagements=[])

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching client engagements: {e}")
        # Return demo data as fallback only for demo client
        if client_id == "11111111-1111-1111-1111-111111111111":
            demo_engagements = [
                EngagementResponse(
                    id="22222222-2222-2222-2222-222222222222",
                    name="Cloud Migration 2024",
                    client_id=client_id,
                    status="active",
                    type="migration"
                )
            ]
            return EngagementsListResponse(engagements=demo_engagements)
        else:
            return EngagementsListResponse(engagements=[])
