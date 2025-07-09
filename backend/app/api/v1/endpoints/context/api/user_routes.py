"""
User Routes

API endpoints for user context operations.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.api.v1.auth.auth_utils import get_current_user
from app.schemas.context import UserContext
from app.services.discovery_flow_service import DiscoveryFlowService
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from ..services.user_service import UserService
from ..models.context_schemas import UpdateUserDefaultsRequest, UpdateUserDefaultsResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, session, and active flows."
)
async def get_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserContext:
    """Get complete context for the current user"""
    try:
        service = UserService(db)
        return await service.get_user_context_with_flows(current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user context: {str(e)}"
        )


@router.put(
    "/me/defaults",
    response_model=UpdateUserDefaultsResponse,
    summary="Update user default context",
    description="Update the user's default client and engagement preferences."
)
async def update_user_defaults(
    request: UpdateUserDefaultsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UpdateUserDefaultsResponse:
    """Update the user's default client and engagement preferences"""
    try:
        service = UserService(db)
        result = await service.update_user_defaults(
            current_user,
            request.client_id,
            request.engagement_id
        )
        return UpdateUserDefaultsResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user defaults: {str(e)}"
        )


@router.post(
    "/flow/activate",
    summary="Activate a flow",
    description="Activate a specific flow for the current user."
)
async def activate_flow(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Activate a specific flow for the current user.
    
    This sets the primary flow for the user and returns flow information.
    """
    flow_id = request.get("flow_id")
    
    if not flow_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="flow_id is required"
        )
    
    try:
        # Import here to avoid circular dependencies
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator
        
        # Initialize the orchestrator
        orchestrator = MasterFlowOrchestrator(db)
        
        # Get flow information
        flow_info = await orchestrator.get_flow_status(flow_id)
        
        if not flow_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow {flow_id} not found"
            )
        
        # Verify the user has access to this flow's engagement
        service = UserService(db)
        user_context = await service.get_user_context_with_flows(current_user)
        
        if (not user_context.engagement or 
            str(user_context.engagement.id) != str(flow_info.get("engagement_id"))):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this flow"
            )
        
        # Update user defaults to set primary flow
        # For now, we'll update the engagement_id to ensure proper context
        await service.update_user_defaults(
            current_user,
            engagement_id=str(flow_info.get("engagement_id"))
        )
        
        return {
            "status": "success",
            "message": "Flow activated successfully",
            "flow_id": flow_id,
            "flow_name": flow_info.get("name"),
            "flow_type": flow_info.get("flow_type"),
            "flow_status": flow_info.get("status"),
            "engagement_id": flow_info.get("engagement_id")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error activating flow: {str(e)}"
        )