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
from app.models import User
from app.api.v1.auth.auth_utils import get_current_user
from app.schemas.context import UserContext, ClientBase, EngagementBase, SessionBase
from datetime import datetime
from app.services.discovery_flow_service import DiscoveryFlowService
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
import logging

router = APIRouter(tags=["context"])

# Demo mode constants
DEMO_USER_ID = UUID("44444444-4444-4444-4444-444444444444")
DEMO_USER_EMAIL = "demo@democorp.com"
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")

logger = logging.getLogger(__name__)

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
        # First, determine the user's role from UserRole table
        from app.models.rbac import UserRole
        from sqlalchemy import select, and_
        
        user_role = "user"  # Default role
        actual_role_type = None  # Track the actual role type
        try:
            roles_query = select(UserRole).where(
                and_(UserRole.user_id == current_user.id, UserRole.is_active == True)
            )
            roles_result = await db.execute(roles_query)
            user_roles = roles_result.scalars().all()
            
            # Use the actual role type instead of simplified mapping
            if user_roles:
                # Get the highest privilege role
                role_hierarchy = {
                    "platform_admin": 5,
                    "client_admin": 4,
                    "engagement_manager": 3,
                    "analyst": 2,
                    "viewer": 1
                }
                
                highest_role = max(user_roles, key=lambda r: role_hierarchy.get(r.role_type, 0))
                actual_role_type = highest_role.role_type
                user_role = actual_role_type  # Use actual role type for security transparency
        except Exception as role_error:
            print(f"Error determining user role: {role_error}")
            # Continue with default role
        
        # Only fallback to demo context for actual demo user
        if str(current_user.id) == "44444444-4444-4444-4444-444444444444":
            # Demo user gets demo context
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
            
            return UserContext(
                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                client=demo_client,
                engagement=demo_engagement,
                session=demo_session,
                available_sessions=[demo_session]
            )
        else:
            # Real users: Create context from their client access
            try:
                from app.models.client_account import ClientAccount, Engagement
                from app.models.rbac import ClientAccess
                from sqlalchemy import select, and_
                
                # Get user's first accessible client
                access_query = select(ClientAccess, ClientAccount).join(
                    ClientAccount, ClientAccess.client_account_id == ClientAccount.id
                ).where(
                    and_(
                        ClientAccess.user_profile_id == str(current_user.id),
                        ClientAccess.is_active == True,
                        ClientAccount.is_active == True
                    )
                ).limit(1)
                
                access_result = await db.execute(access_query)
                client_access = access_result.first()
                
                if client_access:
                    client_access_obj, client = client_access
                    
                    # Get first engagement for this client
                    engagement_query = select(Engagement).where(
                        and_(
                            Engagement.client_account_id == client.id,
                            Engagement.is_active == True
                        )
                    ).limit(1)
                    
                    engagement_result = await db.execute(engagement_query)
                    engagement = engagement_result.scalar_one_or_none()
                    
                    if engagement:
                        now = datetime.utcnow()
                        
                        # Create context from real data
                        client_base = ClientBase(
                            id=str(client.id),
                            name=client.name,
                            description=client.description or f"Client: {client.name}",
                            created_at=client.created_at or now,
                            updated_at=client.updated_at or now
                        )
                        
                        engagement_base = EngagementBase(
                            id=str(engagement.id),
                            name=engagement.name,
                            description=engagement.description or f"Engagement: {engagement.name}",
                            client_id=str(client.id),
                            created_at=engagement.created_at or now,
                            updated_at=engagement.updated_at or now
                        )
                        
                        # Create a default session for this engagement
                        session_base = SessionBase(
                            id=str(engagement.id),  # Use engagement ID as session ID for now
                            name=f"Default Session - {engagement.name}",
                            description=f"Default session for {engagement.name}",
                            engagement_id=str(engagement.id),
                            is_default=True,
                            created_by=str(current_user.id),
                            created_at=now,
                            updated_at=now
                        )
                        
                        return UserContext(
                            user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                            client=client_base,
                            engagement=engagement_base,
                            session=session_base,
                            available_sessions=[session_base]
                        )
                        
            except Exception as fallback_error:
                print(f"Error creating real user context: {fallback_error}")
            
            # 🔧 PLATFORM ADMIN FIX: If user is platform admin, create a minimal context
            if user_role == "admin":
                # Platform admins get a minimal context that allows them to access admin functions
                now = datetime.utcnow()
                
                # Use first available client for admin context
                try:
                    from app.models.client_account import ClientAccount, Engagement
                    
                    # Get first client for admin context
                    client_query = select(ClientAccount).where(
                        ClientAccount.is_active == True
                    ).limit(1)
                    
                    client_result = await db.execute(client_query)
                    first_client = client_result.scalar_one_or_none()
                    
                    if first_client:
                        # Get first engagement for this client
                        engagement_query = select(Engagement).where(
                            and_(
                                Engagement.client_account_id == first_client.id,
                                Engagement.is_active == True
                            )
                        ).limit(1)
                        
                        engagement_result = await db.execute(engagement_query)
                        first_engagement = engagement_result.scalar_one_or_none()
                        
                        if first_engagement:
                            # Create admin context from first available client/engagement
                            client_base = ClientBase(
                                id=str(first_client.id),
                                name=first_client.name,
                                description=first_client.description or f"Client: {first_client.name}",
                                created_at=first_client.created_at or now,
                                updated_at=first_client.updated_at or now
                            )
                            
                            engagement_base = EngagementBase(
                                id=str(first_engagement.id),
                                name=first_engagement.name,
                                description=first_engagement.description or f"Engagement: {first_engagement.name}",
                                client_id=str(first_client.id),
                                created_at=first_engagement.created_at or now,
                                updated_at=first_engagement.updated_at or now
                            )
                            
                            # Create a default session for this engagement
                            session_base = SessionBase(
                                id=str(first_engagement.id),  # Use engagement ID as session ID for now
                                name=f"Admin Session - {first_engagement.name}",
                                description=f"Admin session for {first_engagement.name}",
                                engagement_id=str(first_engagement.id),
                                is_default=True,
                                created_by=str(current_user.id),
                                created_at=now,
                                updated_at=now
                            )
                            
                            return UserContext(
                                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                                client=client_base,
                                engagement=engagement_base,
                                session=session_base,
                                available_sessions=[session_base]
                            )
                            
                except Exception as admin_context_error:
                    print(f"Error creating admin context: {admin_context_error}")
                
                # If no clients/engagements exist, create minimal admin-only context
                return UserContext(
                    user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                    client=None,
                    engagement=None,
                    session=None,
                    available_sessions=[]
                )
            
            # If all else fails for regular users, raise an error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible clients or engagements found for user. Please contact administrator."
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
        # First, determine the user's role from UserRole table
        from app.models.rbac import UserRole
        from sqlalchemy import select, and_
        
        user_role = "user"  # Default role
        actual_role_type = None  # Track the actual role type
        try:
            roles_query = select(UserRole).where(
                and_(UserRole.user_id == current_user.id, UserRole.is_active == True)
            )
            roles_result = await db.execute(roles_query)
            user_roles = roles_result.scalars().all()
            
            # Use the actual role type instead of simplified mapping
            if user_roles:
                # Get the highest privilege role
                role_hierarchy = {
                    "platform_admin": 5,
                    "client_admin": 4,
                    "engagement_manager": 3,
                    "analyst": 2,
                    "viewer": 1
                }
                
                highest_role = max(user_roles, key=lambda r: role_hierarchy.get(r.role_type, 0))
                actual_role_type = highest_role.role_type
                user_role = actual_role_type  # Use actual role type for security transparency
        except Exception as role_error:
            print(f"Error determining user role: {role_error}")
            # Continue with default role
        
        # Only fallback to demo context for actual demo user
        if str(current_user.id) == "44444444-4444-4444-4444-444444444444":
            # Demo user gets demo context
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
            
            return UserContext(
                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                client=demo_client,
                engagement=demo_engagement,
                session=demo_session,
                available_sessions=[demo_session]
            )
        else:
            # Real users: Create context from their client access
            try:
                from app.models.client_account import ClientAccount, Engagement
                from app.models.rbac import ClientAccess
                from sqlalchemy import select, and_
                
                # Get user's first accessible client
                access_query = select(ClientAccess, ClientAccount).join(
                    ClientAccount, ClientAccess.client_account_id == ClientAccount.id
                ).where(
                    and_(
                        ClientAccess.user_profile_id == str(current_user.id),
                        ClientAccess.is_active == True,
                        ClientAccount.is_active == True
                    )
                ).limit(1)
                
                access_result = await db.execute(access_query)
                client_access = access_result.first()
                
                if client_access:
                    client_access_obj, client = client_access
                    
                    # Get first engagement for this client
                    engagement_query = select(Engagement).where(
                        and_(
                            Engagement.client_account_id == client.id,
                            Engagement.is_active == True
                        )
                    ).limit(1)
                    
                    engagement_result = await db.execute(engagement_query)
                    engagement = engagement_result.scalar_one_or_none()
                    
                    if engagement:
                        now = datetime.utcnow()
                        
                        # Create context from real data
                        client_base = ClientBase(
                            id=str(client.id),
                            name=client.name,
                            description=client.description or f"Client: {client.name}",
                            created_at=client.created_at or now,
                            updated_at=client.updated_at or now
                        )
                        
                        engagement_base = EngagementBase(
                            id=str(engagement.id),
                            name=engagement.name,
                            description=engagement.description or f"Engagement: {engagement.name}",
                            client_id=str(client.id),
                            created_at=engagement.created_at or now,
                            updated_at=engagement.updated_at or now
                        )
                        
                        # Create a default session for this engagement
                        session_base = SessionBase(
                            id=str(engagement.id),  # Use engagement ID as session ID for now
                            name=f"Default Session - {engagement.name}",
                            description=f"Default session for {engagement.name}",
                            engagement_id=str(engagement.id),
                            is_default=True,
                            created_by=str(current_user.id),
                            created_at=now,
                            updated_at=now
                        )
                        
                        return UserContext(
                            user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                            client=client_base,
                            engagement=engagement_base,
                            session=session_base,
                            available_sessions=[session_base]
                        )
                        
            except Exception as fallback_error:
                print(f"Error creating real user context: {fallback_error}")
            
            # 🔧 PLATFORM ADMIN FIX: If user is platform admin, create a minimal context
            if user_role == "admin":
                # Platform admins get a minimal context that allows them to access admin functions
                now = datetime.utcnow()
                
                # Use first available client for admin context
                try:
                    from app.models.client_account import ClientAccount, Engagement
                    
                    # Get first client for admin context
                    client_query = select(ClientAccount).where(
                        ClientAccount.is_active == True
                    ).limit(1)
                    
                    client_result = await db.execute(client_query)
                    first_client = client_result.scalar_one_or_none()
                    
                    if first_client:
                        # Get first engagement for this client
                        engagement_query = select(Engagement).where(
                            and_(
                                Engagement.client_account_id == first_client.id,
                                Engagement.is_active == True
                            )
                        ).limit(1)
                        
                        engagement_result = await db.execute(engagement_query)
                        first_engagement = engagement_result.scalar_one_or_none()
                        
                        if first_engagement:
                            # Create admin context from first available client/engagement
                            client_base = ClientBase(
                                id=str(first_client.id),
                                name=first_client.name,
                                description=first_client.description or f"Client: {first_client.name}",
                                created_at=first_client.created_at or now,
                                updated_at=first_client.updated_at or now
                            )
                            
                            engagement_base = EngagementBase(
                                id=str(first_engagement.id),
                                name=first_engagement.name,
                                description=first_engagement.description or f"Engagement: {first_engagement.name}",
                                client_id=str(first_client.id),
                                created_at=first_engagement.created_at or now,
                                updated_at=first_engagement.updated_at or now
                            )
                            
                            # Create a default session for this engagement
                            session_base = SessionBase(
                                id=str(first_engagement.id),  # Use engagement ID as session ID for now
                                name=f"Admin Session - {first_engagement.name}",
                                description=f"Admin session for {first_engagement.name}",
                                engagement_id=str(first_engagement.id),
                                is_default=True,
                                created_by=str(current_user.id),
                                created_at=now,
                                updated_at=now
                            )
                            
                            return UserContext(
                                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                                client=client_base,
                                engagement=engagement_base,
                                session=session_base,
                                available_sessions=[session_base]
                            )
                            
                except Exception as admin_context_error:
                    print(f"Error creating admin context: {admin_context_error}")
                
                # If no clients/engagements exist, create minimal admin-only context
                return UserContext(
                    user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                    client=None,
                    engagement=None,
                    session=None,
                    available_sessions=[]
                )
            
            # If all else fails for regular users, raise an error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible clients or engagements found for user. Please contact administrator."
            )
    except Exception as e:
        print(f"Context error: {e}")
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

