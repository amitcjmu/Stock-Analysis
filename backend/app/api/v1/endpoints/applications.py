from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.asset.models import Asset

router = APIRouter()


# =============================================================================
# Response Models (snake_case per CLAUDE.md)
# =============================================================================


class ApplicationResponse(BaseModel):
    """Response model for application data (uses snake_case)"""

    id: str = Field(..., description="Asset UUID as string")
    application_name: Optional[str] = Field(None, description="Application name")
    asset_name: Optional[str] = Field(None, description="Asset display name")
    six_r_strategy: Optional[str] = Field(None, description="6R migration strategy")
    tech_stack: Optional[str] = Field(None, description="Technology stack")
    complexity_score: Optional[float] = Field(
        None, description="Assessment readiness score (0-100)"
    )
    asset_type: Optional[str] = Field(None, description="Asset type")

    class Config:
        from_attributes = True


class ApplicationsListResponse(BaseModel):
    """Paginated response for applications list"""

    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/applications", response_model=ApplicationsListResponse)
async def get_applications(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by application/asset name"),
):
    """
    Fetch applications from Asset table with pagination and search.

    Returns assets that have application_name populated, suitable for
    Planning Flow initialization wizard.

    Multi-tenant scoped by client_account_id and engagement_id per CLAUDE.md.
    """
    # Build base query with tenant scoping (REQUIRED per CLAUDE.md)
    query = select(Asset).where(
        Asset.client_account_id == context.client_account_id,
        Asset.engagement_id == context.engagement_id,
        # Only assets with application_name (applications, not infrastructure)
        Asset.application_name.isnot(None),
        Asset.application_name != "",
    )

    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Asset.application_name.ilike(search_term),
                Asset.asset_name.ilike(search_term),
            )
        )

    # Order by application name for consistent results
    query = query.order_by(Asset.application_name)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    assets = result.scalars().all()

    # Transform to response format
    applications = [
        ApplicationResponse(
            id=str(asset.id),
            application_name=asset.application_name,
            asset_name=asset.asset_name,
            six_r_strategy=asset.six_r_strategy,
            tech_stack=asset.technology_stack,
            complexity_score=asset.assessment_readiness_score,
            asset_type=asset.asset_type,
        )
        for asset in assets
    ]

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ApplicationsListResponse(
        applications=applications,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
