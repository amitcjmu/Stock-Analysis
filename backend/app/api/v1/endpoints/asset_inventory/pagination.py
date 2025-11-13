"""
Asset paginated listing endpoints.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.context import RequestContext, get_current_context
from app.core.database_timeout import get_db_for_asset_list

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


def _create_empty_response(
    page: int, page_size: int, data_source: str = "fallback"
) -> Dict[str, Any]:
    """Create standardized empty response structure."""
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
        "data_source": data_source,
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


def _convert_assets_to_dicts(assets) -> List[Dict[str, Any]]:
    """Convert SQLAlchemy asset objects to dictionaries."""
    asset_dicts = []
    for asset in assets:
        asset_dict = {
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
            "created_at": (asset.created_at.isoformat() if asset.created_at else None),
            "updated_at": (asset.updated_at.isoformat() if asset.updated_at else None),
            # CMDB Enhancement Fields (Issue #833)
            "business_unit": asset.business_unit,
            "vendor": asset.vendor,
            "application_type": asset.application_type,
            "lifecycle": asset.lifecycle,
            "hosting_model": asset.hosting_model,
            "server_role": asset.server_role,
            "security_zone": asset.security_zone,
            "database_type": asset.database_type,
            "database_version": asset.database_version,
            "database_size_gb": asset.database_size_gb,
            "cpu_utilization_percent_max": asset.cpu_utilization_percent_max,
            "memory_utilization_percent_max": asset.memory_utilization_percent_max,
            "storage_free_gb": asset.storage_free_gb,
            "storage_used_gb": asset.storage_used_gb,
            "tech_debt_flags": asset.tech_debt_flags,
            "pii_flag": asset.pii_flag,
            "application_data_classification": asset.application_data_classification,
            "has_saas_replacement": asset.has_saas_replacement,
            "risk_level": asset.risk_level,
            "tshirt_size": asset.tshirt_size,
            "proposed_treatmentplan_rationale": asset.proposed_treatmentplan_rationale,
            "annual_cost_estimate": asset.annual_cost_estimate,
            "backup_policy": asset.backup_policy,
            "asset_tags": asset.asset_tags,
            # Child table relationships
            "contacts": (
                [c.to_dict() for c in asset.contacts]
                if hasattr(asset, "contacts") and asset.contacts
                else []
            ),
            "eol_assessments": (
                [e.to_dict() for e in asset.eol_assessments]
                if hasattr(asset, "eol_assessments") and asset.eol_assessments
                else []
            ),
        }
        asset_dicts.append(asset_dict)
    return asset_dicts


def _analyze_asset_types(
    asset_dicts: List[Dict[str, Any]],
) -> Tuple[Dict[str, int], int, bool]:
    """Analyze asset types and determine if classification is needed."""
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
            f"🚨 Assets need CrewAI classification: {unclassified_count} unclassified, "
            f"types found: {asset_types_found}"
        )

    return asset_types_found, unclassified_count, needs_classification


def _calculate_summary_stats(
    asset_dicts: List[Dict[str, Any]], total_items: int
) -> Dict[str, Any]:
    """Calculate summary statistics for assets."""
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

    device_terms = ["device", "network", "storage", "security", "infrastructure"]

    for asset_dict in asset_dicts:
        asset_type = (asset_dict.get("asset_type") or "").lower()
        status = asset_dict.get("status")

        # Count by asset type
        if asset_type == "application":
            summary_stats["applications"] += 1
        elif asset_type == "server":
            summary_stats["servers"] += 1
        elif asset_type == "database":
            summary_stats["databases"] += 1
        elif any(term in asset_type for term in device_terms):
            summary_stats["devices"] += 1
        elif not asset_type or asset_type == "unknown":
            summary_stats["unknown"] += 1

        # Count by status
        if status == "discovered":
            summary_stats["discovered"] += 1
        elif status == "pending":
            summary_stats["pending"] += 1

    return summary_stats


def _find_last_updated(asset_dicts: List[Dict[str, Any]]) -> Optional[str]:
    """Find the most recent updated_at timestamp."""
    last_updated = None
    for asset_dict in asset_dicts:
        updated_at = asset_dict.get("updated_at")
        if updated_at and (not last_updated or updated_at > last_updated):
            last_updated = updated_at
    return last_updated


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
    """
    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload
    from app.models.asset import Asset

    # Build filter conditions once (DRY principle)
    # SECURITY: Always enforce multi-tenancy - no platform admin bypass for regular users
    filter_conditions = [
        Asset.client_account_id == context.client_account_id,
        Asset.engagement_id == context.engagement_id,
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

    return assets, total_items, total_pages


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

        # Calculate summary statistics
        summary_stats = _calculate_summary_stats(asset_dicts, total_items)

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