@router.get("/clients/public", response_model=ClientsListResponse)
async def get_public_clients(
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all active clients (public endpoint for context establishment).
    This endpoint doesn't require authentication to avoid circular dependency.
    """
    try:
        # Import models with fallback
        try:
            from app.models.client_account import ClientAccount
            from sqlalchemy import select
            
            # Get all active clients (public access for context establishment)
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
        print(f"Error fetching public clients: {e}")
        # Return demo data as fallback
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
        actual_role_type = None  # Track the actual role type
        try:
            roles_query = select(UserRole).where(
                and_(UserRole.user_id == current_user.id, UserRole.is_active == True)
            )
            roles_result = await db.execute(roles_query)
            user_roles = roles_result.scalars().all()
            
            # Use the actual role type instead of simplified mapping
            if user_roles:
                # Get the highest privilege role
                role_hierarchy = {
                    "platform_admin": 5,
                    "client_admin": 4,
                    "engagement_manager": 3,
                    "analyst": 2,
                    "viewer": 1
                }
                
                highest_role = max(user_roles, key=lambda r: role_hierarchy.get(r.role_type, 0))
                actual_role_type = highest_role.role_type
                user_role = actual_role_type  # Use actual role type for security transparency
        except Exception as role_error:
            print(f"Error determining user role: {role_error}")
            # Continue with default role
        
        # Only fallback to demo context for actual demo user
        if str(current_user.id) == "44444444-4444-4444-4444-444444444444":
            # Demo user gets demo context
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
            
            return UserContext(
                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                client=demo_client,
                engagement=demo_engagement,
                session=demo_session,
                available_sessions=[demo_session]
            )
        else:
            # Real users: Create context from their client access
            try:
                from app.models.client_account import ClientAccount, Engagement
                from app.models.rbac import ClientAccess
                from sqlalchemy import select, and_
                
                # Get user's first accessible client
                access_query = select(ClientAccess, ClientAccount).join(
                    ClientAccount, ClientAccess.client_account_id == ClientAccount.id
                ).where(
                    and_(
                        ClientAccess.user_profile_id == str(current_user.id),
                        ClientAccess.is_active == True,
                        ClientAccount.is_active == True
                    )
                ).limit(1)
                
                access_result = await db.execute(access_query)
                client_access = access_result.first()
                
                if client_access:
                    client_access_obj, client = client_access
                    
                    # Get first engagement for this client
                    engagement_query = select(Engagement).where(
                        and_(
                            Engagement.client_account_id == client.id,
                            Engagement.is_active == True
                        )
                    ).limit(1)
                    
                    engagement_result = await db.execute(engagement_query)
                    engagement = engagement_result.scalar_one_or_none()
                    
                    if engagement:
                        now = datetime.utcnow()
                        
                        # Create context from real data
                        client_base = ClientBase(
                            id=str(client.id),
                            name=client.name,
                            description=client.description or f"Client: {client.name}",
                            created_at=client.created_at or now,
                            updated_at=client.updated_at or now
                        )
                        
                        engagement_base = EngagementBase(
                            id=str(engagement.id),
                            name=engagement.name,
                            description=engagement.description or f"Engagement: {engagement.name}",
                            client_id=str(client.id),
                            created_at=engagement.created_at or now,
                            updated_at=engagement.updated_at or now
                        )
                        
                        # Create a default session for this engagement
                        session_base = SessionBase(
                            id=str(engagement.id),  # Use engagement ID as session ID for now
                            name=f"Default Session - {engagement.name}",
                            description=f"Default session for {engagement.name}",
                            engagement_id=str(engagement.id),
                            is_default=True,
                            created_by=str(current_user.id),
                            created_at=now,
                            updated_at=now
                        )
                        
                        return UserContext(
                            user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                            client=client_base,
                            engagement=engagement_base,
                            session=session_base,
                            available_sessions=[session_base]
                        )
                        
            except Exception as fallback_error:
                print(f"Error creating real user context: {fallback_error}")
            
            # 🔧 PLATFORM ADMIN FIX: If user is platform admin, create a minimal context
            if user_role == "admin":
                # Platform admins get a minimal context that allows them to access admin functions
                now = datetime.utcnow()
                
                # Use first available client for admin context
                try:
                    from app.models.client_account import ClientAccount, Engagement
                    
                    # Get first client for admin context
                    client_query = select(ClientAccount).where(
                        ClientAccount.is_active == True
                    ).limit(1)
                    
                    client_result = await db.execute(client_query)
                    first_client = client_result.scalar_one_or_none()
                    
                    if first_client:
                        # Get first engagement for this client
                        engagement_query = select(Engagement).where(
                            and_(
                                Engagement.client_account_id == first_client.id,
                                Engagement.is_active == True
                            )
                        ).limit(1)
                        
                        engagement_result = await db.execute(engagement_query)
                        first_engagement = engagement_result.scalar_one_or_none()
                        
                        if first_engagement:
                            # Create admin context from first available client/engagement
                            client_base = ClientBase(
                                id=str(first_client.id),
                                name=first_client.name,
                                description=first_client.description or f"Client: {first_client.name}",
                                created_at=first_client.created_at or now,
                                updated_at=first_client.updated_at or now
                            )
                            
                            engagement_base = EngagementBase(
                                id=str(first_engagement.id),
                                name=first_engagement.name,
                                description=first_engagement.description or f"Engagement: {first_engagement.name}",
                                client_id=str(first_client.id),
                                created_at=first_engagement.created_at or now,
                                updated_at=first_engagement.updated_at or now
                            )
                            
                            # Create a default session for this engagement
                            session_base = SessionBase(
                                id=str(first_engagement.id),  # Use engagement ID as session ID for now
                                name=f"Admin Session - {first_engagement.name}",
                                description=f"Admin session for {first_engagement.name}",
                                engagement_id=str(first_engagement.id),
                                is_default=True,
                                created_by=str(current_user.id),
                                created_at=now,
                                updated_at=now
                            )
                            
                            return UserContext(
                                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                                client=client_base,
                                engagement=engagement_base,
                                session=session_base,
                                available_sessions=[session_base]
                            )
                            
                except Exception as admin_context_error:
                    print(f"Error creating admin context: {admin_context_error}")
                
                # If no clients/engagements exist, create minimal admin-only context
                return UserContext(
                    user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                    client=None,
                    engagement=None,
                    session=None,
                    available_sessions=[]
                )
            
            # If all else fails for regular users, raise an error
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accessible clients or engagements found for user. Please contact administrator."
            )
    except Exception as e:
        print(f"Context error: {e}")
        # Fallback to demo client
        return {
            "id": str(DEMO_CLIENT_ID),
            "name": "Democorp",
            "is_demo": True
        }

@router.get("/context")
async def get_context(
    flow_id: Optional[str] = Query(None, description="Discovery Flow ID"),
    db: AsyncSession = Depends(get_db),
    context: dict = Depends(get_current_context)
):
    """
    Get context information for discovery flows.
    Updated to use V2 Discovery Flow architecture with flow_id.
    """
    try:
        logger.info(f"📋 Getting context for flow: {flow_id}")
        
        # Initialize V2 services
        flow_repo = DiscoveryFlowRepository(db, context.get('client_account_id'))
        flow_service = DiscoveryFlowService(flow_repo)
        
        # Base context
        context_data = {
            "client_account_id": context.get('client_account_id'),
            "engagement_id": context.get('engagement_id'),
            "user_id": context.get('user_id'),
            "api_version": "v2",
            "discovery_flow_architecture": "V2 - CrewAI Flow Based"
        }
        
        # Add flow-specific context if flow_id provided
        if flow_id:
            flow = await flow_service.get_flow(flow_id)
            if flow:
                flow_summary = await flow_service.get_flow_summary(flow_id)
                context_data.update({
                    "flow_id": flow.flow_id,
                    "current_phase": flow.current_phase,
                    "progress_percentage": flow.progress_percentage,
                    "status": flow.status,
                    "flow_summary": flow_summary,
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None
                })
            else:
                context_data.update({
                    "flow_error": f"Flow not found: {flow_id}",
                    "suggestion": "Check flow_id or use /api/v2/discovery-flows/ to list available flows"
                })
        
        # Add flow statistics
        flow_stats = await flow_service.get_flow_statistics()
        context_data["flow_statistics"] = flow_stats
        
        return {
            "success": True,
            "context": context_data,
            "migration_info": {
                "message": "Context now uses V2 Discovery Flow architecture",
                "changes": [
                    "session_id replaced with flow_id",
                    "Enhanced flow tracking and statistics",
                    "CrewAI Flow integration",
                    "Multi-tenant isolation"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get context: {e}")
        return {
            "success": False,
            "error": str(e),
            "context": {
                "client_account_id": context.get('client_account_id'),
                "engagement_id": context.get('engagement_id'),
                "user_id": context.get('user_id'),
                "api_version": "v2",
                "error_message": "Failed to get context - using fallback"
            }
        }

@router.post("/context/validate")
async def validate_context(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    context: dict = Depends(get_current_context)
):
    """
    Validate context for discovery operations.
    Updated to use V2 Discovery Flow patterns.
    """
    try:
        logger.info("🔍 Validating context for V2 Discovery Flow")
        
        # Initialize V2 services
        flow_repo = DiscoveryFlowRepository(db, context.get('client_account_id'))
        flow_service = DiscoveryFlowService(flow_repo)
        
        # Validate required context fields
        required_fields = ['client_account_id', 'engagement_id', 'user_id']
        missing_fields = [field for field in required_fields if not context.get(field)]
        
        if missing_fields:
            return {
                "success": False,
                "valid": False,
                "missing_fields": missing_fields,
                "message": "Context validation failed - missing required fields"
            }
        
        # Validate flow_id if provided
        flow_id = request.get('flow_id')
        flow_validation = {"flow_id_provided": bool(flow_id)}
        
        if flow_id:
            flow = await flow_service.get_flow(flow_id)
            flow_validation.update({
                "flow_exists": bool(flow),
                "flow_status": flow.status if flow else None,
                "flow_phase": flow.current_phase if flow else None
            })
        
        # Get context statistics
        flow_stats = await flow_service.get_flow_statistics()
        
        return {
            "success": True,
            "valid": True,
            "context_validation": {
                "client_account_id": bool(context.get('client_account_id')),
                "engagement_id": bool(context.get('engagement_id')),
                "user_id": bool(context.get('user_id')),
                "multi_tenant_isolation": True
            },
            "flow_validation": flow_validation,
            "flow_statistics": flow_stats,
            "api_version": "v2",
            "message": "Context validation successful"
        }
        
    except Exception as e:
        logger.error(f"❌ Context validation failed: {e}")
        return {
            "success": False,
            "valid": False,
            "error": str(e),
            "message": "Context validation failed"
        }
