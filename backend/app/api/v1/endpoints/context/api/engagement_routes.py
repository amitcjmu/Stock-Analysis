"""
Engagement Routes

API endpoints for engagement-related operations.
"""

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models import User
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.context_schemas import EngagementsListResponse
from ..services.client_service import ClientService
from ..services.engagement_service import EngagementService

router = APIRouter()


@router.get("/clients/{client_id}/engagements", response_model=EngagementsListResponse)
async def get_client_engagements(
    client_id: str = Path(..., description="The client ID to get engagements for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EngagementsListResponse:
    """
    Get list of engagements for a specific client.

    Returns all engagements for the specified client that the user has access to.
    """
    try:
        # Get user role
        client_service = ClientService(db)
        user_role, _ = await client_service.get_user_role(current_user.id)
        is_platform_admin = user_role == "platform_admin"

        # Get engagements
        service = EngagementService(db)
        return await service.get_client_engagements(
            client_id, current_user.id, is_platform_admin
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching engagements: {str(e)}",
        )
