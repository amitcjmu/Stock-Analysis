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
    description="Get complete context for the current user including client, engagement, and session."
)
async def get_user_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserContext:
    """Get complete context for the current user"""
    try:
        service = UserService(db)
        return await service.get_user_context(current_user)
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
    "/session/switch",
    summary="Switch user session",
    description="Switch the current user's active session."
)
async def switch_session(
    request: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Switch the current user's active session.
    
    This updates the user's context and returns the new session information.
    """
    engagement_id = request.get("engagement_id")
    
    if not engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="engagement_id is required"
        )
    
    try:
        # Create repository and service instances
        flow_repository = DiscoveryFlowRepository(db, client_account_id="11111111-1111-1111-1111-111111111111", engagement_id=engagement_id, user_id=current_user)
        flow_service = DiscoveryFlowService(flow_repository)
        
        # Get flows for the new engagement
        flows = await flow_service.get_flows_by_engagement(engagement_id)
        
        # Update user defaults
        service = UserService(db)
        await service.update_user_defaults(
            current_user,
            engagement_id=engagement_id
        )
        
        return {
            "status": "success",
            "message": "Session switched successfully",
            "engagement_id": engagement_id,
            "active_flows": len(flows) if flows else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error switching session: {str(e)}"
        )