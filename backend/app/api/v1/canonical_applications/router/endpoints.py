"""
API route handlers for canonical applications.

Endpoints for listing applications, mapping assets, and querying readiness status.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.asset.models import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)

from .models import MapAssetRequest, MapAssetResponse
from .queries import (
    calculate_readiness_metadata,
    get_readiness_stats,
    get_unmapped_assets,
)

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
    include_unmapped_assets: bool = Query(
        False,
        description="Include assets not of type 'application' (databases, servers, network devices, etc.)",
    ),
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

    **UNMAPPED ASSETS** (when include_unmapped_assets=true):
    - Also returns assets where asset_type != "application" (databases, servers, network devices)
    - Each unmapped asset includes:
      - is_unmapped_asset: true (flag to differentiate from canonical apps)
      - asset_id: The actual asset UUID
      - asset_name: Asset name
      - asset_type: database, server, network, etc.
      - mapped_to_application_id: UUID if already mapped to canonical app
      - mapped_to_application_name: Name if already mapped
      - discovery_status: Asset discovery status
      - assessment_readiness: Asset readiness status

    Query Parameters:
        - search: Optional substring search (canonical_name or normalized_name, or asset_name for unmapped)
        - page: Page number starting from 1
        - page_size: Items per page (1-100, default 50)
        - include_unmapped_assets: Include non-application assets (default false)

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
                },
                {
                    "is_unmapped_asset": true,
                    "asset_id": "uuid",
                    "asset_name": "DB-Server-01",
                    "asset_type": "database",
                    "mapped_to_application_id": "uuid" | null,
                    "mapped_to_application_name": "MyApp" | null,
                    "discovery_status": "completed",
                    "assessment_readiness": "ready"
                }
            ],
            "total": int,
            "canonical_apps_count": int,
            "unmapped_assets_count": int,
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

        # Calculate pagination offset
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
        readiness_map = await get_readiness_stats(
            db, app_ids, client_account_id, engagement_id
        )

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

            # Calculate readiness status, blockers, recommendations
            readiness_status, blockers, recommendations = calculate_readiness_metadata(
                linked_count, ready_count
            )

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

        # Fetch unmapped assets if requested
        unmapped_assets_data = []
        unmapped_total = 0

        if include_unmapped_assets:
            unmapped_assets_data, unmapped_total = await get_unmapped_assets(
                db, client_account_id, engagement_id, search
            )

        # Combine canonical apps and unmapped assets
        combined_data = applications_data + unmapped_assets_data
        combined_total = total + unmapped_total
        combined_total_pages = (
            (combined_total + page_size - 1) // page_size if combined_total > 0 else 0
        )

        return {
            "applications": combined_data,
            "total": combined_total,
            "canonical_apps_count": len(applications_data),
            "unmapped_assets_count": len(unmapped_assets_data),
            "page": page,
            "page_size": page_size,
            "total_pages": combined_total_pages,
        }

    except Exception as e:
        logger.error(f"Failed to list canonical applications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve canonical applications: {str(e)}",
        )


@router.post("/map-asset", response_model=MapAssetResponse)
async def map_asset_to_application(
    request: MapAssetRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> MapAssetResponse:
    """
    Map an asset to a canonical application.

    Creates a record in CollectionFlowApplication junction table to link
    the asset to the canonical application. This enables:
    - Including the asset in application-level assessments
    - Tracking asset dependencies within the application context
    - Better data association for collection flows

    Args:
        request: Mapping request with asset_id and canonical_application_id
        db: Database session
        context: Request context with tenant info

    Returns:
        Success status and created mapping ID

    Raises:
        HTTPException 400: If asset or application not found or invalid UUID
        HTTPException 409: If mapping already exists (idempotent - returns existing)
    """
    try:
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and engagement ID required"
            )

        # Convert string UUIDs to UUID objects
        try:
            asset_uuid = UUID(request.asset_id)
            canonical_app_uuid = UUID(request.canonical_application_id)
            collection_flow_uuid = (
                UUID(request.collection_flow_id) if request.collection_flow_id else None
            )
        except (ValueError, TypeError) as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid UUID format: {str(e)}"
            )

        # Validate asset exists and belongs to tenant
        asset_query = select(Asset).where(
            Asset.id == asset_uuid,
            Asset.client_account_id == client_account_id,
            Asset.engagement_id == engagement_id,
        )
        asset_result = await db.execute(asset_query)
        asset = asset_result.scalar_one_or_none()

        if not asset:
            raise HTTPException(
                status_code=404,
                detail=f"Asset {request.asset_id} not found or access denied",
            )

        # Validate canonical application exists and belongs to tenant
        app_query = select(CanonicalApplication).where(
            CanonicalApplication.id == canonical_app_uuid,
            CanonicalApplication.client_account_id == client_account_id,
            CanonicalApplication.engagement_id == engagement_id,
        )
        app_result = await db.execute(app_query)
        canonical_app = app_result.scalar_one_or_none()

        if not canonical_app:
            raise HTTPException(
                status_code=404,
                detail=f"Canonical application {request.canonical_application_id} not found or access denied",
            )

        # Check if mapping already exists
        existing_mapping_query = select(CollectionFlowApplication).where(
            CollectionFlowApplication.asset_id == asset_uuid,
            CollectionFlowApplication.canonical_application_id == canonical_app_uuid,
            CollectionFlowApplication.client_account_id == client_account_id,
            CollectionFlowApplication.engagement_id == engagement_id,
        )
        existing_mapping_result = await db.execute(existing_mapping_query)
        existing_mapping = existing_mapping_result.scalar_one_or_none()

        if existing_mapping:
            # Mapping already exists - return success (idempotent)
            logger.info(
                f"Mapping already exists: asset {request.asset_id} → app {request.canonical_application_id}"
            )
            return MapAssetResponse(
                success=True,
                message=f"Asset '{asset.name}' is already mapped to application '{canonical_app.canonical_name}'",
                mapping_id=str(existing_mapping.id),
            )

        # Create new mapping
        new_mapping = CollectionFlowApplication(
            id=uuid.uuid4(),
            asset_id=asset_uuid,
            canonical_application_id=canonical_app_uuid,
            collection_flow_id=collection_flow_uuid,
            application_name=canonical_app.canonical_name,  # Legacy field for backward compatibility
            client_account_id=UUID(str(client_account_id)),
            engagement_id=UUID(str(engagement_id)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(new_mapping)
        await db.commit()
        await db.refresh(new_mapping)

        logger.info(
            f"✅ Created mapping: asset '{asset.name}' ({request.asset_id}) → "
            f"application '{canonical_app.canonical_name}' ({request.canonical_application_id})"
        )

        return MapAssetResponse(
            success=True,
            message=f"Successfully mapped asset '{asset.name}' to application '{canonical_app.canonical_name}'",
            mapping_id=str(new_mapping.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to map asset to application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to create mapping: {str(e)}"
        )
