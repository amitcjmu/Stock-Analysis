"""
Client Service

Business logic for client-related operations.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import User
from app.models.client_account import ClientAccount, Engagement
from app.models.rbac import UserRole, ClientAccess
from app.schemas.context import UserContext, ClientBase, EngagementBase, SessionBase
from ..models.context_schemas import ClientResponse, ClientsListResponse

logger = logging.getLogger(__name__)

# Demo constants
DEMO_USER_ID = UUID("44444444-4444-4444-4444-444444444444")
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
DEMO_SESSION_ID = UUID("33333333-3333-3333-3333-333333333333")


class ClientService:
    """Service for client-related business logic"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_role(self, user_id: UUID) -> tuple[str, Optional[str]]:
        """
        Get user's role from UserRole table.
        
        Returns:
            Tuple of (effective_role, actual_role_type)
        """
        user_role = "user"  # Default role
        actual_role_type = None
        
        try:
            roles_query = select(UserRole).where(
                and_(UserRole.user_id == user_id, UserRole.is_active == True)
            )
            roles_result = await self.db.execute(roles_query)
            user_roles = roles_result.scalars().all()
            
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
                user_role = actual_role_type
        except Exception as e:
            logger.error(f"Error determining user role: {e}")
        
        return user_role, actual_role_type
    
    def create_demo_context(self, user_id: str, user_email: str, user_role: str) -> UserContext:
        """Create demo context for demo user"""
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
            user={"id": user_id, "email": user_email, "role": user_role},
            client=demo_client,
            engagement=demo_engagement,
            session=demo_session,
            available_sessions=[demo_session]
        )
    
    async def get_user_context_from_access(self, user: User, user_role: str) -> Optional[UserContext]:
        """Get user context from their client access"""
        try:
            # Get user's first accessible client
            access_query = select(ClientAccess, ClientAccount).join(
                ClientAccount, ClientAccess.client_account_id == ClientAccount.id
            ).where(
                and_(
                    ClientAccess.user_profile_id == str(user.id),
                    ClientAccess.is_active == True,
                    ClientAccount.is_active == True
                )
            ).limit(1)
            
            access_result = await self.db.execute(access_query)
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
                
                engagement_result = await self.db.execute(engagement_query)
                engagement = engagement_result.scalar_one_or_none()
                
                if engagement:
                    return self._create_context_from_client_engagement(
                        user, user_role, client, engagement
                    )
        except Exception as e:
            logger.error(f"Error creating real user context: {e}")
        
        return None
    
    async def get_admin_context(self, user: User, user_role: str) -> Optional[UserContext]:
        """Get context for platform admin"""
        try:
            # Get first client for admin context
            client_query = select(ClientAccount).where(
                ClientAccount.is_active == True
            ).limit(1)
            
            client_result = await self.db.execute(client_query)
            first_client = client_result.scalar_one_or_none()
            
            if first_client:
                # Get first engagement for this client
                engagement_query = select(Engagement).where(
                    and_(
                        Engagement.client_account_id == first_client.id,
                        Engagement.is_active == True
                    )
                ).limit(1)
                
                engagement_result = await self.db.execute(engagement_query)
                first_engagement = engagement_result.scalar_one_or_none()
                
                if first_engagement:
                    return self._create_context_from_client_engagement(
                        user, user_role, first_client, first_engagement, is_admin=True
                    )
        except Exception as e:
            logger.error(f"Error creating admin context: {e}")
        
        # Return minimal admin context if no clients exist
        return UserContext(
            user={"id": str(user.id), "email": user.email, "role": user_role},
            client=None,
            engagement=None,
            session=None,
            available_sessions=[]
        )
    
    def _create_context_from_client_engagement(
        self, 
        user: User, 
        user_role: str, 
        client: ClientAccount, 
        engagement: Engagement,
        is_admin: bool = False
    ) -> UserContext:
        """Create user context from client and engagement"""
        now = datetime.utcnow()
        
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
        session_type = "Admin Session" if is_admin else "Default Session"
        session_base = SessionBase(
            id=str(engagement.id),  # Use engagement ID as session ID for now
            name=f"{session_type} - {engagement.name}",
            description=f"{session_type.lower()} for {engagement.name}",
            engagement_id=str(engagement.id),
            is_default=True,
            created_by=str(user.id),
            created_at=now,
            updated_at=now
        )
        
        return UserContext(
            user={"id": str(user.id), "email": user.email, "role": user_role},
            client=client_base,
            engagement=engagement_base,
            session=session_base,
            available_sessions=[session_base]
        )
    
    async def get_user_clients(self, user_id: UUID, is_platform_admin: bool) -> ClientsListResponse:
        """Get clients accessible to user"""
        clients = []
        
        try:
            if is_platform_admin:
                # Platform admins can see all clients
                query = select(ClientAccount).where(ClientAccount.is_active == True)
                result = await self.db.execute(query)
                client_accounts = result.scalars().all()
                
                clients = [
                    ClientResponse(
                        id=str(client.id),
                        name=client.name,
                        industry=client.industry,
                        company_size=client.company_size,
                        status="active" if client.is_active else "inactive"
                    )
                    for client in client_accounts
                ]
            else:
                # Regular users see only their accessible clients
                query = select(ClientAccount).join(
                    ClientAccess, ClientAccess.client_account_id == ClientAccount.id
                ).where(
                    and_(
                        ClientAccess.user_profile_id == str(user_id),
                        ClientAccess.is_active == True,
                        ClientAccount.is_active == True
                    )
                )
                result = await self.db.execute(query)
                client_accounts = result.scalars().all()
                
                clients = [
                    ClientResponse(
                        id=str(client.id),
                        name=client.name,
                        industry=client.industry,
                        company_size=client.company_size,
                        status="active"
                    )
                    for client in client_accounts
                ]
        except Exception as e:
            logger.error(f"Error fetching user clients: {e}")
            # Return demo client as fallback
            clients = [
                ClientResponse(
                    id="11111111-1111-1111-1111-111111111111",
                    name="Democorp",
                    industry="Technology",
                    company_size="1000-5000",
                    status="active"
                )
            ]
        
        return ClientsListResponse(clients=clients)