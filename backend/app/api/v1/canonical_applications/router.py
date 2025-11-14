"""
Canonical Applications API Router.

Endpoints for listing and querying canonical applications with multi-tenant isolation.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.api_tags import APITags
from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.asset.models import Asset

# Import bulk mapping router
from . import bulk_mapping

logger = logging.getLogger(__name__)

router = APIRouter()

# Include bulk mapping endpoints
router.include_router(bulk_mapping.router, tags=[APITags.CANONICAL_APPLICATIONS])


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
    List canonical applications with tenant scoping, search, pagination, and readiness metadata.

    Returns paginated list of canonical applications for the current engagement.
    Supports case-insensitive search across canonical_name and normalized_name.

    Multi-tenant isolation: All queries scoped by client_account_id and engagement_id.

    **NEW**: Each application now includes assessment readiness information:
    - linked_asset_count: Total assets linked to this canonical application
    - ready_asset_count: Assets with discovery_status="completed" AND assessment_readiness="ready"
    - not_ready_asset_count: Assets not meeting readiness criteria
    - readiness_status: "ready" (all ready) | "partial" (some ready) | "not_ready" (none ready)
    - readiness_blockers: List of issues preventing readiness
    - readiness_recommendations: Suggested actions to achieve readiness

    Query Parameters:
        - search: Optional substring search (canonical_name or normalized_name)
        - page: Page number starting from 1
        - page_size: Items per page (1-100, default 50)

    Returns:
        {
            "applications": [
                {
                    "id": "uuid",
                    "canonical_name": "MyApp",
                    "linked_asset_count": 5,
                    "ready_asset_count": 3,
                    "not_ready_asset_count": 2,
                    "readiness_status": "partial",
                    "readiness_blockers": ["2 asset(s) not ready for assessment"],
                    "readiness_recommendations": ["Complete discovery for remaining assets"],
                    ...
                }
            ],
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

        # Build readiness metadata for all applications
        app_ids = [app.id for app in applications]

        # Query to get asset readiness stats per canonical app
        # JOIN: CollectionFlowApplication -> Asset
        # GROUP BY: canonical_application_id
        # COUNT: total assets, ready assets
        readiness_query = (
            select(
                CollectionFlowApplication.canonical_application_id,
                func.count(Asset.id).label("linked_asset_count"),
                func.sum(
                    case(
                        (
                            and_(
                                Asset.discovery_status == "completed",
                                Asset.assessment_readiness == "ready",
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("ready_asset_count"),
            )
            .join(
                Asset,
                and_(
                    Asset.id == CollectionFlowApplication.asset_id,
                    Asset.client_account_id == client_account_id,
                    Asset.engagement_id == engagement_id,
                ),
            )
            .where(
                CollectionFlowApplication.canonical_application_id.in_(app_ids),
                CollectionFlowApplication.client_account_id == client_account_id,
                CollectionFlowApplication.engagement_id == engagement_id,
            )
            .group_by(CollectionFlowApplication.canonical_application_id)
        )

        readiness_result = await db.execute(readiness_query)
        readiness_rows = readiness_result.all()

        # Build readiness map: canonical_app_id -> {linked_count, ready_count}
        readiness_map = {
            row.canonical_application_id: {
                "linked_asset_count": row.linked_asset_count or 0,
                "ready_asset_count": row.ready_asset_count or 0,
            }
            for row in readiness_rows
        }

        # Enhance application dicts with readiness metadata
        applications_data = []
        for app in applications:
            app_dict = app.to_dict()

            # Get readiness stats (default to 0 if no assets linked)
            readiness_stats = readiness_map.get(
                app.id,
                {
                    "linked_asset_count": 0,
                    "ready_asset_count": 0,
                },
            )

            linked_count = readiness_stats["linked_asset_count"]
            ready_count = readiness_stats["ready_asset_count"]
            not_ready_count = linked_count - ready_count

            # Determine overall readiness status
            if linked_count == 0:
                readiness_status = "not_ready"  # No assets = not ready
                blockers = ["No assets linked to this application"]
                recommendations = [
                    "Complete Collection Flow to gather application data"
                ]
            elif ready_count == linked_count:
                readiness_status = "ready"  # All assets ready
                blockers = []
                recommendations = []
            elif ready_count > 0:
                readiness_status = "partial"  # Some ready, some not
                blockers = [f"{not_ready_count} asset(s) not ready for assessment"]
                recommendations = [
                    "Complete discovery and data collection for remaining assets"
                ]
            else:
                readiness_status = "not_ready"  # None ready
                blockers = ["Assets require discovery completion and data collection"]
                recommendations = ["Run Collection Flow to gather missing data"]

            # Add readiness fields to application dict
            app_dict.update(
                {
                    "linked_asset_count": linked_count,
                    "ready_asset_count": ready_count,
                    "not_ready_asset_count": not_ready_count,
                    "readiness_status": readiness_status,  # "ready" | "partial" | "not_ready"
                    "readiness_blockers": blockers,
                    "readiness_recommendations": recommendations,
                }
            )

            applications_data.append(app_dict)

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
