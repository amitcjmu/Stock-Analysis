"""
Engagement Management API
Admin endpoints for managing engagements.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.engagement import Engagement, EngagementSession
import uuid
import logging
from app.api.v1.admin.engagement_management_handlers.engagement_crud_handler import EngagementCRUDHandler
from app.schemas.admin_schemas import PaginatedResponse, AdminPaginationParams, EngagementDashboardStats, EngagementCreate, EngagementResponse
from app.core.database import get_db
from app.core.rbac_middleware import require_admin_access
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import get_current_user_id

logger = logging.getLogger(__name__)

# Create the router with proper configuration
router = APIRouter(
    tags=["Admin - Engagement Management"]
)

# Define the API endpoints with their routes

@router.post("/", response_model=EngagementResponse, status_code=status.HTTP_201_CREATED)
async def create_engagement(
    engagement_data: EngagementCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Create a new engagement.
    
    Required fields:
    - engagement_name: str
    - client_account_id: UUID
    - engagement_type: str (e.g., 'migration', 'assessment')
    - status: str (e.g., 'planning', 'active', 'completed')
    - start_date: date (optional)
    - end_date: date (optional)
    - description: str (optional)
    """
    try:
        # Convert Pydantic model to dict and remove unset fields
        engagement_dict = engagement_data.dict(exclude_unset=True)
        
        # Create the engagement
        result = await EngagementCRUDHandler.create_engagement(
            db=db,
            engagement_data=engagement_dict,
            created_by=current_user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating engagement: {e}", exc_info=True)
        if hasattr(e, 'status_code') and hasattr(e, 'detail'):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create engagement: {str(e)}"
        )

@router.get("/", response_model=PaginatedResponse)
async def list_engagements(
    client_account_id: Optional[str] = Query(None, description="Client account ID to filter by"),
    pagination: AdminPaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """List engagements for a client or all engagements if no client specified."""
    # Don't force a specific client ID - let it be None for "All Clients"
    
    paginated_result = await EngagementCRUDHandler.list_engagements(
        db=db,
        client_account_id=client_account_id,  # Pass None if not specified
        pagination=pagination.dict()
    )
    return PaginatedResponse(**paginated_result)

@router.get("/{engagement_id}/sessions", response_model=List[EngagementSession])
async def list_engagement_sessions(
    engagement_id: str
):
    """List sessions for an engagement."""
    # Demo implementation
    return [
        EngagementSession(id=str(uuid.uuid4()), name="Q1 Assessment", start_date=datetime.now()),
        EngagementSession(id=str(uuid.uuid4()), name="Q2 Migration", start_date=datetime.now())
    ]

@router.get("/dashboard/stats", response_model=EngagementDashboardStats)
async def get_engagement_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: str = Depends(require_admin_access)
):
    """Get engagement dashboard statistics."""
    try:
        stats_data = await EngagementCRUDHandler.get_dashboard_stats(db)
        return EngagementDashboardStats(**stats_data)
    except Exception as e:
        logger.error(f"Error getting engagement dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

# Export the router for use in the API
export_router = router