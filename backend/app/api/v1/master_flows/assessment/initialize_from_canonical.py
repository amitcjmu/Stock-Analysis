"""
Initialize Assessment from Canonical Applications Endpoint

Allows users to start assessments directly from canonical applications,
breaking the collection→assessment circular dependency (GPT-5 suggestion).

Per ADR-027 and Phase 2 architecture requirements.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.asset import Asset

logger = logging.getLogger(__name__)

router = APIRouter()


class InitializeFromCanonicalRequest(BaseModel):
    """Request model for initializing assessment from canonical applications"""

    canonical_application_ids: List[str] = Field(
        ...,
        min_items=1,
        description="List of canonical application UUIDs (min 1 required)",
    )
    optional_collection_flow_id: Optional[str] = Field(
        None,
        description="Optional collection flow ID for traceability",
    )


class InitializeFromCanonicalResponse(BaseModel):
    """Response model for canonical app initialization"""

    flow_id: str = Field(..., description="Created assessment flow UUID")
    master_flow_id: str = Field(..., description="Master flow UUID (same as flow_id)")
    application_groups: List[Dict[str, Any]] = Field(
        ..., description="Resolved application-asset groups"
    )
    total_assets: int = Field(..., description="Total number of assets across all apps")
    unmapped_applications: int = Field(
        ..., description="Count of apps with 0 assets (zero-asset apps)"
    )


@router.post(
    "/new/assessment/initialize-from-canonical",
    response_model=InitializeFromCanonicalResponse,
    summary="Initialize Assessment from Canonical Applications",
    description="""
    Creates a new assessment flow by starting from canonical applications
    instead of requiring a completed collection flow.

    This endpoint:
    1. Validates canonical_application_ids exist and match tenant context
    2. Resolves assets for each canonical app via collection_flow_applications table
    3. Creates assessment flow with resolved asset IDs
    4. Returns application groups with enrichment/readiness metadata

    Supports zero-asset applications (canonical apps with no mapped assets).
    """,
)
async def initialize_assessment_from_canonical(
    request: InitializeFromCanonicalRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> InitializeFromCanonicalResponse:
    """
    Initialize assessment flow directly from canonical applications.

    Breaking collection→assessment circular dependency by allowing users
    to start assessments from canonical app registry without full collection.
    """
    client_account_id = context.client_account_id
    engagement_id = context.engagement_id

    if not client_account_id or not engagement_id:
        raise HTTPException(
            status_code=400,
            detail="Client account ID and engagement ID required",
        )

    # Step 1: Validate canonical_application_ids
    canonical_app_uuids = await _validate_canonical_apps(
        db=db,
        canonical_app_ids=request.canonical_application_ids,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Step 2: Resolve assets for each canonical app
    resolved_assets_map = await _resolve_assets_from_canonical_apps(
        db=db,
        canonical_app_uuids=canonical_app_uuids,
        optional_collection_flow_id=request.optional_collection_flow_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )

    # Step 3: Flatten asset IDs for flow creation
    all_asset_ids = []
    for assets in resolved_assets_map.values():
        all_asset_ids.extend(assets)

    # Log warning for zero-asset apps
    unmapped_count = sum(
        1 for assets in resolved_assets_map.values() if len(assets) == 0
    )
    if unmapped_count > 0:
        logger.warning(
            f"Assessment initialization has {unmapped_count} canonical apps "
            f"with 0 assets. These will create empty application groups."
        )

    # Step 4: Create assessment flow using existing service
    from app.services.assessment.application_resolver import (
        AssessmentApplicationResolver,
    )

    resolver = AssessmentApplicationResolver(
        db=db,
        client_account_id=UUID(str(client_account_id)),
        engagement_id=UUID(str(engagement_id)),
    )

    # Compute application groups (handles zero-asset apps gracefully)
    application_groups = await resolver.resolve_assets_to_applications(
        asset_ids=all_asset_ids,
        collection_flow_id=(
            UUID(request.optional_collection_flow_id)
            if request.optional_collection_flow_id
            else None
        ),
    )

    # Step 5: Use existing FlowCommands.create_assessment_flow
    from app.repositories.assessment_flow_repository import AssessmentFlowRepository

    repo = AssessmentFlowRepository(
        db=db,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=context.user_id,
    )

    # Create flow with asset IDs (backward compatible field name)
    flow_id = await repo.create_assessment_flow(
        engagement_id=str(engagement_id),
        selected_application_ids=[str(aid) for aid in all_asset_ids],
        created_by=context.user_id,
    )

    # Step 6: Update flow metadata with traceability info
    await _update_flow_metadata(
        db=db,
        flow_id=flow_id,
        canonical_app_ids=request.canonical_application_ids,
        optional_collection_flow_id=request.optional_collection_flow_id,
    )

    # Step 7: Convert application groups to dict for response
    app_groups_dict = [group.dict() for group in application_groups]

    logger.info(
        f"Created assessment flow {flow_id} from {len(canonical_app_uuids)} "
        f"canonical apps with {len(all_asset_ids)} total assets "
        f"({unmapped_count} apps with 0 assets)"
    )

    return InitializeFromCanonicalResponse(
        flow_id=flow_id,
        master_flow_id=flow_id,  # Same as flow_id per MFO pattern
        application_groups=app_groups_dict,
        total_assets=len(all_asset_ids),
        unmapped_applications=unmapped_count,
    )


async def _validate_canonical_apps(
    db: AsyncSession,
    canonical_app_ids: List[str],
    client_account_id: int,
    engagement_id: int,
) -> List[UUID]:
    """
    Validate that all canonical_application_ids exist and match tenant.

    Args:
        db: Database session
        canonical_app_ids: List of canonical app UUID strings
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        List of validated canonical app UUIDs

    Raises:
        HTTPException: If any IDs are invalid or don't match tenant
    """
    try:
        canonical_app_uuids = [UUID(cid) for cid in canonical_app_ids]
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid canonical_application_id format: {str(e)}",
        )

    # Query canonical apps with tenant scoping
    query = select(CanonicalApplication).where(
        CanonicalApplication.id.in_(canonical_app_uuids),
        CanonicalApplication.client_account_id == client_account_id,
        CanonicalApplication.engagement_id == engagement_id,
    )

    result = await db.execute(query)
    found_apps = result.scalars().all()

    # Verify all requested apps exist
    if len(found_apps) != len(canonical_app_uuids):
        found_ids = {str(app.id) for app in found_apps}
        missing_ids = [
            str(cid) for cid in canonical_app_uuids if str(cid) not in found_ids
        ]
        raise HTTPException(
            status_code=404,
            detail=f"Canonical applications not found or access denied: {missing_ids}",
        )

    return canonical_app_uuids


async def _resolve_assets_from_canonical_apps(
    db: AsyncSession,
    canonical_app_uuids: List[UUID],
    optional_collection_flow_id: Optional[str],
    client_account_id: int,
    engagement_id: int,
) -> Dict[UUID, List[UUID]]:
    """
    Resolve asset IDs for each canonical application.

    Uses CollectionFlowApplication junction table to find assets
    linked to each canonical app. Supports zero-asset apps.

    Args:
        db: Database session
        canonical_app_uuids: List of canonical app UUIDs
        optional_collection_flow_id: Optional collection flow for scoping
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        Dict mapping canonical_app_id → [asset_ids]
    """
    # Build query with tenant scoping
    query = select(
        CollectionFlowApplication.canonical_application_id,
        CollectionFlowApplication.asset_id,
    ).where(
        CollectionFlowApplication.canonical_application_id.in_(canonical_app_uuids),
        CollectionFlowApplication.client_account_id == client_account_id,
        CollectionFlowApplication.engagement_id == engagement_id,
    )

    # Optional: Filter by collection flow if provided
    if optional_collection_flow_id:
        try:
            collection_flow_uuid = UUID(optional_collection_flow_id)
            query = query.where(
                CollectionFlowApplication.collection_flow_id == collection_flow_uuid
            )
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid optional_collection_flow_id: {optional_collection_flow_id}"
            )

    result = await db.execute(query)
    rows = result.all()

    # Group assets by canonical app (including zero-asset apps)
    assets_map: Dict[UUID, List[UUID]] = {
        canonical_id: [] for canonical_id in canonical_app_uuids
    }

    for row in rows:
        canonical_id = row.canonical_application_id
        asset_id = row.asset_id

        if canonical_id in assets_map and asset_id:
            # Verify asset exists and matches tenant
            asset_query = select(Asset.id).where(
                Asset.id == asset_id,
                Asset.client_account_id == client_account_id,
                Asset.engagement_id == engagement_id,
            )
            asset_result = await db.execute(asset_query)
            if asset_result.scalar_one_or_none():
                assets_map[canonical_id].append(asset_id)

    return assets_map


async def _update_flow_metadata(
    db: AsyncSession,
    flow_id: str,
    canonical_app_ids: List[str],
    optional_collection_flow_id: Optional[str],
):
    """
    Update assessment flow metadata with traceability info.

    Stores initialization_method and canonical_application_ids for auditability.
    """
    from app.models.assessment_flow import AssessmentFlow
    from sqlalchemy import update

    metadata_update = {
        "source_collection": optional_collection_flow_id,
        "initialization_method": "canonical_applications",
        "canonical_application_ids": canonical_app_ids,
    }

    await db.execute(
        update(AssessmentFlow)
        .where(AssessmentFlow.id == UUID(flow_id))
        .values(configuration=AssessmentFlow.configuration.concat(metadata_update))
    )
    await db.commit()
