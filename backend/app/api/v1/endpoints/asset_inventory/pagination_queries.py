"""
Database query functions for asset pagination endpoints.
Contains async database operations for fetching and summarizing assets.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.context import RequestContext
from app.models.asset import Asset


async def _get_assets_from_db(
    db: AsyncSession,
    context: RequestContext,
    page: int,
    page_size: int,
    flow_id: Optional[str] = None,
    search: Optional[str] = None,
    environment: Optional[str] = None,
    business_criticality: Optional[str] = None,
):
    """Fetch assets from database with pagination and filtering.

    Args:
        db: Database session
        context: Request context with tenant information
        page: Page number (1-indexed)
        page_size: Number of items per page
        flow_id: Optional discovery flow ID to filter assets
        search: Optional search term to filter by asset name (case-insensitive)
        environment: Optional environment filter
        business_criticality: Optional business criticality filter

    Returns:
        Tuple of (assets, total_items, total_pages, filter_conditions)
    """
    # Build filter conditions once (DRY principle)
    # SECURITY: Always enforce multi-tenancy - no platform admin bypass for regular users
    filter_conditions = [
        Asset.client_account_id == context.client_account_id,
        Asset.engagement_id == context.engagement_id,
        Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
    ]

    # Add flow_id filter if provided
    if flow_id:
        filter_conditions.append(Asset.discovery_flow_id == flow_id)

    # Add search filter if provided (case-insensitive name search)
    if search and search.strip():
        filter_conditions.append(Asset.name.ilike(f"%{search.strip()}%"))

    # Add environment filter if provided
    if environment:
        filter_conditions.append(Asset.environment == environment)

    # Add business_criticality filter if provided
    if business_criticality:
        filter_conditions.append(Asset.business_criticality == business_criticality)

    # Build base query with shared filter conditions
    query = (
        select(Asset)  # SKIP_TENANT_CHECK - Filters applied via filter_conditions list
        .where(*filter_conditions)
        .options(selectinload(Asset.eol_assessments), selectinload(Asset.contacts))
        .order_by(Asset.created_at.desc())
    )

    # Get total count with same filter conditions (ensures consistency)
    count_query = select(func.count()).select_from(Asset).where(*filter_conditions)

    count_result = await db.execute(count_query)
    total_items = count_result.scalar() or 0

    # Calculate pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    assets = result.scalars().all()

    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0

    return assets, total_items, total_pages, filter_conditions


async def _get_summary_stats_from_db(
    db: AsyncSession,
    filter_conditions: List,
    total_items: int,
) -> Dict[str, Any]:
    """Get summary statistics from database query (all assets, not just current page).

    Args:
        db: Database session
        filter_conditions: List of filter conditions to apply
        total_items: Total count of assets (already calculated, to avoid redundant query)
    """
    from sqlalchemy import case
    from sqlalchemy.sql.functions import coalesce

    summary_query = select(
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "application", 1), else_=0)),
            0,
        ).label("applications"),
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "server", 1), else_=0)), 0
        ).label("servers"),
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "database", 1), else_=0)), 0
        ).label("databases"),
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "component", 1), else_=0)), 0
        ).label("components"),
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "network", 1), else_=0)), 0
        ).label("network"),
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "storage", 1), else_=0)), 0
        ).label("storage"),
        coalesce(
            func.sum(
                case((func.lower(Asset.asset_type) == "security_group", 1), else_=0)
            ),
            0,
        ).label("security"),
        coalesce(
            func.sum(
                case((func.lower(Asset.asset_type) == "virtual_machine", 1), else_=0)
            ),
            0,
        ).label("virtualization"),
        coalesce(
            func.sum(case((func.lower(Asset.asset_type) == "container", 1), else_=0)), 0
        ).label("containers"),
        coalesce(
            func.sum(
                case((func.lower(Asset.asset_type) == "load_balancer", 1), else_=0)
            ),
            0,
        ).label("load_balancers"),
        coalesce(
            func.sum(
                case(
                    (
                        (Asset.asset_type.is_(None))
                        | (func.lower(Asset.asset_type).in_(["unknown", "other"])),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("unknown"),
        coalesce(func.sum(case((Asset.status == "discovered", 1), else_=0)), 0).label(
            "discovered"
        ),
        coalesce(func.sum(case((Asset.status == "pending", 1), else_=0)), 0).label(
            "pending"
        ),
    ).where(*filter_conditions)

    result = await db.execute(summary_query)
    row = result.first()

    if row is None:
        return {
            "total": total_items,
            "filtered": total_items,
            "applications": 0,
            "servers": 0,
            "databases": 0,
            "components": 0,
            "network": 0,
            "storage": 0,
            "security": 0,
            "virtualization": 0,
            "containers": 0,
            "load_balancers": 0,
            "unknown": 0,
            "discovered": 0,
            "pending": 0,
            "device_breakdown": {},
        }

    return {
        "total": total_items,
        "filtered": total_items,
        "applications": int(row.applications) if row.applications is not None else 0,
        "servers": int(row.servers) if row.servers is not None else 0,
        "databases": int(row.databases) if row.databases is not None else 0,
        "components": int(row.components) if row.components is not None else 0,
        "network": int(row.network) if row.network is not None else 0,
        "storage": int(row.storage) if row.storage is not None else 0,
        "security": int(row.security) if row.security is not None else 0,
        "virtualization": (
            int(row.virtualization) if row.virtualization is not None else 0
        ),
        "containers": int(row.containers) if row.containers is not None else 0,
        "load_balancers": (
            int(row.load_balancers) if row.load_balancers is not None else 0
        ),
        "unknown": int(row.unknown) if row.unknown is not None else 0,
        "discovered": int(row.discovered) if row.discovered is not None else 0,
        "pending": int(row.pending) if row.pending is not None else 0,
        "device_breakdown": {},
    }
