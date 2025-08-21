"""
Asset Management Handlers for Unified Discovery

Handles asset listing and summary operations within the unified discovery context.
Extracted from the main unified_discovery.py file for better maintainability.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format

# Import the asset list handler
from app.services.unified_discovery_handlers.asset_list_handler import (
    create_asset_list_handler,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/assets")
async def list_assets(
    page_size: int = Query(50, ge=1, le=200, description="Number of assets per page"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    status_filter: Optional[str] = Query(None, description="Filter by asset status"),
    flow_id: Optional[str] = Query(None, description="Filter by discovery flow ID"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    List assets with tenant isolation and pagination support.

    This endpoint provides asset listing functionality within the unified discovery
    context, following the established modular handler pattern.

    Features:
    - Tenant-scoped queries (client_account_id, engagement_id)
    - Pagination with configurable page sizes
    - Optional filtering by asset type, status, and flow ID
    - Fallback behavior for resilience
    - Comprehensive error handling and logging
    """
    try:
        # Create asset list handler following the modular pattern
        asset_handler = await create_asset_list_handler(db, context)

        # Execute asset listing with provided parameters
        result = await asset_handler.list_assets(
            page_size=page_size,
            page=page,
            asset_type=asset_type,
            status_filter=status_filter,
            flow_id=flow_id,
        )

        logger.info(
            safe_log_format(
                "Asset listing request completed: {success}, assets returned: {count}",
                success=result["success"],
                count=len(result.get("assets", [])),
            )
        )

        return result

    except Exception as e:
        logger.error(
            safe_log_format(
                "Asset listing endpoint failed: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list assets: {str(e)}",
        )


@router.get("/assets/summary")
async def get_assets_summary(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get asset summary statistics for the current tenant context.

    Provides overview information about assets including:
    - Total asset count
    - Asset type distribution
    - Status distribution
    """
    try:
        # Create asset list handler
        asset_handler = await create_asset_list_handler(db, context)

        # Get asset summary
        result = await asset_handler.get_asset_summary()

        logger.info(
            safe_log_format(
                "Asset summary request completed: {success}",
                success=result["success"],
            )
        )

        return result

    except Exception as e:
        logger.error(
            safe_log_format(
                "Asset summary endpoint failed: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get asset summary: {str(e)}",
        )
