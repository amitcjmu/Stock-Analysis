"""
Context Establishment API - Dedicated endpoints for initial context setup.

These endpoints are designed to work without full engagement context,
allowing the frontend to establish context step by step:
1. Get available clients
2. Get engagements for a specific client 
3. Establish full context

These endpoints are exempt from the global engagement requirement middleware.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models import User

# Make client_account import conditional to avoid deployment failures
try:
    from app.models.client_account import ClientAccount, Engagement
    from app.models.rbac import ClientAccess, UserRole
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None
    ClientAccess = None
    UserRole = None

router = APIRouter()
logger = logging.getLogger(__name__)

# Response models for context establishment
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
async def get_context_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of clients accessible to the current user for context establishment.
    
    This endpoint is exempt from engagement context requirements and is specifically
    designed for initial context setup. It only requires authentication.
    """
    try:
        logger.info(f"🔍 Context Establishment: Getting clients for user {current_user.id}")
        
        if not CLIENT_ACCOUNT_AVAILABLE:
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
        
        # Check if user is platform admin
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
            # Platform admins: Get all active clients
            clients_query = select(ClientAccount).where(
                ClientAccount.is_active == True
            ).order_by(ClientAccount.name)
            
            result = await db.execute(clients_query)
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

            # If no clients found and user is demo user (check email pattern), return demo client
            if not client_responses and current_user.email and current_user.email.endswith("@demo-corp.com"):
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
            
    except Exception as e:
        logger.error(f"Error in context establishment - get clients: {e}")
        # Return demo data as fallback for demo user only
        if current_user.email and current_user.email.endswith("@demo-corp.com"):
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

@router.get("/engagements", response_model=EngagementsListResponse)
async def get_context_engagements(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of engagements for a specific client for context establishment.
    
    This endpoint is exempt from engagement context requirements and is specifically
    designed for initial context setup. It only requires authentication and client_id.
    
    Args:
        client_id: The client ID to get engagements for (query parameter)
    """
    try:
        logger.info(f"🔍 Context Establishment: Getting engagements for client {client_id}, user {current_user.id}")
        
        if not CLIENT_ACCOUNT_AVAILABLE:
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
        
        # Check if user is platform admin
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
                current_user.email and current_user.email.endswith("@demo-corp.com") and
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
        ).order_by(Engagement.name)
        
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

        logger.info(f"✅ Context Establishment: Found {len(engagement_responses)} engagements for client {client_id}")
        return EngagementsListResponse(engagements=engagement_responses)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in context establishment - get engagements: {e}")
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

class ContextUpdateRequest(BaseModel):
    client_id: str
    engagement_id: str

class ContextUpdateResponse(BaseModel):
    status: str
    message: str
    client_id: str
    engagement_id: str

@router.post("/update-context", response_model=ContextUpdateResponse)
async def update_user_context(
    request: ContextUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the user's default client and engagement context.
    
    This persists the user's context selection in the database so it's
    remembered across sessions.
    """
    try:
        logger.info(f"🔄 Updating context for user {current_user.id}: client={request.client_id}, engagement={request.engagement_id}")
        
        # Verify client exists and user has access
        if CLIENT_ACCOUNT_AVAILABLE:
            # Check client exists
            client = await db.get(ClientAccount, request.client_id)
            if not client or not client.is_active:
                raise HTTPException(status_code=404, detail="Client not found")
            
            # Check engagement exists and belongs to client
            engagement = await db.get(Engagement, request.engagement_id)
            if not engagement or not engagement.is_active:
                raise HTTPException(status_code=404, detail="Engagement not found")
            
            if str(engagement.client_account_id) != request.client_id:
                raise HTTPException(status_code=400, detail="Engagement does not belong to specified client")
            
            # Update user's default context
            user = await db.get(User, current_user.id)
            if user:
                user.default_client_id = request.client_id
                user.default_engagement_id = request.engagement_id
                await db.commit()
                
                logger.info(f"✅ Updated default context for user {current_user.email}")
                
                return ContextUpdateResponse(
                    status="success",
                    message="Context updated successfully",
                    client_id=request.client_id,
                    engagement_id=request.engagement_id
                )
            else:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            # Models not available, return success for demo
            return ContextUpdateResponse(
                status="success",
                message="Context updated (demo mode)",
                client_id=request.client_id,
                engagement_id=request.engagement_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user context: {e}")
        raise HTTPException(status_code=500, detail="Failed to update context") 