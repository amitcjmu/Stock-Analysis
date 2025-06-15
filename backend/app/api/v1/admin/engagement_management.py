"""
Engagement Management API
Admin endpoints for managing engagements.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from app.schemas.engagement import Engagement, EngagementSession
import uuid
import logging
from app.api.v1.admin.engagement_management_handlers.engagement_crud_handler import EngagementCRUDHandler
from app.schemas.admin_schemas import PaginatedResponse, AdminPaginationParams, EngagementDashboardStats
from app.core.database import get_db
from app.core.rbac_middleware import require_admin_access
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Engagement Management"])

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