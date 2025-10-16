"""
Canonical Applications API Router.

Endpoints for listing and querying canonical applications with multi-tenant isolation.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.canonical_applications import CanonicalApplication

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def list_canonical_applications(
    search: Optional[str] = Query(
        None,
        description="Search query for application names (case-insensitive substring match)",
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    List canonical applications with tenant scoping, search, and pagination.

    Returns paginated list of canonical applications for the current engagement.
    Supports case-insensitive search across canonical_name and normalized_name.

    Multi-tenant isolation: All queries scoped by client_account_id and engagement_id.

    Query Parameters:
        - search: Optional substring search (canonical_name or normalized_name)
        - page: Page number starting from 1
        - page_size: Items per page (1-100, default 50)

    Returns:
        {
            "applications": [...],
            "total": int,
            "page": int,
            "page_size": int,
            "total_pages": int
        }
    """
    try:
        # Convert context IDs to UUID
        client_account_id = (
            UUID(context.client_account_id)
            if isinstance(context.client_account_id, str)
            else context.client_account_id
        )
        engagement_id = (
            UUID(context.engagement_id)
            if isinstance(context.engagement_id, str)
            else context.engagement_id
        )

        # Base query with tenant scoping (CRITICAL for security)
        base_query = select(CanonicalApplication).where(
            CanonicalApplication.client_account_id == client_account_id,
            CanonicalApplication.engagement_id == engagement_id,
        )

        # Apply search filter if provided
        if search and search.strip():
            search_term = f"%{search.strip().lower()}%"
            base_query = base_query.where(
                or_(
                    func.lower(CanonicalApplication.canonical_name).like(search_term),
                    func.lower(CanonicalApplication.normalized_name).like(search_term),
                )
            )

        # Count total matching records
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        offset = (page - 1) * page_size

        # Fetch paginated results, ordered by usage and name
        query = (
            base_query.order_by(
                CanonicalApplication.usage_count.desc(),
                CanonicalApplication.canonical_name.asc(),
            )
            .limit(page_size)
            .offset(offset)
        )

        result = await db.execute(query)
        applications = result.scalars().all()

        # Convert to dict format
        applications_data = [app.to_dict() for app in applications]

        return {
            "applications": applications_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    except Exception as e:
        logger.error(f"Failed to list canonical applications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve canonical applications: {str(e)}",
        )
