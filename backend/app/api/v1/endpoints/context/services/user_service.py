"""
User Service

Business logic for user context operations.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.models import User
from app.models.client_account import ClientAccount, Engagement
from app.models.rbac import UserRole, ClientAccess
from app.schemas.context import UserContext, ClientBase, EngagementBase, SessionBase
from app.schemas.flow import FlowBase
from .client_service import (
    DEMO_USER_ID, DEMO_CLIENT_ID, DEMO_ENGAGEMENT_ID, DEMO_SESSION_ID
)

logger = logging.getLogger(__name__)


class UserService:
    """Service for user context business logic"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_context_with_flows(self, current_user: User) -> UserContext:
        """
        Get complete context for the current user including active flows.
        This is the new flow-based method that replaces session-based context.
        """
        # Get the basic user context first
        basic_context = await self.get_user_context(current_user)
        
        # Get active flows for the user's engagement
        active_flows = []
        primary_flow_id = None
        
        if basic_context.engagement:
            try:
                # Import here to avoid circular dependencies
                from app.services.master_flow_orchestrator import MasterFlowOrchestrator
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as db:
                    orchestrator = MasterFlowOrchestrator(db)
                    
                    # Get active flows for the engagement
                    flows = await orchestrator.list_flows_by_engagement(
                        engagement_id=basic_context.engagement.id
                    )
                    
                    for flow in flows:
                        if flow.get("status") in ["active", "in_progress", "pending"]:
                            flow_info = FlowBase(
                                id=flow["id"],
                                name=flow["name"],
                                flow_type=flow["flow_type"],
                                status=flow["status"],
                                engagement_id=flow["engagement_id"],
                                created_by=flow.get("created_by", current_user.id),
                                metadata=flow.get("metadata", {})
                            )
                            active_flows.append(flow_info)
                            
                            # Set primary flow (first active discovery flow)
                            if flow["flow_type"] == "discovery" and not primary_flow_id:
                                primary_flow_id = flow["id"]
                
            except Exception as e:
                logger.warning(f"Failed to get active flows for user {current_user.id}: {e}")
                # Continue with empty flows list
        
        # Create enhanced user context with flows
        return UserContext(
            user=basic_context.user,
            client=basic_context.client,
            engagement=basic_context.engagement,
            active_flows=active_flows,
            current_flow=active_flows[0] if active_flows else None
        )

    async def get_user_context(self, current_user: User) -> UserContext:
        """
        Get complete context for the current user.
        
        Platform admins: Get access to all clients/engagements, with preference for defaults
        Regular users: Get access based on their client associations
        """
        now = datetime.utcnow()
        
        # Determine user role and admin status
        is_platform_admin, user_role = await self._get_user_admin_status(current_user.id)
        
        logger.info(f"Context for user {current_user.id}: admin={is_platform_admin}, role={user_role}")
        
        # Handle platform admin access
        if is_platform_admin:
            context = await self._get_platform_admin_context(current_user, user_role, now)
            if context:
                return context
        
        # Handle regular user access
        else:
            context = await self._get_regular_user_context(current_user, user_role, now)
            if context:
                return context
            
            # Check for demo user special case
            if str(current_user.id) == str(DEMO_USER_ID):
                return self._create_demo_context(current_user, user_role, now)
        
        # If all else fails, return minimal context or raise error
        if is_platform_admin:
            # Platform admins get minimal context
            return UserContext(
                user={"id": str(current_user.id), "email": current_user.email, "role": user_role},
                client=None,
                engagement=None,
                active_flows=[],
                current_flow=None
            )
        else:
            # Regular users get demo context as fallback
            return self._create_demo_context(current_user, user_role, now)
    
    async def _get_user_admin_status(self, user_id: UUID) -> tuple[bool, str]:
        """Get user admin status and role"""
        role_query = select(UserRole).where(
            and_(
                UserRole.user_id == str(user_id),
                UserRole.is_active == True
            )
        ).limit(1)
        
        role_result = await self.db.execute(role_query)
        user_role_obj = role_result.scalar_one_or_none()
        
        is_platform_admin = (
            user_role_obj and 
            user_role_obj.role_type == 'platform_admin'
        )
        
        user_role = "admin" if is_platform_admin else (
            user_role_obj.role_type if user_role_obj else "analyst"
        )
        
        return is_platform_admin, user_role
    
    async def _get_platform_admin_context(
        self, 
        current_user: User, 
        user_role: str, 
        now: datetime
    ) -> Optional[UserContext]:
        """Get context for platform admin"""
        logger.info("Platform admin detected - providing access to all clients/engagements")
        
        target_client = None
        target_engagement = None
        
        # Try to use user's default client if set
        if current_user.default_client_id:
            target_client = await self._get_client_by_id(current_user.default_client_id)
        
        # If no default client, use first available
        if not target_client:
            target_client = await self._get_first_active_client()
        
        if target_client:
            # Try to use user's default engagement if set
            if current_user.default_engagement_id:
                target_engagement = await self._get_engagement_by_id(
                    current_user.default_engagement_id, 
                    target_client.id
                )
            
            # If no default engagement, use first available
            if not target_engagement:
                target_engagement = await self._get_first_active_engagement(target_client.id)
            
            if target_engagement:
                return self._create_context_from_entities(
                    current_user, user_role, target_client, target_engagement, now, is_admin=True
                )
        
        return None
    
    async def _get_regular_user_context(
        self, 
        current_user: User, 
        user_role: str, 
        now: datetime
    ) -> Optional[UserContext]:
        """Get context for regular user based on client access"""
        logger.info("Regular user - checking client associations")
        
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
        
        access_result = await self.db.execute(access_query)
        client_access_data = access_result.first()
        
        if client_access_data:
            client_access_obj, client = client_access_data
            logger.info(f"Found client access: {client.name}")
            
            # Get first engagement for this client
            engagement = await self._get_first_active_engagement(client.id)
            
            if engagement:
                return self._create_context_from_entities(
                    current_user, user_role, client, engagement, now, is_admin=False
                )
        
        return None
    
    async def _get_client_by_id(self, client_id: UUID) -> Optional[ClientAccount]:
        """Get active client by ID"""
        query = select(ClientAccount).where(
            and_(
                ClientAccount.id == client_id,
                ClientAccount.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_first_active_client(self) -> Optional[ClientAccount]:
        """Get first active client"""
        query = select(ClientAccount).where(
            ClientAccount.is_active == True
        ).order_by(ClientAccount.name).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_engagement_by_id(
        self, 
        engagement_id: UUID, 
        client_id: UUID
    ) -> Optional[Engagement]:
        """Get active engagement by ID for specific client"""
        query = select(Engagement).where(
            and_(
                Engagement.id == engagement_id,
                Engagement.client_account_id == client_id,
                Engagement.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_first_active_engagement(self, client_id: UUID) -> Optional[Engagement]:
        """Get first active engagement for client"""
        query = select(Engagement).where(
            and_(
                Engagement.client_account_id == client_id,
                Engagement.is_active == True
            )
        ).order_by(Engagement.name).limit(1)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _create_context_from_entities(
        self,
        user: User,
        user_role: str,
        client: ClientAccount,
        engagement: Engagement,
        now: datetime,
        is_admin: bool = False
    ) -> UserContext:
        """Create UserContext from database entities"""
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
        
        logger.info(f"Context created: {client.name} / {engagement.name}")
        return UserContext(
            user={"id": str(user.id), "email": user.email, "role": user_role},
            client=client_base,
            engagement=engagement_base,
            active_flows=[],  # Will be populated by get_user_context_with_flows
            current_flow=None
        )
    
    def _create_demo_context(self, user: User, user_role: str, now: datetime) -> UserContext:
        """Create demo context"""
        logger.info("Creating demo context")
        
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
            created_by=str(user.id),
            created_at=now,
            updated_at=now
        )
        
        return UserContext(
            user={"id": str(user.id), "email": user.email, "role": user_role},
            client=demo_client,
            engagement=demo_engagement,
            active_flows=[],  # Will be populated by get_user_context_with_flows
            current_flow=None
        )
    
    async def update_user_defaults(
        self, 
        user: User,
        client_id: Optional[str] = None,
        engagement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user's default client and engagement"""
        updated_fields = {}
        
        try:
            # Build update query
            update_values = {}
            
            if client_id is not None:
                update_values['default_client_id'] = UUID(client_id) if client_id else None
                updated_fields['default_client_id'] = client_id
            
            if engagement_id is not None:
                update_values['default_engagement_id'] = UUID(engagement_id) if engagement_id else None
                updated_fields['default_engagement_id'] = engagement_id
            
            if update_values:
                stmt = update(User).where(User.id == user.id).values(**update_values)
                await self.db.execute(stmt)
                await self.db.commit()
                
                logger.info(f"Updated user defaults: {updated_fields}")
            
            return {
                "message": "User defaults updated successfully",
                "updated_fields": updated_fields
            }
            
        except Exception as e:
            logger.error(f"Error updating user defaults: {e}")
            await self.db.rollback()
            raise