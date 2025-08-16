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

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Asset Pagination"])


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
            # Return empty placeholder response
            total_pages = 0
            return {
                "assets": [],
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": 0,
                    "total_pages": total_pages,
                    "has_next": False,
                    "has_previous": False,
                },
                "summary": {
                    "total": 0,
                    "filtered": 0,
                    "applications": 0,
                    "servers": 0,
                    "databases": 0,
                    "devices": 0,
                    "unknown": 0,
                    "discovered": 0,
                    "pending": 0,
                    "device_breakdown": {},
                },
                "last_updated": None,
                "data_source": "demo",
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
        logger.error(f"Error in paginated fallback endpoint: {e}")
        # Continue to fallback response below

    # Ensure we always return something - fallback response
    return {
        "assets": [],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_items": 0,
            "total_pages": 0,
            "has_next": False,
            "has_previous": False,
        },
        "summary": {
            "total": 0,
            "filtered": 0,
            "applications": 0,
            "servers": 0,
            "databases": 0,
            "devices": 0,
            "unknown": 0,
            "discovered": 0,
            "pending": 0,
            "device_breakdown": {},
        },
        "last_updated": None,
        "data_source": "fallback",
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


@router.get("/list/paginated")
async def list_assets_paginated(
    db: AsyncSession = Depends(get_db_for_asset_list),
    context: RequestContext = Depends(get_current_context),
    page: int = Query(1, gt=0),
    page_size: int = Query(20, gt=0, le=100),
    per_page: int = Query(None),  # Support both page_size and per_page
):
    """Get paginated list of assets for the current context."""
    try:
        # Support both page_size and per_page parameters
        if per_page is not None:
            page_size = per_page

        # Import here to avoid circular imports
        from sqlalchemy import func, select

        from app.models.asset import Asset

        # Build base query with context filtering
        # SECURITY: Always enforce multi-tenancy - no platform admin bypass for regular users
        # Regular users see only their context assets
        query = (
            select(Asset)
            .where(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
            .order_by(Asset.created_at.desc())
        )

        # Get total count with proper context filtering
        count_query = (
            select(func.count())
            .select_from(Asset)
            .where(
                Asset.client_account_id == context.client_account_id,
                Asset.engagement_id == context.engagement_id,
            )
        )
        count_result = await db.execute(count_query)
        total_items = count_result.scalar() or 0

        # Calculate pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await db.execute(query)
        assets = result.scalars().all()

        # Calculate totals
        total_pages = (
            (total_items + page_size - 1) // page_size if total_items > 0 else 0
        )

        # Build response - optimize by pre-calculating summary stats
        # Convert assets to dicts first to avoid multiple attribute access
        asset_dicts = []
        for asset in assets:
            asset_dicts.append(
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "environment": asset.environment,
                    "criticality": asset.criticality,
                    "status": asset.status,
                    "six_r_strategy": asset.six_r_strategy,
                    "migration_wave": asset.migration_wave,
                    "application_name": asset.application_name,
                    "hostname": asset.hostname,
                    "operating_system": asset.operating_system,
                    "cpu_cores": asset.cpu_cores,
                    "memory_gb": asset.memory_gb,
                    "storage_gb": asset.storage_gb,
                    "created_at": (
                        asset.created_at.isoformat() if asset.created_at else None
                    ),
                    "updated_at": (
                        asset.updated_at.isoformat() if asset.updated_at else None
                    ),
                }
            )

        # Calculate summary stats efficiently using the dictionaries
        summary_stats = {
            "total": total_items,
            "filtered": total_items,
            "applications": 0,
            "servers": 0,
            "databases": 0,
            "devices": 0,
            "unknown": 0,
            "discovered": 0,
            "pending": 0,
            "device_breakdown": {},
        }

        # Debug logging to understand asset types
        logger.info(f"🔍 Asset Inventory Debug: Found {len(asset_dicts)} assets")
        asset_types_found = {}
        unclassified_count = 0
        for asset_dict in asset_dicts:
            asset_type = asset_dict.get("asset_type")
            if asset_type:
                asset_types_found[asset_type] = asset_types_found.get(asset_type, 0) + 1
            else:
                unclassified_count += 1
        logger.info(f"🔍 Asset types in database: {asset_types_found}")
        logger.info(f"🔍 Unclassified assets: {unclassified_count}")

        # Check if assets need CrewAI classification
        needs_classification = (
            unclassified_count > 0
            or len(asset_types_found) == 0
            or all(
                asset_type in ["unknown", "other", None]
                for asset_type in asset_types_found.keys()
            )
        )

        if needs_classification and len(asset_dicts) > 0:
            logger.warning(
                f"🚨 Assets need CrewAI classification: {unclassified_count} unclassified, types found: {asset_types_found}"
            )
            # Add a header to indicate assets need classification
            # Note: The actual classification will be triggered by the frontend refresh button

        # Single pass through assets for counting
        for asset_dict in asset_dicts:
            asset_type = (asset_dict.get("asset_type") or "").lower()
            status = asset_dict.get("status")

            if asset_type == "application":
                summary_stats["applications"] += 1
            elif asset_type == "server":
                summary_stats["servers"] += 1
            elif asset_type == "database":
                summary_stats["databases"] += 1
            elif any(
                term in asset_type
                for term in [
                    "device",
                    "network",
                    "storage",
                    "security",
                    "infrastructure",
                ]
            ):
                summary_stats["devices"] += 1
            elif not asset_type or asset_type == "unknown":
                summary_stats["unknown"] += 1

            if status == "discovered":
                summary_stats["discovered"] += 1
            elif status == "pending":
                summary_stats["pending"] += 1

        # Find last updated efficiently
        last_updated = None
        for asset_dict in asset_dicts:
            if asset_dict.get("updated_at") and (
                not last_updated or asset_dict["updated_at"] > last_updated
            ):
                last_updated = asset_dict["updated_at"]

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
        # Return empty result on error
        return {
            "assets": [],
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": 0,
                "total_pages": 0,
                "has_next": False,
                "has_previous": False,
            },
            "summary": {
                "total": 0,
                "filtered": 0,
                "applications": 0,
                "servers": 0,
                "databases": 0,
                "devices": 0,
                "unknown": 0,
                "discovered": 0,
                "pending": 0,
                "device_breakdown": {},
            },
            "last_updated": None,
            "data_source": "error",
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
