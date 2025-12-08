"""
Asset paginated listing endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.context import RequestContext, get_current_context
from app.core.database_timeout import get_db_for_asset_list

from .pagination_queries import _get_assets_from_db, _get_summary_stats_from_db
from .pagination_utils import (
    _analyze_asset_types,
    _convert_assets_to_dicts,
    _create_empty_response,
    _find_last_updated,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/list/paginated-fallback")
async def list_assets_paginated_fallback(
    page: int = 1,
    page_size: int = 50,
    db: Optional[Session] = Depends(get_db_for_asset_list),
    context: RequestContext = Depends(get_current_context),
):
    """Lightweight fallback that returns an empty asset list when DB or context unavailable."""
    try:
        if db is None or context.client_account_id is None:
            return _create_empty_response(page, page_size, "demo")
    except Exception as e:
        logger.error(f"Error in paginated fallback endpoint: {e}")

    return _create_empty_response(page, page_size, "fallback")


@router.get("/list/paginated")
async def list_assets_paginated(
    db: AsyncSession = Depends(get_db_for_asset_list),
    context: RequestContext = Depends(get_current_context),
    page: int = Query(1, gt=0),
    page_size: int = Query(20, gt=0, le=100),
    per_page: int = Query(None),  # Support both page_size and per_page
    flow_id: Optional[str] = Query(
        None,
        description="Optional discovery flow ID to filter assets. "
        "Uses Optional[str] instead of UUID4 for flexibility: "
        "(1) Frontend validation in useDiscoveryFlowAutoDetection ensures UUID v4 format, "
        "(2) Allows graceful error messages for invalid formats, "
        "(3) Maintains backward compatibility with non-UUID flow IDs, "
        "(4) SQLAlchemy safely handles type conversion for database queries.",
    ),
    search: Optional[str] = Query(
        None, description="Search assets by name (case-insensitive)"
    ),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    business_criticality: Optional[str] = Query(
        None, description="Filter by business criticality"
    ),
):
    """Get paginated list of assets for the current context.

    Args:
        db: Database session
        context: Request context with tenant information
        page: Page number (1-indexed)
        page_size: Number of items per page
        per_page: Alternative parameter for page_size (for compatibility)
        flow_id: Optional discovery flow ID to filter assets by specific flow

    Returns:
        Paginated asset list with summary statistics
    """
    try:
        # Support both page_size and per_page parameters
        if per_page is not None:
            page_size = per_page

        # Fetch assets from database with optional filters
        assets, total_items, total_pages = await _get_assets_from_db(
            db,
            context,
            page,
            page_size,
            flow_id,
            search,
            environment,
            business_criticality,
        )

        # Convert assets to dictionaries
        asset_dicts = _convert_assets_to_dicts(assets)

        # Analyze asset types and classification needs
        asset_types_found, unclassified_count, needs_classification = (
            _analyze_asset_types(asset_dicts)
        )

        # Calculate summary statistics from ALL assets (not just current page)
        summary_stats = await _get_summary_stats_from_db(
            db, context, total_items, flow_id, search, environment, business_criticality
        )

        # Find last updated timestamp
        last_updated = _find_last_updated(asset_dicts)

        return {
            "assets": asset_dicts,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "summary": summary_stats,
            "needs_classification": needs_classification,
            "last_updated": last_updated,
            "data_source": "database",
            "suggested_headers": [],
            "app_mappings": [],
            "unlinked_assets": [],
            "unlinked_summary": {
                "total_unlinked": 0,
                "by_type": {},
                "by_environment": {},
                "by_criticality": {},
                "migration_impact": "none",
            },
        }

    except Exception as e:
        logger.error(f"Error in list_assets_paginated: {e}")
        return _create_empty_response(page, page_size, "error")
